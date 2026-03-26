"""
CrawlSource model - 爬虫源配置
"""
from django.db import models


class CrawlSource(models.Model):
    """
    爬虫源配置模型
    用于管理可爬取的招标网站
    """

    # 状态选项
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, '启用'),
        (STATUS_INACTIVE, '禁用'),
        (STATUS_MAINTENANCE, '维护中'),
    ]

    name = models.CharField(max_length=100, verbose_name='网站名称')
    base_url = models.URLField(max_length=500, verbose_name='基础URL')
    list_url_pattern = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='列表页URL模式',
        help_text='如: /ggzy/jyxx/001001/001001001/?page={page}'
    )

    # CSS选择器配置
    selector_title = models.CharField(
        max_length=200,
        default='h1, .title, .article-title',
        verbose_name='标题选择器'
    )
    selector_content = models.CharField(
        max_length=200,
        default='.content, .article-content, .detail',
        verbose_name='内容选择器'
    )
    selector_publish_date = models.CharField(
        max_length=200,
        default='.publish-date, .time, .date',
        verbose_name='发布日期选择器'
    )
    selector_tenderer = models.CharField(
        max_length=200,
        default='.tenderer, .buyer, .purchaser',
        verbose_name='招标人选择器'
    )
    selector_budget = models.CharField(
        max_length=200,
        default='.budget, .amount, .price',
        verbose_name='预算金额选择器'
    )

    # ==================== 数据提取模式配置 ====================
    EXTRACTION_MODE_HTML = 'html'
    EXTRACTION_MODE_API = 'api'
    EXTRACTION_MODE_INTELLIGENT = 'intelligent'
    EXTRACTION_MODE_LLM = 'llm'
    EXTRACTION_MODE_AUTO = 'auto'
    EXTRACTION_MODE_CHOICES = [
        (EXTRACTION_MODE_HTML, 'HTML解析'),
        (EXTRACTION_MODE_API, 'API调用'),
        (EXTRACTION_MODE_INTELLIGENT, '智能提取'),
        (EXTRACTION_MODE_LLM, 'LLM提取'),
        (EXTRACTION_MODE_AUTO, '自动选择最佳模式'),
    ]

    extraction_mode = models.CharField(
        max_length=20,
        choices=EXTRACTION_MODE_CHOICES,
        default=EXTRACTION_MODE_AUTO,
        verbose_name='数据提取模式',
        help_text='选择数据提取方式，"自动选择"会依次尝试智能提取、LLM、HTML解析'
    )

    # ==================== API配置（用于动态加载的网站） ====================
    api_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='API端点URL',
        help_text='如: https://api.example.com/search'
    )
    api_method = models.CharField(
        max_length=10,
        choices=[('GET', 'GET'), ('POST', 'POST')],
        default='POST',
        verbose_name='API请求方法'
    )
    api_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='API参数模板',
        help_text='JSON格式的请求参数，支持 {page} 占位符'
    )
    api_headers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='API请求头',
        help_text='自定义请求头，如 {"Content-Type": "application/json"}'
    )
    api_response_path = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='响应数据路径',
        help_text='JSON路径，如: data.list 或 data.middle.listAndBox'
    )

    # ==================== API字段映射（JSON路径） ====================
    api_field_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='标题字段路径',
        help_text='如: title 或 data.title'
    )
    api_field_url = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='URL字段路径',
        help_text='详情页URL的JSON路径'
    )
    api_field_date = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='日期字段路径',
        help_text='发布日期的JSON路径'
    )
    api_field_budget = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='预算字段路径',
        help_text='预算金额的JSON路径'
    )
    api_field_tenderer = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='招标人字段路径',
        help_text='招标人/采购人的JSON路径'
    )

    # ==================== 分页配置 ====================
    page_param_name = models.CharField(
        max_length=20,
        default='page',
        verbose_name='分页参数名',
        help_text='API请求中的页码参数名'
    )
    page_start = models.IntegerField(
        default=1,
        verbose_name='起始页码',
        help_text='分页起始页码，通常为1'
    )
    max_pages = models.IntegerField(
        default=10,
        verbose_name='最大爬取页数',
        help_text='单次爬取的最大页数限制'
    )

    # ==================== 列表页配置（HTML模式） ====================
    list_container_selector = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='列表容器选择器',
        help_text='包含招标列表的容器，如: .list-container, #tender-list'
    )
    list_item_selector = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='列表项选择器',
        help_text='每个招标条目的选择器，如: .list-item, tr.data-row'
    )
    list_link_selector = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='详情链接选择器',
        help_text='从列表项中提取详情页链接的选择器，如: a.title, td:first-child a'
    )

    # ==================== JavaScript渲染配置 ====================
    use_javascript = models.BooleanField(
        default=False,
        verbose_name='需要JavaScript渲染',
        help_text='开启后将使用Playwright渲染页面'
    )
    wait_for_selector = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='等待元素选择器',
        help_text='等待此元素出现后再提取数据'
    )
    wait_timeout = models.IntegerField(
        default=5000,
        verbose_name='等待超时(毫秒)',
        help_text='等待元素出现的最大时间'
    )

    # ==================== 请求配置 ====================
    request_headers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='请求头配置'
    )
    request_cookies = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Cookie配置'
    )
    delay_seconds = models.IntegerField(
        default=1,
        verbose_name='请求间隔(秒)',
        help_text='每次请求之间的间隔时间'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name='状态'
    )

    # 统计信息
    last_crawl_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='最后爬取时间'
    )
    total_crawled = models.IntegerField(
        default=0,
        verbose_name='总爬取数'
    )
    success_rate = models.FloatField(
        default=100.0,
        verbose_name='成功率(%)'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'crawler_sources'
        verbose_name = '爬虫源配置'
        verbose_name_plural = '爬虫源配置'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
