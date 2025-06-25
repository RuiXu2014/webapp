# deploy.ps1 - PowerShell部署脚本
# 创建虚拟环境
Write-Host "正在创建虚拟环境..." -ForegroundColor Green
python -m venv venv

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1

# 安装依赖项
Write-Host "安装依赖项..." -ForegroundColor Green
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动服务
Write-Host "启动Web应用..." -ForegroundColor Green
python run_prod.py
