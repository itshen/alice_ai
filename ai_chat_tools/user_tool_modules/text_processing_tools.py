# MODULE_DESCRIPTION: 文本处理工具集合，提供文本转换、编码解码、加密解密、分析等功能
# MODULE_CATEGORY: text_processing
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 1.0.0

"""
文本处理工具模块
提供文本转换、编码解码、加密解密、格式化、分析等功能
"""

import os
import re
import json
import csv
import xml.dom.minidom
import hashlib
import base64
import random
import string
import time
import html
import urllib.parse
from typing import Union, List, Dict, Any
from io import StringIO

# 使用绝对导入避免相对导入问题
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# 临时文件目录配置
TEMP_DIR = os.path.join(os.getcwd(), 'tmp', 'text_processing')
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.join(TEMP_DIR, 'formatted'), exist_ok=True)
os.makedirs(os.path.join(TEMP_DIR, 'encoded'), exist_ok=True)
os.makedirs(os.path.join(TEMP_DIR, 'analysis'), exist_ok=True)
os.makedirs(os.path.join(TEMP_DIR, 'generated'), exist_ok=True)

def check_file_manager_available():
    """检查文件管理模块是否可用"""
    try:
        # 尝试导入文件管理工具
        from ai_chat_tools.user_tool_modules.file_manager_tools import read_file
        return True
    except ImportError:
        return False

def get_content_preview(content: str, max_lines: int = 10, max_chars: int = 200) -> str:
    """获取内容预览，控制长度避免过长"""
    lines = content.split('\n')
    
    if len(lines) <= max_lines and len(content) <= max_chars:
        return content
    
    # 截取前几行
    preview_lines = lines[:max_lines]
    preview = '\n'.join(preview_lines)
    
    # 如果还是太长，按字符截取
    if len(preview) > max_chars:
        preview = preview[:max_chars] + "..."
    elif len(lines) > max_lines:
        preview += f"\n... (还有 {len(lines) - max_lines} 行)"
    
    return preview

def format_file_result(file_path: str, content_preview: str, operation_name: str) -> str:
    """格式化文件保存结果的返回值"""
    # 获取文件信息
    file_size = os.path.getsize(file_path)
    file_size_str = f"{file_size:,} 字节" if file_size < 1024 else f"{file_size/1024:.1f} KB"
    
    # 检查文件管理模块是否可用
    file_manager_available = check_file_manager_available()
    
    result = f"[成功] {operation_name}完成\n"
    result += f"文件路径: {file_path}\n"
    result += f"文件大小: {file_size_str}\n\n"
    result += f"内容预览:\n{content_preview}\n\n"
    
    if file_manager_available:
        result += f"使用以下命令读取完整内容:\n"
        result += f"read_file(file_path='{file_path}')"
    else:
        result += f"[警告] 文件管理模块未加载，无法直接读取文件\n\n"
        result += f"请按以下步骤操作:\n"
        result += f"1. 加载文件管理模块: load_tool_module('file_manager_tools')\n"
        result += f"2. 读取文件内容: read_file(file_path='{file_path}')"
    
    return result

def generate_temp_filename(prefix: str, extension: str) -> str:
    """生成临时文件名"""
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{timestamp}_{random_str}.{extension}"

def clean_old_temp_files(max_age_hours: int = 24):
    """清理过期的临时文件"""
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < current_time - max_age_seconds:
                    os.remove(file_path)
    except Exception:
        pass  # 静默处理清理错误 

# ==================== 基础文本操作 ====================

@register_tool(
    name="to_uppercase",
    description="将文本转换为大写",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要转换的文本"
            }
        },
        "required": ["text"]
    }
)
def to_uppercase(text: str) -> str:
    """将文本转换为大写"""
    try:
        result = text.upper()
        return f"[成功] 文本已转换为大写:\n{result}"
    except Exception as e:
        return f"[错误] 转换失败: {str(e)}"

@register_tool(
    name="to_lowercase",
    description="将文本转换为小写",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要转换的文本"
            }
        },
        "required": ["text"]
    }
)
def to_lowercase(text: str) -> str:
    """将文本转换为小写"""
    try:
        result = text.lower()
        return f"[成功] 文本已转换为小写:\n{result}"
    except Exception as e:
        return f"[错误] 转换失败: {str(e)}"

@register_tool(
    name="to_title_case",
    description="将文本转换为标题格式",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要转换的文本"
            }
        },
        "required": ["text"]
    }
)
def to_title_case(text: str) -> str:
    """将文本转换为标题格式"""
    try:
        result = text.title()
        return f"[成功] 文本已转换为标题格式:\n{result}"
    except Exception as e:
        return f"[错误] 转换失败: {str(e)}"

@register_tool(
    name="reverse_text",
    description="反转文本",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要反转的文本"
            }
        },
        "required": ["text"]
    }
)
def reverse_text(text: str) -> str:
    """反转文本"""
    try:
        result = text[::-1]
        return f"[成功] 文本已反转:\n{result}"
    except Exception as e:
        return f"[错误] 反转失败: {str(e)}"

@register_tool(
    name="remove_whitespace",
    description="移除多余空白字符",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要处理的文本"
            },
            "mode": {
                "type": "string",
                "description": "处理模式: 'all'(移除所有空白), 'leading'(移除开头), 'trailing'(移除结尾), 'extra'(移除多余空白)",
                "enum": ["all", "leading", "trailing", "extra"],
                "default": "extra"
            }
        },
        "required": ["text"]
    }
)
def remove_whitespace(text: str, mode: str = "extra") -> str:
    """移除多余空白字符"""
    try:
        if mode == "all":
            result = re.sub(r'\s+', '', text)
        elif mode == "leading":
            result = text.lstrip()
        elif mode == "trailing":
            result = text.rstrip()
        elif mode == "extra":
            result = re.sub(r'\s+', ' ', text).strip()
        else:
            return f"[错误] 无效的处理模式: {mode}"
        
        return f"[成功] 空白字符已处理 (模式: {mode}):\n{result}"
    except Exception as e:
        return f"[错误] 处理失败: {str(e)}"

@register_tool(
    name="extract_numbers",
    description="从文本中提取数字",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要处理的文本"
            },
            "include_decimals": {
                "type": "boolean",
                "description": "是否包含小数，默认为 True",
                "default": True
            }
        },
        "required": ["text"]
    }
)
def extract_numbers(text: str, include_decimals: bool = True) -> str:
    """从文本中提取数字"""
    try:
        if include_decimals:
            pattern = r'-?\d+\.?\d*'
        else:
            pattern = r'-?\d+'
        
        numbers = re.findall(pattern, text)
        numbers = [num for num in numbers if num and num != '.']
        
        if not numbers:
            return f"[结果] 未找到数字"
        
        result = f"[成功] 找到 {len(numbers)} 个数字:\n"
        result += ", ".join(numbers)
        return result
    except Exception as e:
        return f"[错误] 提取失败: {str(e)}"

@register_tool(
    name="extract_letters",
    description="从文本中提取字母",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要处理的文本"
            },
            "preserve_case": {
                "type": "boolean",
                "description": "是否保持大小写，默认为 True",
                "default": True
            }
        },
        "required": ["text"]
    }
)
def extract_letters(text: str, preserve_case: bool = True) -> str:
    """从文本中提取字母"""
    try:
        letters = re.findall(r'[a-zA-Z]', text)
        
        if not preserve_case:
            letters = [letter.lower() for letter in letters]
        
        if not letters:
            return f"[结果] 未找到字母"
        
        result = f"[成功] 找到 {len(letters)} 个字母:\n"
        result += "".join(letters)
        return result
    except Exception as e:
        return f"[错误] 提取失败: {str(e)}"

# ==================== 编码解码工具 ====================

@register_tool(
    name="base64_encode",
    description="Base64编码",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要编码的文本"
            }
        },
        "required": ["text"]
    }
)
def base64_encode(text: str) -> str:
    """Base64编码"""
    try:
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        return f"[成功] Base64编码完成:\n{encoded}"
    except Exception as e:
        return f"[错误] 编码失败: {str(e)}"

@register_tool(
    name="base64_decode",
    description="Base64解码",
    schema={
        "type": "object",
        "properties": {
            "encoded_text": {
                "type": "string",
                "description": "要解码的Base64文本"
            }
        },
        "required": ["encoded_text"]
    }
)
def base64_decode(encoded_text: str) -> str:
    """Base64解码"""
    try:
        decoded = base64.b64decode(encoded_text.encode('utf-8')).decode('utf-8')
        return f"[成功] Base64解码完成:\n{decoded}"
    except Exception as e:
        return f"[错误] 解码失败: {str(e)}"

@register_tool(
    name="url_encode",
    description="URL编码",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要编码的文本"
            }
        },
        "required": ["text"]
    }
)
def url_encode(text: str) -> str:
    """URL编码"""
    try:
        encoded = urllib.parse.quote(text, safe='')
        return f"[成功] URL编码完成:\n{encoded}"
    except Exception as e:
        return f"[错误] 编码失败: {str(e)}"

@register_tool(
    name="url_decode",
    description="URL解码",
    schema={
        "type": "object",
        "properties": {
            "encoded_text": {
                "type": "string",
                "description": "要解码的URL编码文本"
            }
        },
        "required": ["encoded_text"]
    }
)
def url_decode(encoded_text: str) -> str:
    """URL解码"""
    try:
        decoded = urllib.parse.unquote(encoded_text)
        return f"[成功] URL解码完成:\n{decoded}"
    except Exception as e:
        return f"[错误] 解码失败: {str(e)}"

@register_tool(
    name="html_encode",
    description="HTML实体编码",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要编码的文本"
            }
        },
        "required": ["text"]
    }
)
def html_encode(text: str) -> str:
    """HTML实体编码"""
    try:
        clean_old_temp_files()
        encoded = html.escape(text)
        
        # 如果内容较长，保存到文件
        if len(encoded) > 2000:
            filename = generate_temp_filename("html_encoded", "html")
            file_path = os.path.join(TEMP_DIR, 'encoded', filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(encoded)
            
            preview = get_content_preview(encoded)
            return format_file_result(file_path, preview, "HTML编码")
        else:
            return f"[成功] HTML编码完成:\n{encoded}"
    except Exception as e:
        return f"[错误] 编码失败: {str(e)}"

@register_tool(
    name="html_decode",
    description="HTML实体解码",
    schema={
        "type": "object",
        "properties": {
            "encoded_text": {
                "type": "string",
                "description": "要解码的HTML实体文本"
            }
        },
        "required": ["encoded_text"]
    }
)
def html_decode(encoded_text: str) -> str:
    """HTML实体解码"""
    try:
        clean_old_temp_files()
        decoded = html.unescape(encoded_text)
        
        # 如果内容较长，保存到文件
        if len(decoded) > 2000:
            filename = generate_temp_filename("html_decoded", "html")
            file_path = os.path.join(TEMP_DIR, 'encoded', filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(decoded)
            
            preview = get_content_preview(decoded)
            return format_file_result(file_path, preview, "HTML解码")
        else:
            return f"[成功] HTML解码完成:\n{decoded}"
    except Exception as e:
        return f"[错误] 解码失败: {str(e)}"

# ==================== 加密解密工具 ====================

@register_tool(
    name="generate_hash",
    description="生成文本的哈希值",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要生成哈希的文本"
            },
            "algorithm": {
                "type": "string",
                "description": "哈希算法",
                "enum": ["md5", "sha1", "sha256", "sha512"],
                "default": "md5"
            }
        },
        "required": ["text"]
    }
)
def generate_hash(text: str, algorithm: str = "md5") -> str:
    """生成文本的哈希值"""
    try:
        text_bytes = text.encode('utf-8')
        
        if algorithm == "md5":
            hash_obj = hashlib.md5(text_bytes)
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1(text_bytes)
        elif algorithm == "sha256":
            hash_obj = hashlib.sha256(text_bytes)
        elif algorithm == "sha512":
            hash_obj = hashlib.sha512(text_bytes)
        else:
            return f"[错误] 不支持的哈希算法: {algorithm}"
        
        hash_value = hash_obj.hexdigest()
        return f"[成功] {algorithm.upper()}哈希值:\n{hash_value}"
    except Exception as e:
        return f"[错误] 生成哈希失败: {str(e)}"

@register_tool(
    name="caesar_cipher",
    description="凯撒密码加密/解密",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要处理的文本"
            },
            "shift": {
                "type": "integer",
                "description": "位移量，正数为加密，负数为解密",
                "default": 3
            },
            "mode": {
                "type": "string",
                "description": "处理模式",
                "enum": ["letters", "digits", "all"],
                "default": "letters"
            }
        },
        "required": ["text"]
    }
)
def caesar_cipher(text: str, shift: int = 3, mode: str = "letters") -> str:
    """凯撒密码加密/解密"""
    try:
        result = []
        
        for char in text:
            if mode == "letters" and char.isalpha():
                # 处理字母
                base = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - base + shift) % 26 + base
                result.append(chr(shifted))
            elif mode == "digits" and char.isdigit():
                # 处理数字
                shifted = (int(char) + shift) % 10
                result.append(str(shifted))
            elif mode == "all":
                if char.isalpha():
                    base = ord('A') if char.isupper() else ord('a')
                    shifted = (ord(char) - base + shift) % 26 + base
                    result.append(chr(shifted))
                elif char.isdigit():
                    shifted = (int(char) + shift) % 10
                    result.append(str(shifted))
                else:
                    result.append(char)
            else:
                result.append(char)
        
        processed_text = ''.join(result)
        action = "加密" if shift > 0 else "解密"
        return f"[成功] 凯撒密码{action}完成 (位移: {shift}, 模式: {mode}):\n{processed_text}"
    except Exception as e:
        return f"[错误] 处理失败: {str(e)}"

@register_tool(
    name="simple_xor_encrypt",
    description="简单XOR加密/解密",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要处理的文本"
            },
            "key": {
                "type": "string",
                "description": "加密密钥",
                "default": "key"
            }
        },
        "required": ["text"]
    }
)
def simple_xor_encrypt(text: str, key: str = "key") -> str:
    """简单XOR加密/解密"""
    try:
        if not key:
            return f"[错误] 密钥不能为空"
        
        result = []
        key_len = len(key)
        
        for i, char in enumerate(text):
            key_char = key[i % key_len]
            encrypted_char = chr(ord(char) ^ ord(key_char))
            result.append(encrypted_char)
        
        processed_text = ''.join(result)
        # 转换为十六进制显示，避免不可打印字符
        hex_result = processed_text.encode('utf-8').hex()
        
        return f"[成功] XOR加密/解密完成 (密钥: {key}):\n十六进制结果: {hex_result}\n原始结果: {repr(processed_text)}"
    except Exception as e:
        return f"[错误] 处理失败: {str(e)}"

@register_tool(
    name="generate_uuid",
    description="生成UUID或随机ID",
    schema={
        "type": "object",
        "properties": {
            "prefix": {
                "type": "string",
                "description": "ID前缀",
                "default": ""
            },
            "suffix": {
                "type": "string",
                "description": "ID后缀",
                "default": ""
            },
            "length": {
                "type": "integer",
                "description": "随机部分长度",
                "default": 8
            },
            "include_timestamp": {
                "type": "boolean",
                "description": "是否包含时间戳",
                "default": True
            }
        }
    }
)
def generate_uuid(prefix: str = "", suffix: str = "", length: int = 8, include_timestamp: bool = True) -> str:
    """生成UUID或随机ID"""
    try:
        # 生成随机字符串
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        
        # 构建ID
        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(random_str)
        if include_timestamp:
            parts.append(str(int(time.time())))
        if suffix:
            parts.append(suffix)
        
        uuid_str = '_'.join(parts)
        return f"[成功] 生成UUID:\n{uuid_str}"
    except Exception as e:
        return f"[错误] 生成失败: {str(e)}"

# ==================== 格式化工具 ====================

@register_tool(
    name="format_json",
    description="格式化JSON文本",
    schema={
        "type": "object",
        "properties": {
            "json_text": {
                "type": "string",
                "description": "要格式化的JSON文本"
            },
            "indent": {
                "type": "integer",
                "description": "缩进空格数",
                "default": 2
            }
        },
        "required": ["json_text"]
    }
)
def format_json(json_text: str, indent: int = 2) -> str:
    """格式化JSON文本"""
    try:
        clean_old_temp_files()
        
        # 解析JSON
        json_obj = json.loads(json_text)
        
        # 格式化JSON
        formatted_json = json.dumps(json_obj, indent=indent, ensure_ascii=False, sort_keys=True)
        
        # 保存到临时文件
        filename = generate_temp_filename("formatted_json", "json")
        file_path = os.path.join(TEMP_DIR, 'formatted', filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_json)
        
        preview = get_content_preview(formatted_json)
        return format_file_result(file_path, preview, "JSON格式化")
        
    except json.JSONDecodeError as e:
        return f"[错误] JSON格式错误: {str(e)}"
    except Exception as e:
        return f"[错误] 格式化失败: {str(e)}"

@register_tool(
    name="minify_json",
    description="压缩JSON文本",
    schema={
        "type": "object",
        "properties": {
            "json_text": {
                "type": "string",
                "description": "要压缩的JSON文本"
            }
        },
        "required": ["json_text"]
    }
)
def minify_json(json_text: str) -> str:
    """压缩JSON文本"""
    try:
        clean_old_temp_files()
        
        # 解析JSON
        json_obj = json.loads(json_text)
        
        # 压缩JSON
        minified_json = json.dumps(json_obj, separators=(',', ':'), ensure_ascii=False)
        
        # 保存到临时文件
        filename = generate_temp_filename("minified_json", "json")
        file_path = os.path.join(TEMP_DIR, 'formatted', filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(minified_json)
        
        preview = get_content_preview(minified_json)
        return format_file_result(file_path, preview, "JSON压缩")
        
    except json.JSONDecodeError as e:
        return f"[错误] JSON格式错误: {str(e)}"
    except Exception as e:
        return f"[错误] 压缩失败: {str(e)}"

@register_tool(
    name="format_xml",
    description="格式化XML文本",
    schema={
        "type": "object",
        "properties": {
            "xml_text": {
                "type": "string",
                "description": "要格式化的XML文本"
            }
        },
        "required": ["xml_text"]
    }
)
def format_xml(xml_text: str) -> str:
    """格式化XML文本"""
    try:
        clean_old_temp_files()
        
        # 解析并格式化XML
        dom = xml.dom.minidom.parseString(xml_text)
        formatted_xml = dom.toprettyxml(indent="  ", encoding=None)
        
        # 移除空行
        lines = [line for line in formatted_xml.split('\n') if line.strip()]
        formatted_xml = '\n'.join(lines)
        
        # 保存到临时文件
        filename = generate_temp_filename("formatted_xml", "xml")
        file_path = os.path.join(TEMP_DIR, 'formatted', filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)
        
        preview = get_content_preview(formatted_xml)
        return format_file_result(file_path, preview, "XML格式化")
        
    except Exception as e:
        return f"[错误] XML格式化失败: {str(e)}"

@register_tool(
    name="csv_to_json",
    description="将CSV转换为JSON",
    schema={
        "type": "object",
        "properties": {
            "csv_text": {
                "type": "string",
                "description": "要转换的CSV文本"
            },
            "delimiter": {
                "type": "string",
                "description": "CSV分隔符",
                "default": ","
            }
        },
        "required": ["csv_text"]
    }
)
def csv_to_json(csv_text: str, delimiter: str = ",") -> str:
    """将CSV转换为JSON"""
    try:
        clean_old_temp_files()
        
        # 解析CSV
        csv_reader = csv.DictReader(StringIO(csv_text), delimiter=delimiter)
        data = list(csv_reader)
        
        # 转换为JSON
        json_result = json.dumps(data, indent=2, ensure_ascii=False)
        
        # 保存到临时文件
        filename = generate_temp_filename("csv_to_json", "json")
        file_path = os.path.join(TEMP_DIR, 'formatted', filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_result)
        
        preview = get_content_preview(json_result)
        return format_file_result(file_path, preview, "CSV转JSON")
        
    except Exception as e:
        return f"[错误] CSV转JSON失败: {str(e)}"

@register_tool(
    name="json_to_csv",
    description="将JSON转换为CSV",
    schema={
        "type": "object",
        "properties": {
            "json_text": {
                "type": "string",
                "description": "要转换的JSON文本（必须是对象数组）"
            },
            "delimiter": {
                "type": "string",
                "description": "CSV分隔符",
                "default": ","
            }
        },
        "required": ["json_text"]
    }
)
def json_to_csv(json_text: str, delimiter: str = ",") -> str:
    """将JSON转换为CSV"""
    try:
        clean_old_temp_files()
        
        # 解析JSON
        json_data = json.loads(json_text)
        
        if not isinstance(json_data, list):
            return f"[错误] JSON必须是对象数组格式"
        
        if not json_data:
            return f"[错误] JSON数组为空"
        
        # 获取所有字段名
        fieldnames = set()
        for item in json_data:
            if isinstance(item, dict):
                fieldnames.update(item.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        # 转换为CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(json_data)
        
        csv_result = output.getvalue()
        
        # 保存到临时文件
        filename = generate_temp_filename("json_to_csv", "csv")
        file_path = os.path.join(TEMP_DIR, 'formatted', filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_result)
        
        preview = get_content_preview(csv_result)
        return format_file_result(file_path, preview, "JSON转CSV")
        
    except json.JSONDecodeError as e:
        return f"[错误] JSON格式错误: {str(e)}"
    except Exception as e:
        return f"[错误] JSON转CSV失败: {str(e)}"

# ==================== 文本分析工具 ====================

@register_tool(
    name="count_words",
    description="统计文本中的单词数",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要统计的文本"
            }
        },
        "required": ["text"]
    }
)
def count_words(text: str) -> str:
    """统计文本中的单词数"""
    try:
        # 统计字符数
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        
        # 统计单词数（按空白字符分割）
        words = text.split()
        word_count = len(words)
        
        # 统计行数
        line_count = len(text.split('\n'))
        
        # 统计段落数（按空行分割）
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        result = f"[成功] 文本统计结果:\n"
        result += f"字符数: {char_count:,}\n"
        result += f"字符数(不含空格): {char_count_no_spaces:,}\n"
        result += f"单词数: {word_count:,}\n"
        result += f"行数: {line_count:,}\n"
        result += f"段落数: {paragraph_count:,}"
        
        return result
    except Exception as e:
        return f"[错误] 统计失败: {str(e)}"

@register_tool(
    name="find_all_matches",
    description="查找所有正则表达式匹配项",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要搜索的文本"
            },
            "pattern": {
                "type": "string",
                "description": "正则表达式模式"
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "是否区分大小写",
                "default": False
            }
        },
        "required": ["text", "pattern"]
    }
)
def find_all_matches(text: str, pattern: str, case_sensitive: bool = False) -> str:
    """查找所有正则表达式匹配项"""
    try:
        clean_old_temp_files()
        
        # 编译正则表达式
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        # 查找所有匹配项
        matches = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                matches.append({
                    "line": line_num,
                    "column": match.start() + 1,
                    "text": match.group(),
                    "line_content": line.strip()
                })
        
        if not matches:
            return f"[结果] 未找到匹配项: {pattern}"
        
        # 如果匹配项太多，保存到文件
        if len(matches) > 50:
            result_text = f"正则表达式匹配结果 (模式: {pattern})\n"
            result_text += f"区分大小写: {'是' if case_sensitive else '否'}\n"
            result_text += f"总匹配数: {len(matches)}\n\n"
            
            for i, match in enumerate(matches, 1):
                result_text += f"匹配 {i}:\n"
                result_text += f"  位置: 第 {match['line']} 行，第 {match['column']} 列\n"
                result_text += f"  内容: {match['text']}\n"
                result_text += f"  上下文: {match['line_content']}\n\n"
            
            filename = generate_temp_filename("regex_matches", "txt")
            file_path = os.path.join(TEMP_DIR, 'analysis', filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result_text)
            
            preview = get_content_preview(result_text)
            return format_file_result(file_path, preview, "正则表达式匹配")
        else:
            # 直接返回结果
            result = f"[成功] 找到 {len(matches)} 个匹配项 (模式: {pattern}):\n\n"
            for i, match in enumerate(matches, 1):
                result += f"匹配 {i}: 第 {match['line']} 行，第 {match['column']} 列\n"
                result += f"  内容: {match['text']}\n"
                result += f"  上下文: {match['line_content']}\n\n"
            return result
        
    except re.error as e:
        return f"[错误] 正则表达式错误: {str(e)}"
    except Exception as e:
        return f"[错误] 搜索失败: {str(e)}"

@register_tool(
    name="extract_emails",
    description="从文本中提取邮箱地址",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要处理的文本"
            }
        },
        "required": ["text"]
    }
)
def extract_emails(text: str) -> str:
    """从文本中提取邮箱地址"""
    try:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # 去重并排序
        unique_emails = sorted(list(set(emails)))
        
        if not unique_emails:
            return f"[结果] 未找到邮箱地址"
        
        result = f"[成功] 找到 {len(unique_emails)} 个邮箱地址:\n"
        for email in unique_emails:
            result += f"  {email}\n"
        
        return result
    except Exception as e:
        return f"[错误] 提取失败: {str(e)}"

@register_tool(
    name="extract_urls",
    description="从文本中提取URL链接",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要处理的文本"
            }
        },
        "required": ["text"]
    }
)
def extract_urls(text: str) -> str:
    """从文本中提取URL链接"""
    try:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        # 去重并排序
        unique_urls = sorted(list(set(urls)))
        
        if not unique_urls:
            return f"[结果] 未找到URL链接"
        
        result = f"[成功] 找到 {len(unique_urls)} 个URL链接:\n"
        for url in unique_urls:
            result += f"  {url}\n"
        
        return result
    except Exception as e:
        return f"[错误] 提取失败: {str(e)}"

@register_tool(
    name="generate_random_text",
    description="生成随机文本",
    schema={
        "type": "object",
        "properties": {
            "length": {
                "type": "integer",
                "description": "文本长度",
                "default": 100
            },
            "type": {
                "type": "string",
                "description": "文本类型",
                "enum": ["letters", "digits", "mixed", "words"],
                "default": "mixed"
            }
        }
    }
)
def generate_random_text(length: int = 100, type: str = "mixed") -> str:
    """生成随机文本"""
    try:
        if type == "letters":
            chars = string.ascii_letters
        elif type == "digits":
            chars = string.digits
        elif type == "mixed":
            chars = string.ascii_letters + string.digits
        elif type == "words":
            # 生成随机单词
            word_list = ['apple', 'banana', 'cherry', 'dog', 'elephant', 'forest', 'garden', 'house', 'island', 'jungle']
            words = random.choices(word_list, k=length // 6)  # 平均单词长度约6字符
            result_text = ' '.join(words)
            return f"[成功] 生成随机单词文本 ({len(result_text)} 字符):\n{result_text}"
        else:
            return f"[错误] 不支持的文本类型: {type}"
        
        result_text = ''.join(random.choices(chars, k=length))
        return f"[成功] 生成随机文本 ({length} 字符):\n{result_text}"
    except Exception as e:
        return f"[错误] 生成失败: {str(e)}"

@register_tool(
    name="generate_password",
    description="生成安全密码",
    schema={
        "type": "object",
        "properties": {
            "length": {
                "type": "integer",
                "description": "密码长度",
                "default": 12
            },
            "include_uppercase": {
                "type": "boolean",
                "description": "包含大写字母",
                "default": True
            },
            "include_lowercase": {
                "type": "boolean",
                "description": "包含小写字母",
                "default": True
            },
            "include_digits": {
                "type": "boolean",
                "description": "包含数字",
                "default": True
            },
            "include_symbols": {
                "type": "boolean",
                "description": "包含特殊符号",
                "default": True
            }
        }
    }
)
def generate_password(length: int = 12, include_uppercase: bool = True, 
                     include_lowercase: bool = True, include_digits: bool = True, 
                     include_symbols: bool = True) -> str:
    """生成安全密码"""
    try:
        chars = ""
        
        if include_uppercase:
            chars += string.ascii_uppercase
        if include_lowercase:
            chars += string.ascii_lowercase
        if include_digits:
            chars += string.digits
        if include_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if not chars:
            return f"[错误] 至少需要选择一种字符类型"
        
        password = ''.join(random.choices(chars, k=length))
        
        # 密码强度评估
        strength = 0
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            strength += 1
        
        strength_levels = ["很弱", "弱", "中等", "强", "很强"]
        strength_desc = strength_levels[min(strength, 4)]
        
        return f"[成功] 生成密码 (长度: {length}, 强度: {strength_desc}):\n{password}"
    except Exception as e:
        return f"[错误] 生成失败: {str(e)}"

# ==================== 实用工具 ====================

@register_tool(
    name="clean_temp_files_manual",
    description="手动清理临时文件",
    schema={
        "type": "object",
        "properties": {
            "max_age_hours": {
                "type": "integer",
                "description": "文件最大保留时间（小时）",
                "default": 24
            }
        }
    }
)
def clean_temp_files_manual(max_age_hours: int = 24) -> str:
    """手动清理临时文件"""
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < current_time - max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
        
        return f"[成功] 清理完成，删除了 {deleted_count} 个过期文件"
    except Exception as e:
        return f"[错误] 清理失败: {str(e)}" 