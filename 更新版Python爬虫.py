import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
import logging
from tqdm import tqdm  # 进度条支持（需安装：pip install tqdm）

class EnhancedWebCrawler:
    def __init__(self):
        self.visited_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.setup_logging()

    def setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('web_crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def is_valid_url(self, url):
        """检查URL是否有效"""
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False
        
        # 排除非HTTP协议和常见非网页文件
        if parsed.scheme not in ('http', 'https'):
            return False
        if any(parsed.path.lower().endswith(ext) for ext in 
              ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.rar', '.exe', '.dmg']):
            return False
            
        return True

    def sanitize_filename(self, text, max_length=150):
        """生成安全的文件名"""
        text = text.replace('/', '_').replace('\\', '_')
        text = re.sub(r'[^\w\-_. ]', '_', text)
        return text[:max_length].strip('_')

    def get_all_links(self, url):
        """获取页面中的所有有效链接"""
        links = set()
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 检查内容类型是否为HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'html' not in content_type:
                self.logger.warning(f"非HTML内容: {url} (Content-Type: {content_type})")
                return links
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有可能的链接标签
            for tag in soup.find_all(['a', 'link', 'area'], href=True):
                href = tag['href'].strip()
                if href.startswith('javascript:') or href.startswith('mailto:'):
                    continue
                full_url = urljoin(url, href)
                if self.is_valid_url(full_url):
                    links.add(full_url)
            
            # 处理iframe/srcset等特殊标签
            for tag in soup.find_all(['iframe', 'frame'], src=True):
                full_url = urljoin(url, tag['src'].strip())
                if self.is_valid_url(full_url):
                    links.add(full_url)
            
            self.logger.info(f"从 {url} 提取到 {len(links)} 个链接")
            return links
            
        except Exception as e:
            self.logger.error(f"获取 {url} 链接时出错: {str(e)}")
            return set()

    def download_resource(self, url, save_path):
        """通用资源下载方法"""
        try:
            for attempt in range(3):  # 重试机制
                try:
                    with self.session.get(url, stream=True, timeout=15) as response:
                        response.raise_for_status()
                        
                        # 检查内容类型
                        content_type = response.headers.get('content-type', '').lower()
                        if 'image' in content_type or url.lower().split('?')[0].split('.')[-1] in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            os.makedirs(os.path.dirname(save_path), exist_ok=True)
                            with open(save_path, 'wb') as f:
                                for chunk in response.iter_content(8192):
                                    f.write(chunk)
                            return True
                        else:
                            self.logger.warning(f"非图片内容: {url} (Content-Type: {content_type})")
                            return False
                except requests.exceptions.RequestException as e:
                    if attempt == 2:
                        raise
                    time.sleep(1)
        except Exception as e:
            self.logger.error(f"下载 {url} 失败: {str(e)}")
            return False

    def crawl(self, start_url, max_depth=1, content_types=None, save_dir='./crawled_data'):
        """
        增强版爬取方法
        :param start_url: 起始URL
        :param max_depth: 爬取深度
        :param content_types: 内容类型 ('text', 'images', 'links', 'all')
        :param save_dir: 保存目录
        """
        if content_types is None:
            content_types = ['all']
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self.logger.info(f"开始爬取: {start_url} (深度: {max_depth})")
        self._crawl_recursive(start_url, max_depth=max_depth, current_depth=1, 
                            content_types=content_types, save_dir=save_dir)
        self.logger.info("爬取完成!")

    def _crawl_recursive(self, url, max_depth, current_depth, content_types, save_dir):
        """递归爬取核心方法"""
        if url in self.visited_urls or current_depth > max_depth:
            return
            
        self.visited_urls.add(url)
        self.logger.info(f"处理 [{current_depth}/{max_depth}] {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if not ('html' in content_type or 'text' in content_type):
                self.logger.warning(f"跳过非文本内容: {url} (Content-Type: {content_type})")
                return
            
            # 解析HTML内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 保存文本内容
            if 'all' in content_types or 'text' in content_types:
                self._save_text_content(url, soup, save_dir)
            
            # 保存图片
            if 'all' in content_types or 'images' in content_types:
                self._save_images(url, soup, save_dir)
            
            # 保存链接
            if 'all' in content_types or 'links' in content_types:
                self._save_links(url, soup, save_dir)
            
            # 递归爬取
            if current_depth < max_depth:
                links = self.get_all_links(url)
                for link in tqdm(links, desc=f"深度 {current_depth} 爬取进度"):
                    self._crawl_recursive(link, max_depth, current_depth + 1, 
                                        content_types, save_dir)
            
            # 礼貌延迟
            time.sleep(0.5)
            
        except Exception as e:
            self.logger.error(f"处理 {url} 时出错: {str(e)}")

    def _save_text_content(self, url, soup, save_dir):
        """保存文本内容"""
        try:
            # 提取主要文本内容（可优化为读取<article>或<main>标签）
            for unwanted in soup(['script', 'style', 'nav', 'footer', 'iframe']):
                unwanted.decompose()
                
            text = soup.get_text(separator='\n', strip=True)
            
            # 生成文件名
            parsed_url = urlparse(url)
            filename = f"{parsed_url.netloc}_{self.sanitize_filename(parsed_url.path)}.txt"
            filepath = os.path.join(save_dir, 'text', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n\n")
                f.write(text)
            
            self.logger.info(f"已保存文本: {filepath}")
        except Exception as e:
            self.logger.error(f"保存文本失败: {str(e)}")

    def _save_images(self, base_url, soup, save_dir):
        """保存图片（优化版）"""
        try:
            # 查找所有可能的图片标签和属性
            img_tags = []
            for tag in soup.find_all(['img', 'picture', 'source', 'figure']):
                for attr in ['src', 'data-src', 'srcset', 'data-original', 'content']:
                    if tag.has_attr(attr):
                        img_tags.append((tag, attr))
            
            if not img_tags:
                self.logger.info(f"未在 {base_url} 中找到图片")
                return
            
            domain = urlparse(base_url).netloc.replace(':', '_')
            image_dir = os.path.join(save_dir, 'images', domain)
            
            for tag, attr in img_tags:
                img_urls = []
                if attr == 'srcset':
                    # 处理srcset属性（可能包含多个URL）
                    for src in tag[attr].split(','):
                        img_urls.append(src.strip().split(' ')[0])
                else:
                    img_urls.append(tag[attr].strip())
                
                for img_url in img_urls:
                    try:
                        # 处理URL
                        img_url = urljoin(base_url, img_url.split('?')[0])
                        
                        # 生成文件名
                        img_name = os.path.basename(urlparse(img_url).path)
                        if not img_name:
                            img_name = f"image_{int(time.time() * 1000)}"
                        
                        # 确保有扩展名
                        if '.' not in img_name:
                            ext = self.guess_file_extension(img_url)
                            img_name = f"{img_name}.{ext}"
                        
                        # 安全文件名
                        img_name = self.sanitize_filename(img_name)
                        filepath = os.path.join(image_dir, img_name)
                        
                        # 下载图片
                        if not os.path.exists(filepath):
                            if self.download_resource(img_url, filepath):
                                self.logger.info(f"已保存图片: {filepath}")
                            else:
                                self.logger.warning(f"图片下载失败: {img_url}")
                        else:
                            self.logger.info(f"图片已存在: {filepath}")
                            
                        time.sleep(0.2)  # 礼貌延迟
                        
                    except Exception as e:
                        self.logger.error(f"处理图片 {img_url} 时出错: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"保存图片时发生错误: {str(e)}")

    def guess_file_extension(self, url):
        """从URL猜测文件扩展名"""
        path = urlparse(url).path.lower()
        if '.jpg' in path or '.jpeg' in path:
            return 'jpg'
        elif '.png' in path:
            return 'png'
        elif '.gif' in path:
            return 'gif'
        elif '.webp' in path:
            return 'webp'
        return 'jpg'  # 默认

    def _save_links(self, url, soup, save_dir):
        """保存链接"""
        try:
            links = set()
            for tag in soup.find_all(['a', 'link', 'area'], href=True):
                href = tag['href'].strip()
                if href.startswith(('javascript:', 'mailto:', 'tel:')):
                    continue
                full_url = urljoin(url, href)
                if self.is_valid_url(full_url):
                    links.add(full_url)
            
            if links:
                parsed_url = urlparse(url)
                filename = f"{parsed_url.netloc}_{self.sanitize_filename(parsed_url.path)}_links.txt"
                filepath = os.path.join(save_dir, 'links', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"从 {url} 提取的 {len(links)} 个链接:\n\n")
                    for link in sorted(links):
                        f.write(f"{link}\n")
                
                self.logger.info(f"已保存链接列表: {filepath}")
        except Exception as e:
            self.logger.error(f"保存链接失败: {str(e)}")


def main():
    print("=== 增强版网页爬虫 ===")
    print("注意: 请遵守robots.txt协议和目标网站的使用条款")
    
    # 用户输入
    start_url = input("请输入起始URL (例如 https://example.com): ").strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"
    
    max_depth = input("请输入爬取深度 (1-3推荐): ").strip()
    max_depth = int(max_depth) if max_depth.isdigit() and 0 < int(max_depth) <= 5 else 1
    
    print("\n请选择爬取内容类型:")
    print("1. 文本内容")
    print("2. 图片")
    print("3. 链接")
    print("4. 所有内容")
    choices = input("输入选项 (如 1,2 或 4): ").strip().split(',')
    
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
    
    save_dir = input(f"保存目录 (默认: ./crawled_data): ").strip()
    save_dir = save_dir if save_dir else './crawled_data'
    
    # 开始爬取
    crawler = EnhancedWebCrawler()
    print("\n开始爬取 (查看web_crawler.log获取详细日志)...")
    crawler.crawl(
        start_url=start_url,
        max_depth=max_depth,
        content_types=content_types,
        save_dir=save_dir
    )
    print("爬取完成!")


if __name__ == "__main__":
    main()
