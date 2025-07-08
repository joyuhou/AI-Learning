from playwright.sync_api import sync_playwright
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from .parser import download_resource
from .parser import parse_page_and_download_images
from .parser import save_html
from urllib.parse import urljoin, urlparse

def fetch_page_with_browser(url):
    content = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            # 清空cookie缓存
            context.clear_cookies()
            page = context.new_page()
            page.goto(url, timeout=60000)
            try:
                # 优先尝试 networkidle，失败则 fallback 到 load
                page.wait_for_load_state("networkidle", timeout=30000)
            except PlaywrightTimeoutError:
                print("[Warn] networkidle 超时，尝试 load 状态...")
                try:
                    page.wait_for_load_state("load", timeout=30000)
                except PlaywrightTimeoutError:
                    print("[Error] load 状态也超时，页面可能未完全加载。")
            content = page.content()
            browser.close()
    except Exception as e:
        print(f"[Exception] 抓取页面失败: {e}")
    return content

def fetch_page_with_resources_recursive(seed_url, offer_url, offer_url_2, replace_url, output_dir):
    visited = set()
    to_visit = [seed_url]

    idx = 0
    while to_visit:
        url = to_visit.pop(0)
        if url in visited or offer_url in url or offer_url_2 in url:
            continue
        print(f"Crawling {idx}: {url}")
        html_with_assets = fetch_page_with_resources(url,output_dir)

        # 替换offer_url为replace_url
        soup = BeautifulSoup(html_with_assets, 'html.parser')
        for a in soup.find_all('a', href=True):
            if offer_url in a['href'] or offer_url_2 in a['href']:
                a['href'] = replace_url
        html_with_assets = str(soup)

        parsed = parse_page_and_download_images(html_with_assets, url, output_dir)
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path.endswith('/') or path == '':
            filename = 'index.html'
        else:
            filename = os.path.basename(path)
        # 保证有.html后缀
        if not filename.endswith('.html'):
            filename = filename + '.html'
        local_dir = output_dir
        os.makedirs(local_dir, exist_ok=True)
        save_path = os.path.join(local_dir, filename)
        # 如果index.html已存在，自动重命名
        if filename == 'index.html' and os.path.exists(save_path):
            save_path = os.path.join(local_dir, f'index_{idx+1}.html')
        save_html(parsed, save_path)
        visited.add(url)
        idx += 1

        new_links = extract_internal_links(html_with_assets, url)
        for link in new_links:
            # 不爬取包含offer_url的链接
            if offer_url in link or offer_url_2 in link:
                continue
            if link not in visited and link not in to_visit:
                to_visit.append(link)



def fetch_page_with_resources(url, output_dir):
    html = fetch_page_with_browser(url)
    soup = BeautifulSoup(html, "html.parser")
    os.makedirs(output_dir, exist_ok=True)

    # 下载 CSS 文件
    for link_tag in soup.find_all("link", href=True):
        href = link_tag.get("href")
        if not href:
            continue
        full_url = urljoin(url, href)
        rel_path = download_resource(full_url, url, output_dir, 'css')
        if rel_path:
            link_tag["href"] = rel_path

    # 下载 JS 文件
    for script_tag in soup.find_all("script", src=True):
        src = script_tag.get("src")
        if not src:
            continue
        full_url = urljoin(url, src)
        rel_path = download_resource(full_url, url, output_dir, 'js')
        if rel_path:
            script_tag["src"] = rel_path

    return soup.prettify()

def extract_internal_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    base_domain = urlparse(base_url).netloc
    for a in soup.find_all('a', href=True):
        href = urljoin(base_url, a['href'])
        parsed = urlparse(href)
        if parsed.netloc == base_domain:
            links.add(href.split('#')[0])
    return list(links)