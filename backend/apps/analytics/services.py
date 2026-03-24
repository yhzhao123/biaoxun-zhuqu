"""
Data analysis service - Phase 5 Task 026-035
数据分析服务

包含：
- 数据清洗
- 统计分析
- 趋势分析
- 商机识别
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
from decimal import Decimal

from django.db.models import Sum, Avg, Count, Max, Min, Q
from django.utils import timezone

from apps.tenders.models import TenderNotice
from apps.crawler.models import CrawlTask


logger = logging.getLogger(__name__)


class DataCleaningService:
    """
    数据清洗服务 - Task 026-027

    清洗招标公告数据：
    - 标准化金额格式
    - 补全缺失字段
    - 数据验证
    """

    def __init__(self):
        self.cleaned_count = 0
        self.errors = []

    def clean_tender(self, tender: TenderNotice) -> bool:
        """清洗单个招标记录"""
        try:
            # 清洗金额
            if tender.budget is not None:
                tender.budget = self._normalize_amount(tender.budget)

            # 标准化地区
            if tender.region:
                tender.region = self._normalize_region(tender.region)

            # 标准化行业
            if tender.industry:
                tender.industry = self._normalize_industry(tender.industry)

            # 设置状态（基于截止日期）
            if tender.deadline_date:
                tender.status = self._determine_status(tender.deadline_date)

            tender.save()
            self.cleaned_count += 1
            return True

        except Exception as e:
            logger.error(f"Failed to clean tender {tender.id}: {e}")
            self.errors.append({
                'tender_id': tender.id,
                'error': str(e)
            })
            return False

    def clean_all_pending(self) -> Dict[str, Any]:
        """清洗所有待处理记录"""
        tenders = TenderNotice.objects.filter(status='pending')
        success_count = 0

        for tender in tenders:
            if self.clean_tender(tender):
                success_count += 1

        return {
            'total': tenders.count(),
            'cleaned': success_count,
            'errors': len(self.errors),
            'error_details': self.errors[:10]  # 只返回前10个错误
        }

    def _normalize_amount(self, amount) -> Decimal:
        """标准化金额"""
        if amount is None:
            return Decimal('0')
        return Decimal(str(amount)).quantize(Decimal('0.01'))

    def _normalize_region(self, region: str) -> str:
        """标准化地区名称"""
        region_map = {
            '北京': 'Beijing',
            '上海': 'Shanghai',
            '广州': 'Guangzhou',
            '深圳': 'Shenzhen',
            '浙江': 'Zhejiang',
            '江苏': 'Jiangsu',
            '广东': 'Guangdong',
        }
        return region_map.get(region, region)

    def _normalize_industry(self, industry: str) -> str:
        """标准化行业名称"""
        industry_map = {
            'IT': 'IT',
            '信息技术': 'IT',
            '建筑': 'Construction',
            '医疗': 'Healthcare',
            '教育': 'Education',
            '金融': 'Finance',
        }
        return industry_map.get(industry, industry)

    def _determine_status(self, deadline_date) -> str:
        """根据截止日期确定状态"""
        if deadline_date < timezone.now():
            return TenderNotice.STATUS_EXPIRED
        return TenderNotice.STATUS_ACTIVE


class StatisticsService:
    """
    统计服务 - Task 028-031

    提供招标数据统计：
    - 总览统计
    - 地区分布
    - 行业分布
    - 趋势分析
    """

    def get_overview(self) -> Dict[str, Any]:
        """获取总览统计"""
        queryset = TenderNotice.objects.filter(is_deleted=False)

        total = queryset.count()
        active = queryset.filter(status='active').count()
        total_budget = queryset.aggregate(
            total=Sum('budget')
        )['total'] or 0

        # 按状态分布
        by_status = list(
            queryset.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # 按地区分布（Top 10）
        by_region = list(
            queryset.exclude(region='')
            .values('region')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # 按行业分布（Top 10）
        by_industry = list(
            queryset.exclude(industry='')
            .values('industry')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        return {
            'total_tenders': total,
            'active_tenders': active,
            'total_budget': float(total_budget),
            'by_status': by_status,
            'by_region': by_region,
            'by_industry': by_industry,
        }

    def get_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取趋势数据 - Task 030-031

        Args:
            days: 天数

        Returns:
            每日趋势数据
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 生成日期范围
        trend_data = []
        current = start_date

        while current <= end_date:
            count = TenderNotice.objects.filter(
                is_deleted=False,
                created_at__date=current
            ).count()

            trend_data.append({
                'date': current.isoformat(),
                'count': count
            })
            current += timedelta(days=1)

        return trend_data

    def get_budget_distribution(self) -> Dict[str, Any]:
        """获取预算分布"""
        queryset = TenderNotice.objects.filter(
            is_deleted=False,
            budget__isnull=False
        )

        # 预算区间统计
        ranges = [
            ('0-10万', 0, 100000),
            ('10-50万', 100000, 500000),
            ('50-100万', 500000, 1000000),
            ('100-500万', 1000000, 5000000),
            ('500万+', 5000000, float('inf')),
        ]

        distribution = []
        for label, min_val, max_val in ranges:
            if max_val == float('inf'):
                count = queryset.filter(budget__gte=min_val).count()
            else:
                count = queryset.filter(
                    budget__gte=min_val,
                    budget__lt=max_val
                ).count()
            distribution.append({'range': label, 'count': count})

        # 统计值
        stats = queryset.aggregate(
            avg=Avg('budget'),
            max=Max('budget'),
            min=Min('budget')
        )

        return {
            'distribution': distribution,
            'average': float(stats['avg'] or 0),
            'max': float(stats['max'] or 0),
            'min': float(stats['min'] or 0),
        }

    def get_top_tenderers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取活跃招标人排行"""
        return list(
            TenderNotice.objects.filter(is_deleted=False)
            .exclude(tenderer='')
            .values('tenderer')
            .annotate(
                count=Count('id'),
                total_budget=Sum('budget')
            )
            .order_by('-count')[:limit]
        )


class OpportunityAnalyzer:
    """
    商机识别服务 - Task 032-033

    识别高价值商机：
    - 大额招标
    - 热门行业
    - 紧急招标
    """

    def __init__(self):
        self.high_value_threshold = 1000000  # 100万
        self.urgent_days = 7  # 7天内截止

    def analyze_opportunities(self) -> Dict[str, Any]:
        """分析商机"""
        return {
            'high_value': self._find_high_value(),
            'hot_industries': self._find_hot_industries(),
            'urgent': self._find_urgent(),
            'recommendations': self._generate_recommendations(),
        }

    def _find_high_value(self, limit: int = 20) -> List[Dict[str, Any]]:
        """识别高价值招标"""
        tenders = TenderNotice.objects.filter(
            is_deleted=False,
            status='active',
            budget__gte=self.high_value_threshold
        ).order_by('-budget')[:limit]

        return [
            {
                'id': t.id,
                'title': t.title,
                'tenderer': t.tenderer,
                'budget': float(t.budget) if t.budget else 0,
                'deadline': t.deadline_date.isoformat() if t.deadline_date else None,
                'industry': t.industry,
            }
            for t in tenders
        ]

    def _find_hot_industries(self) -> List[Dict[str, Any]]:
        """识别热门行业"""
        # 最近30天新增招标数
        recent_date = timezone.now() - timedelta(days=30)

        industries = TenderNotice.objects.filter(
            is_deleted=False,
            created_at__gte=recent_date
        ).exclude(industry='').values('industry').annotate(
            count=Count('id'),
            total_budget=Sum('budget')
        ).order_by('-count')[:5]

        return [
            {
                'industry': i['industry'],
                'count': i['count'],
                'total_budget': float(i['total_budget'] or 0),
                'trend': 'up' if i['count'] > 10 else 'stable'
            }
            for i in industries
        ]

    def _find_urgent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """识别紧急招标（即将截止）"""
        deadline_threshold = timezone.now() + timedelta(days=self.urgent_days)

        tenders = TenderNotice.objects.filter(
            is_deleted=False,
            status='active',
            deadline_date__lte=deadline_threshold,
            deadline_date__gte=timezone.now()
        ).order_by('deadline_date')[:limit]

        return [
            {
                'id': t.id,
                'title': t.title,
                'tenderer': t.tenderer,
                'budget': float(t.budget) if t.budget else 0,
                'deadline': t.deadline_date.isoformat() if t.deadline_date else None,
                'days_left': (t.deadline_date - timezone.now()).days if t.deadline_date else None,
            }
            for t in tenders
        ]

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """生成推荐"""
        recommendations = []

        # 基于预算的推荐
        high_budget = self._find_high_value(5)
        if high_budget:
            recommendations.append({
                'type': 'high_value',
                'title': 'High-value opportunities',
                'count': len(high_budget),
                'items': high_budget[:3]
            })

        # 基于紧急度的推荐
        urgent = self._find_urgent(5)
        if urgent:
            recommendations.append({
                'type': 'urgent',
                'title': 'Urgent deadlines',
                'count': len(urgent),
                'items': urgent[:3]
            })

        return recommendations


class ReportGenerator:
    """
    报告生成服务 - Task 034-035

    生成统计报告
    """

    def __init__(self):
        self.stats_service = StatisticsService()
        self.opportunity_analyzer = OpportunityAnalyzer()

    def generate_daily_report(self) -> Dict[str, Any]:
        """生成日报"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # 今日新增
        new_today = TenderNotice.objects.filter(
            created_at__date=today
        ).count()

        # 昨日对比
        new_yesterday = TenderNotice.objects.filter(
            created_at__date=yesterday
        ).count()

        # 活跃招标
        active_count = TenderNotice.objects.filter(
            status='active'
        ).count()

        return {
            'date': today.isoformat(),
            'new_tenders': new_today,
            'change_from_yesterday': new_today - new_yesterday,
            'active_tenders': active_count,
            'opportunities': self.opportunity_analyzer.analyze_opportunities(),
        }

    def generate_weekly_report(self) -> Dict[str, Any]:
        """生成周报"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)

        # 本周统计
        weekly_stats = TenderNotice.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).aggregate(
            total=Count('id'),
            total_budget=Sum('budget')
        )

        # 按行业分布
        by_industry = list(
            TenderNotice.objects.filter(
                created_at__date__gte=start_date
            ).exclude(industry='').values('industry').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
        )

        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'total_tenders': weekly_stats['total'] or 0,
            'total_budget': float(weekly_stats['total_budget'] or 0),
            'by_industry': by_industry,
            'trend': self.stats_service.get_trend(7),
        }


# Convenience functions
def get_statistics_service() -> StatisticsService:
    """获取统计服务实例"""
    return StatisticsService()


def get_opportunity_analyzer() -> OpportunityAnalyzer:
    """获取商机分析器实例"""
    return OpportunityAnalyzer()


def get_report_generator() -> ReportGenerator:
    """获取报告生成器实例"""
    return ReportGenerator()
