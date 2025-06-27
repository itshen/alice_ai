#!/usr/bin/env python3
"""
Web服务器启动脚本
运行AI Chat Tools的Web界面
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动Web服务器"""
    print("🚀 启动 Alice Web 界面...")
    print("📁 项目目录:", project_root)
    
    # 检查静态文件目录
    static_dir = project_root / "static"
    if not static_dir.exists():
        print("⚠️  静态文件目录不存在，正在创建...")
        static_dir.mkdir(exist_ok=True)
    
    # 检查前端文件
    index_file = static_dir / "index.html"
    if not index_file.exists():
        print("❌ 前端文件不存在: static/index.html")
        print("请确保已经创建了前端文件")
        return
    
    print("✅ 前端文件检查完成")
    print("🌐 启动服务器...")
    print("📱 Web界面地址: http://localhost:8000")
    print("📚 API文档地址: http://localhost:8000/docs")
    print("🛑 按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    try:
        # 启动服务器
        uvicorn.run(
            "ai_chat_tools.api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(project_root)],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 