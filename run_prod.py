"""
生产环境启动脚本 - 使用waitress作为WSGI服务器
"""
from waitress import serve
from app import app
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='server.log'
)
logger = logging.getLogger('waitress')

if __name__ == "__main__":
    # 从环境变量获取端口，默认5000
    port = int(os.environ.get('PORT', 5000))
    
    # 设置生产环境变量
    os.environ['FLASK_ENV'] = 'production'
    
    logger.info(f"Starting server on port {port}")
    print(f"Server running on http://0.0.0.0:{port}")
    
    # 启动waitress服务器
    serve(app, host='0.0.0.0', port=port, threads=6)
