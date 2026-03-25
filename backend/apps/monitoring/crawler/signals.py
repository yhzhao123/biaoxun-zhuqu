"""
Task 059: Celery Signals Integration
Celery 信号集成 - 任务生命周期信号处理
"""
from celery import signals
from apps.monitoring.crawler.task_tracker import get_task_tracker
from apps.monitoring.crawler.counter import get_counter


def setup_task_signals():
    """设置 Celery 任务信号处理器"""

    @signals.task_prerun.connect
    def task_prerun_handler(task_id, task, *args, **kwargs):
        """
        任务执行前信号处理器

        Args:
            task_id: 任务 ID
            task: 任务对象
            *args: 位置参数
            **kwargs: 关键字参数
        """
        tracker = get_task_tracker()
        tracker.start(
            task_id=task_id,
            name=task.name,
            *args,
            **kwargs
        )

    @signals.task_postrun.connect
    def task_postrun_handler(task_id, task, *args, **kwargs):
        """
        任务执行后信号处理器

        Args:
            task_id: 任务 ID
            task: 任务对象
            *args: 位置参数
            **kwargs: 关键字参数
        """
        tracker = get_task_tracker()
        counter = get_counter(task.name)

        # 获取任务状态
        state = kwargs.get('state')
        if state and state.upper() == 'SUCCESS':
            tracker.complete(task_id, result=kwargs.get('result'))
            counter.record_success()
        else:
            tracker.fail(task_id, error_message=str(kwargs.get('result', 'Unknown error')))
            counter.record_failure()

    @signals.task_failure.connect
    def task_failure_handler(task_id, exception, *args, **kwargs):
        """
        任务失败信号处理器

        Args:
            task_id: 任务 ID
            exception: 异常对象
            *args: 位置参数
            **kwargs: 关键字参数
        """
        tracker = get_task_tracker()
        counter = get_counter(kwargs.get('task').name if kwargs.get('task') else 'unknown')

        error_msg = str(exception)
        tracker.fail(task_id, error_message=error_msg)
        counter.record_failure()

    @signals.task_retry.connect
    def task_retry_handler(request, reason, *args, **kwargs):
        """
        任务重试信号处理器

        Args:
            request: 请求对象
            reason: 重试原因
            *args: 位置参数
            **kwargs: 关键字参数
        """
        tracker = get_task_tracker()
        task_id = request.id if hasattr(request, 'id') else str(request)
        task_name = request.name if hasattr(request, 'name') else 'unknown'

        tracker.retry(task_id)

        counter = get_counter(task_name)
        counter.record_retry()

    @signals.task_revoked.connect
    def task_revoked_handler(request, *args, **kwargs):
        """
        任务撤销信号处理器

        Args:
            request: 请求对象
            *args: 位置参数
            **kwargs: 关键字参数
        """
        tracker = get_task_tracker()
        task_id = request.id if hasattr(request, 'id') else str(request)

        tracker.fail(task_id, error_message='Task revoked')


def unregister_signals():
    """注销信号处理器（用于测试）"""
    # Celery 信号处理器的注销比较复杂
    # 在测试环境中通常使用 CELERY_TASK_ALWAYS_EAGER
    pass


# 自动设置信号（在模块导入时）
try:
    setup_task_signals()
except Exception:
    # 在非 Celery 环境（如测试）中可能失败，这是预期的
    pass