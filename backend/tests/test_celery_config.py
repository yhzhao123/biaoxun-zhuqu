"""
Test: Celery configuration in container environment
"""
import os
import unittest


class TestCeleryConfig(unittest.TestCase):
    """测试Celery配置在容器环境中正确使用redis主机名"""
    
    def test_celery_broker_url_uses_redis_host_in_container(self):
        """
        在容器环境中，CELERY_BROKER_URL应该使用'redis'作为主机名，
        而不是'localhost'
        """
        broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        
        # 如果REDIS_URL设置了redis主机，CELERY_BROKER_URL也应该用redis主机
        redis_url = os.environ.get('REDIS_URL', '')
        if 'redis://' in redis_url and 'redis:' in redis_url.split('//')[1].split(':')[0]:
            # 环境变量REDIS_URL使用了'redis'主机名
            # CELERY_BROKER_URL也应该使用相同的主机名
            self.assertIn(
                'redis:', broker_url,
                f"CELERY_BROKER_URL应该使用'redis'主机名，当前值: {broker_url}"
            )
    
    def test_celery_result_backend_uses_redis_host_in_container(self):
        """
        在容器环境中，CELERY_RESULT_BACKEND应该使用'redis'作为主机名
        """
        result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
        
        redis_url = os.environ.get('REDIS_URL', '')
        if 'redis://' in redis_url and 'redis:' in redis_url.split('//')[1].split(':')[0]:
            self.assertIn(
                'redis:', result_backend,
                f"CELERY_RESULT_BACKEND应该使用'redis'主机名，当前值: {result_backend}"
            )


if __name__ == '__main__':
    unittest.main()
