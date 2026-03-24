"""创建测试数据"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.tenders.models import TenderNotice

# 创建测试数据
tenders_data = [
    {
        'notice_id': 'TEST001',
        'title': '北京市政府办公设备采购项目',
        'description': '采购办公电脑、打印机等设备',
        'tenderer': '北京市政府采购中心',
        'budget': 500000,
        'currency': 'CNY',
        'region': 'Beijing',
        'industry': 'IT',
        'source_site': '中国政府采购网',
        'status': TenderNotice.STATUS_ACTIVE,
    },
    {
        'notice_id': 'TEST002',
        'title': '上海地铁线路扩建工程',
        'description': '地铁3号线扩建工程招标',
        'tenderer': '上海市轨道交通建设指挥部',
        'budget': 50000000,
        'currency': 'CNY',
        'region': 'Shanghai',
        'industry': 'Construction',
        'source_site': '中国招标投标公共服务平台',
        'status': TenderNotice.STATUS_ACTIVE,
    },
    {
        'notice_id': 'TEST003',
        'title': '广州医院信息化建设',
        'description': '医院信息管理系统升级',
        'tenderer': '广州市第一人民医院',
        'budget': 2000000,
        'currency': 'CNY',
        'region': 'Guangdong',
        'industry': 'Healthcare',
        'source_site': '中国政府采购网',
        'status': TenderNotice.STATUS_PENDING,
    },
]

for data in tenders_data:
    obj, created = TenderNotice.objects.get_or_create(
        notice_id=data['notice_id'],
        defaults=data
    )
    if created:
        print(f"Created: {obj.title}")
    else:
        print(f"Exists: {obj.title}")

print(f"\nTotal tenders: {TenderNotice.objects.count()}")
