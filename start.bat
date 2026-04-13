@echo off
REM 快速启动脚本 - Windows 开发环境

echo 启动合同管理系统...

REM 检查虚拟环境
if not exist "venv" (
    echo × 虚拟环境不存在，请先运行 deploy.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat
echo √ 虚拟环境已激活

REM 检查数据库
if not exist "instance\contracts.db" (
    echo × 数据库文件不存在，请先运行 migrate_db.py
    pause
    exit /b 1
)

REM 启动应用
echo.
echo ==========================================
echo 合同管理系统 v2.0
echo ==========================================
echo.
echo 访问地址：
echo   http://localhost:5000
echo.
echo 默认账号：
echo   superadmin / 654321
echo.
echo 按 Ctrl+C 停止服务
echo.

python app.py
