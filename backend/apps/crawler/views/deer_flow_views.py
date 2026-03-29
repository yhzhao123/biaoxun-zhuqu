"""
Deer-Flow API 视图

提供招标数据提取的 REST API 端点
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import Serializer, CharField, IntegerField, BooleanField

logger = logging.getLogger(__name__)


class ExtractRequestSerializer(Serializer):
    """提取请求序列化器"""
    source_url = CharField(required=True, help_text="源 URL")
    site_type = CharField(default="api", help_text="网站类型: api, web, etc.")
    max_pages = IntegerField(default=5, min_value=1, max_value=100, help_text="最大页数")
    max_items = IntegerField(required=False, min_value=1, help_text="最大项目数")
    api_config = CharField(required=False, allow_blank=True, help_text="API 配置 JSON")
    fetch_details = BooleanField(default=False, help_text="是否获取详情")


class ExtractionStatusSerializer(Serializer):
    """提取状态序列化器"""
    task_id = CharField()
    source_url = CharField()
    status = CharField()
    success = BooleanField()
    error_message = CharField(allow_null=True)


@api_view(["POST"])
def start_extraction(request):
    """
    开始提取任务

    POST /api/crawler/deer-flow/extract

    Request body:
    {
        "source_url": "http://api.example.com",
        "site_type": "api",
        "max_pages": 5,
        "max_items": 10,
        "api_config": "{}",
        "fetch_details": false
    }

    Response:
    {
        "task_id": "uuid",
        "status": "pending|running|completed|failed",
        "message": "任务已创建"
    }
    """
    serializer = ExtractRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Invalid request", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    data = serializer.validated_data

    # 创建提取服务
    from apps.crawler.services.deer_flow_extraction import get_extraction_service
    service = get_extraction_service()

    # 检查是否需要异步执行
    use_async = data.get("max_pages", 5) > 10 or data.get("fetch_details", False)

    if use_async:
        # 创建异步任务
        task = service.create_task(
            source_url=data["source_url"],
            site_type=data.get("site_type", "api"),
            max_pages=data.get("max_pages", 5),
            max_items=data.get("max_items"),
            api_config=data.get("api_config"),
            fetch_details=data.get("fetch_details", False),
        )

        # 触发 Celery 任务
        from apps.crawler.tasks import run_deer_flow_extraction
        celery_task = run_deer_flow_extraction.delay(task.id)

        return Response({
            "task_id": task.id,
            "celery_task_id": celery_task.id,
            "status": task.status,
            "message": "异步任务已创建"
        }, status=status.HTTP_202_ACCEPTED)
    else:
        # 同步执行
        result = service.extract_tenders(
            source_url=data["source_url"],
            site_type=data.get("site_type", "api"),
            max_pages=data.get("max_pages", 5),
            max_items=data.get("max_items"),
            api_config=data.get("api_config"),
        )

        return Response({
            "status": "completed",
            "result": result
        }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_extraction_status(request, task_id: str):
    """
    获取提取任务状态

    GET /api/crawler/deer-flow/status/{task_id}

    Response:
    {
        "task_id": "uuid",
        "source_url": "http://api.example.com",
        "status": "pending|running|completed|failed",
        "success": true,
        "error_message": null
    }
    """
    from apps.crawler.services.deer_flow_extraction import get_extraction_service
    service = get_extraction_service()

    task = service.get_task(task_id)
    if not task:
        return Response(
            {"error": f"Task {task_id} not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        "task_id": task.id,
        "source_url": task.source_url,
        "status": task.status,
        "success": task.status == "completed",
        "error_message": task.error_message,
    })


@api_view(["GET"])
def get_extraction_results(request, task_id: str):
    """
    获取提取结果

    GET /api/crawler/deer-flow/results/{task_id}

    Response:
    {
        "task_id": "uuid",
        "status": "completed",
        "result": {
            "items": [...],
            "details": [...],
            "success": true,
            "total_fetched": 10
        }
    }
    """
    from apps.crawler.services.deer_flow_extraction import get_extraction_service
    service = get_extraction_service()

    task = service.get_task(task_id)
    if not task:
        return Response(
            {"error": f"Task {task_id} not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if task.status != "completed":
        return Response({
            "task_id": task.id,
            "status": task.status,
            "message": "任务尚未完成",
            "error_message": task.error_message,
        })

    return Response({
        "task_id": task.id,
        "status": task.status,
        "result": task.result
    })


@api_view(["GET"])
def list_extractions(request):
    """
    列出所有提取任务

    GET /api/crawler/deer-flow/list

    Response:
    {
        "tasks": [
            {
                "task_id": "uuid",
                "source_url": "...",
                "status": "completed",
                "created_at": "..."
            }
        ]
    }
    """
    from apps.crawler.services.deer_flow_extraction import get_extraction_service
    service = get_extraction_service()

    tasks = service.list_tasks()

    return Response({
        "tasks": [
            {
                "task_id": task["id"],
                "source_url": task["source_url"],
                "status": task["status"],
                "fetch_details": task["fetch_details"],
            }
            for task in tasks
        ]
    })