import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

class WebCrawler:
    def __init__(self):
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def is_valid_url(self, url):
        """检查URL是否有效"""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    
    def get_all_links(self, url):
        """获取页面中的所有链接"""
        links = set()
        try:
            response = self.session.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                if self.is_valid_url(full_url):
                    links.add(full_url)
            
            return links
        except Exception as e:
            print(f"获取链接时出错: {e}")
            return set()
    
    def crawl(self, start_url, max_depth=1, content_types=None, save_dir='./crawled_data'):
        """
        爬取网页内容
        :param start_url: 起始URL
        :param max_depth: 爬取深度
        :param content_types: 要爬取的内容类型 ('text', 'images', 'links', 'all')
        :param save_dir: 保存目录
        """
        if content_types is None:
            content_types = ['all']
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self._crawl_recursive(start_url, max_depth=max_depth, current_depth=1, 
                            content_types=content_types, save_dir=save_dir)
    
    def _crawl_recursive(self, url, max_depth, current_depth, content_types, save_dir):
        """递归爬取网页"""
        if url in self.visited_urls or current_depth > max_depth:
            return
        
        self.visited_urls.add(url)
        print(f"正在爬取: {url} (深度: {current_depth})")
        
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            # 根据内容类型保存数据
            if 'all' in content_types or 'text' in content_types:
                self._save_text_content(url, response.text, save_dir)
            
            if 'all' in content_types or 'images' in content_types:
                self._save_images(url, response.text, save_dir)
            
            if 'all' in content_types or 'links' in content_types:
                self._save_links(url, response.text, save_dir)
            
            # 如果未达到最大深度，继续爬取链接
            if current_depth < max_depth:
                links = self.get_all_links(url)
                for link in links:
                    self._crawl_recursive(link, max_depth, current_depth + 1, 
                                         content_types, save_dir)
                    
            # 礼貌性延迟
            time.sleep(1)
            
        except Exception as e:
            print(f"爬取 {url} 时出错: {e}")
    
    def _save_text_content(self, url, html_content, save_dir):
        """保存文本内容"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            
            # 创建有效的文件名
            parsed_url = urlparse(url)
            filename = f"{parsed_url.netloc}{parsed_url.path}".replace('/', '_')
            if not filename:
                filename = "index"
            filename = re.sub(r'[^\w\-_. ]', '_', filename)[:100] + '.txt'
            
            filepath = os.path.join(save_dir, 'text', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n\n")
                f.write(text)
            
            print(f"已保存文本内容到: {filepath}")
        except Exception as e:
            print(f"保存文本内容时出错: {e}")
    
    def _save_images(self, base_url, html_content, save_dir):
        """保存图片"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            img_tags = soup.find_all('img')
            
            if not img_tags:
                return
            
            image_dir = os.path.join(save_dir, 'images', urlparse(base_url).netloc)
            os.makedirs(image_dir, exist_ok=True)
            
            for img_tag in img_tags:
                img_url = img_tag.get('src')
                if not img_url:
                    continue
                
                img_url = urljoin(base_url, img_url)
                
                try:
                    response = self.session.get(img_url, stream=True, timeout=5)
                    response.raise_for_status()
                    
                    # 获取图片扩展名
                    content_type = response.headers.get('content-type', '').split('/')[-1]
                    if content_type not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
                        continue
                    
                    # 创建有效的文件名
                    img_name = os.path.basename(urlparse(img_url).path)
                    if not img_name:
                        img_name = f"image_{int(time.time())}.{content_type}"
                    elif '.' not in img_name:
                        img_name += f".{content_type}"
                    
                    filepath = os.path.join(image_dir, img_name)
                    
                    # 保存图片
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    
                    print(f"已保存图片: {filepath}")
                    
                except Exception as e:
                    print(f"下载图片 {img_url} 时出错: {e}")
                
                # 礼貌性延迟
                time.sleep(0.5)
                
        except Exception as e:
            print(f"保存图片时出错: {e}")
    
    def _save_links(self, url, html_content, save_dir):
        """保存链接"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = set()
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                if self.is_valid_url(full_url):
                    links.add(full_url)
            
            if not links:
                return
            
            # 创建有效的文件名
            parsed_url = urlparse(url)
            filename = f"{parsed_url.netloc}{parsed_url.path}".replace('/', '_')
            if not filename:
                filename = "index"
            filename = re.sub(r'[^\w\-_. ]', '_', filename)[:100] + '_links.txt'
            
            filepath = os.path.join(save_dir, 'links', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"从 {url} 找到的链接:\n\n")
                for link in sorted(links):
                    f.write(f"{link}\n")
            
            print(f"已保存链接到: {filepath}")
        except Exception as e:
            print(f"保存链接时出错: {e}")


def main():
    print("=== Python 爬虫工具 ===")
    
    # 获取用户输入
    start_url = input("请输入起始URL (例如: https://example.com): ").strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = 'https://' + start_url
    
    max_depth = input("请输入爬取深度 (默认为1): ").strip()
    max_depth = int(max_depth) if max_depth.isdigit() else 1
    
    print("\n请选择要爬取的内容类型 (可多选):")
    print("1. 文本内容")
    print("2. 图片")
    print("3. 链接")
    print("4. 所有内容")
    choices = input("请输入选项 (用逗号分隔, 如 1,2,3): ").strip().split(',')
    
    content_types = []
    for choice in choices:
        choice = choice.strip()
        if choice == '1':
            content_types.append('text')
        elif choice == '2':
            content_types.append('images')
        elif choice == '3':
            content_types.append('links')
        elif choice == '4':
            content_types = ['all']
            break
    
    if not content_types:
        content_types = ['all']
    
    save_dir = input(f"请输入保存目录 (默认为 ./crawled_data): ").strip()
    save_dir = save_dir if save_dir else './crawled_data'
    
    # 开始爬取
    crawler = WebCrawler()
    print("\n开始爬取...")
    crawler.crawl(start_url, max_depth=max_depth, content_types=content_types, save_dir=save_dir)
    print("\n爬取完成!")


if __name__ == "__main__":
    main()
