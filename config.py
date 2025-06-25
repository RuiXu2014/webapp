import os
from app import app

# 从环境变量读取配置
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'default-secret-key-change-in-production'),
    DEBUG=os.environ.get('DEBUG', 'False') == 'True',
    # 添加其他配置...
)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
