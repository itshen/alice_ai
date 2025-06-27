#!/usr/bin/env python3.11
"""
快速启动脚本 - 默认模型，不加载工具
"""
import subprocess
import sys
import os

def main():
    """主函数"""
    print("🚀 AI Chat Tools 快速启动")
    print("=" * 30)
    print("✅ 配置: 默认模型 + 不加载工具")
    print("💡 输入 'help' 查看帮助，输入 'quit' 退出")
    print("=" * 30)
    
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        # 设置环境变量，跳过交互式模型选择
        env = os.environ.copy()
        env['AI_CHAT_TOOLS_AUTO_MODEL'] = '1'  # 自动使用默认模型
        
        # 运行主程序，跳过模块加载
        subprocess.run([
            sys.executable, 
            "main.py", 
            "--skip-modules"
        ], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
        return 0
    
    return 0

if __name__ == "__main__":
    exit(main()) 