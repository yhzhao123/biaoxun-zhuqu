"""
爬取智能体

负责列表页和详情页的爬取
"""
import io
import logging
import asyncio
import aiohttp
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from apps.crawler.agents.schema import (
    ExtractionStrategy,
    DetailResult,
    Attachment
)

logger = logging.getLogger(__name__)

# 常量配置
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_URL_SCHEMES = {'http', 'https'}


class ListFetcherAgent:
    """
    列表页爬取智能体
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def fetch(self, strategy: ExtractionStrategy) -> List[Dict]:
        """
        爬取列表页

        Args:
            strategy: 提取策略

        Returns:
            列表项列表
        """
        if strategy.site_type == 'api':
            return await self._fetch_api(strategy)
        else:
            return await self._fetch_html(strategy)

    async def _fetch_api(self, strategy: ExtractionStrategy) -> List[Dict]:
        """从API获取列表"""
        items = []
        config = strategy.api_config

        if not config:
            logger.error("API config not provided")
            return items

        async with aiohttp.ClientSession(headers=self.headers) as session:
            for page in range(1, strategy.max_pages + 1):
                try:
                    # 构建请求参数
                    params = dict(config.get('params', {}))

                    # 找到页码参数并设置
                    for key in params:
                        if isinstance(params[key], int):
                            params[key] = page
                            break

                    logger.info(f"Fetching API page {page}: {config['url']}")

                    # 发送请求
                    method = config.get('method', 'GET').upper()
                    headers = config.get('headers', {})

                    if method == 'GET':
                        async with session.get(
                            config['url'],
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            response.raise_for_status()
                            data = await response.json()
                    else:
                        async with session.post(
                            config['url'],
                            json=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            response.raise_for_status()
                            data = await response.json()

                    # 解析响应
                    page_items = self._parse_api_response(data, strategy)

                    if not page_items:
                        logger.info(f"No more items on page {page}")
                        break

                    items.extend(page_items)
                    logger.info(f"Page {page}: fetched {len(page_items)} items")

                    # 延迟
                    await asyncio.sleep(strategy.anti_detection.get('delay_seconds', 1))

                except Exception as e:
                    logger.error(f"Failed to fetch page {page}: {e}")
                    break

        return items

    def _parse_api_response(self, data: Dict, strategy: ExtractionStrategy) -> List[Dict]:
        """解析API响应"""
        items = []

        # 根据response_path获取数据列表
        response_path = strategy.api_config.get('response_path') if strategy.api_config else None

        if response_path:
            # 使用点号路径
            parts = response_path.split('.')
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    logger.warning(f"Could not find path: {response_path}")
                    return items
            list_data = current
        else:
            # 尝试常见路径
            list_data = data.get('data', {}).get('list', []) or data.get('data', {}).get('items', []) or []

        if not isinstance(list_data, list):
            logger.warning(f"List data is not a list: {type(list_data)}")
            return items

        # 字段映射
        field_map = strategy.list_strategy

        for item_data in list_data:
            if isinstance(item_data, dict):
                # 处理嵌套data结构
                if 'data' in item_data and isinstance(item_data['data'], dict):
                    item_data = item_data['data']

                # 提取字段
                item = {
                    'title': self._get_nested_value(item_data, field_map.get('title_field', 'title')),
                    'url': self._get_nested_value(item_data, field_map.get('url_field', 'url')),
                    'publish_date': self._get_nested_value(item_data, field_map.get('date_field', 'time')),
                    'budget': self._get_nested_value(item_data, field_map.get('budget_field', 'budget')),
                    'tenderer': self._get_nested_value(item_data, field_map.get('tenderer_field', 'tenderer')),
                    'source': 'api_list',
                }

                if item.get('title'):
                    items.append(item)

        return items

    def _get_nested_value(self, data: Dict, path: str, default=None):
        """获取嵌套字典值"""
        if not path:
            return default

        current = data
        for key in path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default

    async def _fetch_html(self, strategy: ExtractionStrategy) -> List[Dict]:
        """从HTML页面获取列表"""
        # 实现HTML列表页爬取
        logger.info("HTML list fetching not implemented yet")
        return []


class DetailFetcherAgent:
    """
    详情页爬取智能体

    支持两种详情页格式：
    1. HTML页面 - 提取HTML内容和附件
    2. PDF页面 - 检测并下载正文PDF
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名，移除非法字符"""
        import os
        # 获取basename防止路径遍历
        filename = os.path.basename(filename)
        # 替换Windows非法字符
        filename = re.sub(r'[<>\":/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:196] + ext
        return filename or 'document.pdf'

    @staticmethod
    def _is_safe_url(url: str, base_url: str) -> bool:
        """验证URL是否安全（防止SSRF）"""
        try:
            parsed = urlparse(url)
            # 检查scheme
            if parsed.scheme not in ALLOWED_URL_SCHEMES:
                return False
            # 检查是否是IP地址（简单检查）
            hostname = parsed.hostname or ''
            # 阻止私有IP
            if hostname.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                                   '172.2', '172.3', '127.', '0.', '::1', 'fe80:', 'fc', 'fd')):
                logger.warning(f"Blocked private IP access: {url}")
                return False
            return True
        except Exception:
            return False

    async def fetch(self, list_item: Dict) -> Optional[DetailResult]:
        """
        爬取详情页

        Args:
            list_item: 列表项数据

        Returns:
            DetailResult 详情页结果
        """
        url = list_item.get('url')
        if not url:
            logger.warning("No URL in list item")
            return None

        try:
            logger.info(f"Fetching detail page: {url}")

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '').lower()

                    # 检查是否是PDF内容
                    if 'pdf' in content_type or url.lower().endswith('.pdf'):
                        return await self._handle_pdf_response(response, url, list_item)

                    html = await response.text()

            # 检查HTML中是否包含正文PDF链接（某些网站详情页是框架，主要内容在PDF中）
            main_pdf_info = self._detect_main_pdf(html, url)
            if main_pdf_info:
                logger.info(f"Detected main PDF: {main_pdf_info['url']}")
                pdf_content = await self._download_pdf_content(main_pdf_info['url'])
                if pdf_content:
                    return DetailResult(
                        url=url,
                        html=html,
                        attachments=self._extract_attachments(html, url),
                        list_data=list_item,
                        main_pdf_content=pdf_content,
                        main_pdf_url=main_pdf_info['url'],
                        main_pdf_filename=main_pdf_info.get('filename', 'main.pdf')
                    )

            # 提取附件
            attachments = self._extract_attachments(html, url)

            return DetailResult(
                url=url,
                html=html,
                attachments=attachments,
                list_data=list_item
            )

        except Exception as e:
            logger.error(f"Failed to fetch detail page {url}: {e}")
            return None

    async def _handle_pdf_response(
        self,
        response: aiohttp.ClientResponse,
        url: str,
        list_item: Dict
    ) -> DetailResult:
        """处理直接返回PDF的响应"""
        # 检查文件大小
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_PDF_SIZE:
            logger.warning(f"PDF too large: {content_length} bytes, max: {MAX_PDF_SIZE}")
            return DetailResult(
                url=url,
                html='',
                attachments=[],
                list_data=list_item,
                main_pdf_content=None,
                main_pdf_url=url,
                main_pdf_filename='oversized.pdf'
            )

        pdf_bytes = await response.read()
        # 双重检查实际大小
        if len(pdf_bytes) > MAX_PDF_SIZE:
            logger.warning(f"PDF content exceeds limit: {len(pdf_bytes)} bytes")
            pdf_bytes = pdf_bytes[:MAX_PDF_SIZE]

        pdf_content = self._extract_text_from_pdf_bytes(pdf_bytes)

        filename = self._sanitize_filename(url.split('/')[-1]) or 'document.pdf'

        logger.info(f"Fetched PDF directly: {filename}, extracted {len(pdf_content)} chars")

        return DetailResult(
            url=url,
            html='',  # PDF没有HTML
            attachments=[],  # 附件需要另外提取
            list_data=list_item,
            main_pdf_content=pdf_content,
            main_pdf_url=url,
            main_pdf_filename=filename
        )

    def _detect_main_pdf(self, html: str, base_url: str) -> Optional[Dict]:
        """
        检测详情页中的正文PDF链接

        常见的正文PDF特征：
        1. 链接文本包含"公告"、"正文"、"下载"等关键词
        2. 链接在主要内容区域
        3. 可能是页面中最大的PDF或第一个PDF
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 关键词匹配（按优先级排序）
            keywords = [
                '公告', '正文', '文件下载', '下载附件', '招标公告',
                '中标公告', '采购公告', '项目公告', '查看详情',
                'document', 'download', '公告正文', '采购文件'
            ]

            pdf_links = []

            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)

                if not href.lower().endswith('.pdf'):
                    continue

                full_url = urljoin(base_url, href)

                # URL安全检查（防止SSRF）
                if not self._is_safe_url(full_url, base_url):
                    continue

                # 计算匹配分数
                score = 0
                text_lower = text.lower()

                for i, keyword in enumerate(keywords):
                    if keyword in text or keyword in href:
                        score += len(keywords) - i  # 前面的关键词分数更高

                # 在主要内容区域的加分
                parent = link.parent
                for _ in range(3):  # 向上检查3层
                    if parent:
                        parent_class = ' '.join(parent.get('class', [])).lower()
                        parent_id = parent.get('id', '').lower()
                        if any(x in parent_class or x in parent_id for x in [
                            'content', 'main', 'detail', 'article', 'body'
                        ]):
                            score += 5
                            break
                        parent = parent.parent

                pdf_links.append({
                    'url': full_url,
                    'filename': text or 'document.pdf',
                    'score': score
                })

            if pdf_links:
                # 按分数排序，取最高分
                pdf_links.sort(key=lambda x: x['score'], reverse=True)
                best_match = pdf_links[0]

                # 只有当分数足够高时才认为是正文PDF
                if best_match['score'] > 0:
                    return best_match

                # 如果没有匹配关键词，返回第一个PDF（可能是唯一的正文PDF）
                if len(pdf_links) == 1:
                    return pdf_links[0]

        except Exception as e:
            logger.warning(f"Failed to detect main PDF: {e}")

        return None

    async def _download_pdf_content(self, url: str) -> Optional[str]:
        """下载PDF并提取文本内容"""
        try:
            # URL安全检查
            if not self._is_safe_url(url, url):
                logger.warning(f"Unsafe PDF URL blocked: {url}")
                return None

            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    response.raise_for_status()

                    # 检查文件大小
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > MAX_PDF_SIZE:
                        logger.warning(f"PDF too large: {content_length} bytes")
                        return None

                    pdf_bytes = await response.read()

                    # 双重检查
                    if len(pdf_bytes) > MAX_PDF_SIZE:
                        logger.warning(f"PDF content exceeds limit: {len(pdf_bytes)} bytes")
                        return None

                    return self._extract_text_from_pdf_bytes(pdf_bytes)
        except Exception as e:
            logger.error(f"Failed to download PDF {url}: {e}")
            return None

    def _extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """从PDF字节中提取文本"""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except ImportError:
            logger.warning("pdfplumber not installed")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        try:
            import fitz
            text = ""
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
            return text.strip()
        except ImportError:
            logger.warning("PyMuPDF not installed")
        except Exception as e:
            logger.error(f"PyMuPDF failed: {e}")

        return ""

    def _extract_attachments(self, html: str, base_url: str) -> List[Attachment]:
        """提取附件链接"""
        attachments = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 查找PDF链接
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)

                if href.lower().endswith('.pdf'):
                    full_url = urljoin(base_url, href)
                    attachments.append(Attachment(
                        url=full_url,
                        filename=text or 'attachment.pdf',
                        type='pdf'
                    ))

            # 查找其他常见附件
            for ext in ['.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.lower().endswith(ext):
                        full_url = urljoin(base_url, href)
                        attachments.append(Attachment(
                            url=full_url,
                            filename=link.get_text(strip=True) or f'attachment{ext}',
                            type=ext.lstrip('.')
                        ))

        except Exception as e:
            logger.warning(f"Failed to extract attachments: {e}")

        if attachments:
            logger.info(f"Found {len(attachments)} attachments")

        return attachments
