"""
Users API URLs
"""
from django.urls import path
from .views import UserPreferencesView

urlpatterns = [
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
]
