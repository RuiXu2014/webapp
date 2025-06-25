@echo off
REM 启动脚本 - 自动激活虚拟环境并启动应用

echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

echo 安装或更新依赖项...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo 启动Web应用...
python run_prod.py

REM 如果应用停止，保持窗口开启
pause
