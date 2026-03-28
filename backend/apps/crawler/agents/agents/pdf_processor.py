"""
PDF 处理智能体

下载并解析PDF附件，提取文本和表格
"""
import logging
import io
import os
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import aiohttp

from apps.crawler.agents.schema import Attachment, TenderNoticeSchema

logger = logging.getLogger(__name__)


class PDFProcessorAgent:
    """
    PDF处理智能体

    下载并解析招标公告PDF附件
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.llm_service = None
        # 延迟初始化
        # self._init_llm()

    def _init_llm(self):
        """初始化LLM服务"""
        try:
            from apps.llm.services import LLMService
            from apps.llm.models import LLMConfig

            config = LLMConfig.objects.filter(is_active=True, is_default=True).first()
            if not config:
                config = LLMConfig.objects.filter(is_active=True).first()

            if config:
                self.llm_service = LLMService(config)
        except Exception as e:
            logger.warning(f"Failed to init LLM: {e}")

    async def process(self, attachment: Attachment) -> Optional[Dict]:
        """
        处理PDF附件

        Args:
            attachment: 附件信息

        Returns:
            提取的字段字典
        """
        try:
            logger.info(f"Processing PDF: {attachment.filename}")

            # 下载PDF
            pdf_bytes = await self._download_pdf(attachment.url)
            if not pdf_bytes:
                return None

            # 提取文本
            text = self._extract_text(pdf_bytes)
            if not text:
                logger.warning(f"No text extracted from PDF: {attachment.filename}")
                return None

            # 提取表格
            tables = self._extract_tables(pdf_bytes)

            # 使用LLM提取字段
            extracted = await self._extract_from_content(text, tables)
            extracted['source'] = 'pdf'

            return extracted

        except Exception as e:
            logger.error(f"Failed to process PDF {attachment.filename}: {e}")
            return None

    async def _download_pdf(self, url: str) -> Optional[bytes]:
        """下载PDF文件"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    response.raise_for_status()

                    # 检查Content-Type
                    content_type = response.headers.get('Content-Type', '')
                    if 'pdf' not in content_type.lower():
                        logger.warning(f"Content-Type not PDF: {content_type}")

                    return await response.read()

        except Exception as e:
            logger.error(f"Failed to download PDF {url}: {e}")
            return None

    def _extract_text(self, pdf_bytes: bytes) -> str:
        """从PDF提取文本"""
        try:
            # 尝试使用 pdfplumber
            import pdfplumber

            text = ""
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            return text.strip()

        except ImportError:
            logger.warning("pdfplumber not installed, trying PyMuPDF")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        try:
            # 备用：使用 PyMuPDF (fitz)
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

    def _extract_tables(self, pdf_bytes: bytes) -> List[List[List[str]]]:
        """从PDF提取表格"""
        tables = []

        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")

        return tables

    async def _extract_from_content(
        self,
        text: str,
        tables: List[List[List[str]]]
    ) -> Dict:
        """使用LLM从PDF内容提取字段"""
        if not self.llm_service:
            return self._fallback_extract(text)

        try:
            from apps.crawler.agents.agents.field_extractor import FieldExtractorAgent

            # 格式化表格
            tables_text = self._format_tables(tables)

            prompt = f"""从以下PDF文档内容中提取招标信息：

文档文本:
{text[:8000]}

提取的表格:
{tables_text}

请提取以下字段（JSON格式）：
- tenderer: 招标人/采购人
- budget_amount: 预算金额（转换为元）
- contact_person: 联系人
- contact_phone: 联系电话
- description: 项目描述
- project_number: 项目编号

只返回JSON对象。"""

            response = self.llm_service.chat([
                {"role": "system", "content": "你是一个专业的招标信息提取专家。"},
                {"role": "user", "content": prompt}
            ], "")

            raw_response = response.get('message', '')

            # 解析JSON
            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                return json.loads(json_match.group(0))

        except Exception as e:
            logger.error(f"LLM extraction from PDF failed: {e}")

        return self._fallback_extract(text)

    def _format_tables(self, tables: List[List[List[str]]]) -> str:
        """格式化表格为文本"""
        if not tables:
            return "无表格"

        text = ""
        for i, table in enumerate(tables[:3], 1):  # 只取前3个表格
            text += f"\n表格 {i}:\n"
            for row in table[:10]:  # 每表只取前10行
                text += " | ".join(str(cell) for cell in row if cell) + "\n"

        return text

    def _fallback_extract(self, text: str) -> Dict:
        """备用提取方法"""
        import re

        result = {'source': 'pdf_fallback'}

        # 简单正则匹配
        patterns = {
            'tenderer': r'(招标人|采购人|采购单位)[：:]\s*([^\n]+)',
            'contact_person': r'(联系人|经办人)[：:]\s*([^\n]+)',
            'contact_phone': r'(联系电话|联系方式|电话)[：:]\s*([^\n]+)',
            'project_number': r'(项目编号|采购编号|招标编号)[：:]\s*([^\n]+)',
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                result[field] = match.group(2).strip()

        return result
