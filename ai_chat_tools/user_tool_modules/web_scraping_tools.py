# MODULE_DESCRIPTION: 网页抓取（联网）工具集合，用于搜索、获取网页内容和API数据
# MODULE_CATEGORY: web_scraping
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 1.0.0

"""
网页抓取（联网）工具模块
提供完整的网页抓取和API调用功能，包括：
- 获取网页纯文本内容（过滤JS、CSS、样式等无关内容）
- 执行API GET/POST请求
- 获取和分析JSON数据
- 提取网页链接和摘要信息
- 检查网页状态和可访问性
专门用于节省AI上下文长度，优化网页内容获取
"""

import os
import re
import time
import json
import requests
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment, Tag
import html2text
from readability import Document
from datetime import datetime
from requests_html import HTMLSession, HTMLResponse

# 使用绝对导入避免相对导入问题
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# ==================== 网页抓取管理器 ====================

class WebScraperManager:
    """网页抓取管理器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 创建 requests-html 会话
        self.html_session = HTMLSession()
        
        # HTML转文本转换器配置
        self.html2text_converter = html2text.HTML2Text()
        self.html2text_converter.ignore_links = True
        self.html2text_converter.ignore_images = True
        self.html2text_converter.ignore_emphasis = True
        self.html2text_converter.body_width = 0  # 不换行
        self.html2text_converter.unicode_snob = True
        
        # 创建数据存储目录
        self.data_dir = os.path.join(os.getcwd(), "scraped_data")
        os.makedirs(self.data_dir, exist_ok=True)
    
    def fetch_page(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """获取网页内容"""
        try:
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            
            # 检查 Content-Encoding 头
            content_encoding = response.headers.get('content-encoding', '').lower()
            
            # 检查是否需要手动处理压缩内容
            content_text = None
            detected_encoding = response.encoding
            
            # 先尝试 requests 的自动处理
            try:
                content_text = response.text
                detected_encoding = response.encoding
                
                # 检查是否解码成功（如果包含大量乱码字符，可能解码失败）
                if len(content_text) > 0:
                    # 统计非ASCII字符和控制字符的比例
                    non_printable = sum(1 for c in content_text[:1000] if ord(c) < 32 and c not in '\n\r\t')
                    if non_printable > len(content_text[:1000]) * 0.1:  # 如果超过10%是非打印字符
                        raise UnicodeDecodeError("auto", b"", 0, 0, "Too many non-printable characters")
                        
            except (UnicodeDecodeError, UnicodeError):
                # 如果自动处理失败，尝试手动处理
                import gzip
                import chardet
                
                try:
                    # 尝试手动解压缩
                    content_bytes = response.content
                    content_encoding = response.headers.get('content-encoding', '').lower()
                    
                    if content_encoding == 'gzip':
                        try:
                            content_bytes = gzip.decompress(content_bytes)
                        except:
                            pass  # 如果解压失败，使用原始内容
                    
                    # 检测编码
                    detected = chardet.detect(content_bytes)
                    if detected['confidence'] > 0.7:
                        detected_encoding = detected['encoding']
                    else:
                        detected_encoding = 'utf-8'
                    
                    # 解码为文本
                    encoding = detected_encoding or 'utf-8'
                    content_text = content_bytes.decode(encoding, errors='replace')
                    
                except Exception:
                    # 最后的备用方案
                    content_text = response.content.decode('utf-8', errors='replace')
                    detected_encoding = 'utf-8'
            else:
                # 没有压缩，正常处理
                detected_encoding = response.encoding
                if detected_encoding == 'ISO-8859-1':
                    # 尝试从content中检测编码
                    content_type = response.headers.get('content-type', '')
                    if 'charset=' in content_type:
                        charset = content_type.split('charset=')[1].split(';')[0].strip()
                        response.encoding = charset
                    else:
                        # 尝试从HTML中检测编码
                        import chardet
                        detected = chardet.detect(response.content)
                        if detected['confidence'] > 0.7:
                            response.encoding = detected['encoding']
                
                content_text = response.text
                detected_encoding = response.encoding
            
            return {
                'success': True,
                'content': content_text,
                'url': response.url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'encoding': detected_encoding
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def api_request(self, url: str, method: str = "GET", headers: Optional[Dict[str, Any]] = None, 
                   data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
        """执行API请求"""
        try:
            # 准备请求头
            request_headers = dict(self.session.headers)
            if headers:
                request_headers.update(headers)
            
            # 如果有JSON数据，设置Content-Type
            if json_data:
                request_headers['Content-Type'] = 'application/json'
            
            # 执行请求
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers, params=data, timeout=timeout)
            elif method.upper() == "POST":
                if json_data:
                    response = self.session.post(url, headers=request_headers, json=json_data, timeout=timeout)
                else:
                    response = self.session.post(url, headers=request_headers, data=data, timeout=timeout)
            elif method.upper() == "PUT":
                if json_data:
                    response = self.session.put(url, headers=request_headers, json=json_data, timeout=timeout)
                else:
                    response = self.session.put(url, headers=request_headers, data=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers, timeout=timeout)
            else:
                return {
                    'success': False,
                    'error': f"不支持的HTTP方法: {method}",
                    'url': url
                }
            
            # 尝试解析JSON响应
            try:
                json_content = response.json()
                is_json = True
            except:
                json_content = None
                is_json = False
            
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'json': json_content,
                'is_json': is_json,
                'url': response.url,
                'encoding': response.encoding
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def save_json_data(self, data: Dict, filename_prefix: str = "api_data") -> str:
        """保存JSON数据到本地文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            raise Exception(f"保存JSON文件失败: {str(e)}")
    
    def analyze_json_structure(self, data: Any, max_depth: int = 3, current_depth: int = 0) -> str:
        """分析JSON数据结构"""
        if current_depth > max_depth:
            return "..."
        
        if isinstance(data, dict):
            if not data:
                return "{}"
            
            items = []
            for key, value in list(data.items())[:5]:  # 最多显示5个键
                value_desc = self.analyze_json_structure(value, max_depth, current_depth + 1)
                items.append(f'"{key}": {value_desc}')
            
            if len(data) > 5:
                items.append("...")
            
            return "{\n" + ",\n".join(f"  {item}" for item in items) + "\n}"
        
        elif isinstance(data, list):
            if not data:
                return "[]"
            
            # 只分析第一个元素的结构
            first_item = self.analyze_json_structure(data[0], max_depth, current_depth + 1)
            length_info = f" (共{len(data)}个元素)" if len(data) > 1 else ""
            return f"[{first_item}{length_info}]"
        
        elif isinstance(data, str):
            return f'"string" (示例: "{data[:50]}{"..." if len(data) > 50 else ""}")'
        elif isinstance(data, (int, float)):
            return f"number (示例: {data})"
        elif isinstance(data, bool):
            return f"boolean (示例: {data})"
        elif data is None:
            return "null"
        else:
            return f"unknown ({type(data).__name__})"

    def extract_main_content(self, html: str, url: str = "") -> str:
        """使用readability提取主要内容"""
        try:
            doc = Document(html)
            main_content = doc.summary()
            
            # 进一步清理
            soup = BeautifulSoup(main_content, 'html.parser')
            return self._clean_soup(soup)
        except Exception:
            # 如果readability失败，回退到BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return self._extract_content_fallback(soup)
    
    def _clean_soup(self, soup: BeautifulSoup) -> str:
        """清理BeautifulSoup对象，移除无用元素"""
        # 移除脚本和样式
        for element in soup(['script', 'style', 'meta', 'link', 'noscript']):
            element.decompose()
        
        # 移除注释
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # 移除空的div和span
        for tag in soup.find_all(['div', 'span']):
            if isinstance(tag, Tag) and not tag.get_text(strip=True) and not tag.find_all():
                tag.decompose()
        
        # 移除广告相关的元素
        ad_patterns = [
            'ad', 'ads', 'advertisement', 'banner', 'popup', 'modal',
            'sidebar', 'footer', 'header', 'nav', 'menu', 'breadcrumb'
        ]
        
        for pattern in ad_patterns:
            for element in soup.find_all(attrs={'class': re.compile(pattern, re.I)}):
                element.decompose()
            for element in soup.find_all(attrs={'id': re.compile(pattern, re.I)}):
                element.decompose()
        
        # 转换为纯文本
        text = self.html2text_converter.handle(str(soup))
        
        # 清理文本
        return self._clean_text(text)
    
    def _extract_content_fallback(self, soup: BeautifulSoup) -> str:
        """备用内容提取方法"""
        # 尝试找到主要内容区域
        main_selectors = [
            'main', 'article', '[role="main"]',
            '.content', '.main-content', '.post-content',
            '.entry-content', '.article-content', '.story-body'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # 如果找不到主要内容区域，使用body
            main_content = soup.find('body') or soup
        
        return self._clean_soup(BeautifulSoup(str(main_content), 'html.parser'))
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        # 移除多余的空白字符
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 多个空行变成两个空行
        text = re.sub(r'[ \t]+', ' ', text)      # 多个空格变成一个空格
        text = re.sub(r'\n[ \t]+', '\n', text)   # 行首空格
        text = re.sub(r'[ \t]+\n', '\n', text)   # 行尾空格
        
        # 移除过多的换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def search_with_requests_html(self, keywords: str, max_results: int = 10, timeout: int = 15, 
                                include_snippets: bool = True, language: str = "zh-cn", region: str = "CN") -> Dict[str, Any]:
        """使用 requests-html 进行搜索"""
        try:
            import urllib.parse
            
            # 构建搜索URL
            encoded_keywords = urllib.parse.quote(keywords)
            search_url = f"https://www.bing.com/search?q={encoded_keywords}&count={max_results}&setlang={language}&cc={region}&first=1"
            
            # 使用 requests-html 获取页面
            r = self.html_session.get(search_url, timeout=timeout)  # type: ignore
            r.raise_for_status()
            
            # 查找搜索结果
            search_results = []
            
            # 使用多种选择器策略
            result_selectors = [
                'li.b_algo',
                'div.b_algo', 
                '.b_algo',
                'li[data-priority]',
                'div[data-priority]'
            ]
            
            result_elements = []
            for selector in result_selectors:
                try:
                    elements = r.html.find(selector)  # type: ignore
                    if elements:
                        result_elements = list(elements)[:max_results]  # type: ignore
                        break
                except Exception:
                    continue
            
            # 如果没找到结果，尝试更广泛的搜索
            if not result_elements:
                # 查找包含链接的所有元素
                all_links = r.html.find('a[href]')  # type: ignore
                for link in all_links:  # type: ignore
                    href = link.attrs.get('href', '')  # type: ignore
                    if (href.startswith('http') and 
                        'bing.com' not in href and 
                        'microsoft.com' not in href and
                        len(link.text.strip()) > 10):  # type: ignore
                        result_elements.append(link.element.getparent())  # type: ignore
                        if len(result_elements) >= max_results:
                            break
            
            # 解析每个搜索结果
            for element in result_elements[:max_results]:  # type: ignore
                try:
                    # 查找标题和链接
                    title = ""
                    url = ""
                    snippet = ""
                    
                    # 尝试多种方式找到标题链接
                    link_selectors = ['h2 a', 'h3 a', 'a[href^="http"]', '.b_title a']
                    for selector in link_selectors:
                        try:
                            link_elem = element.find(selector)  # type: ignore
                            if link_elem:
                                link_elem = link_elem[0] if isinstance(link_elem, list) else link_elem  # type: ignore
                                title = link_elem.text.strip()  # type: ignore
                                url = link_elem.attrs.get('href', '')  # type: ignore
                                if title and url and url.startswith('http'):
                                    break
                        except:
                            continue
                    
                    # 如果没找到，尝试直接查找链接
                    if not title or not url:
                        try:
                            all_links = element.find('a[href]')  # type: ignore
                            for link in all_links:  # type: ignore
                                href = link.attrs.get('href', '')  # type: ignore
                                if href.startswith('http') and 'bing.com' not in href:
                                    title = link.text.strip()  # type: ignore
                                    url = href
                                    break
                        except:
                            continue
                    
                    # 查找摘要
                    if include_snippets:
                        snippet_selectors = ['.b_caption p', '.b_snippetText', '.b_caption']
                        for selector in snippet_selectors:
                            try:
                                snippet_elem = element.find(selector)  # type: ignore
                                if snippet_elem:
                                    snippet_elem = snippet_elem[0] if isinstance(snippet_elem, list) else snippet_elem  # type: ignore
                                    snippet = snippet_elem.text.strip()  # type: ignore
                                    if snippet and len(snippet) > 10:
                                        break
                            except:
                                continue
                    
                    # 验证结果
                    if title and url and len(title) > 3:
                        search_results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                        
                except Exception as e:
                    continue
            
            return {
                'success': True,
                'results': search_results,
                'total_found': len(search_results),
                'search_url': search_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'search_url': search_url if 'search_url' in locals() else ''
            }

# 创建全局实例
_web_scraper = WebScraperManager()

# ==================== API调用工具 ====================

@register_tool(
    name="api_get_request",
    description="执行GET API请求",
    requires_confirmation=True,
    confirmation_category="network_request",
    risk_level="low",
    schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "API端点URL"
            },
            "headers": {
                "type": "object",
                "description": "请求头，如认证信息、Content-Type等",
                "default": {}
            },
            "params": {
                "type": "object",
                "description": "查询参数",
                "default": {}
            },
            "timeout": {
                "type": "integer",
                "description": "请求超时时间（秒），默认30秒",
                "default": 30,
                "minimum": 1,
                "maximum": 120
            },
            "save_response": {
                "type": "boolean",
                "description": "是否保存响应到本地文件（仅JSON响应），默认False",
                "default": False
            }
        },
        "required": ["url"]
    }
)
def api_get_request(url: str, headers: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, 
                   timeout: int = 30, save_response: bool = False) -> str:
    """执行GET API请求"""
    try:
        # 执行GET请求
        result = _web_scraper.api_request(url, "GET", headers=headers, data=params, timeout=timeout)
        
        if not result['success']:
            return f"[错误] GET请求失败: {result['error']}"
        
        # 构建基本信息
        info = f"[成功] GET请求完成\n"
        info += f"URL: {result['url']}\n"
        info += f"状态码: {result['status_code']}\n"
        info += f"内容类型: {result['headers'].get('content-type', '未知')}\n"
        info += f"响应大小: {len(result['content'])} 字符\n"
        
        # 如果是JSON响应且需要保存
        filepath = None
        if result['is_json'] and save_response:
            filepath = _web_scraper.save_json_data(result['json'], "get_response")
            info += f"本地文件: {filepath}\n"
        
        info += f"{'=' * 50}\n\n"
        
        # 显示响应内容
        if result['is_json']:
            # JSON响应显示结构
            structure = _web_scraper.analyze_json_structure(result['json'])
            info += f"JSON响应结构:\n{structure}"
            if filepath:
                info += f"\n\n文件路径（供AI使用）: {filepath}"
        else:
            # 文本响应显示前1000字符
            content = result['content']
            if len(content) > 1000:
                info += f"响应内容（前1000字符）:\n{content[:1000]}...\n\n[内容已截断]"
            else:
                info += f"响应内容:\n{content}"
        
        return info
        
    except Exception as e:
        return f"[错误] GET请求失败: {str(e)}"

@register_tool(
    name="api_post_request",
    description="执行POST API请求",
    requires_confirmation=True,
    confirmation_category="network_request",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "API端点URL"
            },
            "headers": {
                "type": "object",
                "description": "请求头，如认证信息、Content-Type等",
                "default": {}
            },
            "json_data": {
                "type": "object",
                "description": "JSON格式的请求体数据",
                "default": None
            },
            "form_data": {
                "type": "object",
                "description": "表单格式的请求体数据（与json_data二选一）",
                "default": None
            },
            "timeout": {
                "type": "integer",
                "description": "请求超时时间（秒），默认30秒",
                "default": 30,
                "minimum": 1,
                "maximum": 120
            },
            "save_response": {
                "type": "boolean",
                "description": "是否保存响应到本地文件（仅JSON响应），默认False",
                "default": False
            }
        },
        "required": ["url"]
    }
)
def api_post_request(url: str, headers: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, 
                    form_data: Optional[Dict[str, Any]] = None, timeout: int = 30, save_response: bool = False) -> str:
    """执行POST API请求"""
    try:
        # 检查数据格式
        if json_data and form_data:
            return "[错误] json_data和form_data不能同时指定，请选择其中一种"
        
        # 执行POST请求
        result = _web_scraper.api_request(
            url, "POST", 
            headers=headers, 
            data=form_data, 
            json_data=json_data, 
            timeout=timeout
        )
        
        if not result['success']:
            return f"[错误] POST请求失败: {result['error']}"
        
        # 构建基本信息
        info = f"[成功] POST请求完成\n"
        info += f"URL: {result['url']}\n"
        info += f"状态码: {result['status_code']}\n"
        info += f"内容类型: {result['headers'].get('content-type', '未知')}\n"
        info += f"响应大小: {len(result['content'])} 字符\n"
        
        # 显示请求数据信息
        if json_data:
            info += f"请求格式: JSON\n"
        elif form_data:
            info += f"请求格式: 表单数据\n"
        else:
            info += f"请求格式: 无数据\n"
        
        # 如果是JSON响应且需要保存
        filepath = None
        if result['is_json'] and save_response:
            filepath = _web_scraper.save_json_data(result['json'], "post_response")
            info += f"本地文件: {filepath}\n"
        
        info += f"{'=' * 50}\n\n"
        
        # 显示响应内容
        if result['is_json']:
            # JSON响应显示结构
            structure = _web_scraper.analyze_json_structure(result['json'])
            info += f"JSON响应结构:\n{structure}"
            if filepath:
                info += f"\n\n文件路径（供AI使用）: {filepath}"
        else:
            # 文本响应显示前1000字符
            content = result['content']
            if len(content) > 1000:
                info += f"响应内容（前1000字符）:\n{content[:1000]}...\n\n[内容已截断]"
            else:
                info += f"响应内容:\n{content}"
        
        return info
        
    except Exception as e:
        return f"[错误] POST请求失败: {str(e)}"



@register_tool(
    name="fetch_json_data",
    description="获取返回JSON格式的API数据，自动保存到本地文件并分析数据结构",
    requires_confirmation=True,
    confirmation_category="network_request",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "返回JSON数据的API URL"
            },
            "timeout": {
                "type": "integer",
                "description": "请求超时时间（秒），默认30秒",
                "default": 30,
                "minimum": 1,
                "maximum": 120
            },
            "headers": {
                "type": "object",
                "description": "自定义请求头，如API密钥等",
                "default": {}
            },
            "filename_prefix": {
                "type": "string",
                "description": "保存文件的前缀名，默认为'json_data'",
                "default": "json_data"
            }
        },
        "required": ["url"]
    }
)
def fetch_json_data(url: str, timeout: int = 30, headers: Optional[Dict[str, Any]] = None, filename_prefix: str = "json_data") -> str:
    """获取JSON数据并保存到本地"""
    try:
        # 执行API请求
        result = _web_scraper.api_request(url, "GET", headers=headers, timeout=timeout)
        
        if not result['success']:
            return f"[错误] API请求失败: {result['error']}"
        
        if not result['is_json']:
            return f"[错误] 响应不是JSON格式\n状态码: {result['status_code']}\n内容类型: {result['headers'].get('content-type', '未知')}"
        
        # 保存JSON数据到本地
        filepath = _web_scraper.save_json_data(result['json'], filename_prefix)
        
        # 分析JSON结构
        structure = _web_scraper.analyze_json_structure(result['json'])
        
        # 构建返回信息
        info = f"[成功] JSON数据获取完成\n"
        info += f"URL: {result['url']}\n"
        info += f"状态码: {result['status_code']}\n"
        info += f"内容类型: {result['headers'].get('content-type', '未知')}\n"
        info += f"本地文件: {filepath}\n"
        info += f"数据大小: {len(json.dumps(result['json']))} 字符\n"
        info += f"{'=' * 50}\n\n"
        info += f"JSON数据结构:\n{structure}\n\n"
        info += f"文件路径（供AI使用）: {filepath}"
        
        return info
        
    except Exception as e:
        return f"[错误] 获取JSON数据失败: {str(e)}"



@register_tool(
    name="fetch_webpage_content",
    description="获取网页的纯文本内容，自动过滤JS、CSS、广告等无关内容",
    schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要获取内容的网页URL"
            },
            "timeout": {
                "type": "integer",
                "description": "请求超时时间（秒），默认10秒",
                "default": 10,
                "minimum": 1,
                "maximum": 60
            },
            "max_length": {
                "type": "integer",
                "description": "返回内容的最大长度，默认10000字符",
                "default": 10000,
                "minimum": 100,
                "maximum": 50000
            }
        },
        "required": ["url"]
    }
)
def fetch_webpage_content(url: str, timeout: int = 10, max_length: int = 10000) -> str:
    """获取网页的纯文本内容"""
    try:
        # 验证URL格式
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return f"[错误] 无效的URL格式: {url}"
        
        # 获取网页内容
        result = _web_scraper.fetch_page(url, timeout)
        
        if not result['success']:
            return f"[错误] 获取网页失败: {result['error']}"
        
        # 提取主要内容
        content = _web_scraper.extract_main_content(result['content'], url)
        
        # 限制长度
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[内容已截断...]"
        
        # 构建返回信息
        info = f"[成功] 网页内容获取完成\n"
        info += f"URL: {result['url']}\n"
        info += f"状态码: {result['status_code']}\n"
        info += f"编码: {result['encoding']}\n"
        info += f"内容长度: {len(content)} 字符\n"
        info += f"{'=' * 50}\n\n"
        
        return info + content
        
    except Exception as e:
        return f"[错误] 获取网页内容失败: {str(e)}"



@register_tool(
    name="extract_webpage_links",
    description="提取网页中的所有链接",
    schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要提取链接的网页URL"
            },
            "timeout": {
                "type": "integer",
                "description": "请求超时时间（秒），默认10秒",
                "default": 10,
                "minimum": 1,
                "maximum": 60
            },
            "internal_only": {
                "type": "boolean",
                "description": "是否只返回内部链接（同域名），默认False",
                "default": False
            },
            "max_links": {
                "type": "integer",
                "description": "返回链接的最大数量，默认50",
                "default": 50,
                "minimum": 1,
                "maximum": 200
            }
        },
        "required": ["url"]
    }
)
def extract_webpage_links(url: str, timeout: int = 10, internal_only: bool = False, max_links: int = 50) -> str:
    """提取网页中的所有链接"""
    try:
        # 获取网页内容
        result = _web_scraper.fetch_page(url, timeout)
        
        if not result['success']:
            return f"[错误] 获取网页失败: {result['error']}"
        
        soup = BeautifulSoup(result['content'], 'html.parser')
        base_domain = urlparse(url).netloc
        
        links = []
        for link in soup.find_all('a', href=True):
            if not isinstance(link, Tag):
                continue
                
            href_attr = link.get('href')
            if not href_attr:
                continue
                
            href = str(href_attr).strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # 转换为绝对URL
            absolute_url = urljoin(url, href)
            link_domain = urlparse(absolute_url).netloc
            
            # 如果只要内部链接，检查域名
            if internal_only and link_domain != base_domain:
                continue
            
            # 获取链接文本
            link_text = link.get_text().strip()
            if not link_text:
                link_text = "无文本"
            
            links.append({
                'url': absolute_url,
                'text': link_text,
                'is_internal': link_domain == base_domain
            })
            
            if len(links) >= max_links:
                break
        
        # 去重
        seen_urls = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        # 构建结果
        result_text = f"[成功] 网页链接提取完成\n"
        result_text += f"URL: {result['url']}\n"
        result_text += f"找到链接: {len(unique_links)} 个\n"
        result_text += f"筛选条件: {'仅内部链接' if internal_only else '所有链接'}\n"
        result_text += f"{'=' * 50}\n\n"
        
        for i, link in enumerate(unique_links, 1):
            link_type = "内部" if link['is_internal'] else "外部"
            result_text += f"{i}. [{link_type}] {link['text']}\n"
            result_text += f"   {link['url']}\n\n"
        
        return result_text
        
    except Exception as e:
        return f"[错误] 提取网页链接失败: {str(e)}"



@register_tool(
    name="search_bing",
    description="使用关键词搜索Bing搜索引擎，获取搜索结果",
    requires_confirmation=True,
    confirmation_category="network_request", 
    risk_level="low",
    schema={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "搜索关键词"
            },
            "max_results": {
                "type": "integer",
                "description": "返回的最大搜索结果数量，默认10",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            },
            "timeout": {
                "type": "integer",
                "description": "请求超时时间（秒），默认15秒",
                "default": 15,
                "minimum": 1,
                "maximum": 60
            },
            "include_snippets": {
                "type": "boolean",
                "description": "是否包含搜索结果摘要，默认True",
                "default": True
            },
            "language": {
                "type": "string",
                "description": "搜索语言，默认zh-cn（中文）",
                "default": "zh-cn",
                "enum": ["zh-cn", "en-us", "ja-jp", "ko-kr", "de-de", "fr-fr", "es-es"]
            },
            "region": {
                "type": "string", 
                "description": "搜索地区，默认CN（中国）",
                "default": "CN",
                "enum": ["CN", "US", "JP", "KR", "DE", "FR", "ES", "GB"]
            }
        },
        "required": ["keywords"]
    }
)
def search_bing(keywords: str, max_results: int = 10, timeout: int = 15, include_snippets: bool = True, 
                language: str = "zh-cn", region: str = "CN") -> str:
    """使用关键词搜索Bing搜索引擎"""
    try:
        # 使用 requests-html 进行搜索
        result = _web_scraper.search_with_requests_html(keywords, max_results, timeout, include_snippets, language, region)
        
        if not result['success']:
            return f"[错误] 搜索失败: {result['error']}"
        
        # 构建返回结果
        result_text = f"[成功] 搜索完成\n"
        result_text += f"搜索关键词: {keywords}\n"
        result_text += f"搜索语言: {language}, 地区: {region}\n"
        result_text += f"找到结果: {result['total_found']} 条\n"
        result_text += f"搜索URL: {result['search_url']}\n"
        result_text += f"{'=' * 60}\n\n"
        
        for i, result_item in enumerate(result['results'], 1):
            result_text += f"{i}. {result_item['title']}\n"
            result_text += f"   链接: {result_item['url']}\n"
            
            if include_snippets and result_item['snippet']:
                result_text += f"   摘要: {result_item['snippet']}\n"
            
            result_text += f"\n"
        
        return result_text
        
    except Exception as e:
        return f"[错误] 搜索过程中发生异常: {str(e)}\n调试信息: 请检查网络连接和搜索关键词格式" 