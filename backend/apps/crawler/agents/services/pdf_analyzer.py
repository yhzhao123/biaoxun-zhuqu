"""
PDF内容深度提取服务

专门用于从PDF文本中提取：
1. 采购物品/标的详细信息
2. 技术参数和规格要求
3. 投标人资格条件
4. 交付和付款条件
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass

from apps.crawler.agents.schema import TenderItem, TechnicalParameter

logger = logging.getLogger(__name__)


@dataclass
class ProcurementItem:
    """内部使用的采购项数据结构"""
    name: str = ''
    specification: str = ''
    quantity: Optional[float] = None
    unit: str = ''
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    category: str = ''
    technical_params: List[TechnicalParameter] = None

    def __post_init__(self):
        if self.technical_params is None:
            self.technical_params = []


class PDFContentAnalyzer:
    """
    PDF内容分析器

    从PDF文本中提取结构化的招标信息
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        分析PDF文本内容

        Args:
            text: PDF提取的文本内容

        Returns:
            包含提取信息的字典
        """
        result = {
            'items': [],
            'technical_parameters': [],
            'qualification_requirements': '',
            'delivery_period': '',
            'warranty_period': '',
            'payment_terms': '',
            'evaluation_method': '',
        }

        try:
            # 提取采购物品/标的
            result['items'] = self._extract_procurement_items(text)

            # 提取技术参数
            result['technical_parameters'] = self._extract_technical_parameters(text)

            # 提取资格条件
            result['qualification_requirements'] = self._extract_qualification_requirements(text)

            # 提取交付条件
            result['delivery_period'] = self._extract_delivery_period(text)

            # 提取质保期
            result['warranty_period'] = self._extract_warranty_period(text)

            # 提取付款方式
            result['payment_terms'] = self._extract_payment_terms(text)

            # 提取评标方法
            result['evaluation_method'] = self._extract_evaluation_method(text)

        except Exception as e:
            self.logger.error(f"PDF content analysis failed: {e}")

        return result

    def _extract_procurement_items(self, text: str) -> List[Dict]:
        """
        提取采购物品/标的列表

        常见的表格格式：
        - 序号、名称、规格、数量、单位、预算单价、预算总价
        - 品目、标的名称、数量、单位、技术参数
        """
        items = []

        # 尝试匹配物品表格
        # 模式1: 带序号的表格行
        item_patterns = [
            # 匹配类似 "1. 服务器 2台 规格:xxx" 的行
            r'(?:^|\n)\s*(\d+)[\.\、\s]+([^\n]{2,50}?)(\d+(?:\.\d+)?)\s*(台|套|个|件|套|批|组|辆|艘|架|份|套)(?:\s|[^\d]|$)',
            # 匹配 "物品名称: xxx 数量: x" 格式
            r'(采购标的|采购物品|货物名称|设备名称|商品名称|项目名称)[：:]*\s*([^\n]{2,50}?)[,，\s]+(?:数量|采购数量)[：:]*\s*(\d+(?:\.\d+)?)\s*(台|套|个|件|批|组|辆)?',
            # 匹配表格行
            r'\|\s*(\d+)\s*\|\s*([^|]{2,50})\s*\|\s*([^|]*)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*(台|套|个|件|批|组)?\s*\|',
        ]

        for pattern in item_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                try:
                    item = self._parse_item_match(match, text)
                    if item and item.get('name'):
                        items.append(item)
                except Exception as e:
                    self.logger.debug(f"Failed to parse item: {e}")

        # 如果没有找到，尝试使用段落分析
        if not items:
            items = self._extract_items_from_paragraphs(text)

        return items

    def _parse_item_match(self, match: re.Match, full_text: str) -> Optional[Dict]:
        """解析匹配到的物品信息"""
        groups = match.groups()
        if len(groups) < 2:
            return None

        item = {
            'name': '',
            'specification': '',
            'quantity': None,
            'unit': '',
            'budget_unit_price': None,
            'budget_total_price': None,
            'category': '',
            'technical_requirements': '',
            'delivery_requirements': '',
        }

        # 根据匹配的组数解析
        if len(groups) >= 2:
            item['name'] = groups[1].strip() if groups[1] else ''

        if len(groups) >= 3:
            try:
                item['quantity'] = float(groups[2])
            except (ValueError, TypeError):
                pass

        if len(groups) >= 4:
            item['unit'] = groups[3] if groups[3] else ''

        # 尝试提取规格信息（从匹配位置周围）
        start_pos = max(0, match.start() - 200)
        end_pos = min(len(full_text), match.end() + 200)
        context = full_text[start_pos:end_pos]

        # 提取规格
        spec_match = re.search(r'(?:规格[型号]*|技术参数|配置要求)[：:]*\s*([^\n]{2,100})', context)
        if spec_match:
            item['specification'] = spec_match.group(1).strip()

        # 提取单价
        price_match = re.search(r'(?:单价|单台价格|每台)[：:\s]*([\d,\.]+)\s*元?', context)
        if price_match:
            try:
                item['budget_unit_price'] = Decimal(price_match.group(1).replace(',', ''))
            except:
                pass

        return item

    def _extract_items_from_paragraphs(self, text: str) -> List[Dict]:
        """从段落中提取物品信息（当表格匹配失败时使用）"""
        items = []

        # 查找包含"采购"、"标的"等关键词的段落
        procurement_keywords = [
            '采购标的', '采购物品', '采购内容', '采购货物', '采购设备',
            '招标内容', '招标范围', '供货范围', '服务范围'
        ]

        for keyword in procurement_keywords:
            # 查找相关段落
            pattern = rf'(?:{keyword})[^。]*(?:如下|包括|主要|内容)[：:\s]*([^。]*)'
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                content = match.group(1)
                # 分割多个物品（按逗号、顿号或分号）
                item_names = re.split(r'[,，;；、]', content)

                for name in item_names:
                    name = name.strip()
                    if len(name) > 2 and len(name) < 100:
                        items.append({
                            'name': name,
                            'specification': '',
                            'quantity': None,
                            'unit': '',
                            'budget_unit_price': None,
                            'budget_total_price': None,
                            'category': '',
                            'technical_requirements': '',
                            'delivery_requirements': '',
                        })

        return items

    def _extract_technical_parameters(self, text: str) -> List[Dict]:
        """
        提取技术参数列表

        常见的技术参数格式：
        - 参数名：参数值
        - 技术规格：xxx
        - 性能指标：xxx
        """
        parameters = []

        # 技术参数区块识别
        tech_sections = [
            r'(?:技术参数|技术规格|技术指标|性能指标|功能要求|配置要求)[：:\s]*([^\n]*(?:\n[^\n]{0,2}[^\n]*)*)',
            r'(?:技术需求|技术要求|规格参数|设备参数|产品参数)[：:\s]*([^\n]*(?:\n[^\n]{0,2}[^\n]*)*)',
        ]

        for section_pattern in tech_sections:
            section_matches = re.finditer(section_pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in section_matches:
                section_text = match.group(1)
                params = self._parse_technical_section(section_text)
                parameters.extend(params)

        # 如果没有找到区块，尝试逐行匹配
        if not parameters:
            parameters = self._parse_inline_parameters(text)

        return parameters

    def _parse_technical_section(self, section_text: str) -> List[Dict]:
        """解析技术参数区块"""
        parameters = []

        # 模式1: "参数名：参数值" 或 "参数名：参数值（单位）"
        param_pattern = r'(?:^|\n)\s*(?:\d+[\.\s]+)?([^：:\n]{2,30})[：:]\s*([^\n]{1,100})'
        matches = re.finditer(param_pattern, section_text)

        for match in matches:
            name = match.group(1).strip()
            value = match.group(2).strip()

            # 过滤掉非参数行
            if self._is_valid_parameter_name(name):
                parameters.append({
                    'name': name,
                    'value': value,
                    'category': self._categorize_parameter(name),
                    'is_mandatory': '必须' in value or '强制' in value or '≥' in value or '>=' in value
                })

        return parameters

    def _parse_inline_parameters(self, text: str) -> List[Dict]:
        """从正文中逐行解析参数"""
        parameters = []

        # 常见参数模式
        inline_patterns = [
            # 性能指标
            r'(?:处理器|CPU|内存|硬盘|存储|显卡|分辨率|尺寸|重量|功耗)[\s]*[：:≥<≥≤]*\s*([^,，;；\n]{1,50})',
            # 网络指标
            r'(?:带宽|速率|延迟|吞吐量|并发数)[\s]*[：:≥<≥≤]*\s*([^,，;；\n]{1,30})',
            # 质量指标
            r'(?:质保|保修|寿命|MTBF|可用性|可靠性)[\s]*[：:≥<≥≤]*\s*([^,，;；\n]{1,30})',
        ]

        for pattern in inline_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # 提取参数名（匹配前的文字）
                start = max(0, match.start() - 30)
                context = text[start:match.start()]
                name_match = re.search(r'([\w\s]+)$', context)
                if name_match:
                    name = name_match.group(1).strip()
                    value = match.group(1).strip()
                    if name and value:
                        parameters.append({
                            'name': name,
                            'value': value,
                            'category': self._categorize_parameter(name),
                            'is_mandatory': True
                        })

        return parameters

    def _is_valid_parameter_name(self, name: str) -> bool:
        """判断是否是有效的参数名称"""
        # 排除常见的非参数文本
        invalid_patterns = [
            '投标人', '供应商', '资格要求', '报名时间', '开标时间',
            '联系人', '联系电话', '公告', '说明', '备注'
        ]
        return not any(pattern in name for pattern in invalid_patterns)

    def _categorize_parameter(self, name: str) -> str:
        """对参数进行分类"""
        categories = {
            '性能指标': ['处理器', 'CPU', '内存', '硬盘', '存储', '显卡', '分辨率', '主频', '速度', '速率'],
            '功能要求': ['功能', '支持', '兼容', '接口', '协议', '标准'],
            '物理规格': ['尺寸', '重量', '体积', '高度', '宽度', '长度'],
            '电气规格': ['电压', '电流', '功耗', '功率', '频率'],
            '环境要求': ['温度', '湿度', '防护', '防尘', '防水'],
            '质量要求': ['质保', '保修', '寿命', 'MTBF', '可靠性', '可用性'],
            '服务要求': ['响应时间', '服务', '维护', '培训'],
        }

        for category, keywords in categories.items():
            if any(kw in name for kw in keywords):
                return category

        return '其他'

    def _extract_qualification_requirements(self, text: str) -> str:
        """提取投标人资格要求"""
        patterns = [
            r'(?:投标人资格要求|供应商资格要求|资格要求)[：:\s]*([^\n]*(?:\n(?![一二三四五六七八九十123456789]\s|第[一二三四五六七八九十]).*)*)',
            r'(?:合格投标人|合格供应商)[应须]+[具备满足]*[如下条件]*[：:\s]*([^\n]*(?:\n(?![一二三四五六七八九十123456789]\s|第[一二三四五六七八九十]).*)*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:1000]  # 限制长度

        return ''

    def _extract_delivery_period(self, text: str) -> str:
        """提取交付期限"""
        patterns = [
            r'(?:交付期|供货期|工期|实施期|服务期|完成期限|交付时间)[\s]*[：:]*\s*([^，；;。\n]{1,50})',
            r'(?:合同签订后|中标后|确定供应商后)\s*(\d+)\s*(个)?\s*(日历天|工作日|天|日|月|年|周内)',
            r'(?:交货时间|完工时间|完成时间|实施周期)[\s]*[：:]*\s*([^，；;。\n]{1,50})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()[:100]

        return ''

    def _extract_warranty_period(self, text: str) -> str:
        """提取质保期"""
        patterns = [
            r'(?:质保期|保修期|质量保证期|免费维护期)[\s]*[：:]*\s*([^，；;。\n]{1,50})',
            r'(?:质保|保修)\s*(不少于|至少|≥|至少为|最低)?\s*(\d+)\s*(个)?\s*(年|月|日|天)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()[:100]

        return ''

    def _extract_payment_terms(self, text: str) -> str:
        """提取付款方式"""
        patterns = [
            r'(?:付款方式|支付条件|结算方式|合同款支付|价款支付)[\s]*[：:]*\s*([^\n]*(?:\n[^\n]{0,2}[^\n]*)*)',
            r'(?:预付款|进度款|验收款|质保金|尾款|分期付款)[\s]*[：:]*\s*([^，；;。\n]{1,100})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()[:200]

        return ''

    def _extract_evaluation_method(self, text: str) -> str:
        """提取评标方法"""
        patterns = [
            r'(?:评标方法|评审方法|评审标准|评分标准|评审办法|中标原则)[\s]*[：:]*\s*([^\n]{1,100})',
            r'(?:综合评分法|最低价法|最低评标价法|竞争性谈判|单一来源|询价)[\s]*',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()[:100]

        return ''
