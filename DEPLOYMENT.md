# 生产环境部署指南

本文档介绍如何将Web应用部署到生产环境。

## 方法1：服务器直接部署（包含虚拟环境）

### 准备工作
1. 确保服务器上已安装Python 3.9+
2. 创建项目目录并上传项目代码

### 部署步骤
1. 创建虚拟环境：
   ```
   python -m venv venv
   ```

2. 激活虚拟环境：
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. 安装依赖：
   ```
   # 使用默认PyPI源
   pip install -r requirements.txt
   
   # 或使用国内镜像源（推荐，下载更快）
   # 清华大学镜像
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   
   # 阿里云镜像
   # pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
   
   # 腾讯云镜像
   # pip install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple
   ```

4. 启动应用：
   ```
   python run_prod.py
   ```
   或使用提供的启动脚本：
   - Windows: `start_app.bat`
   - PowerShell: `.\deploy.ps1`

## 方法2：Docker容器部署（推荐）

### 准备工作
1. 确保服务器上已安装Docker和Docker Compose
2. 上传项目代码到服务器

### 部署步骤
1. 构建并启动容器：
   ```
   docker-compose up -d
   ```

2. 查看日志：
   ```
   docker-compose logs -f
   ```

3. 停止服务：
   ```
   docker-compose down
   ```

## 重要文件

- `run_prod.py` - 生产环境启动脚本
- `requirements.txt` - 项目依赖清单
- `Dockerfile` - Docker镜像构建文件
- `docker-compose.yml` - 容器编排配置
- `pip_mirror_config.md` - PyPI镜像源配置指南

## 注意事项

1. 生产环境必须设置安全的SECRET_KEY
2. 确保数据目录（uploads、output_csv、output_json）有正确的访问权限
3. 定期备份模型和配置数据
4. 考虑使用Nginx作为反向代理，处理SSL和静态文件
