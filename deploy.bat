@echo off
REM 合同管理系统 v2.0 - Windows 部署脚本
REM 使用方法：双击运行或在命令行执行 deploy.bat

echo ==========================================
echo 合同管理系统 v2.0 - 部署脚本 (Windows)
echo ==========================================
echo.

REM 检查 Python 版本
echo 检查 Python 版本...
python --version
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 创建虚拟环境
echo.
echo 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo √ 虚拟环境创建成功
) else (
    echo √ 虚拟环境已存在
)

REM 激活虚拟环境并安装依赖
echo.
echo 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
pip install -r "requirements(m).txt"
if errorlevel 1 (
    echo 错误：依赖安装失败
    pause
    exit /b 1
)
echo √ 依赖安装成功

REM 执行数据库迁移
echo.
echo 执行数据库迁移...
python migrate_db.py
if errorlevel 1 (
    echo 错误：数据库迁移失败
    pause
    exit /b 1
)
echo √ 数据库迁移成功

REM 创建必要的目录
echo.
echo 创建必要的目录...
if not exist "uploads" mkdir uploads
if not exist "static" mkdir static
if not exist "instance" mkdir instance
echo √ 目录创建成功

echo.
echo ==========================================
echo 部署完成！
echo ==========================================
echo.
echo 启动方式：
echo.
echo 1. 开发环境（测试）：
echo    venv\Scripts\activate.bat
echo    python app.py
echo.
echo 2. 生产环境（推荐）：
echo    venv\Scripts\activate.bat
echo    waitress-serve --host=0.0.0.0 --port=5000 app:app
echo.
echo 访问地址：
echo    http://localhost:5000
echo.
echo 默认账号：
echo    superadmin / 654321
echo.
echo 重要提示：
echo    1. 首次登录后请立即修改默认密码
echo    2. 生产环境请修改 app.py 中的 SECRET_KEY
echo    3. 定期备份 instance\contracts.db 数据库文件
echo.
pause
