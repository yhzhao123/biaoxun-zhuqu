"""
TDD Test: deer-flow Configuration Deployment
"""
import os
import pytest
import yaml

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "deer-flow", "config.yaml")


class TestDeerFlowConfig:
    """测试 deer-flow 配置"""

    def test_config_file_exists(self):
        """测试 config.yaml 文件存在"""
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Config path: {CONFIG_PATH}")
        print(f"Exists: {os.path.exists(CONFIG_PATH)}")
        assert os.path.exists(CONFIG_PATH), f"Config file not found at {CONFIG_PATH}"

    def test_config_is_valid_yaml(self):
        """测试 config.yaml 是有效的 YAML"""
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        assert config is not None
        assert isinstance(config, dict)

    def test_config_has_required_sections(self):
        """测试配置包含必需的部分"""
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "config_version" in config
        assert "models" in config
        assert "tools" in config

    def test_tender_tools_configured(self):
        """测试招标 Tools 已配置"""
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tools = config.get("tools", [])
        tool_names = [t.get("name") for t in tools]

        assert "fetch_tender_list" in tool_names
        assert "fetch_tender_detail" in tool_names


class TestDeerFlowExtensionsConfig:
    """测试 deer-flow 扩展配置"""

    EXTENSIONS_PATH = os.path.join(PROJECT_ROOT, "deer-flow", "extensions_config.json")

    def test_extensions_config_exists(self):
        """测试 extensions_config.json 存在"""
        assert os.path.exists(self.EXTENSIONS_PATH), f"Extensions config not found"

    def test_extensions_config_is_valid_json(self):
        """测试 extensions_config.json 是有效的 JSON"""
        import json
        with open(self.EXTENSIONS_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert config is not None
        assert isinstance(config, dict)

    def test_tender_extraction_skill_registered(self):
        """测试 tender-extraction Skill 已注册"""
        import json
        with open(self.EXTENSIONS_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        skills = config.get("skills", {})
        assert "tender-extraction" in skills, "tender-extraction skill not registered"
        assert skills["tender-extraction"].get("enabled") is True
