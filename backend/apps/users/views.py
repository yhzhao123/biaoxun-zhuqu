"""
Users API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class UserPreferencesView(APIView):
    """
    用户偏好设置API
    """

    def get(self, request):
        """获取用户偏好设置"""
        # Return format matching frontend expectations
        return Response({
            'id': 'default',
            'username': '用户',
            'email': '',
            'notification_preferences': {
                'email_enabled': True,
                'tender_match_enabled': False,
                'price_alert_enabled': False,
                'system_notifications_enabled': True,
                'crawl_complete_enabled': False
            },
            'default_region': None,
            'default_industry': None,
            'display_settings': {
                'theme': 'light',
                'language': 'zh',
                'items_per_page': 20
            },
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        })

    def put(self, request):
        """更新用户偏好设置"""
        # 模拟更新成功
        return Response({
            'message': 'Preferences updated successfully',
            'data': request.data
        })

    def patch(self, request):
        """部分更新用户偏好设置"""
        return Response({
            'message': 'Preferences updated successfully',
            'data': request.data
        })
