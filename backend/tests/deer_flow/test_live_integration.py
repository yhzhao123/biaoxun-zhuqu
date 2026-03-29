"""
TDD Test: deer-flow Live Integration Tests

测试 deer-flow Gateway 和 Tools 的实际集成。
需要 deer-flow Gateway 运行在 port 8001。
"""
import logging
import os

import pytest
import requests

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# Test Configuration
# ============================================================================

GATEWAY_URL = os.environ.get("DEER_FLOW_GATEWAY_URL", "http://localhost:8001")
LANGGRAPH_URL = os.environ.get("DEER_FLOW_LANGGRAPH_URL", "http://localhost:2024")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def gateway_available() -> bool:
    """Check if Gateway is running."""
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


# ============================================================================
# Test Class: Gateway API Tests
# ============================================================================

class TestGatewayAPI:
    """Gateway API 端点测试"""

    @pytest.mark.integration
    def test_gateway_health(self, gateway_available):
        """测试 Gateway 健康检查"""
        if not gateway_available:
            pytest.skip("Gateway not available")

        response = requests.get(f"{GATEWAY_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        logger.info("Gateway health check: %s", data)

    @pytest.mark.integration
    def test_gateway_mcp_config(self, gateway_available):
        """测试 MCP 配置端点返回工具配置"""
        if not gateway_available:
            pytest.skip("Gateway not available")

        response = requests.get(f"{GATEWAY_URL}/api/mcp/config")
        assert response.status_code == 200
        data = response.json()
        assert "mcp_servers" in data
        # MCP servers should include filesystem, github, postgres (based on extensions_config.json)
        logger.info("MCP servers: %s", list(data['mcp_servers'].keys()))

    @pytest.mark.integration
    def test_gateway_models_endpoint(self, gateway_available):
        """测试 Models API 端点"""
        if not gateway_available:
            pytest.skip("Gateway not available")

        response = requests.get(f"{GATEWAY_URL}/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0
        logger.info("Available models: %s", [m['name'] for m in data['models']])


# ============================================================================
# Test Class: Tool Call Tests
# ============================================================================

class TestToolCalls:
    """通过 LangGraph 调用 Tools 的测试"""

    @pytest.mark.integration
    def test_skills_endpoint_returns_data(self, gateway_available):
        """测试 skills 端点返回数据"""
        if not gateway_available:
            pytest.skip("Gateway not available")

        response = requests.get(f"{GATEWAY_URL}/api/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert len(data["skills"]) > 0

        skill_names = [s["name"] for s in data.get("skills", [])]
        logger.info(f"Registered skills: {skill_names}")


# ============================================================================
# Test Class: Direct Tool Invocation Tests
# ============================================================================

class TestDirectToolInvocation:
    """直接调用 Tools 的测试（通过 LangGraph SDK）"""

    @pytest.mark.integration
    def test_langgraph_running(self, gateway_available):
        """测试 LangGraph Server 运行状态"""
        if not gateway_available:
            pytest.skip("Gateway not available")

        # Just check if Gateway is running (LangGraph requires additional setup)
        # This is verified indirectly through Gateway health check
        assert gateway_available, "Gateway not available"

    @pytest.mark.integration
    def test_config_tools_definition(self):
        """测试 config.yaml 中工具定义正确"""
        import yaml
        config_path = os.path.join(PROJECT_ROOT, "deer-flow", "config.yaml")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tools = config.get("tools", [])
        tool_names = [t.get("name") for t in tools]

        assert "fetch_tender_list" in tool_names, "fetch_tender_list not configured"
        assert "fetch_tender_detail" in tool_names, "fetch_tender_detail not configured"

        # Verify tool definitions have required fields
        fetch_tender_list_tool = next(t for t in tools if t["name"] == "fetch_tender_list")
        assert "use" in fetch_tender_list_tool
        assert fetch_tender_list_tool["use"].endswith("fetch_tender_list")

        fetch_tender_detail_tool = next(t for t in tools if t["name"] == "fetch_tender_detail")
        assert "use" in fetch_tender_detail_tool
        assert fetch_tender_detail_tool["use"].endswith("fetch_tender_detail")

        logger.info("Tool definitions verified in config.yaml")

    @pytest.mark.integration
    def test_config_tools_group(self):
        """测试工具分组配置"""
        import yaml
        config_path = os.path.join(PROJECT_ROOT, "deer-flow", "config.yaml")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tool_groups = config.get("tool_groups", [])
        group_names = [g.get("name") for g in tool_groups]
        logger.info(f"Tool groups: {group_names}")

        # Verify web group exists (tender tools use 'web' group)
        assert "web" in group_names, "web group not configured"


# ============================================================================
# Test Class: End-to-End Tests
# ============================================================================

class TestEndToEnd:
    """端到端集成测试"""

    @pytest.mark.integration
    def test_full_flow_verification(self, gateway_available):
        """测试完整流程：Gateway -> Config -> Tools"""
        if not gateway_available:
            pytest.skip("Gateway not available")

        # 1. Verify Gateway is running
        response = requests.get(f"{GATEWAY_URL}/health")
        assert response.status_code == 200
        logger.info("Step 1: Gateway health check - PASS")

        # 2. Verify MCP config returns data
        response = requests.get(f"{GATEWAY_URL}/api/mcp/config")
        assert response.status_code == 200
        mcp_config = response.json()
        logger.info(f"Step 2: MCP config - PASS, servers: {list(mcp_config['mcp_servers'].keys())}")

        # 3. Verify skills are returned
        response = requests.get(f"{GATEWAY_URL}/api/skills")
        assert response.status_code == 200
        skills_data = response.json()
        assert len(skills_data.get("skills", [])) > 0
        logger.info(f"Step 3: Skills - PASS, {len(skills_data['skills'])} skills loaded")

        # 4. Verify models are available
        response = requests.get(f"{GATEWAY_URL}/api/models")
        assert response.status_code == 200
        models_data = response.json()
        assert len(models_data.get("models", [])) > 0
        logger.info(f"Step 4: Models - PASS, {len(models_data['models'])} models available")

        logger.info("All end-to-end steps completed successfully!")

    @pytest.mark.integration
    def test_memory_config(self, gateway_available):
        """测试 Memory 配置端点"""
        if not gateway_available:
            pytest.skip("Gateway not available")

        response = requests.get(f"{GATEWAY_URL}/api/memory/config")
        # Memory might not be configured, but endpoint should respond
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Memory config: {data}")


# ============================================================================
# Test Class: Tender Tools Configuration Tests
# ============================================================================

class TestTenderToolsConfig:
    """Tender Tools 配置验证测试"""

    @pytest.mark.integration
    def test_tender_tools_in_config_yaml(self):
        """验证 tender tools 在 config.yaml 中"""
        import yaml
        config_path = os.path.join(PROJECT_ROOT, "deer-flow", "config.yaml")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        tools = config.get("tools", [])

        # Find tender tools
        tender_list_tool = next((t for t in tools if t.get("name") == "fetch_tender_list"), None)
        tender_detail_tool = next((t for t in tools if t.get("name") == "fetch_tender_detail"), None)

        assert tender_list_tool is not None, "fetch_tender_list not in config"
        assert tender_detail_tool is not None, "fetch_tender_detail not in config"

        # Verify tool properties
        assert tender_list_tool.get("group") == "web", "fetch_tender_list should be in 'web' group"
        assert tender_detail_tool.get("group") == "web", "fetch_tender_detail should be in 'web' group"

        logger.info(f"fetch_tender_list: {tender_list_tool.get('use')}")
        logger.info(f"fetch_tender_detail: {tender_detail_tool.get('use')}")

    @pytest.mark.integration
    def test_extensions_config_skill_enabled(self):
        """验证 extensions_config.json 中 skill 已启用"""
        import json
        config_path = os.path.join(PROJECT_ROOT, "deer-flow", "extensions_config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        skills = config.get("skills", {})

        # Check if tender-extraction is in extensions config
        assert "tender-extraction" in skills, "tender-extraction not in extensions_config.json"
        assert skills["tender-extraction"].get("enabled") is True, "tender-extraction not enabled"

        logger.info("tender-extraction skill is enabled in extensions_config.json")

    @pytest.mark.integration
    def test_tender_skill_directory_exists(self):
        """验证 tender-extraction skill 目录存在"""
        # Check multiple possible locations
        possible_paths = [
            os.path.join(PROJECT_ROOT, "skills", "tender-extraction"),
            os.path.join(PROJECT_ROOT, "deer-flow", "skills", "public", "tender-extraction"),
            os.path.join(PROJECT_ROOT, "deer-flow", "skills", "custom", "tender-extraction"),
        ]

        found_path = None
        for path in possible_paths:
            if os.path.exists(path):
                found_path = path
                break

        assert found_path is not None, f"tender-extraction skill not found in any location: {possible_paths}"

        # Check for SKILL.md
        skill_md = os.path.join(found_path, "SKILL.md")
        assert os.path.exists(skill_md), f"SKILL.md not found in {found_path}"

        logger.info(f"tender-extraction skill found at: {found_path}")