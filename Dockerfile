FROM python:3.9-slim

WORKDIR /webapp

# 复制依赖文件
COPY requirements.txt .

# 安装依赖（使用国内镜像源且不保留缓存以减小镜像大小）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY . .

# 创建上传目录并设置权限
RUN mkdir -p /app/uploads && chmod 777 /app/uploads
RUN mkdir -p /app/output_csv && chmod 777 /app/output_csv
RUN mkdir -p /app/output_json && chmod 777 /app/output_json

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV FLASK_ENV=production
ENV PORT=8000

# 启动命令
CMD ["python", "run_prod.py"]
