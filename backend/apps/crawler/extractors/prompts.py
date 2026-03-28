"""
LLM Prompt 模板管理

提供高质量的中文 Prompt 模板，用于招标信息结构化提取
支持 OpenRouter、OpenAI、Claude、Ollama 等提供商
"""
from typing import List, Dict, Optional


class TenderExtractionPrompts:
    """招标信息提取 Prompt 模板"""

    # System Prompt - 定义角色和任务
    SYSTEM_PROMPT = """你是一个专业的招标信息提取专家。你的任务是从网页内容中提取结构化的招标信息，并以 JSON 格式返回。

请严格按照以下 JSON Schema 格式返回结果：
{schema_description}

重要规则：
1. **只返回 JSON 格式**，不要有任何其他文字、解释或 markdown 标记
2. 如果某个字段无法确定，设为 null
3. **金额处理**：统一转换为"元"为单位（如：100万元 = 1000000）
4. **日期格式**：使用 ISO 8601 格式 (YYYY-MM-DD)，如：2024-01-15
5. **清理 HTML**：从文本内容中提取，忽略 HTML 标签和样式
6. **保持字段准确性**：确保每个字段的名称和值准确对应
7. **公告类型判断**：
   - 包含"招标公告"、"采购公告"、"竞争性磋商"等 -> bidding
   - 包含"中标公告"、"成交公告"、"结果公告"、"中标候选人"等 -> win
   - 包含"变更公告"、"补遗"、"澄清"等 -> change
8. **地区识别**：从标题或内容中提取省份/城市名称
9. **行业识别**：根据项目内容判断行业类型（如：工程建设、医疗设备、IT软件等）

请确保返回的是有效的 JSON 对象，可以被 Python 的 json.loads() 解析。"""

    # Schema 描述（用于 Prompt）
    SCHEMA_DESCRIPTION = """{
    "title": "string - 招标/中标/变更公告标题",
    "tenderer": "string - 招标人/采购单位名称",
    "winner": "string - 中标人/成交供应商名称（中标公告时填写）",
    "budget_amount": "number - 预算/中标金额，统一转换为元（如：1000000表示100万元）",
    "budget_unit": "string - 原始金额单位（元/万元/亿元）",
    "currency": "string - 货币类型（CNY/USD/EUR），默认CNY",
    "publish_date": "string - 发布日期，格式：YYYY-MM-DD",
    "deadline_date": "string - 截止日期/开标日期，格式：YYYY-MM-DD",
    "project_number": "string - 项目编号/采购编号",
    "region": "string - 地区/省份（如：吉林省、北京市、上海市）",
    "industry": "string - 行业分类（如：工程建设、医疗设备、IT软件、办公用品）",
    "contact_person": "string - 联系人姓名",
    "contact_phone": "string - 联系电话",
    "description": "string - 项目简要描述",
    "notice_type": "string - 公告类型：bidding(招标)|win(中标)|change(变更)"
}"""

    # Few-shot 示例 - 招标公告
    EXAMPLE_BIDDING = {
        "input": """
        吉林省信息化建设促进中心委托业务服务项目竞争性磋商公告

        项目编号：JLTC-2024-001
        采购单位：吉林省信息化建设促进中心
        预算金额：50万元
        发布时间：2024年3月15日
        截止时间：2024年3月25日 14:00

        项目概况：
        本次采购内容为信息化建设促进中心的委托业务服务，包括系统维护、技术支持等。

        联系人：李明
        联系电话：0431-12345678
        """,
        "output": {
            "title": "吉林省信息化建设促进中心委托业务服务项目竞争性磋商公告",
            "tenderer": "吉林省信息化建设促进中心",
            "winner": None,
            "budget_amount": 500000,
            "budget_unit": "万元",
            "currency": "CNY",
            "publish_date": "2024-03-15",
            "deadline_date": "2024-03-25",
            "project_number": "JLTC-2024-001",
            "region": "吉林省",
            "industry": "IT服务",
            "contact_person": "李明",
            "contact_phone": "0431-12345678",
            "description": "信息化建设促进中心的委托业务服务，包括系统维护、技术支持等",
            "notice_type": "bidding"
        }
    }

    # Few-shot 示例 - 中标公告
    EXAMPLE_WIN = {
        "input": """
        长春市公共资源交易中心办公设备采购项目中标公告

        项目编号：CCGG-2024-008
        采购单位：长春市公共资源交易中心
        中标单位：长春某某科技有限公司
        中标金额：28.5万元
        公告日期：2024年4月10日

        采购内容：办公电脑、打印机、投影仪等设备
        """,
        "output": {
            "title": "长春市公共资源交易中心办公设备采购项目中标公告",
            "tenderer": "长春市公共资源交易中心",
            "winner": "长春某某科技有限公司",
            "budget_amount": 285000,
            "budget_unit": "万元",
            "currency": "CNY",
            "publish_date": "2024-04-10",
            "deadline_date": None,
            "project_number": "CCGG-2024-008",
            "region": "吉林省",
            "industry": "办公设备",
            "contact_person": None,
            "contact_phone": None,
            "description": "办公电脑、打印机、投影仪等设备采购",
            "notice_type": "win"
        }
    }

    # Few-shot 示例 - 带 HTML 标签的内容
    EXAMPLE_HTML = {
        "input": """
        <div class="content">
            <h1><font color='red'>[电子化]</font> 某市人民医院医疗设备采购项目招标公告</h1>
            <p>项目编号：<span class="highlight">XYZ-2024-001</span></p>
            <p>招标人：<b>某市人民医院</b></p>
            <p>预算金额：500万元</p>
            <p>发布时间：2024年1月15日</p>
            <p>投标截止：2024年2月15日</p>
        </div>
        """,
        "output": {
            "title": "某市人民医院医疗设备采购项目招标公告",
            "tenderer": "某市人民医院",
            "winner": None,
            "budget_amount": 5000000,
            "budget_unit": "万元",
            "currency": "CNY",
            "publish_date": "2024-01-15",
            "deadline_date": "2024-02-15",
            "project_number": "XYZ-2024-001",
            "region": None,
            "industry": "医疗设备",
            "contact_person": None,
            "contact_phone": None,
            "description": None,
            "notice_type": "bidding"
        }
    }

    @classmethod
    def build_messages(
        cls,
        content: str,
        source_url: str = "",
        use_few_shot: bool = True,
        custom_schema: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        构建完整的消息列表

        Args:
            content: 网页文本内容
            source_url: 来源 URL
            use_few_shot: 是否使用 few-shot 示例
            custom_schema: 自定义 Schema 描述

        Returns:
            消息列表，可直接传递给 LLM
        """
        schema_desc = custom_schema or cls.SCHEMA_DESCRIPTION

        # 构建 system prompt
        system_prompt = cls.SYSTEM_PROMPT.format(schema_description=schema_desc.strip())

        messages = [{"role": "system", "content": system_prompt}]

        # 添加 few-shot 示例
        if use_few_shot:
            # 示例 1：招标公告
            messages.append({
                "role": "user",
                "content": f"请从以下内容中提取招标信息：\n\n{cls.EXAMPLE_BIDDING['input']}"
            })
            messages.append({
                "role": "assistant",
                "content": cls._format_json(cls.EXAMPLE_BIDDING['output'])
            })

            # 示例 2：中标公告
            messages.append({
                "role": "user",
                "content": f"请从以下内容中提取招标信息：\n\n{cls.EXAMPLE_WIN['input']}"
            })
            messages.append({
                "role": "assistant",
                "content": cls._format_json(cls.EXAMPLE_WIN['output'])
            })

            # 示例 3：带 HTML 的内容
            messages.append({
                "role": "user",
                "content": f"请从以下内容中提取招标信息：\n\n{cls.EXAMPLE_HTML['input']}"
            })
            messages.append({
                "role": "assistant",
                "content": cls._format_json(cls.EXAMPLE_HTML['output'])
            })

        # 添加实际请求
        user_content = f"""请从以下网页内容中提取招标信息：

网页来源：{source_url or '未知'}

网页内容：
{content[:6000]}

请提取结构化信息并返回 JSON。"""

        messages.append({"role": "user", "content": user_content})

        return messages

    @classmethod
    def build_simple_prompt(
        cls,
        content: str,
        source_url: str = ""
    ) -> str:
        """
        构建简单 Prompt（用于不支持多轮对话的模型）

        Args:
            content: 网页内容
            source_url: 来源 URL

        Returns:
            完整的 Prompt 字符串
        """
        prompt = f"""{cls.SYSTEM_PROMPT.format(schema_description=cls.SCHEMA_DESCRIPTION)}

请从以下网页内容中提取招标信息：

网页来源：{source_url or '未知'}

网页内容：
{content[:6000]}

请提取结构化信息并返回 JSON。"""

        return prompt

    @staticmethod
    def _format_json(data: dict) -> str:
        """格式化 JSON 输出"""
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)


class TenderExtractionConfig:
    """提取配置"""

    # OpenRouter 推荐的模型（按性能和成本排序）
    OPENROUTER_MODELS = {
        # 高性能（推荐用于生产环境）
        'high_quality': [
            'anthropic/claude-3.5-sonnet',  # 最佳性价比
            'openai/gpt-4o-mini',  # 快速且便宜
            'google/gemini-flash-1.5',  # 免费额度大
        ],
        # 经济型
        'economy': [
            'google/gemini-flash-1.5',
            'openai/gpt-4o-mini',
            'meta-llama/llama-3.1-8b-instruct',
        ],
        # 免费模型
        'free': [
            'google/gemini-flash-1.5:free',
            'meta-llama/llama-3.1-70b-instruct:free',
        ]
    }

    # 默认配置
    DEFAULT_CONFIG = {
        'max_retries': 3,
        'retry_delay': 1.0,
        'timeout_seconds': 60,
        'max_content_length': 6000,  # 发送到 LLM 的最大内容长度
        'use_few_shot': True,
        'min_confidence': 0.5,
        'preferred_model': 'anthropic/claude-3.5-sonnet',
    }
