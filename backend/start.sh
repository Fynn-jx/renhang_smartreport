#!/bin/bash
# 公文写作 AI 系统 - 快速启动脚本（macOS/Linux）

echo "========================================"
echo " 公文写作 AI 系统 - 快速启动"
echo "========================================"
echo ""

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "[1/5] 激活虚拟环境..."
    source venv/bin/activate
else
    echo "[!] 虚拟环境不存在，请先创建："
    echo "    python3 -m venv venv"
    exit 1
fi

echo ""
echo "[2/5] 检查环境变量..."
if [ ! -f ".env" ]; then
    echo "[!] 环境变量文件不存在，从模板创建..."
    cp .env.example .env
    echo "[!] 请编辑 .env 文件，填入必要的配置"
    read -p "按 Enter 继续..."
fi

echo ""
echo "[3/5] 检查数据库连接..."
# 这里可以添加数据库连接检查

echo ""
echo "[4/5] 启动 FastAPI 服务..."
echo ""
echo "========================================"
echo " 服务启动成功！"
echo "========================================"
echo " API 文档： http://localhost:8000/docs"
echo " ReDoc：    http://localhost:8000/redoc"
echo " 健康检查： http://localhost:8000/api/v1/health"
echo ""
echo " 按 Ctrl+C 停止服务"
echo "========================================"
echo ""

python main.py
