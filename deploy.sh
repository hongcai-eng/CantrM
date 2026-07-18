#!/bin/bash
# 合同管理系统 - 快速部署脚本
# 使用方法：bash deploy.sh

echo "=========================================="
echo "合同管理系统 v2.0 - 部署脚本"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误：未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 创建虚拟环境
echo ""
echo "创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 虚拟环境创建成功"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "安装 Python 依赖..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误：依赖安装失败"
    exit 1
fi
echo "✓ 依赖安装成功"

# 执行数据库迁移
echo ""
echo "执行数据库迁移..."
python migrate_db.py
if [ $? -ne 0 ]; then
    echo "错误：数据库迁移失败"
    exit 1
fi
echo "✓ 数据库迁移成功"

# 创建必要的目录
echo ""
echo "创建必要的目录..."
mkdir -p uploads
mkdir -p static
mkdir -p instance
echo "✓ 目录创建成功"

# 设置权限
echo ""
echo "设置文件权限..."
chmod -R 755 static/
chmod -R 755 uploads/
chmod 664 instance/contracts.db 2>/dev/null || true
echo "✓ 权限设置完成"

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "启动方式："
echo ""
echo "1. 开发环境（测试）："
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "2. 生产环境（推荐）："
echo "   source venv/bin/activate"
echo "   gunicorn -c gunicorn_config.py app:app"
echo ""
echo "访问地址："
echo "   http://localhost:5000"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "默认账号："
echo "   superadmin / 654321"
echo ""
echo "⚠️  重要提示："
echo "   1. 首次登录后请立即修改默认密码"
echo "   2. 生产环境请修改 app.py 中的 SECRET_KEY"
echo "   3. 建议配置 Nginx 反向代理"
echo "   4. 定期备份 instance/contracts.db 数据库文件"
echo ""
