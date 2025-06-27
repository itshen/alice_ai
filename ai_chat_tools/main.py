#!/usr/bin/env python3.11
"""
AI Chat Tools 主启动文件
"""
import argparse
from .api import run_server
from .tool_module_manager import tool_module_manager
from .config import config

# 导入核心工具（确保它们被注册）
from . import tools

def load_tool_modules():
    """加载工具模块"""
    print("\n" + "="*60)
    print("🔧 工具模块加载")
    print("="*60)
    
    # 扫描并加载所有模块
    tool_module_manager.scan_and_load_all_modules()
    
    # 检查是否启用交互式选择
    if config.get("tool_modules", {}).get("interactive_selection", True):
        # 进行交互式模块激活选择
        selected_modules = tool_module_manager.interactive_module_selection()
        
        if selected_modules:
            print(f"\n✅ 已激活 {len(selected_modules)} 个工具模块: {', '.join(selected_modules)}")
            
            # 询问是否保存为默认配置
            try:
                save_default = input("\n💾 是否将这些模块保存为默认激活模块？(y/N): ").strip().lower()
                if save_default in ['y', 'yes', '是']:
                    tool_module_manager.save_active_modules_to_config()
                    print("✅ 已保存为默认配置")
            except KeyboardInterrupt:
                print("\n⚠️  跳过保存配置")
    else:
        # 自动激活默认模块
        default_active = config.get("tool_modules", {}).get("default_active", [])
        if default_active:
            tool_module_manager.activate_modules(default_active)
            print(f"✅ 已自动激活默认模块: {', '.join(default_active)}")
    
    # 显示最终状态
    active_modules = list(tool_module_manager.active_modules)
    if active_modules:
        print(f"\n🎉 当前已激活 {len(active_modules)} 个工具模块: {', '.join(active_modules)}")
    else:
        print("\n⚠️  当前没有激活任何工具模块，只有核心工具可用")
    
    print("="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI Chat Tools - 简化的AI工具调用框架")
    parser.add_argument("--host", default=None, help="服务器主机地址")
    parser.add_argument("--port", type=int, default=None, help="服务器端口")
    parser.add_argument("--no-modules", action="store_true", help="跳过工具模块加载")
    parser.add_argument("--load-modules", nargs="*", help="指定要加载的工具模块")
    
    args = parser.parse_args()
    
    # 处理工具模块加载
    if args.no_modules:
        print("⚠️  跳过工具模块加载")
    elif args.load_modules is not None:
        # 命令行指定模块
        if args.load_modules:
            print(f"📦 扫描并激活指定的工具模块: {', '.join(args.load_modules)}")
            tool_module_manager.scan_and_load_all_modules()
            success = tool_module_manager.activate_modules(args.load_modules)
            if success:
                print(f"✅ 成功激活 {len(args.load_modules)} 个模块")
            else:
                print("⚠️  部分模块激活失败")
        else:
            print("⚠️  未指定要激活的模块，将扫描所有模块")
            tool_module_manager.scan_and_load_all_modules()
    else:
        # 默认加载流程
        load_tool_modules()
    
    # 启动服务器
    run_server(host=args.host, port=args.port)

if __name__ == "__main__":
    main() 