#!/usr/bin/env python3.11
"""
AI Chat Tools 启动脚本 (Python版本)
"""
import os
import sys
import socket
import subprocess

def check_port(port):
    """检查端口是否可用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def find_available_port():
    """查找可用端口"""
    for port in [8000, 8001, 8002, 8003, 8004]:
        if check_port(port):
            return port
    return 8005

def run_command(cmd):
    """运行命令"""
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
    except KeyboardInterrupt:
        print("\n👋 用户中断")

def main():
    print("🚀 AI Chat Tools 启动脚本")
    print("==========================")
    
    # 检查虚拟环境
    if os.environ.get('VIRTUAL_ENV'):
        print(f"✅ 虚拟环境已激活: {os.environ['VIRTUAL_ENV']}")
    else:
        print("⚠️  建议激活虚拟环境: source .venv/bin/activate")
    
    # 检查是否已安装
    try:
        import ai_chat_tools
        print("✅ AI Chat Tools 已安装")
    except ImportError:
        print("📦 正在安装 AI Chat Tools...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."])
    
    print()
    print("🎯 选择运行模式:")
    print("聊天功能:")
    print("  1) 🚀 快速对话模式 (使用默认值)")
    print("  2) 🔧 指定模块启动对话")
    print("  3) ⏭️  跳过模块启动对话")
    print("")
    print("模型管理:")
    print("  4) 🤖 列出可用模型")
    print("  5) 🔄 选择模型启动对话")
    print("")
    print("开发与测试:")
    print("  6) 🧪 运行测试")
    print("  7) 📚 查看工具列表")
    print("")
    print("API服务:")
    print("  8) 🚀 启动API服务器")
    print("")
    print("任务调度:")
    print("  9) 📅 启动任务调度器")
    print("  10) 🛠️ 任务管理模式")
    
    try:
        choice = input("请输入选择 (1-10): ").strip()
    except KeyboardInterrupt:
        print("\n👋 再见!")
        return
    
    if choice == "1":
        print("\n🚀 启动快速对话模式...")
        print("💡 使用默认值，跳过模块启动")
        print("💡 输入 'help' 查看帮助，输入 'quit' 退出")
        print("==========================")
        run_command("python3.11 main.py --skip-modules")
        
    elif choice == "2":
        print("\n🔧 指定模块启动对话...")
        modules = input("请输入要激活的模块名称 (用逗号分隔，如: file_manager_tools): ").strip()
        if modules:
            print(f"启动对话模式，激活模块: {modules}")
            print("==========================")
            run_command(f"python3.11 main.py --modules {modules}")
        else:
            print("❌ 未输入模块名称")
            
    elif choice == "3":
        print("\n⏭️ 跳过模块启动对话...")
        print("只使用核心工具启动对话模式")
        print("==========================")
        run_command("python3.11 main.py --skip-modules")
        
    elif choice == "4":
        print("\n🤖 列出可用模型...")
        run_command("python3.11 main.py --list-models")
        
    elif choice == "5":
        print("\n🔄 选择模型启动对话...")
        model = input("请输入要使用的模型名称 (ollama/qwen/openrouter): ").strip()
        if model:
            print(f"启动对话模式，使用模型: {model}")
            print("==========================")
            run_command(f"python3.11 main.py --model {model}")
        else:
            print("❌ 未输入模型名称")
        
    elif choice == "6":
        print("\n🧪 运行测试...")
        run_command("python3.11 test_model_management.py")
        
    elif choice == "7":
        print("\n📚 查看工具列表...")
        try:
            from ai_chat_tools.tool_manager import tool_registry
            tools = tool_registry.list_tools()
            print("可用工具:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            print(f"\n总共 {len(tools)} 个工具")
        except Exception as e:
            print(f"❌ 获取工具列表失败: {e}")
            
    elif choice == "8":
        port = find_available_port()
        print(f"\n🚀 启动API服务器...")
        print(f"🌐 访问地址: http://localhost:{port}")
        print("按 Ctrl+C 停止服务器")
        print("==========================")
        run_command(f"python3.11 main.py --api --port {port}")
        
    elif choice == "9":
        print("\n📅 启动任务调度器...")
        print("🎯 任务调度器将在后台运行定时任务")
        print("💡 需要先安装 APScheduler: pip install apscheduler")
        print("🔧 可以通过任务管理模式或API管理任务")
        print("按 Ctrl+C 停止调度器")
        print("==========================")
        run_command("python3.11 main.py --task-scheduler")
        
    elif choice == "10":
        print("\n🛠️ 启动任务管理模式...")
        print("💡 在此模式下可以创建、修改、删除定时任务")
        print("🎯 支持多种调度类型: cron、interval、date等")
        print("💬 使用自然语言与AI交互管理任务")
        print("==========================")
        run_command("python3.11 main.py --task-manager")
        
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 