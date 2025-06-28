# MODULE_DESCRIPTION: 文件管理工具集合，提供文件读写、搜索、管理等功能
# MODULE_CATEGORY: file_management
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 0.0.1

"""
文件管理工具模块
提供文件读写、搜索替换、列表管理等功能
"""

import os
import re
from typing import List

# 使用绝对导入避免相对导入问题
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

@register_tool(
    name="read_file",
    description="读取文件内容",
    schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要读取的文件路径"
            },
            "encoding": {
                "type": "string",
                "description": "文件编码，默认为 utf-8",
                "default": "utf-8"
            }
        },
        "required": ["file_path"]
    }
)
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """读取文件内容"""
    try:
        # 获取模块配置
        module_config = config.get_tool_module_config("file_manager")
        max_size = module_config.get("max_file_size", 1048576)  # 默认1MB
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"❌ 文件不存在: {file_path}"
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return f"❌ 文件太大 ({file_size} 字节)，超过限制 ({max_size} 字节)"
        
        # 读取文件
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return f"✅ 成功读取文件 {file_path} ({len(content)} 字符):\n\n{content}"
        
    except UnicodeDecodeError:
        return f"❌ 文件编码错误，请尝试其他编码格式"
    except Exception as e:
        return f"❌ 读取文件失败: {str(e)}"

@register_tool(
    name="write_file",
    description="写入内容到文件",
    schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要写入的文件路径"
            },
            "content": {
                "type": "string",
                "description": "要写入的内容"
            },
            "encoding": {
                "type": "string",
                "description": "文件编码，默认为 utf-8",
                "default": "utf-8"
            },
            "append": {
                "type": "boolean",
                "description": "是否追加模式，默认为覆盖",
                "default": False
            }
        },
        "required": ["file_path", "content"]
    },
    requires_confirmation=True,
    confirmation_category="file_write",
    risk_level="medium"
)
def write_file(file_path: str, content: str, encoding: str = "utf-8", append: bool = False) -> str:
    """写入内容到文件"""
    try:
        # 获取模块配置
        module_config = config.get_tool_module_config("file_manager")
        allowed_extensions = module_config.get("allowed_extensions", [])
        
        # 检查文件扩展名
        if allowed_extensions:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                return f"❌ 不允许的文件扩展名: {file_ext}，允许的扩展名: {allowed_extensions}"
        
        # 创建目录（如果不存在）
        dir_path = os.path.dirname(file_path)
        if dir_path:  # 只有当目录路径不为空时才创建
            os.makedirs(dir_path, exist_ok=True)
        
        # 写入文件
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        
        action = "追加到" if append else "写入到"
        return f"✅ 成功{action}文件 {file_path} ({len(content)} 字符)"
        
    except Exception as e:
        return f"❌ 写入文件失败: {str(e)}"

@register_tool(
    name="search_in_file",
    description="在文件中搜索文本",
    schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要搜索的文件路径"
            },
            "pattern": {
                "type": "string",
                "description": "搜索模式（支持正则表达式）"
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "是否区分大小写，默认为 False",
                "default": False
            }
        },
        "required": ["file_path", "pattern"]
    }
)
def search_in_file(file_path: str, pattern: str, case_sensitive: bool = False) -> str:
    """在文件中搜索文本"""
    try:
        # 先读取文件
        if not os.path.exists(file_path):
            return f"❌ 文件不存在: {file_path}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 编译正则表达式
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        # 搜索匹配项
        matches = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                matches.append({
                    "line": line_num,
                    "column": match.start() + 1,
                    "text": match.group(),
                    "line_content": line.strip()
                })
        
        if not matches:
            return f"❌ 在文件 {file_path} 中未找到匹配项: {pattern}"
        
        result = f"✅ 在文件 {file_path} 中找到 {len(matches)} 个匹配项:\n\n"
        for match in matches[:10]:  # 限制显示前10个匹配项
            result += f"第 {match['line']} 行，第 {match['column']} 列: {match['text']}\n"
            result += f"  上下文: {match['line_content']}\n\n"
        
        if len(matches) > 10:
            result += f"... 还有 {len(matches) - 10} 个匹配项"
        
        return result
        
    except re.error as e:
        return f"❌ 正则表达式错误: {str(e)}"
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"

@register_tool(
    name="replace_in_file",
    description="在文件中替换文本",
    schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要处理的文件路径"
            },
            "search_pattern": {
                "type": "string",
                "description": "要搜索的模式（支持正则表达式）"
            },
            "replacement": {
                "type": "string",
                "description": "替换文本"
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "是否区分大小写，默认为 False",
                "default": False
            },
            "backup": {
                "type": "boolean",
                "description": "是否创建备份文件，默认为 True",
                "default": True
            }
        },
        "required": ["file_path", "search_pattern", "replacement"]
    },
    requires_confirmation=True,
    confirmation_category="file_modify",
    risk_level="high"
)
def replace_in_file(file_path: str, search_pattern: str, replacement: str, 
                   case_sensitive: bool = False, backup: bool = True) -> str:
    """在文件中替换文本"""
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return f"❌ 文件不存在: {file_path}"
        
        # 读取原文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 创建备份
        if backup:
            backup_path = file_path + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        
        # 执行替换
        flags = 0 if case_sensitive else re.IGNORECASE
        new_content, count = re.subn(search_pattern, replacement, original_content, flags=flags)
        
        if count == 0:
            return f"❌ 在文件 {file_path} 中未找到匹配项: {search_pattern}"
        
        # 写入新内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        backup_info = f"（已创建备份: {backup_path}）" if backup else ""
        return f"✅ 成功在文件 {file_path} 中替换了 {count} 处匹配项 {backup_info}"
        
    except re.error as e:
        return f"❌ 正则表达式错误: {str(e)}"
    except Exception as e:
        return f"❌ 替换失败: {str(e)}"

@register_tool(
    name="list_files",
    description="列出目录中的文件",
    schema={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "要列出的目录路径，默认为当前目录",
                "default": "."
            },
            "pattern": {
                "type": "string",
                "description": "文件名匹配模式（支持通配符），如 '*.py'",
                "default": "*"
            },
            "recursive": {
                "type": "boolean",
                "description": "是否递归搜索子目录，默认为 False",
                "default": False
            }
        }
    }
)
def list_files(directory: str = ".", pattern: str = "*", recursive: bool = False) -> str:
    """列出目录中的文件"""
    try:
        import glob
        
        if not os.path.exists(directory):
            return f"❌ 目录不存在: {directory}"
        
        if not os.path.isdir(directory):
            return f"❌ 路径不是目录: {directory}"
        
        # 构建搜索模式
        if recursive:
            search_pattern = os.path.join(directory, "**", pattern)
            files = glob.glob(search_pattern, recursive=True)
        else:
            search_pattern = os.path.join(directory, pattern)
            files = glob.glob(search_pattern)
        
        # 过滤出文件（排除目录）
        files = [f for f in files if os.path.isfile(f)]
        files.sort()
        
        if not files:
            return f"❌ 在目录 {directory} 中未找到匹配 '{pattern}' 的文件"
        
        result = f"✅ 在目录 {directory} 中找到 {len(files)} 个文件:\n\n"
        for file_path in files:
            file_size = os.path.getsize(file_path)
            file_size_str = f"{file_size:,} 字节" if file_size < 1024 else f"{file_size/1024:.1f} KB"
            result += f"📄 {file_path} ({file_size_str})\n"
        
        return result
        
    except Exception as e:
        return f"❌ 列出文件失败: {str(e)}" 