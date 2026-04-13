#!/bin/bash
# 快速启动脚本 - 开发环境

echo "启动合同管理系统..."

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "✗ 虚拟环境不存在，请先运行 deploy.sh"
    exit 1
fi

# 检查数据库
if [ ! -f "instance/contracts.db" ]; then
    echo "✗ 数据库文件不存在，请先运行 migrate_db.py"
    exit 1
fi

# 启动应用
echo ""
echo "=========================================="
echo "合同管理系统 v2.0"
echo "=========================================="
echo ""
echo "访问地址："
echo "  http://localhost:5000"
echo "  http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "默认账号："
echo "  superadmin / 654321"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python app.py
