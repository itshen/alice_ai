#!/usr/bin/env python3
"""
AI Chat Tools 主启动文件
"""
import argparse
import sys
import os
import asyncio
from ai_chat_tools.config import config
from ai_chat_tools.tool_module_manager import tool_module_manager
from ai_chat_tools.core import ChatBot
from ai_chat_tools.api import run_server

def setup_tool_modules(args):
    """设置工具模块"""
    # 首先加载所有工具模块
    tool_module_manager.scan_and_load_all_modules()
    
    if args.skip_modules:
        print("⏭️  跳过工具模块激活")
        tool_module_manager.active_modules.clear()
        return
    
    if args.modules:
        # 命令行指定的模块
        specified_modules = [m.strip() for m in args.modules.split(',')]
        tool_module_manager.activate_modules(specified_modules)
        print(f"✅ 激活指定模块: {', '.join(specified_modules)}")
        return
    
    # 检查配置文件设置
    tool_config = config.get("tool_modules", {}) or {}
    
    if tool_config.get("interactive_selection", True):
        # 交互式选择
        selected = tool_module_manager.interactive_module_selection()
        
        # 询问是否保存为默认配置
        if selected:
            try:
                save_choice = input("\n💾 是否将这些模块保存为默认激活模块？(y/N): ").strip().lower()
                if save_choice == 'y':
                    tool_module_manager.save_active_modules_to_config()
                    print("✅ 已保存到配置文件")
            except KeyboardInterrupt:
                pass

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI Chat Tools - 智能聊天工具")
    parser.add_argument("--modules", type=str, help="指定要激活的工具模块，用逗号分隔")
    parser.add_argument("--skip-modules", action="store_true", help="跳过工具模块激活")
    parser.add_argument("--api", action="store_true", help="启动 API 服务器")
    parser.add_argument("--host", type=str, help="API 服务器主机")
    parser.add_argument("--port", type=int, help="API 服务器端口")
    parser.add_argument("--model", type=str, help="指定使用的模型提供商 (ollama, qwen, openrouter)")
    parser.add_argument("--list-models", action="store_true", help="列出所有可用模型并退出")
    parser.add_argument("--task-scheduler", action="store_true", help="启动任务调度器模式")
    parser.add_argument("--task-manager", action="store_true", help="启动任务管理模式")
    return parser.parse_args()

def show_available_models():
    """显示所有可用模型"""
    from ai_chat_tools.models import model_manager
    
    print("🤖 可用模型列表:")
    print("=" * 40)
    
    info = model_manager.get_provider_info()
    default_provider = info.get("default_provider")
    
    models_config = config.get('models', {}) or {}
    
    for provider, provider_config in models_config.items():
        status = "✅ 已启用" if provider_config.get("enabled", False) else "❌ 已禁用"
        is_default = "（默认）" if provider == default_provider else ""
        
        print(f"  {provider.upper()}: {status} {is_default}")
        print(f"    模型: {provider_config.get('model', 'unknown')}")
        
        if provider_config.get('host'):
            print(f"    主机: {provider_config.get('host')}")
        
        if provider_config.get('api_key'):
            print(f"    API密钥: {'已设置' if provider_config.get('api_key') else '未设置'}")
        
        print()

def select_model_interactively():
    """交互式选择模型"""
    from ai_chat_tools.models import model_manager
    
    available_providers = model_manager.list_adapters()
    
    if not available_providers:
        print("❌ 没有可用的模型提供商")
        return None
    
    if len(available_providers) == 1:
        print(f"🤖 只有一个可用模型: {available_providers[0]}")
        return available_providers[0]
    
    print("\n🤖 请选择要使用的模型:")
    for i, provider in enumerate(available_providers, 1):
        models_config = config.get('models', {}) or {}
        model_name = models_config.get(provider, {}).get('model', 'unknown')
        print(f"  {i}. {provider.upper()} ({model_name})")
    
    print(f"  0. 使用默认模型 ({model_manager.get_default_provider_name()})")
    
    while True:
        try:
            choice = input("\n请输入选择 (0-{}): ".format(len(available_providers))).strip()
            
            if choice == "0":
                return None  # 使用默认模型
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(available_providers):
                selected_provider = available_providers[choice_num - 1]
                print(f"✅ 已选择: {selected_provider}")
                return selected_provider
            else:
                print("❌ 无效选择，请重新输入")
                
        except (ValueError, KeyboardInterrupt):
            print("\n👋 取消选择，使用默认模型")
            return None

def run_task_scheduler():
    """运行任务调度器"""
    import asyncio
    from ai_chat_tools.task_scheduler import task_scheduler
    from ai_chat_tools.tool_module_manager import tool_module_manager
    
    async def scheduler_main():
        try:
            # 加载任务管理工具模块
            tool_module_manager.load_module("task_management_tools")
            print("✅ 任务管理工具已加载")
            
            # 启动调度器
            await task_scheduler.start()
            print("🚀 任务调度器已启动，按 Ctrl+C 停止")
            
            # 保持运行
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️ 正在停止任务调度器...")
            await task_scheduler.stop()
            print("👋 任务调度器已停止")
        except Exception as e:
            print(f"❌ 任务调度器错误: {e}")
            await task_scheduler.stop()
    
    # 运行调度器
    asyncio.run(scheduler_main())

def run_task_manager():
    """运行任务管理界面"""
    from ai_chat_tools.core import ChatBot
    from ai_chat_tools.tool_module_manager import tool_module_manager
    
    # 加载任务管理工具模块
    tool_module_manager.load_module("task_management_tools")
    print("✅ 任务管理工具已加载")
    
    print("\n🛠️ 任务管理模式")
    print("💡 可以使用以下命令管理任务:")
    print("   - 创建任务: create_scheduled_task")
    print("   - 列出任务: list_scheduled_tasks")
    print("   - 查看详情: get_task_details")
    print("   - 更新任务: update_scheduled_task")
    print("   - 删除任务: delete_scheduled_task")
    print("   - 启用/禁用: enable_scheduled_task")
    print("   - 立即执行: execute_task_now")
    print("   - 查看历史: get_task_history")
    print("   - 调度器状态: get_scheduler_status")
    print("💡 输入 'help' 查看帮助，输入 'quit' 退出\n")
    
    # 创建聊天机器人
    bot = ChatBot(debug=True)
    
    # 启动聊天循环
    import asyncio
    
    async def chat_loop():
        while True:
            try:
                user_input = input("💬 ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见!")
                    break
                
                if not user_input:
                    continue
                
                # 处理输入
                async for chunk in bot.chat_stream(
                    message=user_input,
                    tools=["task_management_tools"]
                ):
                    print(chunk, end='', flush=True)
                print()  # 换行
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
    
    # 运行聊天循环
    asyncio.run(chat_loop())

def main():
    """主函数"""
    args = parse_args()
    
    try:
        # 如果只是列出模型，显示后退出
        if args.list_models:
            show_available_models()
            return
        
        # 处理模型选择
        selected_provider = None
        
        if args.model:
            # 通过命令行参数指定模型
            from ai_chat_tools.models import model_manager
            available_providers = model_manager.list_adapters()
            
            if args.model in available_providers:
                selected_provider = args.model
                print(f"🤖 使用指定模型: {args.model}")
            else:
                print(f"❌ 模型 '{args.model}' 不可用")
                print(f"可用模型: {', '.join(available_providers)}")
                return
        
        # 设置工具模块
        setup_tool_modules(args)
        
        if args.task_scheduler:
            # 启动任务调度器模式
            print("📅 启动任务调度器模式...")
            run_task_scheduler()
        elif args.task_manager:
            # 启动任务管理模式
            print("🛠️ 启动任务管理模式...")
            run_task_manager()
        elif args.api:
            # 启动 API 服务器
            print(f"🚀 启动 API 服务器: http://{args.host or '0.0.0.0'}:{args.port or 8000}")
            run_server(args.host, args.port)
        else:
            # 启动聊天界面
            print("\n🤖 AI Chat Tools 已启动")
            print("💡 输入 /help 查看帮助，输入 quit 退出")
            print("📝 会话管理：/新建会话 [标题] | /会话列表 | /切换会话 <ID> | /显示历史")
            
            # 显示激活的模块信息
            active_modules = list(tool_module_manager.active_modules)
            if active_modules:
                print(f"✅ 已激活工具模块: {', '.join(active_modules)}")
            else:
                print("⚠️  未激活任何工具模块，只有核心工具可用")
            
            # 如果没有通过命令行指定模型，且有多个可用模型，提供交互式选择
            if not selected_provider:
                from ai_chat_tools.models import model_manager
                available_providers = model_manager.list_adapters()
                
                # 检查是否设置了自动使用默认模型的环境变量
                auto_model = os.environ.get('AI_CHAT_TOOLS_AUTO_MODEL')
                
                if len(available_providers) > 1 and not auto_model:
                    print(f"\n🤖 检测到多个可用模型: {', '.join(available_providers)}")
                    choice = input("是否要选择特定模型？[y/N]: ").lower().strip()
                    
                    if choice in ['y', 'yes']:
                        selected_provider = select_model_interactively()
                elif auto_model:
                    print(f"\n🤖 自动使用默认模型 ({model_manager.get_default_provider_name()})")
            
            # 创建聊天机器人（命令行模式默认开启debug显示工具执行详情）
            bot = ChatBot(provider=selected_provider if selected_provider else None, debug=True)
            
            # 显示当前使用的模型信息
            from ai_chat_tools.models import model_manager
            current_provider = bot.provider or model_manager.get_default_provider_name()
            if current_provider:
                models_config = config.get('models', {}) or {}
                model_name = models_config.get(current_provider, {}).get('model', 'unknown')
                print(f"🧠 当前使用模型: {current_provider} ({model_name})")
                
                # 显示可用的其他模型
                available_providers = model_manager.list_adapters()
                other_providers = [p for p in available_providers if p != current_provider]
                if other_providers:
                    print(f"🔄 可切换模型: {', '.join(other_providers)}")
                    print("💡 使用 /list_models 查看详细信息，使用 /switch_model 切换模型")
            else:
                print("⚠️  没有可用的模型")
            
            print("-" * 50)
            
            # 开始聊天循环
            while True:
                try:
                    user_input = input("\n你: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() in ['quit', 'exit', '退出']:
                        print("👋 再见！")
                        break
                    
                    # 处理特殊命令（支持斜杠前缀和中文）
                    if user_input.startswith('/') or user_input.startswith('／'):
                        # 移除斜杠前缀
                        command = user_input[1:].strip()
                        
                        if command.lower().startswith(('new_session', 'newsession', '新建会话', '新会话')):
                            # 新建会话
                            parts = command.split(' ', 1) if ' ' in command else [command]
                            title = parts[1].strip() if len(parts) > 1 else "新对话"
                            session_id = bot.create_session(title)
                            print(f"✅ 已创建新会话: {title}")
                            print(f"🆔 会话ID: {session_id}")
                            continue
                        
                        elif command.lower() in ['list_sessions', 'listsessions', 'sessions', '会话列表', '列出会话', '会话']:
                            # 列出会话
                            sessions = bot.get_sessions()
                            if not sessions:
                                print("📝 暂无对话会话")
                            else:
                                print(f"📝 对话会话列表 (共 {len(sessions)} 个):")
                                print("=" * 50)
                                # 按更新时间排序
                                sessions.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
                                for i, session in enumerate(sessions[:10], 1):  # 只显示最近10个
                                    session_id = session.get("id", "")
                                    title = session.get("title", "未命名会话")
                                    created_at = session.get("created_at", "")
                                    # 获取消息数量
                                    from ai_chat_tools.database import db
                                    message_count = len(db.get_messages(session_id))
                                    current_mark = " 📍 当前" if session_id == bot.current_session_id else ""
                                    print(f"  {i}. {title}{current_mark}")
                                    print(f"      ID: {session_id}")
                                    print(f"      创建时间: {created_at}")
                                    print(f"      消息数: {message_count}")
                                    print()
                            continue
                        
                        elif command.lower().startswith(('switch_session', 'switchsession', '切换会话')):
                            # 切换会话
                            parts = command.split(' ', 1) if ' ' in command else [command]
                            if len(parts) < 2:
                                print("❌ 请指定会话ID，格式: /switch_session <session_id> 或 /切换会话 <session_id>")
                            else:
                                session_id = parts[1].strip()
                                try:
                                    bot.load_session(session_id)
                                    from ai_chat_tools.database import db
                                    session = db.get_session(session_id)
                                    if session:
                                        title = session.get("title", "未命名会话")
                                        print(f"✅ 已切换到会话: {title}")
                                        print(f"🆔 会话ID: {session_id}")
                                    else:
                                        print(f"❌ 会话 {session_id} 不存在")
                                except Exception as e:
                                    print(f"❌ 切换会话失败: {e}")
                            continue
                        
                        elif command.lower() in ['show_history', 'showhistory', 'history', '显示历史', '查看历史', '历史']:
                            # 显示当前会话历史
                            if bot.current_session_id:
                                messages = bot.get_session_messages()
                                if not messages:
                                    print("📝 当前会话暂无消息历史")
                                else:
                                    from ai_chat_tools.database import db
                                    session = db.get_session(bot.current_session_id)
                                    session_title = session.get("title", "未命名会话") if session else "未知会话"
                                    print(f"📝 会话历史: {session_title}")
                                    print(f"🆔 会话ID: {bot.current_session_id}")
                                    print("=" * 50)
                                    # 只显示最近10条消息
                                    recent_messages = messages[-10:] if len(messages) > 10 else messages
                                    for i, msg in enumerate(recent_messages, 1):
                                        role = msg.get("role", "unknown")
                                        content = msg.get("content", "")
                                        timestamp = msg.get("timestamp", "")
                                        
                                        role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(role, "❓")
                                        print(f"{i}. {role_icon} {role.upper()}")
                                        if timestamp:
                                            print(f"   ⏰ {timestamp}")
                                        
                                        # 内容预览（避免过长）
                                        if len(content) > 200:
                                            content_preview = content[:200] + "..."
                                        else:
                                            content_preview = content
                                        print(f"   💬 {content_preview}")
                                        print("-" * 30)
                                    
                                    if len(messages) > 10:
                                        print(f"\n💡 只显示最近10条消息，该会话共有 {len(messages)} 条消息")
                            else:
                                print("❌ 当前没有活动会话")
                            continue
                        
                        elif command.lower() in ['help', '帮助']:
                            print("🔧 AI Chat Tools 帮助")
                            print("=" * 40)
                            print("💬 聊天命令:")
                            print("  直接输入消息 - 与AI对话")
                            print("  quit/exit/退出 - 退出程序")
                            print()
                            print("📝 会话管理 (使用 / 或 ／ 前缀):")
                            print("  /new_session [标题] 或 /新建会话 [标题] - 创建新会话")
                            print("  /list_sessions 或 /会话列表 - 列出所有会话")
                            print("  /switch_session <ID> 或 /切换会话 <ID> - 切换到指定会话")
                            print("  /show_history 或 /显示历史 - 显示当前会话历史")
                            print()
                            print("🤖 模型管理:")
                            print("  /list_models - 列出可用模型")
                            print("  /switch_model <模型名> - 切换模型")
                            print()
                            print("🔧 工具管理:")
                            print("  可以在对话中让AI调用工具来查看和管理工具模块")
                            continue
                        
                        elif command.lower() in ['list_models']:
                            show_available_models()
                            continue
                        
                        elif command.lower().startswith('switch_model'):
                            parts = command.split(' ', 1)
                            if len(parts) < 2:
                                print("❌ 请指定模型名，格式: /switch_model <模型名>")
                            else:
                                model_name = parts[1].strip()
                                try:
                                    success = bot.switch_model(model_name)
                                    if success:
                                        models_config = config.get('models', {}) or {}
                                        model_display = models_config.get(model_name, {}).get('model', model_name)
                                        print(f"✅ 已切换到模型: {model_name} ({model_display})")
                                    else:
                                        print(f"❌ 切换到模型 {model_name} 失败")
                                except Exception as e:
                                    print(f"❌ 切换模型失败: {e}")
                            continue
                        
                        else:
                            print(f"❌ 未知命令: /{command}")
                            print("💡 输入 /help 或 /帮助 查看可用命令")
                            continue
                    
                    # 获取回复（异步处理）
                    print("\nAI: ", end="", flush=True)
                    
                    async def process_response():
                        async for chunk in bot.chat_stream(user_input):
                            print(chunk, end="", flush=True)
                        print()
                    
                    asyncio.run(process_response())
                    
                except KeyboardInterrupt:
                    print("\n👋 再见！")
                    break
                except Exception as e:
                    print(f"\n❌ 发生错误: {e}")
                    
    except KeyboardInterrupt:
        print("\n👋 再见！")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 