"""
AI Chat Tools - 简化的AI工具调用框架
支持多模型、工具调用、SQLite持久化
"""

__version__ = "1.0.0"
__author__ = "AI Chat Tools"

from .core import ChatBot
from .tool_manager import register_tool, ToolRegistry
from .models import ModelAdapter

# 导入工具定义以确保工具被注册
from . import tools

# 安全导入用户自定义工具
try:
    from . import user_tools
except ImportError:
    # 如果 user_tools 不存在或有导入错误，忽略
    pass

__all__ = ["ChatBot", "register_tool", "ToolRegistry", "ModelAdapter"] 