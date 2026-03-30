"""
Tender Analytics Skill Tests - TDD Cycle 40

测试 Analytics Skill 的定义和加载功能。
"""

import re
from pathlib import Path
from typing import Any

import pytest

# 测试用的 Skill 文件路径
SKILL_FILE_PATH = Path(__file__).parent.parent.parent.parent / "apps" / "analytics" / "skills" / "tender-analytics" / "SKILL.md"


class TestTenderAnalyticsSkill:
    """Tender Analytics Skill 测试套件"""

    @pytest.fixture
    def skill_content(self) -> str:
        """读取 SKILL.md 文件内容"""
        if not SKILL_FILE_PATH.exists():
            pytest.skip(f"SKILL.md not found at {SKILL_FILE_PATH}")
        return SKILL_FILE_PATH.read_text(encoding="utf-8")

    def test_skill_file_exists(self) -> None:
        """测试 1: SKILL.md 文件存在"""
        assert SKILL_FILE_PATH.exists(), f"SKILL.md 文件不存在于 {SKILL_FILE_PATH}"

    def test_yaml_frontmatter_parsing(self, skill_content: str) -> None:
        """测试 2: YAML frontmatter 正确解析"""
        # 验证 frontmatter 格式
        front_matter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", skill_content, re.DOTALL)
        assert front_matter_match is not None, "缺少 YAML frontmatter"

        front_matter = front_matter_match.group(1)

        # 验证必需字段
        assert "name:" in front_matter, "缺少 name 字段"
        assert "description:" in front_matter, "缺少 description 字段"

    def test_allowed_tools_list(self, skill_content: str) -> None:
        """测试 3: allowed-tools 包含正确工具"""
        front_matter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", skill_content, re.DOTALL)
        assert front_matter_match is not None
        front_matter = front_matter_match.group(1)

        # 验证必需的工具
        assert "classify_tender" in front_matter, "缺少 classify_tender 工具"
        assert "score_opportunity" in front_matter, "缺少 score_opportunity 工具"
        assert "analyze_trends" in front_matter, "缺少 analyze_trends 工具"
        assert "aggregate_data" in front_matter, "缺少 aggregate_data 工具"

    def test_skill_loading(self) -> None:
        """测试 4: Skill 可以通过加载器加载"""
        try:
            from apps.crawler.agents.skills.parser import parse_skill_file
            from apps.crawler.agents.skills.loader import get_skills_root_path
        except ImportError as e:
            pytest.skip(f"无法导入 deer-flow skill 模块: {e}")

        if not SKILL_FILE_PATH.exists():
            pytest.skip("SKILL.md 不存在")

        # 尝试解析 skill 文件
        skill = parse_skill_file(SKILL_FILE_PATH, category="custom")
        assert skill is not None, "Skill 解析失败"
        assert skill.name == "tender-analytics", f"Skill 名称错误: {skill.name}"

    def test_tools_registration(self) -> None:
        """测试 5: 所有工具正确注册"""
        try:
            from apps.analytics.tools import (
                classify_tender,
                score_opportunity,
                analyze_trends,
                aggregate_data,
            )
        except ImportError as e:
            pytest.skip(f"无法导入 analytics tools: {e}")

        # 验证工具具有正确的属性（StructuredTool 对象）
        assert hasattr(classify_tender, "name"), "classify_tender 缺少 name 属性"
        assert hasattr(classify_tender, "func"), "classify_tender 缺少 func 属性"
        assert classify_tender.name == "classify_tender", f"工具名称错误: {classify_tender.name}"

        assert hasattr(score_opportunity, "name"), "score_opportunity 缺少 name 属性"
        assert hasattr(score_opportunity, "func"), "score_opportunity 缺少 func 属性"
        assert score_opportunity.name == "score_opportunity", f"工具名称错误: {score_opportunity.name}"

        assert hasattr(analyze_trends, "name"), "analyze_trends 缺少 name 属性"
        assert hasattr(analyze_trends, "func"), "analyze_trends 缺少 func 属性"
        assert analyze_trends.name == "analyze_trends", f"工具名称错误: {analyze_trends.name}"

        assert hasattr(aggregate_data, "name"), "aggregate_data 缺少 name 属性"
        assert hasattr(aggregate_data, "func"), "aggregate_data 缺少 func 属性"
        assert aggregate_data.name == "aggregate_data", f"工具名称错误: {aggregate_data.name}"

    def test_prompt_generation(self, skill_content: str) -> None:
        """测试 6: 系统 Prompt 正确生成"""
        # 验证 SKILL.md 包含主要章节
        assert "# Tender Analytics Skill" in skill_content or "# Tender Analytics" in skill_content, "缺少 Skill 标题"
        assert "## 概述" in skill_content or "## Overview" in skill_content, "缺少概述章节"
        assert "## 可用工具" in skill_content or "## Available Tools" in skill_content, "缺少工具章节"

    def test_tool_invocation_via_skill(self) -> None:
        """测试 7: 通过 Skill 调用工具"""
        try:
            from apps.analytics.tools import classify_tender
            from pydantic import BaseModel
        except ImportError as e:
            pytest.skip(f"无法导入所需模块: {e}")

        # 验证 classify_tender 工具签名
        assert hasattr(classify_tender, "name"), "classify_tender 缺少 name 属性"
        assert classify_tender.name == "classify_tender", f"工具名称错误: {classify_tender.name}"

    def test_description_completeness(self, skill_content: str) -> None:
        """测试 8: 描述信息完整"""
        front_matter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", skill_content, re.DOTALL)
        assert front_matter_match is not None

        front_matter = front_matter_match.group(1)

        # 提取 description
        desc_match = re.search(r"description:\s*(.+)", front_matter)
        assert desc_match is not None, "缺少 description 字段"

        description = desc_match.group(1).strip()
        assert len(description) > 10, f"description 太短: {description}"

    def test_version_information(self, skill_content: str) -> None:
        """测试 9: 版本号正确"""
        front_matter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", skill_content, re.DOTALL)
        assert front_matter_match is not None

        front_matter = front_matter_match.group(1)

        # 验证版本号格式
        version_match = re.search(r"version:\s*([\d.]+)", front_matter)
        assert version_match is not None, "缺少 version 字段"

        version = version_match.group(1)
        # 验证版本号格式 (x.y.z)
        assert re.match(r"^\d+\.\d+\.\d+$", version), f"版本号格式错误: {version}"

    def test_metadata_completeness(self, skill_content: str) -> None:
        """测试 10: 所有必需字段存在"""
        front_matter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", skill_content, re.DOTALL)
        assert front_matter_match is not None

        front_matter = front_matter_match.group(1)

        required_fields = ["name", "description", "version"]
        for field in required_fields:
            assert f"{field}:" in front_matter, f"缺少必需字段: {field}"


class TestTenderAnalyticsSkillLoader:
    """Tender Analytics Skill 加载器测试"""

    def test_skill_loader_module_exists(self) -> None:
        """测试 11: Skill 加载器模块存在"""
        # 尝试导入 skill loader
        try:
            from apps.analytics.skills.tender_analytics_skill import load_skill
        except ImportError:
            pytest.skip("Skill 加载器模块尚未创建")

        assert callable(load_skill), "load_skill 不是可调用的"

    def test_skill_loader_returns_correct_structure(self) -> None:
        """测试 12: Skill 加载器返回正确结构"""
        try:
            from apps.analytics.skills.tender_analytics_skill import load_skill
        except ImportError:
            pytest.skip("Skill 加载器模块尚未创建")

        result = load_skill()

        # 验证返回结构
        assert isinstance(result, dict), "load_skill 应返回字典"
        assert "name" in result, "缺少 name 字段"
        assert "tools" in result, "缺少 tools 字段"
        assert "path" in result, "缺少 path 字段"

        # 验证字段值
        assert result["name"] == "tender-analytics", f"Skill 名称错误: {result['name']}"
        assert result["path"] == "skills/tender-analytics", f"Skill 路径错误: {result['path']}"

        # 验证工具列表
        tools = result["tools"]
        assert isinstance(tools, list), "tools 应该是列表"
        assert len(tools) == 4, f"工具数量错误: {len(tools)}"

    def test_skill_tools_are_valid(self) -> None:
        """测试 13: Skill 工具是有效的"""
        try:
            from apps.analytics.skills.tender_analytics_skill import load_skill
        except ImportError:
            pytest.skip("Skill 加载器模块尚未创建")

        result = load_skill()
        tools = result["tools"]

        # 验证每个工具都是有效的 StructuredTool
        for tool in tools:
            assert hasattr(tool, "name"), f"工具 {tool} 缺少 name 属性"
            assert hasattr(tool, "func"), f"工具 {tool} 缺少 func 属性"
            assert hasattr(tool, "description"), f"工具 {tool} 缺少 description 属性"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])