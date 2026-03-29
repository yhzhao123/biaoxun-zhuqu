"""
Deer-Flow 集成配置模块

提供 Deer-Flow 框架集成所需的配置类
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class DeerFlowConfig:
    """Deer-Flow 基础配置"""
    # LLM 配置
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096

    # 并发控制
    max_concurrent_subagents: int = 3
    max_concurrent_llm_calls: int = 2
    request_delay: float = 1.0
    llm_delay: float = 1.0

    # 重试配置
    max_retries: int = 3
    base_delay: float = 2.0
    circuit_breaker_threshold: int = 5

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 7200

    # 技能配置
    skills_dir: str = "skills"
    enabled_skills: list[str] = None

    def __post_init__(self):
        if self.enabled_skills is None:
            self.enabled_skills = [
                "tender-extraction",
                "pdf-analysis",
                "field-validation",
                "error-recovery",
            ]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_concurrent_subagents": self.max_concurrent_subagents,
            "max_concurrent_llm_calls": self.max_concurrent_llm_calls,
            "request_delay": self.request_delay,
            "llm_delay": self.llm_delay,
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "skills_dir": self.skills_dir,
            "enabled_skills": self.enabled_skills,
        }


@dataclass
class TenderToolConfig:
    """招标工具特定配置"""
    # 字段提取配置
    required_fields: list[str] = None
    confidence_threshold: float = 0.6
    use_list_data: bool = True
    use_regex_preprocessing: bool = True

    # PDF 处理配置
    pdf_max_pages: int = 100
    extract_tables: bool = True
    extract_images: bool = False

    # 输出配置
    output_format: str = "json"  # json, schema, dict
    save_raw_html: bool = False
    save_pdf_content: bool = True

    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = [
                "title",
                "tenderer",
                "publish_date",
                "budget_amount",
            ]

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            return False
        if self.pdf_max_pages < 1:
            return False
        if self.output_format not in ["json", "schema", "dict"]:
            return False
        return True


class ConfigManager:
    """配置管理器"""

    _instance: Optional["ConfigManager"] = None
    _deer_flow_config: Optional[DeerFlowConfig] = None
    _tender_tool_config: Optional[TenderToolConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_deer_flow_config(cls) -> DeerFlowConfig:
        """获取 Deer-Flow 配置"""
        if cls._deer_flow_config is None:
            cls._deer_flow_config = DeerFlowConfig()
        return cls._deer_flow_config

    @classmethod
    def get_tender_tool_config(cls) -> TenderToolConfig:
        """获取招标工具配置"""
        if cls._tender_tool_config is None:
            cls._tender_tool_config = TenderToolConfig()
        return cls._tender_tool_config

    @classmethod
    def reset(cls) -> None:
        """重置配置（主要用于测试）"""
        cls._deer_flow_config = None
        cls._tender_tool_config = None
