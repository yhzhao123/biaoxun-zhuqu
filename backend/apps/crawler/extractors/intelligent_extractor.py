"""
Intelligent Content Extraction - 智能内容提取

Plan A: 自动检测页面结构，无需静态CSS选择器
- 分析HTML结构，识别主要内容区域
- 自动提取标题、日期、金额、采购人等信息
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class IntelligentExtractor:
    """
    智能内容提取器

    自动分析HTML页面结构，提取招标关键信息：
    - 标题 (title)
    - 发布日期 (publish_date)
    - 预算金额 (budget)
    - 采购人/招标人 (tenderer)
    - 内容描述 (content)
    """

    # 标题关键词（用于识别标题区域）
    TITLE_KEYWORDS = [
        '招标公告', '中标公告', '采购公告', '成交公告',
        '竞争性谈判', '询价公告', '单一来源', '资格预审',
        '结果公示', '变更公告', '答疑公告'
    ]

    # 日期模式匹配
    DATE_PATTERNS = [
        # 中文格式
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{4})年(\d{1,2})月(\d{1,2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        # 标准格式
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{4})\.(\d{1,2})\.(\d{1,2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    ]

    # 金额模式匹配
    AMOUNT_PATTERNS = [
        # 金额+单位
        r'([¥￥]?\s*[\d,]+\.?\d*)\s*(万元|万元人民币|万)',
        r'([¥￥]?\s*[\d,]+\.?\d*)\s*(亿元|亿)',
        r'([¥￥]?\s*[\d,]+\.?\d*)\s*(元|人民币)',
        # 单位+金额
        r'(预算金额|采购预算|项目预算|中标金额|成交金额)[：:]\s*([¥￥]?\s*[\d,]+\.?\d*)\s*(万元|万|元)?',
        r'(金额|预算)[：:]\s*([¥￥]?\s*[\d,]+\.?\d*)\s*(万元|万|元)?',
    ]

    # 采购人/招标人关键词
    PURCHASER_KEYWORDS = [
        '采购人', '招标人', '采购单位', '招标单位', '业主',
        '采购方', '招标方', '需求方', '甲方'
    ]

    def __init__(self):
        self.soup = None
        self.main_content = None

    def extract(self, html: str) -> Dict:
        """
        从HTML中提取招标信息

        Args:
            html: HTML内容

        Returns:
            提取的信息字典
        """
        if not html:
            return {}

        self.soup = BeautifulSoup(html, 'html.parser')
        self.main_content = self._find_main_content()

        result = {
            'title': self._extract_title(),
            'publish_date': self._extract_publish_date(),
            'budget': self._extract_budget(),
            'tenderer': self._extract_tenderer(),
            'description': self._extract_description(),
            'extraction_method': 'intelligent'
        }

        return result

    def _find_main_content(self) -> Tag:
        """
        查找主要内容区域

        优先级：
        1. article标签
        2. main标签
        3. id包含content/main/article的元素
        4. class包含content/main/article的元素
        5. 最大的文本块
        """
        # 优先级1: article标签
        article = self.soup.find('article')
        if article:
            return article

        # 优先级2: main标签
        main = self.soup.find('main')
        if main:
            return main

        # 优先级3: id匹配
        for pattern in ['content', 'main', 'article', 'detail', 'body']:
            element = self.soup.find(id=re.compile(pattern, re.I))
            if element:
                return element

        # 优先级4: class匹配
        for pattern in ['content', 'main', 'article', 'detail', 'body']:
            element = self.soup.find(class_=re.compile(pattern, re.I))
            if element:
                return element

        # 优先级5: 最大的div或section
        max_len = 0
        max_element = None
        for tag in self.soup.find_all(['div', 'section']):
            text_len = len(tag.get_text(strip=True))
            if text_len > max_len:
                max_len = text_len
                max_element = tag

        return max_element if max_element else self.soup.body or self.soup

    def _extract_title(self) -> Optional[str]:
        """
        提取标题

        策略：
        1. 查找h1标签
        2. 查找包含招标关键词的标题
        3. 从title标签提取
        """
        candidates = []

        # 策略1: h1标签
        h1 = self.soup.find('h1')
        if h1:
            text = h1.get_text(strip=True)
            if len(text) > 5 and len(text) < 200:
                candidates.append((text, 10 if any(k in text for k in self.TITLE_KEYWORDS) else 5))

        # 策略2: 包含关键词的标题
        for tag in self.soup.find_all(['h1', 'h2', 'h3', 'div', 'p']):
            text = tag.get_text(strip=True)
            if any(k in text for k in self.TITLE_KEYWORDS):
                if 10 < len(text) < 200:
                    candidates.append((text, 8))
                    break

        # 策略3: title标签
        title_tag = self.soup.find('title')
        if title_tag:
            text = title_tag.get_text(strip=True)
            # 清理网站名称后缀
            text = re.split(r'[_-]|\\|／', text)[0].strip()
            if len(text) > 5:
                candidates.append((text, 3))

        if candidates:
            # 按权重排序，选择最佳
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return None

    def _extract_publish_date(self) -> Optional[datetime]:
        """
        提取发布日期

        策略：
        1. 查找time标签
        2. 查找包含日期关键词的元素
        3. 在主内容区域搜索日期模式
        """
        text_to_search = []

        # 策略1: time标签
        time_tag = self.soup.find('time')
        if time_tag:
            datetime_val = time_tag.get('datetime')
            if datetime_val:
                text_to_search.append(datetime_val)
            text_to_search.append(time_tag.get_text(strip=True))

        # 策略2: 包含日期关键词的元素
        date_keywords = ['发布时间', '发布日期', '公告日期', '时间', '日期']
        for keyword in date_keywords:
            elements = self.soup.find_all(string=re.compile(keyword))
            for el in elements:
                parent = el.parent
                if parent:
                    text_to_search.append(parent.get_text(strip=True))

        # 策略3: 主内容区域
        if self.main_content:
            text_to_search.append(self.main_content.get_text())

        # 在所有文本中搜索日期
        for text in text_to_search:
            for pattern, parser in self.DATE_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    try:
                        return parser(match)
                    except (ValueError, AttributeError):
                        continue

        return None

    def _extract_budget(self) -> Optional[Decimal]:
        """
        提取预算金额

        策略：
        1. 查找包含金额关键词的元素
        2. 在文本中搜索金额模式
        """
        text_to_search = []

        # 策略1: 包含金额关键词的元素
        amount_keywords = ['预算', '金额', '采购金额', '项目金额', '中标金额', '成交金额']
        for keyword in amount_keywords:
            elements = self.soup.find_all(string=re.compile(keyword))
            for el in elements:
                parent = el.parent
                if parent:
                    # 获取父元素和兄弟元素的文本
                    text_to_search.append(parent.get_text(strip=True))
                    for sibling in parent.find_next_siblings(limit=3):
                        text_to_search.append(sibling.get_text(strip=True))

        # 策略2: 主内容区域
        if self.main_content:
            text_to_search.append(self.main_content.get_text())

        # 搜索金额
        for text in text_to_search:
            for pattern in self.AMOUNT_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    amount = self._parse_amount_from_match(match)
                    if amount and amount > 0:
                        return amount

        return None

    def _parse_amount_from_match(self, match) -> Optional[Decimal]:
        """从正则匹配中解析金额"""
        try:
            groups = match.groups()
            # 找到数字组
            number_str = None
            unit = None

            for g in groups:
                if g is None:
                    continue
                if re.match(r'^[\d,\.]+$', str(g).replace('¥', '').replace('￥', '').replace(',', '')):
                    number_str = g
                elif g in ('万', '万元', '万元人民币', '亿', '亿元', '元', '人民币'):
                    unit = g

            if not number_str:
                return None

            # 清理数字
            number_str = re.sub(r'[¥￥,\s]', '', number_str)
            amount = Decimal(number_str)

            # 单位换算
            if unit in ('亿', '亿元'):
                amount = amount * Decimal('100000000')
            elif unit in ('万', '万元', '万元人民币'):
                amount = amount * Decimal('10000')

            return amount

        except (InvalidOperation, ValueError) as e:
            logger.debug(f"Failed to parse amount: {e}")
            return None

    def _extract_tenderer(self) -> Optional[str]:
        """
        提取采购人/招标人

        策略：
        1. 查找包含采购人关键词的元素
        2. 查找标签后的值
        """
        if self.main_content:
            text = self.main_content.get_text()

            for keyword in self.PURCHASER_KEYWORDS:
                # 模式: 关键词：值 或 关键词:值
                pattern = rf'{keyword}[：:]\s*([^\n，。；;]+)'
                match = re.search(pattern, text)
                if match:
                    value = match.group(1).strip()
                    # 清理常见后缀
                    value = re.sub(r'\s*(联系电话|地址|联系人|电话|邮编).*', '', value)
                    if 2 < len(value) < 100:
                        return value

        return None

    def _extract_description(self) -> Optional[str]:
        """
        提取内容描述

        策略：
        1. 获取主内容区域的纯文本
        2. 清理和格式化
        """
        if not self.main_content:
            return None

        # 获取所有段落
        paragraphs = self.main_content.find_all(['p', 'div'])

        texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20:  # 过滤太短的段落
                texts.append(text)

        if texts:
            content = '\n\n'.join(texts[:10])  # 最多10个段落
            return content[:5000]  # 限制长度

        # 回退到整个内容
        text = self.main_content.get_text(strip=True)
        return text[:5000] if text else None

    def analyze_page_structure(self, html: str) -> Dict:
        """
        分析页面结构

        返回页面结构信息，用于调试和优化
        """
        if not html:
            return {'error': 'Empty HTML'}

        soup = BeautifulSoup(html, 'html.parser')

        structure = {
            'has_article': bool(soup.find('article')),
            'has_main': bool(soup.find('main')),
            'headings': {
                'h1': len(soup.find_all('h1')),
                'h2': len(soup.find_all('h2')),
                'h3': len(soup.find_all('h3')),
            },
            'content_areas': [],
            'potential_selectors': {}
        }

        # 查找可能的内容区域
        for tag in soup.find_all(['div', 'section', 'article']):
            tag_id = tag.get('id', '')
            tag_class = ' '.join(tag.get('class', []))

            if any(k in (tag_id + tag_class).lower() for k in ['content', 'main', 'article', 'detail']):
                structure['content_areas'].append({
                    'tag': tag.name,
                    'id': tag_id,
                    'class': tag_class,
                    'text_length': len(tag.get_text(strip=True))
                })

        # 推荐选择器
        if structure['content_areas']:
            best = max(structure['content_areas'], key=lambda x: x['text_length'])
            if best['id']:
                structure['potential_selectors']['content'] = f"#{best['id']}"
            elif best['class']:
                structure['potential_selectors']['content'] = f".{best['class'].split()[0]}"

        # 查找标题
        h1 = soup.find('h1')
        if h1:
            structure['potential_selectors']['title'] = 'h1'

        # 查找时间
        time_tag = soup.find('time')
        if time_tag:
            structure['potential_selectors']['date'] = 'time'

        return structure