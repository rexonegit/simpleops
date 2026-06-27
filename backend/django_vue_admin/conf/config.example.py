"""
Django 配置中心 - 示例模板
复制为 config.py 并填入真实值,config.py 不会提交到 git
"""

# 安全密钥:用以下命令生成
#   python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = ''

# 允许的主机
ALLOWED_HOSTS = ['*']

# 数据库
DB_NAME = ''
DB_USER = ''
DB_PASSWORD = ''
DB_HOST = 'localhost'
DB_PORT = 3306

