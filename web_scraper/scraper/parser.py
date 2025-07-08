import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from .utils import cdn_domains, is_cdn

def fetch_with_browser(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
        except PlaywrightTimeoutError as e:
            print(f"[警告] 页面加载超时: {url}，将返回部分内容")
        content = page.content()
        browser.close()
        return content

def download_resource(url, base_url, output_dir, subdir, filename=None, skip_cdn=True, cookies=None, use_browser_fallback=False):
    """
    下載資源，支援自訂 headers、cookie，並加強反爬蟲對策與錯誤日誌。
    若 use_browser_fallback=True，requests 失敗時會用 Playwright 真實瀏覽器嘗試抓取 HTML/text。
    """
    if skip_cdn and is_cdn(url):
        print(f"跳过CDN资源: {url}")
        return None
    if not filename:
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = 'unnamed'
    local_dir = os.path.join(output_dir, subdir)
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, filename)
    # 如果本地已存在该文件，直接返回
    if os.path.exists(local_path):
        print(f"本地已存在，无需重复下载: {local_path}")
        return os.path.join(subdir, filename)
    try:
        base_parsed = urlparse(base_url)
        referer = f"{base_parsed.scheme}://{base_parsed.netloc}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.129 Safari/537.36",
            "Referer": referer,
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1"
        }
        session = requests.Session()
        if cookies:
            session.cookies.update(cookies)
        res = session.get(url, headers=headers, timeout=10)
        print(f"请求资源: {url} 状态码: {res.status_code}")
        if res.status_code == 404 or res.status_code == 403 or (res.status_code == 200 and not res.content):
            print(f"资源下载失败: {url} 状态码: {res.status_code}，嘗試 Playwright..." if use_browser_fallback else f"资源下载失败: {url} 状态码: {res.status_code}")
            # 只對 HTML/text 類型用 Playwright
            if use_browser_fallback and (filename.endswith('.html') or filename.endswith('.htm') or filename.endswith('.txt') or '.' not in filename):
                html = fetch_with_browser(url)
                if html:
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"[Playwright] 已下載 HTML: {url} → {local_path}")
                    return os.path.join(subdir, filename)
                else:
                    print(f"[Playwright] 仍然無法下載: {url}")
                    return None
            return None
        if res.status_code != 200:
            print(f"资源下载失败: {url} 状态码: {res.status_code}")
            return None
        # 判斷是否為二進位檔（圖片、PDF等）
        mode = 'wb' if not (filename.endswith('.html') or filename.endswith('.htm') or filename.endswith('.txt') or '.' not in filename) else 'w'
        if mode == 'wb':
            with open(local_path, mode) as f:
                f.write(res.content)
        else:
            with open(local_path, mode, encoding='utf-8') as f:
                f.write(res.text)
        print(f"已下载资源: {url} → {local_path}")
        return os.path.join(subdir, filename)
    except requests.exceptions.RequestException as e:
        print(f"资源下载异常: {url} - {e}")
        if use_browser_fallback and (filename.endswith('.html') or filename.endswith('.htm') or filename.endswith('.txt') or '.' not in filename):
            html = fetch_with_browser(url)
            if html:
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"[Playwright] 已下載 HTML: {url} → {local_path}")
                return os.path.join(subdir, filename)
            else:
                print(f"[Playwright] 仍然無法下載: {url}")
                return None
        return None
    except Exception as e:
        print(f"未知异常: {url} - {e}")
        return None

def parse_page_and_download_images(html, base_url, output_dir):
    soup = BeautifulSoup(html, 'html.parser')
    os.makedirs(output_dir, exist_ok=True)

    # 下载图片
    for img in soup.find_all('img'):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if not src and img.get("srcset"):
            src = img["srcset"].split(",")[0].split()[0]
        if not src:
            continue
        img_url = urljoin(base_url, src)
        rel_path = download_resource(img_url, base_url, output_dir, 'images')
        if rel_path:
            img['src'] = rel_path

    # 处理 style 标签和 style 属性中的 background-image URL
    css_url_pattern = re.compile(r'url\((.*?)\)')
    def download_and_replace_css_images(style_str):
        matches = css_url_pattern.findall(style_str)
        for match in matches:
            clean_url = match.strip('\'" ')
            full_url = urljoin(base_url, clean_url)
            rel_path = download_resource(full_url, base_url, output_dir, 'images')
            if rel_path:
                style_str = style_str.replace(match, rel_path)
        return style_str
    for tag in soup.find_all(style=True):
        tag["style"] = download_and_replace_css_images(tag["style"])
    for style_tag in soup.find_all("style"):
        if style_tag.string:
            style_tag.string.replace_with(download_and_replace_css_images(style_tag.string))

    # 下载并解析 CSS 文件及其背景图
    for link_tag in soup.find_all("link", rel=lambda v: v and "stylesheet" in v.lower()):
        href = link_tag.get("href")
        if not href:
            continue
        css_url = urljoin(base_url, href)
        rel_path = download_resource(css_url, base_url, output_dir, 'css')
        if rel_path:
            link_tag["href"] = rel_path
            # 解析CSS内容中的图片
            try:
                with open(os.path.join(output_dir, rel_path), encoding="utf-8") as f:
                    css_text = f.read()
                matches = css_url_pattern.findall(css_text)
                for match in matches:
                    clean_url = match.strip('\'" ')
                    full_url = urljoin(css_url, clean_url)
                    download_resource(full_url, base_url, output_dir, 'images')
            except Exception as e:
                print(f"CSS内容解析失败: {css_url} - {e}")

    # 下载并解析 JS 文件及其引用资源
    for script_tag in soup.find_all("script", src=True):
        js_href = script_tag.get("src")
        if not js_href:
            continue
        js_url = urljoin(base_url, js_href)
        rel_path = download_resource(js_url, base_url, output_dir, 'js')
        if rel_path:
            script_tag["src"] = rel_path
            # 解析JS内容中的图片/资源
            try:
                with open(os.path.join(output_dir, rel_path), encoding="utf-8") as f:
                    js_text = f.read()
                matches = css_url_pattern.findall(js_text)
                for match in matches:
                    clean_url = match.strip('\'" ')
                    full_url = urljoin(js_url, clean_url)
                    download_resource(full_url, base_url, output_dir, 'images')
            except Exception as e:
                print(f"JS内容解析失败: {js_url} - {e}")

    # 下载 <video> 的 poster 图片
    for video in soup.find_all("video"):
        poster = video.get("poster")
        if not poster:
            continue
        full_url = urljoin(base_url, poster)
        rel_path = download_resource(full_url, base_url, output_dir, 'images')
        if rel_path:
            video["poster"] = rel_path

    # 下载 <object data="...">
    for obj in soup.find_all("object", data=True):
        obj_data = obj.get("data")
        full_url = urljoin(base_url, obj_data)
        rel_path = download_resource(full_url, base_url, output_dir, 'assets')
        if rel_path:
            obj["data"] = rel_path

    # 保存 <iframe srcdoc="..."> 内容为 HTML 文件
    for i, iframe in enumerate(soup.find_all("iframe", srcdoc=True)):
        srcdoc = iframe.get("srcdoc")
        if not srcdoc:
            continue
        filename = f"iframe_srcdoc_{i}.html"
        local_path = os.path.join(output_dir, "iframes", filename)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(srcdoc)
        iframe["srcdoc"] = ""
        iframe["src"] = os.path.join("iframes", filename)
        print(f"已保存 iframe srcdoc → {local_path}")

    # 保存 <iframe src="..."> 内容为本地 HTML
    for i, iframe in enumerate(soup.find_all("iframe", src=True)):
        iframe_src = iframe.get("src")
        if iframe_src and not iframe.get("srcdoc"):
            full_url = urljoin(base_url, iframe_src)
            if is_cdn(full_url):
                print(f"跳过CDN iframe: {full_url}")
                continue
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.129 Safari/537.36",
                    "Referer": base_url
                }
                res = requests.get(full_url, headers=headers, timeout=10)
                iframe_html = res.text
                # 递归解析 iframe 内容
                iframe_processed = parse_page_and_download_images(iframe_html, full_url, output_dir)
                filename = f"iframe_src_{i}.html"
                local_path = os.path.join(output_dir, "iframes", filename)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(iframe_processed)
                iframe["src"] = os.path.join("iframes", filename)
                print(f"已保存嵌套 iframe src: {full_url} → {local_path}")
            except Exception as e:
                print(f"嵌套 iframe src 抓取失败: {full_url} - {e}")

#     # 修改 offer_link 类的链接
#     for link in soup.find_all("a", class_="offer_link"):
#         if "uclick=xsb78rfe" in link.get("href", ""):
#             link["href"] = link["href"].replace("uclick=xsb78rfe", "uclick=")

#     # 添加 JavaScript 脚本
#     script = """
# <script>
#   function getUclick() {
#     const match = document.cookie.match(new RegExp("(?:^|; )uclick=([^;]*)"));
#     return match ? decodeURIComponent(match[1]) : "";
#   }

#   document.addEventListener("DOMContentLoaded", function () {
#     const uclick = getUclick();
#     if (!uclick) return;

#     document.querySelectorAll("a.offer_link").forEach(link => {
#       const url = new URL(link.href, window.location.origin);
#       url.searchParams.set("uclick", uclick);
#       link.href = url.pathname + url.search;
#     });
#   });
# </script>
# """
#    soup.body.append(BeautifulSoup(script, "html.parser"))

    return soup.prettify()

def save_html(html_str, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_str)
    print(f"HTML 保存成功：{output_path}")