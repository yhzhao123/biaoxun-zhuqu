"""
数据验证和清洗系统

TDD Cycle 24: 招标数据验证和清洗系统
- 招标数据验证（标题、金额、日期、URL 等字段验证）
- 数据清洗（去除 HTML 标签、标准化格式、去重）
- 数据转换（货币格式统一、日期格式统一）
- 验证规则配置（可配置的验证规则）
- 批量验证和清洗
- 验证报告生成
"""
import re
import html
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


# ============== 数据类定义 ==============

@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    code: str
    value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "code": self.code,
            "value": self.value,
        }


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "error_count": self.error_count,
        }


# ============== 配置类 ==============

@dataclass
class ValidationConfig:
    """验证配置"""
    # 标题验证
    title_min_length: int = 5
    title_max_length: int = 200

    # 金额验证
    budget_min: Decimal = Decimal("0")
    budget_max: Decimal = Decimal("999999999999")  # 9999亿

    # 日期验证
    date_max_future_years: int = 1  # 未来最多1年

    # 必填字段
    required_fields: List[str] = field(default_factory=lambda: ["title"])

    # 清洗配置
    allow_html_tags: bool = False
    allow_special_chars: bool = False

    # URL 验证
    validate_url: bool = True

    # 电话验证
    validate_phone: bool = True


# ============== 验证器 ==============

class TenderValidator:
    """招标数据验证器"""

    # URL 正则
    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    # 电话正则（中国电话格式）
    PHONE_PATTERN = re.compile(
        r'^(\d{3,4}-?)?\d{7,8}$|'
        r'^1[3-9]\d{9}$'
    )

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()

    def validate(self, data: Optional[Dict[str, Any]]) -> ValidationResult:
        """验证招标数据"""
        if data is None:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field="data",
                    message="数据不能为空",
                    code="NULL_DATA",
                    value=None
                )]
            )

        errors: List[ValidationError] = []

        # 验证必填字段
        errors.extend(self._validate_required_fields(data))

        # 验证标题
        errors.extend(self._validate_title(data.get("title")))

        # 验证金额
        errors.extend(self._validate_budget(data.get("budget_amount")))

        # 验证日期
        errors.extend(self._validate_date(data.get("publish_date"), "publish_date"))
        errors.extend(self._validate_date(data.get("deadline_date"), "deadline_date"))

        # 验证 URL
        errors.extend(self._validate_url(data.get("source_url")))

        # 验证电话
        errors.extend(self._validate_phone(data.get("contact_phone")))

        # 验证置信度
        errors.extend(self._validate_confidence(data.get("extraction_confidence")))

        # 验证公告类型
        errors.extend(self._validate_notice_type(data.get("notice_type")))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def _validate_required_fields(self, data: Dict[str, Any]) -> List[ValidationError]:
        """验证必填字段"""
        errors = []
        for field_name in self.config.required_fields:
            value = data.get(field_name)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                errors.append(ValidationError(
                    field=field_name,
                    message=f"{field_name} 是必填字段",
                    code="REQUIRED",
                    value=value
                ))
        return errors

    def _validate_title(self, title: Any) -> List[ValidationError]:
        """验证标题"""
        errors = []
        if title is None:
            return errors  # 必填字段已单独验证

        if not isinstance(title, str):
            errors.append(ValidationError(
                field="title",
                message="标题必须是字符串",
                code="INVALID_TYPE",
                value=title
            ))
            return errors

        title = title.strip()
        title_len = len(title)

        if title_len < self.config.title_min_length:
            errors.append(ValidationError(
                field="title",
                message=f"标题长度太短（至少{self.config.title_min_length}个字符）",
                code="TITLE_TOO_SHORT",
                value=title
            ))

        if title_len > self.config.title_max_length:
            errors.append(ValidationError(
                field="title",
                message=f"标题长度太长（最多{self.config.title_max_length}个字符）",
                code="TITLE_TOO_LONG",
                value=title
            ))

        return errors

    def _validate_budget(self, budget: Any) -> List[ValidationError]:
        """验证金额"""
        errors = []
        if budget is None:
            return errors

        try:
            budget_decimal = Decimal(str(budget))

            if budget_decimal < self.config.budget_min:
                errors.append(ValidationError(
                    field="budget_amount",
                    message="金额不能为负数",
                    code="BUDGET_NEGATIVE",
                    value=budget
                ))

            if budget_decimal > self.config.budget_max:
                errors.append(ValidationError(
                    field="budget_amount",
                    message=f"金额数值异常过大（最大{self.config.budget_max}）",
                    code="BUDGET_TOO_LARGE",
                    value=budget
                ))
        except (ValueError, TypeError):
            errors.append(ValidationError(
                field="budget_amount",
                message="金额格式无效",
                code="INVALID_BUDGET",
                value=budget
            ))

        return errors

    def _validate_date(self, date_value: Any, field_name: str) -> List[ValidationError]:
        """验证日期"""
        errors = []
        if date_value is None:
            return errors

        # 如果已经是 datetime 类型
        if isinstance(date_value, datetime):
            date_obj = date_value
        elif isinstance(date_value, date):
            date_obj = datetime.combine(date_value, datetime.min.time())
        elif isinstance(date_value, str):
            try:
                # 尝试解析各种日期格式
                date_obj = self._parse_date_string(date_value)
                if date_obj is None:
                    errors.append(ValidationError(
                        field=field_name,
                        message="日期格式无效",
                        code="INVALID_DATE_FORMAT",
                        value=date_value
                    ))
                    return errors
            except Exception:
                errors.append(ValidationError(
                    field=field_name,
                    message="日期格式无效",
                    code="INVALID_DATE_FORMAT",
                    value=date_value
                ))
                return errors
        else:
            errors.append(ValidationError(
                field=field_name,
                message="日期格式无效",
                code="INVALID_DATE_FORMAT",
                value=date_value
            ))
            return errors

        # 验证日期不能太遥远（未来）
        now = datetime.now()
        max_future = now.replace(year=now.year + self.config.date_max_future_years)
        if date_obj > max_future:
            errors.append(ValidationError(
                field=field_name,
                message="日期不能太遥远（未来）",
                code="DATE_TOO_FAR_FUTURE",
                value=date_value
            ))

        return errors

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        # ISO 格式
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            pass

        # 中文格式: 2024年01月15日
        try:
            match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if match:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except Exception:
            pass

        # 斜杠格式: 2024/01/15
        try:
            return datetime.strptime(date_str, "%Y/%m/%d")
        except Exception:
            pass

        # 横杠格式: 2024-01-15
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            pass

        return None

    def _validate_url(self, url: Any) -> List[ValidationError]:
        """验证 URL"""
        errors = []
        if url is None or not self.config.validate_url:
            return errors

        if not isinstance(url, str):
            errors.append(ValidationError(
                field="source_url",
                message="URL 必须是字符串",
                code="INVALID_TYPE",
                value=url
            ))
            return errors

        url = url.strip()
        if url and not self.URL_PATTERN.match(url):
            errors.append(ValidationError(
                field="source_url",
                message="URL 格式无效",
                code="INVALID_URL",
                value=url
            ))

        return errors

    def _validate_phone(self, phone: Any) -> List[ValidationError]:
        """验证电话"""
        errors = []
        if phone is None or not self.config.validate_phone:
            return errors

        if not isinstance(phone, str):
            errors.append(ValidationError(
                field="contact_phone",
                message="电话必须是字符串",
                code="INVALID_TYPE",
                value=phone
            ))
            return errors

        phone = phone.strip()
        if phone and not self.PHONE_PATTERN.match(phone):
            errors.append(ValidationError(
                field="contact_phone",
                message="电话格式无效",
                code="INVALID_PHONE",
                value=phone
            ))

        return errors

    def _validate_confidence(self, confidence: Any) -> List[ValidationError]:
        """验证置信度"""
        errors = []
        if confidence is None:
            return errors

        try:
            conf_value = float(confidence)
            if not 0 <= conf_value <= 1:
                errors.append(ValidationError(
                    field="extraction_confidence",
                    message="置信度必须在 0-1 之间",
                    code="INVALID_CONFIDENCE",
                    value=confidence
                ))
        except (ValueError, TypeError):
            errors.append(ValidationError(
                field="extraction_confidence",
                message="置信度格式无效",
                code="INVALID_CONFIDENCE",
                value=confidence
            ))

        return errors

    def _validate_notice_type(self, notice_type: Any) -> List[ValidationError]:
        """验证公告类型"""
        errors = []
        if notice_type is None:
            return errors

        valid_types = ["bidding", "win", "change"]
        if notice_type not in valid_types:
            errors.append(ValidationError(
                field="notice_type",
                message=f"公告类型必须是以下之一: {valid_types}",
                code="INVALID_NOTICE_TYPE",
                value=notice_type
            ))

        return errors


# ============== 清洗器 ==============

class TenderCleaner:
    """招标数据清洗器"""

    # HTML 标签正则
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    # HTML 实体正则
    HTML_ENTITY_PATTERN = re.compile(r'&[a-zA-Z]+;|&#\d+;')
    # 空白字符正则
    WHITESPACE_PATTERN = re.compile(r'\s+')
    # 特殊空白字符
    SPECIAL_WHITESPACE_PATTERN = re.compile(r'[\u200b-\u200f\u3000\ufeff]')

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()

    def clean_tender_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗招标数据"""
        cleaned = {}

        for key, value in data.items():
            if value is None:
                cleaned[key] = None
                continue

            if isinstance(value, str):
                # 清洗字符串
                cleaned[key] = self._clean_string(value)
            elif isinstance(value, dict):
                # 递归清洗字典
                cleaned[key] = self.clean_tender_data(value)
            elif isinstance(value, list):
                # 清洗列表
                cleaned[key] = [
                    self._clean_string(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                cleaned[key] = value

        return cleaned

    def _clean_string(self, value: str) -> str:
        """清洗字符串"""
        if not isinstance(value, str):
            return value

        # 去除特殊空白字符（零宽字符等）
        if not self.config.allow_special_chars:
            value = self.clean_special_chars(value)

        # 去除 HTML 标签
        if not self.config.allow_html_tags:
            value = self.clean_html_tags(value)

        # 去除 HTML 实体
        value = html.unescape(value)

        # 标准化空白字符
        value = self.clean_whitespace(value)

        # 去除首尾空白
        value = value.strip()

        # 空字符串转为 None
        if value == "":
            return ""

        return value

    def clean_html_tags(self, text: str) -> str:
        """去除 HTML 标签"""
        # 先去除标签
        text = self.HTML_TAG_PATTERN.sub('', text)
        # 再去除 HTML 实体
        text = self.HTML_ENTITY_PATTERN.sub('', text)
        return text

    def clean_whitespace(self, text: str) -> str:
        """标准化空白字符"""
        # 替换多个空白为单个空格
        text = self.WHITESPACE_PATTERN.sub(' ', text)
        return text.strip()

    def clean_special_chars(self, text: str) -> str:
        """去除特殊空白字符"""
        # 去除零宽字符等
        text = self.SPECIAL_WHITESPACE_PATTERN.sub('', text)
        return text

    def normalize_company_name(self, name: str) -> str:
        """标准化企业名称"""
        if not name:
            return ""

        # 去除首尾空白
        name = name.strip()

        # 去除常见后缀（可选）
        suffixes = ["有限公司", "股份有限公司", "有限责任公司", "集团有限公司"]
        # 保留完整名称，仅做简单标准化
        return name


# ============== 转换器 ==============

class TenderTransformer:
    """招标数据转换器"""

    # 金额单位映射
    BUDGET_UNIT_MAP = {
        "元": Decimal("1"),
        "万元": Decimal("10000"),
        "万元": Decimal("10000"),
        "亿元": Decimal("100000000"),
        "亿": Decimal("100000000"),
        "万": Decimal("10000"),
    }

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()

    def transform_tender_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换招标数据"""
        transformed = data.copy()

        # 转换金额
        if "budget_amount" in data and "budget_unit" in data:
            budget_amount = data.get("budget_amount")
            budget_unit = data.get("budget_unit")
            if budget_amount is not None and budget_unit is not None:
                transformed["budget_amount"] = self.transform_budget(budget_amount, budget_unit)

        # 转换日期
        if "publish_date" in data:
            transformed["publish_date"] = self.transform_date(data["publish_date"])

        if "deadline_date" in data:
            transformed["deadline_date"] = self.transform_date(data["deadline_date"])

        # 标准化 URL
        if "source_url" in data and data["source_url"]:
            transformed["source_url"] = self.normalize_url(data["source_url"])

        # 标准化电话
        if "contact_phone" in data and data["contact_phone"]:
            transformed["contact_phone"] = self.normalize_phone(data["contact_phone"])

        return transformed

    def transform_budget(self, amount: Any, unit: str) -> Optional[Decimal]:
        """转换金额到元"""
        if amount is None:
            return None

        from decimal import InvalidOperation, DecimalException

        try:
            # 清理金额字符串
            amount_str = str(amount).strip()
            # 去除货币符号和千分位
            amount_str = re.sub(r'[￥$,，]', '', amount_str)
            amount_str = amount_str.strip()

            amount_decimal = Decimal(amount_str)

            # 应用单位
            unit_normalized = unit.strip()
            multiplier = self.BUDGET_UNIT_MAP.get(unit_normalized, Decimal("1"))

            return amount_decimal * multiplier

        except (ValueError, TypeError, InvalidOperation, DecimalException):
            return None

    def transform_date(self, date_value: Any) -> Optional[datetime]:
        """转换日期"""
        if date_value is None:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, date):
            return datetime.combine(date_value, datetime.min.time())

        if isinstance(date_value, str):
            return self._parse_date_string(date_value.strip())

        return None

    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        # ISO 格式
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            pass

        # 中文格式: 2024年01月15日
        try:
            match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if match:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except Exception:
            pass

        # 斜杠格式: 2024/01/15
        try:
            return datetime.strptime(date_str, "%Y/%m/%d")
        except Exception:
            pass

        # 横杠格式: 2024-01-15
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            pass

        return None

    def normalize_url(self, url: str) -> str:
        """标准化 URL"""
        if not url:
            return ""

        url = url.strip()
        # 去除多余空格
        url = re.sub(r'\s+', '', url)
        return url

    def normalize_phone(self, phone: str) -> str:
        """标准化电话"""
        if not phone:
            return ""

        phone = phone.strip()
        # 去除空格
        phone = re.sub(r'\s+', '', phone)
        return phone


# ============== 批量处理器 ==============

class BatchProcessor:
    """批量处理招标数据"""

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        validator: Optional[TenderValidator] = None,
        cleaner: Optional[TenderCleaner] = None,
        transformer: Optional[TenderTransformer] = None
    ):
        self.config = config or ValidationConfig()
        self.validator = validator or TenderValidator(self.config)
        self.cleaner = cleaner or TenderCleaner(self.config)
        self.transformer = transformer or TenderTransformer(self.config)

    def batch_validate(self, tenders: List[Dict[str, Any]]) -> List[ValidationResult]:
        """批量验证"""
        return [self.validator.validate(tender) for tender in tenders]

    def batch_clean(self, tenders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量清洗"""
        return [self.cleaner.clean_tender_data(tender) for tender in tenders]

    def batch_transform(self, tenders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量转换"""
        return [self.transformer.transform_tender_data(tender) for tender in tenders]

    def process_batch(
        self,
        tenders: List[Dict[str, Any]],
        clean: bool = True,
        transform: bool = True,
        validate: bool = True
    ) -> List[Dict[str, Any]]:
        """完整流水线处理"""
        results = []

        for tender in tenders:
            processed = {"original": tender}

            # 清洗
            if clean:
                tender = self.cleaner.clean_tender_data(tender)
                processed["cleaned"] = tender

            # 转换
            if transform:
                tender = self.transformer.transform_tender_data(tender)
                processed["transformed"] = tender

            # 验证
            if validate:
                validation_result = self.validator.validate(tender)
                processed["validation_result"] = validation_result
                processed["is_valid"] = validation_result.is_valid
            else:
                processed["is_valid"] = None

            results.append(processed)

        return results


# ============== 验证报告 ==============

class ValidationReport:
    """验证报告生成器"""

    def generate_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """生成验证报告"""
        total = len(results)
        if total == 0:
            return {
                "total": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "valid_rate": 0,
                "error_summary": {},
            }

        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total - valid_count

        # 错误摘要
        error_summary: Dict[str, int] = {}
        for result in results:
            if not result.is_valid:
                for error in result.errors:
                    error_summary[error.field] = error_summary.get(error.field, 0) + 1

        return {
            "total": total,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "valid_rate": (valid_count / total) * 100,
            "error_summary": error_summary,
        }