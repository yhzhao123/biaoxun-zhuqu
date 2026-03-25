# Generated manually for Task 067: Database Optimization

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Task 067: 数据库性能优化
    - 添加复合索引优化查询性能
    - 优化常用查询字段的索引配置
    """

    dependencies = [
        ('tenders', '0003_tendernotice_created_by_tendernotice_is_public_and_more'),
    ]

    operations = [
        # 移除旧索引（如果存在）
        migrations.RemoveIndex(
            model_name='tendernotice',
            name='tender_noti_title_5a3907_idx',
        ),
        migrations.RemoveIndex(
            model_name='tendernotice',
            name='tender_noti_tendere_dcd621_idx',
        ),
        migrations.RemoveIndex(
            model_name='tendernotice',
            name='tender_noti_region_56a17d_idx',
        ),
        migrations.RemoveIndex(
            model_name='tendernotice',
            name='tender_noti_crawl_b_671c52_idx',
        ),
        migrations.RemoveIndex(
            model_name='tendernotice',
            name='tender_noti_notice__306bf4_idx',
        ),
        migrations.RemoveIndex(
            model_name='tendernotice',
            name='tender_noti_region__c06434_idx',
        ),

        # 添加优化后的复合索引
        # 1. 标题 + 发布日期（用于列表查询和排序）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['title', 'publish_date'],
                name='tender_title_pub_idx',
            ),
        ),
        # 2. 招标人 + 状态（用于按招标人筛选）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['tenderer', 'status'],
                name='tender_tenderer_status_idx',
            ),
        ),
        # 3. 地区 + 行业（用于分类筛选）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['region', 'industry'],
                name='tender_region_industry_idx',
            ),
        ),
        # 4. 地区编码 + 行业编码（用于编码筛选）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['region_code', 'industry_code'],
                name='tender_region_codes_idx',
            ),
        ),
        # 5. 爬虫批次 + 创建时间（用于批次查询）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['crawl_batch_id', 'created_at'],
                name='tender_crawl_batch_idx',
            ),
        ),
        # 6. 公告类型 + 发布日期（用于类型筛选）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['notice_type', 'publish_date'],
                name='tender_notice_type_date_idx',
            ),
        ),
        # 7. 状态 + 发布日期（用于状态筛选）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['status', 'publish_date'],
                name='tender_status_date_idx',
            ),
        ),
        # 8. 招标人 + 发布日期（用于招标人历史查询）
        migrations.AddIndex(
            model_name='tendernotice',
            index=models.Index(
                fields=['tenderer', 'publish_date'],
                name='tender_tenderer_date_idx',
            ),
        ),
    ]
