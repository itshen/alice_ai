#!/bin/bash

# AI Chat Tools 启动脚本

echo "🚀 AI Chat Tools 启动脚本"
echo "=========================="

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "⚠️  建议激活虚拟环境: source .venv/bin/activate"
fi

# 检查是否已安装
if python3.11 -c "import ai_chat_tools" 2>/dev/null; then
    echo "✅ AI Chat Tools 已安装"
else
    echo "📦 正在安装 AI Chat Tools..."
    pip install -e .
fi

# 检查端口是否可用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # 端口被占用
    else
        return 0  # 端口可用
    fi
}

# 查找可用端口
find_available_port() {
    for port in 8000 8001 8002 8003 8004; do
        if check_port $port; then
            echo $port
            return
        fi
    done
    echo "8005"  # 默认端口
}

echo "=========================="
echo "🤖 AI Chat Tools"
echo "=========================="
echo "请选择要执行的操作:"
echo ""
echo "聊天功能:"
echo "  1) 🚀 快速对话模式 (使用默认值)"
echo "  2) 🔧 指定模块启动对话"
echo "  3) ⏭️  跳过模块启动对话"
echo ""
echo "模型管理:"
echo "  4) 🤖 列出可用模型"
echo "  5) 🔄 选择模型启动对话"
echo ""
echo "开发与测试:"
echo "  6) 🧪 运行测试"
echo "  7) 📚 查看工具格式指南"
echo ""
echo "API服务:"
echo "  8) 🚀 启动API服务器"
echo ""
echo "任务调度:"
echo "  9) 📅 启动任务调度器"
echo "  10) 🛠️ 任务管理模式"
echo ""
read -p "请输入选择 (1-10): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动快速对话模式..."
        echo "💡 使用默认值，跳过模块启动"
        echo "💡 输入 'help' 查看帮助，输入 'quit' 退出"
        echo "=========================="
        python3.11 main.py --skip-modules
        ;;
    2)
        echo ""
        echo "🔧 指定模块启动对话..."
        read -p "请输入要激活的模块名称 (用逗号分隔，如: file_manager_tools): " modules
        if [[ -n "$modules" ]]; then
            echo "启动对话模式，激活模块: $modules"
            echo "=========================="
            python3.11 main.py --modules "$modules"
        else
            echo "❌ 未输入模块名称"
        fi
        ;;
    3)
        echo ""
        echo "⏭️ 跳过模块启动对话..."
        echo "只使用核心工具启动对话模式"
        echo "=========================="
        python3.11 main.py --skip-modules
        ;;
         4)
         echo ""
         echo "🤖 列出可用模型..."
         python3.11 main.py --list-models
         ;;
     5)
         echo ""
         echo "🔄 选择模型启动对话..."
         read -p "请输入要使用的模型名称 (ollama/qwen/openrouter): " model
         if [[ -n "$model" ]]; then
             echo "启动对话模式，使用模型: $model"
             echo "=========================="
             python3.11 main.py --model "$model"
         else
             echo "❌ 未输入模型名称"
         fi
         ;;
     6)
         echo ""
         echo "🧪 运行测试..."
         python3.11 test_model_management.py
         ;;
     7)
         echo ""
         echo "📚 查看工具列表..."
         python3.11 -c "
from ai_chat_tools.tool_manager import tool_registry
tools = tool_registry.list_tools()
print('可用工具:')
for tool in tools:
    print(f'  - {tool[\"name\"]}: {tool[\"description\"]}')
print(f'\\n总共 {len(tools)} 个工具')
"
         ;;
    8)
        echo ""
        available_port=$(find_available_port)
        echo "🚀 启动API服务器..."
        echo "访问地址: http://localhost:$available_port"
        echo "按 Ctrl+C 停止服务器"
        echo ""
        python3.11 main.py --api --port $available_port
        ;;
    9)
        echo ""
        echo "📅 启动任务调度器..."
        echo "🎯 任务调度器将在后台运行定时任务"
        echo "💡 需要先安装 APScheduler: pip install apscheduler"
        echo "🔧 可以通过任务管理模式或API管理任务"
        echo "按 Ctrl+C 停止调度器"
        echo ""
        python3.11 main.py --task-scheduler
        ;;
    10)
        echo ""
        echo "🛠️ 启动任务管理模式..."
        echo "💡 在此模式下可以创建、修改、删除定时任务"
        echo "🎯 支持多种调度类型: cron、interval、date等"
        echo "💬 使用自然语言与AI交互管理任务"
        echo ""
        python3.11 main.py --task-manager
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac 