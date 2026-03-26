"""
LLM URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LLMConfigViewSet, ChatViewSet

router = DefaultRouter()
router.register(r'configs', LLMConfigViewSet, basename='llm-config')
router.register(r'chat', ChatViewSet, basename='chat')

urlpatterns = [
    path('', include(router.urls)),
]
