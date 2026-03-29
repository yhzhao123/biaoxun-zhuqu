"""
TDD Test: deer-flow Configuration Deployment
"""
import json
import os

import pytest
import yaml

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


@pytest.fixture
def project_root() -> str:
    """返回项目根目录路径"""
    return PROJECT_ROOT


@pytest.fixture
def config_path(project_root: str) -> str:
    """返回 deer-flow config.yaml 路径"""
    return os.path.join(project_root, "deer-flow", "config.yaml")


@pytest.fixture
def extensions_path(project_root: str) -> str:
    """返回 deer-flow extensions_config.json 路径"""
    return os.path.join(project_root, "deer-flow", "extensions_config.json")


@pytest.fixture
def config(config_path: str) -> dict:
    """加载并返回 config.yaml 内容"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def extensions_config(extensions_path: str) -> dict:
    """加载并返回 extensions_config.json 内容"""
    with open(extensions_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestDeerFlowConfig:
    """测试 deer-flow 配置"""

    def test_config_file_exists(self, config_path: str):
        """测试 config.yaml 文件存在"""
        assert os.path.exists(config_path), f"Config file not found at {config_path}"

    def test_config_is_valid_yaml(self, config: dict):
        """测试 config.yaml 是有效的 YAML"""
        assert config is not None
        assert isinstance(config, dict)

    def test_config_has_required_sections(self, config: dict):
        """测试配置包含必需的部分"""
        assert "config_version" in config
        assert "models" in config
        assert "tools" in config

    def test_tender_tools_configured(self, config: dict):
        """测试招标 Tools 已配置"""
        tools = config.get("tools", [])
        tool_names = [t.get("name") for t in tools]

        assert "fetch_tender_list" in tool_names
        assert "fetch_tender_detail" in tool_names


class TestDeerFlowExtensionsConfig:
    """测试 deer-flow 扩展配置"""

    def test_extensions_config_exists(self, extensions_path: str):
        """测试 extensions_config.json 存在"""
        assert os.path.exists(extensions_path), f"Extensions config not found at {extensions_path}"

    def test_extensions_config_is_valid_json(self, extensions_config: dict):
        """测试 extensions_config.json 是有效的 JSON"""
        assert extensions_config is not None
        assert isinstance(extensions_config, dict)

    def test_tender_extraction_skill_registered(self, extensions_config: dict):
        """测试 tender-extraction Skill 已注册"""
        skills = extensions_config.get("skills", {})
        assert "tender-extraction" in skills, "tender-extraction skill not registered"
        assert skills["tender-extraction"].get("enabled") is True
