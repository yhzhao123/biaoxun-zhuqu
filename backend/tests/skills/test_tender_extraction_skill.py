"""
TenderExtractionSkill 测试

TDD 循环 3: 测试 Skill 内容格式和有效性
"""
import pytest
import re
from pathlib import Path
from typing import Dict, Any, List


class TestTenderExtractionSkill:
    """TenderExtractionSkill 测试"""

    @pytest.fixture
    def skill_content(self) -> str:
        """读取 Skill 文件内容"""
        # 从 backend/tests/skills/ 向上两级到项目根目录
        skill_path = Path(__file__).parent.parent.parent.parent / "skills" / "tender-extraction" / "SKILL.md"
        if not skill_path.exists():
            # 尝试另一种路径
            skill_path = Path.cwd().parent / "skills" / "tender-extraction" / "SKILL.md"
        return skill_path.read_text(encoding="utf-8")

    @pytest.fixture
    def skill_frontmatter(self, skill_content: str) -> Dict[str, Any]:
        """解析 Skill frontmatter"""
        # 提取 frontmatter
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', skill_content, re.DOTALL)
        if not match:
            return {}

        frontmatter_text = match.group(1)
        result = {}

        # 简单解析 YAML
        for line in frontmatter_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # 处理列表
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                # 处理数字
                elif value.isdigit():
                    value = int(value)

                result[key] = value

        return result

    def test_skill_file_exists(self):
        """测试 Skill 文件存在"""
        skill_path = Path(__file__).parent.parent.parent.parent / "skills" / "tender-extraction" / "SKILL.md"
        if not skill_path.exists():
            skill_path = Path.cwd().parent / "skills" / "tender-extraction" / "SKILL.md"
        assert skill_path.exists(), f"Skill file not found: {skill_path.absolute()}"

    def test_skill_file_not_empty(self, skill_content: str):
        """测试 Skill 文件不为空"""
        assert len(skill_content) > 0, "Skill file is empty"
        assert len(skill_content) > 1000, "Skill file content too short"

    def test_frontmatter_exists(self, skill_content: str):
        """测试 frontmatter 存在"""
        assert skill_content.startswith("---"), "Missing frontmatter start"
        assert "---" in skill_content[3:], "Missing frontmatter end"

    def test_frontmatter_name(self, skill_frontmatter: Dict[str, Any]):
        """测试 name 字段"""
        assert "name" in skill_frontmatter, "Missing 'name' in frontmatter"
        assert skill_frontmatter["name"] == "tender-extraction"

    def test_frontmatter_version(self, skill_frontmatter: Dict[str, Any]):
        """测试 version 字段"""
        assert "version" in skill_frontmatter, "Missing 'version' in frontmatter"
        assert skill_frontmatter["version"] == "1.0.0"

    def test_frontmatter_description(self, skill_frontmatter: Dict[str, Any]):
        """测试 description 字段"""
        assert "description" in skill_frontmatter, "Missing 'description' in frontmatter"
        desc = skill_frontmatter["description"]
        assert "招标" in desc or "tender" in desc.lower()

    def test_frontmatter_tags(self, skill_frontmatter: Dict[str, Any]):
        """测试 tags 字段"""
        assert "tags" in skill_frontmatter, "Missing 'tags' in frontmatter"
        tags = skill_frontmatter["tags"]
        assert isinstance(tags, list), "Tags should be a list"
        assert "extraction" in tags, "Missing 'extraction' tag"
        assert "crawler" in tags, "Missing 'crawler' tag"

    def test_frontmatter_priority(self, skill_frontmatter: Dict[str, Any]):
        """测试 priority 字段"""
        assert "priority" in skill_frontmatter, "Missing 'priority' in frontmatter"
        priority = skill_frontmatter["priority"]
        assert isinstance(priority, int), "Priority should be an integer"
        assert priority == 100, "Priority should be 100"

    def test_content_structure(self, skill_content: str):
        """测试内容结构"""
        # 检查主要章节
        required_sections = [
            "## 1. 概述",
            "## 2. 字段优先级",
            "## 3. 工作流程",
            "## 4. 正文信息完整提取",
            "## 5. 工具调用序列",
            "## 6. 最佳实践",
            "## 7. 质量保证",
            "## 8. 错误处理",
            "## 9. 相关资源",
        ]

        for section in required_sections:
            assert section in skill_content, f"Missing section: {section}"

    def test_p0_fields_defined(self, skill_content: str):
        """测试 P0 必需字段定义"""
        # 检查 P0 字段
        p0_fields = ["title", "tenderer", "publish_date"]
        for field in p0_fields:
            assert field in skill_content, f"Missing P0 field: {field}"

    def test_tenderer_extraction_patterns(self, skill_content: str):
        """测试招标人提取模式（解决用户痛点）"""
        # 检查招标人提取相关内容
        assert "TENDERER_PATTERNS" in skill_content or "招标人" in skill_content
        assert "采购人" in skill_content or "tenderer" in skill_content.lower()

    def test_field_confidence_thresholds(self, skill_content: str):
        """测试字段置信度阈值"""
        # 检查置信度相关内容
        assert "confidence" in skill_content.lower() or "置信度" in skill_content
        assert "0.7" in skill_content or "0.6" in skill_content or "0.5" in skill_content

    def test_website_type_classification(self, skill_content: str):
        """测试网站类型分类"""
        # 检查网站类型分类
        assert "api" in skill_content.lower() or "API" in skill_content
        assert "static" in skill_content.lower() or "静态" in skill_content
        assert "dynamic" in skill_content.lower() or "动态" in skill_content

    def test_pdf_extraction_mentioned(self, skill_content: str):
        """测试 PDF 提取提及"""
        assert "pdf" in skill_content.lower() or "PDF" in skill_content

    def test_quality_levels_defined(self, skill_content: str):
        """测试质量等级定义"""
        # 检查质量等级
        assert "HIGH" in skill_content or "高质量" in skill_content
        assert "MEDIUM" in skill_content or "中质量" in skill_content
        assert "LOW" in skill_content or "低质量" in skill_content

    def test_code_examples_present(self, skill_content: str):
        """测试代码示例存在"""
        # 检查代码块
        code_blocks = re.findall(r'```python\s*\n(.*?)\n```', skill_content, re.DOTALL)
        assert len(code_blocks) > 0, "No Python code examples found"

    def test_yaml_examples_present(self, skill_content: str):
        """测试 YAML 示例存在"""
        code_blocks = re.findall(r'```yaml\s*\n(.*?)\n```', skill_content, re.DOTALL)
        assert len(code_blocks) > 0, "No YAML examples found"


class TestSkillIntegration:
    """Skill 集成测试"""

    def test_skill_parsable(self):
        """测试 Skill 文件可解析"""
        skill_path = Path(__file__).parent.parent.parent.parent / "skills" / "tender-extraction" / "SKILL.md"
        if not skill_path.exists():
            skill_path = Path.cwd().parent / "skills" / "tender-extraction" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        # 提取 frontmatter
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        assert match is not None, "Frontmatter not found"

        frontmatter = match.group(1)
        assert "name:" in frontmatter
        assert "version:" in frontmatter

    def test_skill_content_completeness(self):
        """测试 Skill 内容完整性"""
        skill_path = Path(__file__).parent.parent.parent.parent / "skills" / "tender-extraction" / "SKILL.md"
        if not skill_path.exists():
            skill_path = Path.cwd().parent / "skills" / "tender-extraction" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        # 检查关键内容（使用英文关键词避免编码问题）
        checks = [
            ("招标人提取", "tenderer"),
            ("正文提取", "正文信息完整提取"),
            ("置信度", "confidence"),
            ("API 型", "API"),
            ("静态 HTML", "static"),
            ("动态 JS", "dynamic"),
            ("PDF 处理", "pdf"),
            ("质量保证", "quality"),
        ]

        for name, keyword in checks:
            assert keyword in content, f"Missing content: {name}"


class TestSkillValidation:
    """Skill 验证测试"""

    def test_skill_follows_markdown_format(self):
        """测试 Skill 遵循 Markdown 格式"""
        skill_path = Path(__file__).parent.parent.parent.parent / "skills" / "tender-extraction" / "SKILL.md"
        if not skill_path.exists():
            skill_path = Path.cwd().parent / "skills" / "tender-extraction" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        # 检查 Markdown 标题
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        assert len(headers) > 5, "Not enough headers"

        # 检查表格
        tables = re.findall(r'\|[^\n]+\|', content)
        assert len(tables) > 0, "No tables found"

    def test_skill_has_related_resources(self):
        """测试 Skill 有相关资源链接"""
        skill_path = Path(__file__).parent.parent.parent.parent / "skills" / "tender-extraction" / "SKILL.md"
        if not skill_path.exists():
            skill_path = Path.cwd().parent / "skills" / "tender-extraction" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        # 检查相关资源部分
        resources_section = content.split("## 9. 相关资源")[-1] if "## 9. 相关资源" in content else ""
        assert len(resources_section) > 50, "Resources section too short"

        # 检查文件链接
        links = re.findall(r'\[.*?\]\((.*?)\)', resources_section)
        assert len(links) > 0, "No resource links found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
