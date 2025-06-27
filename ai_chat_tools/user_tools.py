"""
用户自定义工具文件
适合添加简单的、单个的自定义工具
对于复杂的工具集合，建议使用工具模块系统（user_tool_modules/）
"""
from .tool_manager import register_tool

# ==================== 用户自定义工具示例 ====================
# 取消注释并修改以下示例来添加你的简单工具
# 对于复杂的工具集合，建议在 user_tool_modules/ 目录下创建工具模块

# @register_tool(
#     name="text_length",
#     description="计算文本长度",
#     schema={
#         "type": "object",
#         "properties": {
#             "text": {
#                 "type": "string",
#                 "description": "要计算长度的文本"
#             }
#         },
#         "required": ["text"]
#     }
# )
# def text_length(text: str) -> str:
#     """计算文本长度"""
#     return f"文本长度: {len(text)} 个字符"

# @register_tool(
#     name="reverse_text",
#     description="反转文本",
#     schema={
#         "type": "object",
#         "properties": {
#             "text": {
#                 "type": "string",
#                 "description": "要反转的文本"
#             }
#         },
#         "required": ["text"]
#     }
# )
# def reverse_text(text: str) -> str:
#     """反转文本"""
#     return f"反转后的文本: {text[::-1]}"

# @register_tool(
#     name="word_count",
#     description="统计单词数量",
#     schema={
#         "type": "object",
#         "properties": {
#             "text": {
#                 "type": "string",
#                 "description": "要统计的文本"
#             }
#         },
#         "required": ["text"]
#     }
# )
# def word_count(text: str) -> str:
#     """统计单词数量"""
#     words = text.split()
#     return f"单词数量: {len(words)} 个"

# ==================== 添加你的简单工具 ====================
# 在这里添加你的简单自定义工具
# 
# 💡 提示：
# - 这里适合添加简单的、单个的工具
# - 如果你有多个相关的工具，建议创建工具模块：
#   1. 在 ai_chat_tools/user_tool_modules/ 目录下创建 .py 文件
#   2. 添加模块信息注释（# MODULE_DESCRIPTION: 等）
#   3. 定义相关的工具函数
# 
# 工具模块的优势：
# - 按需加载，减少资源占用
# - 模块化管理，便于维护
# - 支持模块特定的配置
# - 更好的组织结构

# 示例：简单的问候工具
# @register_tool(
#     name="greet",
#     description="问候工具",
#     schema={
#         "type": "object",
#         "properties": {
#             "name": {
#                 "type": "string",
#                 "description": "要问候的人的名字"
#             }
#         },
#         "required": ["name"]
#     }
# )
# def greet(name: str) -> str:
#     """问候工具"""
#     return f"你好，{name}！很高兴见到你！"

# ==================== 异步工具示例 ====================

# import asyncio
# import httpx

# @register_tool(
#     name="async_http_get",
#     description="异步HTTP GET请求",
#     schema={
#         "type": "object",
#         "properties": {
#             "url": {
#                 "type": "string",
#                 "description": "请求URL"
#             }
#         },
#         "required": ["url"]
#     }
# )
# async def async_http_get(url: str) -> str:
#     """异步HTTP GET请求"""
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(url)
#             return f"状态码: {response.status_code}, 内容长度: {len(response.text)}"
#     except Exception as e:
#         return f"请求失败: {str(e)}"

# ==================== 添加你的工具 ====================
# 在这里添加你的自定义工具... 