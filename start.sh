#!/bin/bash
# 通宝奖励查询系统 - 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "  通宝奖励查询系统 - 启动中..."
echo "======================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -q -r requirements.txt

# 创建数据目录
mkdir -p data

# 检查配置
if [ -f ".env" ]; then
    echo "📄 加载配置文件 .env"
    export $(grep -v '^#' .env | xargs)
fi

# 检查必要配置
if [ "$TENCENT_DOC_APP_ID" = "你的APP_ID" ] || [ -z "$TENCENT_DOC_APP_ID" ]; then
    echo ""
    echo "⚠️  检测到 API 尚未配置！"
    echo "   请先配置 .env 文件，参考 .env.example"
    echo "   系统将以演示模式启动（无数据同步）"
    echo ""
fi

# 启动服务
echo ""
echo "🚀 启动服务..."
echo "   访问地址: http://localhost:${FLASK_PORT:-5000}"
echo "   按 Ctrl+C 停止服务"
echo ""

python3 app.py
