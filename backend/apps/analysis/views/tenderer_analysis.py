"""
Tenderer Analysis API - 招标人历史分析
使用LLM分析同一招标人的历史招标和交易信息
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from datetime import datetime, timedelta

from apps.tenders.models import TenderNotice
from apps.analysis.services.llm_extractor import LLMExtractor


class TendererAnalysisViewSet(viewsets.ViewSet):
    """
    招标人分析API视图集
    提供招标人历史数据分析和洞察
    """

    @action(detail=False, methods=['get'])
    def analyze(self, request):
        """
        分析指定招标人的历史招标信息

        Query参数:
        - tenderer: 招标人名称
        - days: 分析天数(默认365)
        """
        tenderer_name = request.query_params.get('tenderer', '')
        days = int(request.query_params.get('days', 365))

        if not tenderer_name:
            return Response(
                {'error': '请提供招标人名称'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 获取历史招标记录
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        tenders = TenderNotice.objects.filter(
            tenderer__icontains=tenderer_name,
            created_at__gte=start_date
        ).order_by('-publish_date')

        if not tenders.exists():
            return Response({
                'tenderer': tenderer_name,
                'message': '未找到该招标人的历史记录',
                'analysis_period_days': days,
                'total_tenders': 0,
                'insights': []
            })

        # 基础统计
        total_tenders = tenders.count()
        total_budget = tenders.aggregate(total=Sum('budget'))['total'] or 0
        avg_budget = tenders.aggregate(avg=Avg('budget'))['avg'] or 0

        # 按行业分布
        industry_distribution = list(
            tenders.values('industry').annotate(
                count=Count('id'),
                total_budget=Sum('budget')
            ).order_by('-count')
        )

        # 按地区分布
        region_distribution = list(
            tenders.values('region').annotate(
                count=Count('id'),
                total_budget=Sum('budget')
            ).order_by('-count')
        )

        # 时间趋势 - database agnostic approach
        from collections import defaultdict
        monthly_data = defaultdict(lambda: {'count': 0, 'total_budget': 0})
        for tender in tenders:
            month = tender.created_at.strftime('%Y-%m')
            monthly_data[month]['count'] += 1
            if tender.budget:
                monthly_data[month]['total_budget'] += float(tender.budget)

        monthly_trend = [
            {'month': month, 'count': data['count'], 'total_budget': data['total_budget']}
            for month, data in sorted(monthly_data.items())
        ]

        # 使用LLM生成洞察
        insights = self._generate_insights(tenders, tenderer_name)

        return Response({
            'tenderer': tenderer_name,
            'analysis_period_days': days,
            'total_tenders': total_tenders,
            'total_budget': float(total_budget),
            'avg_budget': float(avg_budget),
            'industry_distribution': industry_distribution,
            'region_distribution': region_distribution,
            'monthly_trend': monthly_trend,
            'recent_tenders': [
                {
                    'id': str(t.id),
                    'title': t.title,
                    'budget': float(t.budget) if t.budget else None,
                    'industry': t.industry,
                    'region': t.region,
                    'publish_date': t.publish_date.isoformat() if t.publish_date else None,
                    'status': t.status,
                }
                for t in tenders[:10]
            ],
            'insights': insights
        })

    def _generate_insights(self, tenders, tenderer_name):
        """生成AI洞察"""
        insights = []

        # 招标频率分析
        total_count = tenders.count()
        if total_count > 0:
            # 计算平均每月招标数
            date_range = (tenders.latest('created_at').created_at -
                         tenders.earliest('created_at').created_at).days
            months = max(date_range / 30, 1)
            avg_monthly = total_count / months

            if avg_monthly > 5:
                insights.append({
                    'type': 'frequency',
                    'level': 'high',
                    'title': '高频招标人',
                    'description': f'该招标人平均每月发布 {avg_monthly:.1f} 个招标项目，属于高频招标单位。'
                })
            elif avg_monthly > 1:
                insights.append({
                    'type': 'frequency',
                    'level': 'medium',
                    'title': '稳定招标人',
                    'description': f'该招标人平均每月发布 {avg_monthly:.1f} 个招标项目，招标活动较为稳定。'
                })
            else:
                insights.append({
                    'type': 'frequency',
                    'level': 'low',
                    'title': '低频招标人',
                    'description': '该招标人招标频率较低，建议长期关注。'
                })

        # 预算规模分析
        budgets = [t.budget for t in tenders if t.budget]
        if budgets:
            avg_budget = sum(budgets) / len(budgets)
            if avg_budget > 10000000:  # 1000万
                insights.append({
                    'type': 'budget',
                    'level': 'high',
                    'title': '大额招标人',
                    'description': f'平均招标金额 {avg_budget/10000:.0f} 万元，属于大额招标单位。'
                })
            elif avg_budget > 1000000:  # 100万
                insights.append({
                    'type': 'budget',
                    'level': 'medium',
                    'title': '中等规模招标人',
                    'description': f'平均招标金额 {avg_budget/10000:.0f} 万元。'
                })

        # 行业专注度分析
        industries = tenders.values('industry').annotate(count=Count('id'))
        if industries:
            top_industry = industries.order_by('-count').first()
            if top_industry and top_industry['count'] > total_count * 0.5:
                insights.append({
                    'type': 'industry',
                    'level': 'info',
                    'title': '行业专注',
                    'description': f'主要集中于{top_industry["industry"]}行业，占比 {top_industry["count"]/total_count*100:.0f}%。'
                })

        # 合作建议
        insights.append({
            'type': 'suggestion',
            'level': 'info',
            'title': '合作建议',
            'description': self._generate_suggestion(tenders, tenderer_name)
        })

        return insights

    def _generate_suggestion(self, tenders, tenderer_name):
        """生成合作建议"""
        total = tenders.count()
        completed = tenders.filter(status='completed').count()
        success_rate = (completed / total * 100) if total > 0 else 0

        if success_rate > 80:
            return f'该招标人项目完成率高({success_rate:.0f}%)，是优质的合作对象。建议重点关注其发布的招标信息，提前准备投标材料。'
        elif success_rate > 50:
            return f'该招标人项目完成率中等({success_rate:.0f}%)，可以作为常规关注对象。'
        else:
            return '该招标人项目取消率较高，参与投标时需谨慎评估风险。'

    @action(detail=False, methods=['get'])
    def list_tenderers(self, request):
        """获取所有招标人列表"""
        tenderers = TenderNotice.objects.values('tenderer').annotate(
            tender_count=Count('id'),
            total_budget=Sum('budget')
        ).order_by('-tender_count')[:100]

        return Response([
            {
                'name': t['tenderer'],
                'tender_count': t['tender_count'],
                'total_budget': float(t['total_budget'] or 0)
            }
            for t in tenderers if t['tenderer']
        ])
