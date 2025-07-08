# Web Scraper

这是一个完整的 Web Scraper Python 工程，项目名为 web_scraper，包含以下模块和功能。目标是从给定种子 URL 开始，递归抓取内部链接页面，并保存每一页为本地 HTML 文件。项目需模块化设计，包含如下内容：

## 项目结构

web_scraper/
├── main.py
├── scraper/
│   ├── __init__.py
│   ├── fetcher.py
│   ├── parser.py
│   └── saver.py
├── output/
└── requirements.txt

## 模块说明与功能要求

### main.py

- 功能：作为爬虫主入口，负责调度整个流程
- 功能流程：
  1. 使用 seed_url = "https://example.com/lander" 作为初始地址；
  2. 利用 fetcher.fetch_page_with_resources() 下载 HTML 页面及资源；
  3. 用 parser.parse_page_and_download_images() 替换并修复 HTML 中的资源路径；
  4. 用 saver.save_html() 保存本地 HTML；
  5. 通过 extract_internal_links() 抽取内部链接并递归抓取；
  6. 避免重复抓取，记录访问过的页面。

### fetcher.py

- 函数：fetch_page_with_resources(url) -> str
- 使用 requests 下载目标 URL；
- 保留原 HTML 格式；
- 支持 JS 渲染可选（如果用 playwright 也可以接受）；
- 返回字符串形式的完整 HTML 内容。

### parser.py

- 函数：parse_page_and_download_images(html: str, base_url: str, output_dir: str) -> str
- 使用 BeautifulSoup：
  - 查找所有 <img>资源；
  - 下载资源至 output_dir 的相应子目录；
  - 将资源链接改为相对路径；
- 返回修改后的 HTML 字符串。

### saver.py

- 函数：save_html(content: str, filepath: str)
- 将 HTML 内容写入本地文件；
- 若目录不存在，自动创建；
- 首页页面文件名为 output/index.html
- 其他页面文件名请保持和原来名字一样

### extract_internal_links(html, base_url)

- 从 HTML 中提取所有 <a href>；
- 使用 urllib.parse.urlparse 判断是否为当前站点内部链接；
- 返回去重后的链接列表，去掉锚点（# 之后的内容）；

### 额外要求：

- 使用 requests, beautifulsoup4, lxml, urllib, os, pathlib；
- 保证模块之间清晰解耦；
- 支持未来扩展图片/video/字体文件处理；
- 所有资源保存在 ../output/ 文件夹中；
- 爬取的时候，使用真实的浏览器模拟器，以绕过反爬虫检测

### 示例调用

运行 python main.py 应完成：

- 递归抓取指定页面和其内部页面；
- 所有资源本地化；
- 第一个页面保存为output/index.html
- 其他所有页面保存在 output/page_*.html
