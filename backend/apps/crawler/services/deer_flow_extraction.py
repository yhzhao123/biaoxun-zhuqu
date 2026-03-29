"""
Deer-Flow 数据提取服务

封装 TenderExtractionWorkflow 和 deer-flow Client 的调用
提供招标数据提取功能
"""
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExtractionTask:
    """提取任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_url: str = ""
    site_type: str = "api"
    max_pages: int = 5
    max_items: Optional[int] = None
    api_config: Optional[str] = None
    fetch_details: bool = False
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source_url": self.source_url,
            "site_type": self.site_type,
            "max_pages": self.max_pages,
            "max_items": self.max_items,
            "api_config": self.api_config,
            "fetch_details": self.fetch_details,
            "status": self.status,
            "result": self.result,
            "error_message": self.error_message,
        }


class DeerFlowExtractionService:
    """
    Deer-Flow 数据提取服务

    使用 TenderExtractionWorkflow 或 DeerFlowClient 提取招标数据
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化服务

        Args:
            config_path: 可选的配置文件路径
        """
        self._config_path = config_path
        self._client = None
        self._workflow = None
        self._tasks: Dict[str, ExtractionTask] = {}

    @property
    def client(self):
        """获取 DeerFlowClient 实例"""
        if self._client is None:
            try:
                from deerflow.client import DeerFlowClient
                self._client = DeerFlowClient(config_path=self._config_path)
                logger.info("DeerFlowClient initialized successfully")
            except ImportError as e:
                logger.warning(f"DeerFlowClient not available: {e}")
                self._client = None
        return self._client

    @property
    def workflow(self):
        """获取 TenderExtractionWorkflow 实例"""
        if self._workflow is None:
            from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
            self._workflow = TenderExtractionWorkflow()
        return self._workflow

    def create_task(
        self,
        source_url: str,
        site_type: str = "api",
        max_pages: int = 5,
        max_items: Optional[int] = None,
        api_config: Optional[str] = None,
        fetch_details: bool = False,
    ) -> ExtractionTask:
        """创建提取任务

        Args:
            source_url: 源 URL
            site_type: 网站类型
            max_pages: 最大页数
            max_items: 最大项目数
            api_config: API 配置 JSON
            fetch_details: 是否获取详情

        Returns:
            ExtractionTask: 创建的任务
        """
        task = ExtractionTask(
            source_url=source_url,
            site_type=site_type,
            max_pages=max_pages,
            max_items=max_items,
            api_config=api_config,
            fetch_details=fetch_details,
            status="pending"
        )
        self._tasks[task.id] = task
        logger.info(f"Created extraction task: {task.id} for {source_url}")
        return task

    def get_task(self, task_id: str) -> Optional[ExtractionTask]:
        """获取任务

        Args:
            task_id: 任务 ID

        Returns:
            ExtractionTask or None
        """
        return self._tasks.get(task_id)

    def extract_tenders(
        self,
        source_url: str,
        site_type: str = "api",
        max_pages: int = 5,
        max_items: Optional[int] = None,
        api_config: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        提取招标列表（同步版本）

        Args:
            source_url: 源 URL
            site_type: 网站类型
            max_pages: 最大页数
            max_items: 最大项目数
            api_config: API 配置 JSON

        Returns:
            Dict containing extraction results
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            self._extract_tenders_async(
                source_url=source_url,
                site_type=site_type,
                max_pages=max_pages,
                max_items=max_items,
                api_config=api_config,
            )
        )
        return result

    async def _extract_tenders_async(
        self,
        source_url: str,
        site_type: str = "api",
        max_pages: int = 5,
        max_items: Optional[int] = None,
        api_config: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        提取招标列表（异步版本）

        Args:
            source_url: 源 URL
            site_type: 网站类型
            max_pages: 最大页数
            max_items: 最大项目数
            api_config: API 配置 JSON

        Returns:
            Dict containing extraction results
        """
        try:
            result = await self.workflow.extract(
                source_url=source_url,
                site_type=site_type,
                max_pages=max_pages,
                max_items=max_items,
                api_config=api_config,
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "items": [],
                "total_fetched": 0,
            }

    def extract_with_details(
        self,
        source_url: str,
        site_type: str = "api",
        max_pages: int = 5,
        max_items: Optional[int] = None,
        api_config: Optional[str] = None,
        concurrent_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        提取招标列表和详情（同步版本）

        Args:
            source_url: 源 URL
            site_type: 网站类型
            max_pages: 最大页数
            max_items: 最大项目数
            api_config: API 配置 JSON
            concurrent_limit: 并发限制

        Returns:
            Dict containing extraction results with details
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            self._extract_with_details_async(
                source_url=source_url,
                site_type=site_type,
                max_pages=max_pages,
                max_items=max_items,
                api_config=api_config,
                concurrent_limit=concurrent_limit,
            )
        )
        return result

    async def _extract_with_details_async(
        self,
        source_url: str,
        site_type: str = "api",
        max_pages: int = 5,
        max_items: Optional[int] = None,
        api_config: Optional[str] = None,
        concurrent_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        提取招标列表和详情（异步版本）

        Args:
            source_url: 源 URL
            site_type: 网站类型
            max_pages: 最大页数
            max_items: 最大项目数
            api_config: API 配置 JSON
            concurrent_limit: 并发限制

        Returns:
            Dict containing extraction results with details
        """
        try:
            result = await self.workflow.extract_with_details(
                source_url=source_url,
                site_type=site_type,
                max_pages=max_pages,
                max_items=max_items,
                api_config=api_config,
                concurrent_limit=concurrent_limit,
                fetch_details=True,
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Extraction with details failed: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "items": [],
                "details": [],
                "total_fetched": 0,
                "total_with_details": 0,
            }

    def run_task(self, task_id: str) -> Dict[str, Any]:
        """
        执行提取任务

        Args:
            task_id: 任务 ID

        Returns:
            执行结果
        """
        task = self.get_task(task_id)
        if not task:
            return {"success": False, "error_message": f"Task {task_id} not found"}

        task.status = "running"

        try:
            if task.fetch_details:
                result = self.extract_with_details(
                    source_url=task.source_url,
                    site_type=task.site_type,
                    max_pages=task.max_pages,
                    max_items=task.max_items,
                    api_config=task.api_config,
                )
            else:
                result = self.extract_tenders(
                    source_url=task.source_url,
                    site_type=task.site_type,
                    max_pages=task.max_pages,
                    max_items=task.max_items,
                    api_config=task.api_config,
                )

            task.result = result
            task.status = "completed" if result.get("success") else "failed"
            if not result.get("success"):
                task.error_message = result.get("error_message")

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = "failed"
            task.error_message = str(e)
            return {"success": False, "error_message": str(e)}

    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        return [task.to_dict() for task in self._tasks.values()]

    def clear_tasks(self) -> None:
        """清空所有任务"""
        self._tasks.clear()


# 全局服务实例
_extraction_service: Optional[DeerFlowExtractionService] = None


def get_extraction_service() -> DeerFlowExtractionService:
    """获取全局提取服务实例"""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = DeerFlowExtractionService()
    return _extraction_service