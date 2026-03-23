"""
Test React frontend setup
"""
import os
import pytest


class TestFrontendStructure:
    """Test frontend project structure."""

    def test_frontend_directory_exists(self):
        """Test that frontend directory exists."""
        # Frontend is in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Navigate from backend/tests to project root, then to frontend
        while not os.path.exists(os.path.join(project_root, 'frontend')):
            if os.path.basename(project_root) == 'biaoxun-zhuqu':
                break
            project_root = os.path.dirname(project_root)

        frontend_path = os.path.join(project_root, 'frontend')
        assert os.path.exists(frontend_path), f"Frontend directory should exist at {frontend_path}"

    def test_package_json_exists(self):
        """Test that package.json exists."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        package_json = os.path.join(project_root, 'frontend', 'package.json')
        assert os.path.exists(package_json), f"package.json should exist at {package_json}"

    def test_vite_config_exists(self):
        """Test that vite.config.ts exists."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        vite_config = os.path.join(project_root, 'frontend', 'vite.config.ts')
        assert os.path.exists(vite_config), f"vite.config.ts should exist at {vite_config}"

    def test_typescript_config_exists(self):
        """Test that tsconfig.json exists."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        tsconfig = os.path.join(project_root, 'frontend', 'tsconfig.json')
        assert os.path.exists(tsconfig), f"tsconfig.json should exist at {tsconfig}"

    def test_tailwind_config_exists(self):
        """Test that tailwind.config.js exists."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        tailwind_config = os.path.join(project_root, 'frontend', 'tailwind.config.js')
        assert os.path.exists(tailwind_config), f"tailwind.config.js should exist"


class TestFrontendDependencies:
    """Test frontend dependencies are installed."""

    def test_node_modules_exists(self):
        """Test that node_modules exists."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        node_modules = os.path.join(project_root, 'frontend', 'node_modules')
        assert os.path.exists(node_modules), "node_modules should exist (dependencies installed)"