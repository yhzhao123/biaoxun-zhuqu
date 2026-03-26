"""
创建测试用户和Token的脚本
运行: python manage.py shell < create_test_user.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

# 创建测试用户
username = 'testuser'
email = 'test@example.com'
password = 'testpass123'

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'email': email,
        'is_active': True,
        'role': 'user'
    }
)

if created:
    user.set_password(password)
    user.save()
    print(f'Created user: {username}')
else:
    print(f'User already exists: {username}')

# 创建或获取token
token, token_created = Token.objects.get_or_create(user=user)

if token_created:
    print(f'Created token: {token.key}')
else:
    print(f'Existing token: {token.key}')

print(f'\n=== 登录信息 ===')
print(f'用户名: {username}')
print(f'密码: {password}')
print(f'Token: {token.key}')
print(f'\n使用方式:')
print(f'1. 登录API: POST /api/v1/auth/login/')
print(f'   数据: {{"username": "{username}", "password": "{password}"}}')
print(f'2. 返回的token放入localStorage: localStorage.setItem("token", "<token>")')
print(f'3. 或者直接在前端设置: localStorage.setItem("token", "{token.key}")')
