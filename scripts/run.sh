#!/bin/bash
# BallonsTranslator 启动脚本 (Linux/Mac)

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "============================================================"
echo "BallonsTranslator 启动脚本"
echo "============================================================"
echo ""

# 检查Python
echo "检查Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到Python"
    echo "请安装Python 3.8或更高版本"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+')
echo "Python版本: $PYTHON_VERSION"

# 检查项目结构
echo ""
echo "检查项目结构..."
if [ ! -f "$PROJECT_ROOT/launch.py" ]; then
    echo "错误: 未找到 launch.py"
    echo "请确保在正确的目录中运行此脚本"
    exit 1
fi
echo "✓ 项目结构正常"

# 检查模型注册表
echo ""
echo "检查模型注册表..."
if [ -d "$PROJECT_ROOT/config/custom_models" ]; then
    MODEL_COUNT=$(find "$PROJECT_ROOT/config/custom_models" -name "*.json" | wc -l)
    echo "✓ 找到 $MODEL_COUNT 个自定义模型"
else
    echo "⚠ 自定义模型目录不存在，运行配置脚本..."
    $PYTHON_CMD "$PROJECT_ROOT/scripts/setup_quick.py"
fi

# 启动应用
echo ""
echo "============================================================"
echo "启动 BallonsTranslator..."
echo "============================================================"
echo ""

cd "$PROJECT_ROOT"
$PYTHON_CMD launch.py "$@"

# 检查退出状态
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "============================================================"
    echo "应用异常退出 (代码: $EXIT_CODE)"
    echo "============================================================"
    
    # 常见错误提示
    if [ $EXIT_CODE -eq 1 ]; then
        echo ""
        echo "可能的解决方案:"
        echo "  1. 安装依赖: pip install -r requirements.txt"
        echo "  2. 运行配置: python3 scripts/setup_quick.py"
        echo "  3. 检查日志: 查看控制台输出"
    fi
    
    exit $EXIT_CODE
fi

echo ""
echo "============================================================"
echo "应用已关闭"
echo "============================================================"
