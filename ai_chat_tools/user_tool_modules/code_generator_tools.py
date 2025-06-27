# MODULE_DESCRIPTION: 代码生成和管理工具集合，帮助AI自主生成、读取和修改代码文件
# MODULE_CATEGORY: code_generation
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 1.0.0

"""
代码生成工具模块
专门用于AI生成和管理user_tool_modules目录中的代码文件
"""

import os
import re
import ast
import importlib.util
import sys
import signal
import subprocess
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# ==================== 自动重启工具 ====================

@register_tool(
    name="restart_application",
    description="重启应用程序加载新代码。参数：delay_seconds(延迟秒数默认3), preserve_session(保持会话默认True)。使用示例：restart_application(delay_seconds=3, preserve_session=True)。AI在使用write_code_file或replace_function_in_file后必须立即调用此工具，否则新代码不会生效。重启会保持当前会话，新工具自动注册。",
    schema={
        "type": "object",
        "properties": {
            "delay_seconds": {
                "type": "integer",
                "default": 3,
                "description": "重启前的延迟时间（秒）"
            },
            "preserve_session": {
                "type": "boolean",
                "default": True,
                "description": "是否保持当前会话状态"
            }
        }
    },
    requires_confirmation=True,
    confirmation_category="system_command",
    risk_level="medium"
)
def restart_application(delay_seconds: int = 3, preserve_session: bool = True) -> str:
    """重启应用程序以加载新代码"""
    try:
        import time
        import threading
        
        def delayed_restart():
            """延迟重启函数"""
            time.sleep(delay_seconds)
            
            # 获取当前Python解释器和脚本路径
            python_executable = sys.executable
            script_path = sys.argv[0]
            
            # 构建重启命令
            restart_cmd = [python_executable, script_path] + sys.argv[1:]
            
            # 如果是在API模式下运行，保持API模式
            if '--api' not in sys.argv:
                # 检查是否在API模式下运行
                try:
                    import inspect
                    for frame_info in inspect.stack():
                        if 'api.py' in frame_info.filename:
                            restart_cmd.append('--api')
                            break
                except:
                    pass
            
            try:
                # 启动新进程
                subprocess.Popen(restart_cmd, cwd=os.getcwd())
                
                # 终止当前进程
                os._exit(0)
                
            except Exception as e:
                print(f"❌ 重启失败: {e}")
                os._exit(1)
        
        # 在后台线程中执行重启
        restart_thread = threading.Thread(target=delayed_restart, daemon=True)
        restart_thread.start()
        
        session_info = ""
        if preserve_session:
            session_info = "\n💾 会话状态将被保持"
        
        return f"🔄 应用程序将在 {delay_seconds} 秒后重启{session_info}\n✨ 新生成的代码将被自动加载"
        
    except Exception as e:
        return f"❌ 重启失败: {str(e)}"



# ==================== 文件操作工具 ====================

# 模块模板 - 用于write_code_file工具
def get_module_template(module_name: str, description: str, doc_string: str, 
                       category: str = "custom", author: str = "AI Assistant", 
                       version: str = "1.0.0") -> str:
    """获取标准模块模板"""
    return f'''# MODULE_DESCRIPTION: {description}
# MODULE_CATEGORY: {category}
# MODULE_AUTHOR: {author}
# MODULE_VERSION: {version}

"""
{module_name}
{doc_string}
"""

import os
import sys
from typing import Optional, List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# 在这里添加您的工具函数

'''



@register_tool(
    name="write_code_file",
    description="AI专用：创建或完全重写工具模块文件。参数：file_path(文件名如my_tools.py), code_content(完整Python代码)。使用示例：write_code_file(file_path='sorting_tools.py', code_content='# MODULE_DESCRIPTION: 排序工具\\n# MODULE_CATEGORY: algorithms\\n...')。注意：1)file_path只需文件名，不要路径 2)code_content必须包含完整的模块头部注释 3)必须包含导入语句和@register_tool装饰器 4)生成后立即调用restart_application重启。",
    schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "文件路径，相对于user_tool_modules目录，如：my_tools.py"
            },
            "code_content": {
                "type": "string",
                "description": "完整的Python代码内容，包括模块头部、导入、函数定义等"
            },
            "backup_existing": {
                "type": "boolean",
                "default": True,
                "description": "是否备份现有文件"
            }
        },
        "required": ["file_path", "code_content"]
    },
    requires_confirmation=True,
    confirmation_category="file_write",
    risk_level="high"
)
def write_code_file(file_path: str, code_content: str, backup_existing: bool = True) -> str:
    """直接写入完整的代码文件（AI专用）"""
    try:
        # 构建完整路径
        modules_dir = os.path.join(os.path.dirname(__file__))
        full_path = os.path.join(modules_dir, file_path)
        
        # 确保文件名以.py结尾
        if not file_path.endswith('.py'):
            return "❌ 文件必须是Python文件（.py扩展名）"
        
        # 备份现有文件
        if backup_existing and os.path.exists(full_path):
            backup_path = full_path + f'.bak.{int(datetime.now().timestamp())}'
            with open(full_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
        
        # 验证代码语法
        try:
            ast.parse(code_content)
        except SyntaxError as e:
            return f"❌ 代码语法错误: {str(e)}\n请检查代码语法。"
        
        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        # 统计信息
        lines = len(code_content.split('\n'))
        functions = len(re.findall(r'def \w+\(', code_content))
        
        result = f"✅ 成功写入文件: {file_path}\n"
        result += f"📊 统计: {lines}行代码, {functions}个函数\n"
        if backup_existing and 'backup_path' in locals():
            result += f"💾 备份文件: {os.path.basename(backup_path)}\n"
        result += "🔄 使用 restart_application 工具重启以加载新代码"
        
        return result
        
    except Exception as e:
        return f"❌ 写入文件失败: {str(e)}"

@register_tool(
    name="replace_function_in_file",
    description="AI专用：精确替换模块中的单个工具函数。参数：file_path(文件名), function_name(函数名), new_function_code(完整函数代码含装饰器)。使用示例：replace_function_in_file(file_path='my_tools.py', function_name='my_tool', new_function_code='@register_tool(...)\\ndef my_tool(param: str) -> str:\\n    return \"result\"')。注意：1)new_function_code必须包含@register_tool装饰器 2)必须包含完整函数定义 3)会自动备份原文件 4)替换后调用restart_application重启。",
    schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "文件路径，相对于user_tool_modules目录"
            },
            "function_name": {
                "type": "string",
                "description": "要替换的函数名"
            },
            "new_function_code": {
                "type": "string",
                "description": "新的完整函数代码（包括装饰器、函数定义、函数体）"
            }
        },
        "required": ["file_path", "function_name", "new_function_code"]
    },
    requires_confirmation=True,
    confirmation_category="file_modify",
    risk_level="medium"
)
def replace_function_in_file(file_path: str, function_name: str, new_function_code: str) -> str:
    """替换文件中的特定函数（AI专用）"""
    try:
        # 构建完整路径
        modules_dir = os.path.join(os.path.dirname(__file__))
        full_path = os.path.join(modules_dir, file_path)
        
        if not os.path.exists(full_path):
            return f"❌ 文件不存在: {file_path}"
        
        # 读取文件内容
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建备份
        backup_path = full_path + f'.bak.{int(datetime.now().timestamp())}'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 查找函数定义（包括装饰器）
        pattern = rf'(@register_tool\(.*?\))\s*def {function_name}\([^)]*\) -> str:.*?(?=@register_tool|def \w+|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return f"❌ 未找到函数 {function_name}"
        
        # 获取函数的起始和结束位置
        start_pos = match.start()
        end_pos = match.end()
        
        # 计算行号
        lines_before = content[:start_pos].count('\n')
        lines_in_function = content[start_pos:end_pos].count('\n')
        start_line = lines_before + 1
        end_line = start_line + lines_in_function
        
        # 替换函数
        new_content = content[:start_pos] + new_function_code + content[end_pos:]
        
        # 验证语法
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return f"❌ 替换后代码语法错误: {str(e)}\n备份文件: {os.path.basename(backup_path)}"
        
        # 写入新内容
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"✅ 成功替换函数 {function_name}\n📍 位置: 第{start_line}-{end_line}行\n💾 备份: {os.path.basename(backup_path)}\n🔄 使用 restart_application 工具重启以加载新代码"
        
    except Exception as e:
        return f"❌ 替换函数失败: {str(e)}"

@register_tool(
    name="read_module_structure",
    description="AI专用：查看现有模块的详细结构。参数：module_name(模块名不含.py), show_code(是否显示代码默认False)。使用示例：read_module_structure(module_name='file_manager_tools', show_code=False)。返回：模块头部信息、所有函数列表、函数描述和参数。AI在修改模块前必须先用此工具了解现有结构，避免重复创建函数。",
    schema={
        "type": "object",
        "properties": {
            "module_name": {
                "type": "string",
                "description": "要查看的模块名称（不含.py扩展名），如：sorting_algorithms_tools"
            },
            "show_code": {
                "type": "boolean",
                "default": False,
                "description": "是否显示函数的具体代码实现（通常不需要）"
            }
        },
        "required": ["module_name"]
    }
)
def read_module_structure(module_name: str, show_code: bool = False) -> str:
    """读取现有模块的结构信息"""
    try:
        # 构建文件路径
        modules_dir = os.path.join(os.path.dirname(__file__))
        file_path = os.path.join(modules_dir, f"{module_name}.py")
        
        if not os.path.exists(file_path):
            return f"❌ 模块文件不存在: {file_path}"
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析模块信息
        module_info = _parse_module_header(content)
        
        # 解析函数信息
        functions = _parse_functions(content, show_code)
        
        result = f"📁 模块信息: {module_name}.py\n"
        result += f"   描述: {module_info.get('description', 'N/A')}\n"
        result += f"   类别: {module_info.get('category', 'N/A')}\n"
        result += f"   作者: {module_info.get('author', 'N/A')}\n"
        result += f"   版本: {module_info.get('version', 'N/A')}\n\n"
        
        if functions:
            result += f"🔧 包含 {len(functions)} 个工具函数:\n\n"
            for func in functions:
                result += f"   📌 {func['name']}\n"
                if func.get('description'):
                    result += f"      描述: {func['description']}\n"
                if func.get('parameters'):
                    result += f"      参数: {', '.join(func['parameters'])}\n"
                if show_code and func.get('body'):
                    result += f"      代码:\n{func['body']}\n"
                result += "\n"
        else:
            result += "🔧 暂无工具函数\n"
        
        return result
        
    except Exception as e:
        return f"❌ 读取模块结构失败: {str(e)}"

@register_tool(
    name="list_user_modules",
    description="AI专用：列出所有现有的工具模块。参数：include_details(是否显示详情默认False)。使用示例：list_user_modules(include_details=True)。返回：所有模块名称列表，可选显示每个模块的描述、类别、函数数量。AI开始任务前必须先调用此工具了解现有模块，决定创建新模块还是扩展现有模块。",
    schema={
        "type": "object",
        "properties": {
            "include_details": {
                "type": "boolean",
                "default": False,
                "description": "是否显示每个模块的详细信息（描述、类别、包含的函数等）"
            }
        }
    }
)
def list_user_modules(include_details: bool = False) -> str:
    """列出user_tool_modules目录中的所有模块"""
    try:
        modules_dir = os.path.join(os.path.dirname(__file__))
        
        # 获取所有Python文件
        modules = []
        for filename in os.listdir(modules_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                modules.append(module_name)
        
        if not modules:
            return "❌ user_tool_modules目录中没有找到任何模块"
        
        result = f"📁 用户工具模块目录 ({len(modules)} 个模块):\n\n"
        
        for module_name in sorted(modules):
            if include_details:
                # 读取模块详细信息
                file_path = os.path.join(modules_dir, f"{module_name}.py")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    module_info = _parse_module_header(content)
                    functions = _parse_functions(content, False)
                    
                    result += f"📄 {module_name}.py\n"
                    result += f"   描述: {module_info.get('description', 'N/A')}\n"
                    result += f"   类别: {module_info.get('category', 'N/A')}\n"
                    result += f"   函数数量: {len(functions)}\n"
                    if functions:
                        func_names = [f['name'] for f in functions]
                        result += f"   函数: {', '.join(func_names)}\n"
                    result += "\n"
                except Exception:
                    result += f"📄 {module_name}.py (读取失败)\n\n"
            else:
                result += f"📄 {module_name}.py\n"
        
        return result
        
    except Exception as e:
        return f"❌ 列出模块失败: {str(e)}"

# 辅助函数
def _parse_module_header(content: str) -> Dict[str, str]:
    """解析模块头部信息"""
    info = {}
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('# MODULE_DESCRIPTION:'):
            info['description'] = line.split(':', 1)[1].strip()
        elif line.startswith('# MODULE_CATEGORY:'):
            info['category'] = line.split(':', 1)[1].strip()
        elif line.startswith('# MODULE_AUTHOR:'):
            info['author'] = line.split(':', 1)[1].strip()
        elif line.startswith('# MODULE_VERSION:'):
            info['version'] = line.split(':', 1)[1].strip()
        elif not line.startswith('#') and line:
            break
    
    return info

def _parse_functions(content: str, include_body: bool = False) -> List[Dict[str, Any]]:
    """解析模块中的函数信息"""
    functions = []
    
    # 查找所有函数定义
    pattern = r'@register_tool\((.*?)\)\s*def (\w+)\((.*?)\) -> str:(.*?)(?=@register_tool|def \w+|\Z)'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        decorator_args = match.group(1)
        func_name = match.group(2)
        func_params = match.group(3)
        func_body = match.group(4)
        
        # 提取描述
        desc_match = re.search(r'description\s*=\s*["\']([^"\']*)["\']', decorator_args)
        description = desc_match.group(1) if desc_match else None
        
        # 解析参数
        parameters = [param.strip() for param in func_params.split(',') if param.strip()]
        
        func_info = {
            'name': func_name,
            'description': description,
            'parameters': parameters
        }
        
        if include_body:
            func_info['body'] = func_body.strip()
        
        functions.append(func_info)
    
    return functions

# ==================== AI专属模块管理工具 ====================

@register_tool(
    name="create_ai_module",
    description="AI专用：创建AI专属工具模块，集中管理AI生成的函数。参数：module_name(模块名默认ai_generated_tools), reset_existing(是否重置现有模块默认False)。推荐工作流程：1)先调用此工具创建专属模块 2)使用add_function_to_ai_module添加具体函数 3)调用restart_application重启生效。这样避免创建过多小模块，所有AI生成的简单函数都集中在一个模块中管理。",
    schema={
        "type": "object",
        "properties": {
            "module_name": {
                "type": "string",
                "default": "ai_generated_tools",
                "description": "AI专属模块名称（不含.py扩展名）"
            },
            "reset_existing": {
                "type": "boolean",
                "default": False,
                "description": "如果模块已存在，是否重置为空模块"
            }
        }
    },
    requires_confirmation=True,
    confirmation_category="file_write",
    risk_level="medium"
)
def create_ai_module(module_name: str = "ai_generated_tools", reset_existing: bool = False) -> str:
    """创建AI专属工具模块"""
    try:
        modules_dir = os.path.join(os.path.dirname(__file__))
        file_path = os.path.join(modules_dir, f"{module_name}.py")
        
        # 检查文件是否已存在
        if os.path.exists(file_path) and not reset_existing:
            return f"ℹ️ 模块 {module_name}.py 已存在，使用 reset_existing=True 来重置模块"
        
        # 创建AI专属模块模板
        ai_module_template = f'''# MODULE_DESCRIPTION: AI生成的工具函数集合
# MODULE_CATEGORY: ai_generated
# MODULE_AUTHOR: AI Assistant
# MODULE_VERSION: 1.0.0

"""
AI生成工具模块
此模块专门用于存放AI生成的简单工具函数
避免创建过多小模块，集中管理AI生成的功能
"""

import os
import sys
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import re

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# ==================== AI生成的工具函数 ====================
# 此区域用于存放AI生成的工具函数
# 每个函数都应该有@register_tool装饰器

# 示例函数（可以删除）
@register_tool(
    name="example_ai_tool",
    description="示例AI工具函数，可以删除。参数：message(消息内容)。使用示例：example_ai_tool(message='Hello World')。",
    schema={{
        "type": "object",
        "properties": {{
            "message": {{
                "type": "string",
                "description": "要处理的消息内容"
            }}
        }},
        "required": ["message"]
    }}
)
def example_ai_tool(message: str) -> str:
    """示例AI工具函数"""
    return f"AI处理结果: {{message}}"

'''
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(ai_module_template)
        
        action = "重置" if reset_existing else "创建"
        return f"✅ 成功{action}AI专属模块: {module_name}.py\n📝 模块已准备好接收AI生成的工具函数\n🔄 请调用 restart_application 重启以加载新模块"
        
    except Exception as e:
        return f"❌ 创建AI专属模块失败: {str(e)}"


@register_tool(
    name="add_function_to_ai_module",
    description="AI专用：向AI专属模块添加工具函数，支持复杂多行代码。参数：function_name(函数名), function_logic(函数逻辑代码支持多行), description(函数描述), parameters(参数定义字典), module_name(目标模块默认ai_generated_tools)。function_logic可以包含复杂逻辑、循环、条件判断等多行代码。示例：add_function_to_ai_module(function_name='process_data', function_logic='result = []\\nfor item in data:\\n    if item > 0:\\n        result.append(item * 2)\\nreturn result', description='处理数据列表', parameters={'data': {'type': 'array', 'description': '数据列表'}})。自动生成@register_tool装饰器。",
    schema={
        "type": "object",
        "properties": {
            "function_name": {
                "type": "string",
                "description": "函数名称（不含def关键字）"
            },
            "function_logic": {
                "type": "string",
                "description": "函数的核心逻辑代码，可以是多行代码"
            },
            "description": {
                "type": "string",
                "description": "函数的详细描述，用于@register_tool装饰器"
            },
            "parameters": {
                "type": "object",
                "description": "函数参数定义，格式：{'param_name': {'type': 'string/number/boolean', 'description': '参数描述', 'default': '默认值(可选)'}}"
            },
            "module_name": {
                "type": "string",
                "default": "ai_generated_tools",
                "description": "目标AI模块名称（不含.py扩展名）"
            },
            "return_type": {
                "type": "string",
                "default": "str",
                "description": "函数返回类型，如：str, int, bool, List[str], Dict[str, Any]等"
            }
        },
        "required": ["function_name", "function_logic", "description", "parameters"]
    },
    requires_confirmation=True,
    confirmation_category="file_modify",
    risk_level="medium"
)
def add_function_to_ai_module(function_name: str, function_logic: str, description: str, 
                             parameters: Dict[str, Dict[str, Any]], module_name: str = "ai_generated_tools",
                             return_type: str = "str") -> str:
    """向AI专属模块添加工具函数"""
    try:
        modules_dir = os.path.join(os.path.dirname(__file__))
        file_path = os.path.join(modules_dir, f"{module_name}.py")
        
        # 检查模块是否存在
        if not os.path.exists(file_path):
            return f"❌ 模块 {module_name}.py 不存在，请先调用 create_ai_module 创建模块"
        
        # 读取现有文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查函数是否已存在
        if f"def {function_name}(" in content:
            return f"❌ 函数 {function_name} 已存在于模块中，请使用不同的函数名或先删除现有函数"
        
        # 构建参数列表和类型注解
        param_list = []
        param_schema = {"type": "object", "properties": {}, "required": []}
        
        for param_name, param_info in parameters.items():
            param_type = param_info.get('type', 'str')
            param_default = param_info.get('default')
            
            # 构建函数参数
            if param_default is not None:
                if param_type == 'string':
                    param_list.append(f"{param_name}: str = '{param_default}'")
                else:
                    param_list.append(f"{param_name}: {param_type} = {param_default}")
            else:
                type_map = {'string': 'str', 'number': 'float', 'integer': 'int', 'boolean': 'bool'}
                py_type = type_map.get(param_type, param_type)
                param_list.append(f"{param_name}: {py_type}")
                param_schema["required"].append(param_name)
            
            # 构建schema
            param_schema["properties"][param_name] = {
                "type": param_info.get('type', 'string'),
                "description": param_info.get('description', f'{param_name}参数')
            }
            if param_default is not None:
                param_schema["properties"][param_name]["default"] = param_default
        
        # 生成函数代码
        param_str = ", ".join(param_list)
        schema_str = json.dumps(param_schema, ensure_ascii=False, indent=8).replace('\n', '\n        ')
        
        # 处理函数逻辑缩进
        logic_lines = function_logic.strip().split('\n')
        indented_logic = '\n'.join('    ' + line if line.strip() else '' for line in logic_lines)
        
        new_function = f'''
@register_tool(
    name="{function_name}",
    description="{description}",
    schema={schema_str}
)
def {function_name}({param_str}) -> {return_type}:
    """AI生成的工具函数: {description}"""
{indented_logic}

'''
        
        # 在文件末尾添加新函数
        updated_content = content.rstrip() + '\n' + new_function
        
        # 验证语法
        try:
            ast.parse(updated_content)
        except SyntaxError as e:
            return f"❌ 生成的代码语法错误: {str(e)}\n请检查function_logic的语法"
        
        # 备份原文件
        backup_path = file_path + f'.bak.{int(datetime.now().timestamp())}'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 写入更新后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return f"✅ 成功添加函数 {function_name} 到模块 {module_name}.py\n📝 函数参数: {list(parameters.keys())}\n💾 原文件已备份: {os.path.basename(backup_path)}\n🔄 请调用 restart_application 重启以加载新函数"
        
    except Exception as e:
        return f"❌ 添加函数失败: {str(e)}"


@register_tool(
    name="list_ai_module_functions",
    description="AI专用：列出AI专属模块中的所有函数。参数：module_name(模块名默认ai_generated_tools), show_details(是否显示详情默认True)。使用示例：list_ai_module_functions(module_name='ai_generated_tools', show_details=True)。返回：模块中所有函数的名称、描述、参数等信息。AI在添加新函数前应该先查看现有函数，避免重复。",
    schema={
        "type": "object",
        "properties": {
            "module_name": {
                "type": "string",
                "default": "ai_generated_tools",
                "description": "AI模块名称（不含.py扩展名）"
            },
            "show_details": {
                "type": "boolean",
                "default": True,
                "description": "是否显示函数的详细信息（参数、描述等）"
            }
        }
    }
)
def list_ai_module_functions(module_name: str = "ai_generated_tools", show_details: bool = True) -> str:
    """列出AI专属模块中的所有函数"""
    try:
        modules_dir = os.path.join(os.path.dirname(__file__))
        file_path = os.path.join(modules_dir, f"{module_name}.py")
        
        if not os.path.exists(file_path):
            return f"❌ 模块 {module_name}.py 不存在"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析函数
        functions = _parse_functions(content, include_body=False)
        
        if not functions:
            return f"📝 模块 {module_name}.py 中暂无函数"
        
        result = f"📋 模块 {module_name}.py 中的函数列表:\n\n"
        
        for i, func in enumerate(functions, 1):
            result += f"{i}. **{func['name']}**\n"
            
            if show_details:
                if func.get('description'):
                    result += f"   📝 描述: {func['description']}\n"
                
                if func.get('parameters'):
                    result += f"   📥 参数: {', '.join(func['parameters'])}\n"
                
                if func.get('return_type'):
                    result += f"   📤 返回: {func['return_type']}\n"
                
                result += "\n"
        
        return result.rstrip()
        
    except Exception as e:
        return f"❌ 列出函数失败: {str(e)}"


@register_tool(
    name="remove_function_from_ai_module",
    description="AI专用：从AI专属模块中删除不需要的函数。参数：function_name(要删除的函数名), module_name(模块名默认ai_generated_tools)。当需要替换或清理旧函数时使用。会完全删除函数定义和@register_tool装饰器，自动备份原文件。删除后需调用restart_application重启生效。",
    schema={
        "type": "object",
        "properties": {
            "function_name": {
                "type": "string",
                "description": "要删除的函数名称"
            },
            "module_name": {
                "type": "string",
                "default": "ai_generated_tools",
                "description": "目标AI模块名称（不含.py扩展名）"
            }
        },
        "required": ["function_name"]
    },
    requires_confirmation=True,
    confirmation_category="file_modify",
    risk_level="medium"
)
def remove_function_from_ai_module(function_name: str, module_name: str = "ai_generated_tools") -> str:
    """从AI专属模块中删除函数"""
    try:
        modules_dir = os.path.join(os.path.dirname(__file__))
        file_path = os.path.join(modules_dir, f"{module_name}.py")
        
        if not os.path.exists(file_path):
            return f"❌ 模块 {module_name}.py 不存在"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查函数是否存在
        if f"def {function_name}(" not in content:
            return f"❌ 函数 {function_name} 不存在于模块中"
        
        # 使用正则表达式删除函数（包括装饰器）
        # 匹配从@register_tool开始到下一个@register_tool或文件结尾的内容
        pattern = rf'@register_tool\([^)]*name="{function_name}"[^)]*\).*?(?=@register_tool|$)'
        
        updated_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # 清理多余的空行
        updated_content = re.sub(r'\n\s*\n\s*\n', '\n\n', updated_content)
        
        # 验证语法
        try:
            ast.parse(updated_content)
        except SyntaxError as e:
            return f"❌ 删除函数后代码语法错误: {str(e)}"
        
        # 备份原文件
        backup_path = file_path + f'.bak.{int(datetime.now().timestamp())}'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 写入更新后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return f"✅ 成功删除函数 {function_name} 从模块 {module_name}.py\n💾 原文件已备份: {os.path.basename(backup_path)}\n🔄 请调用 restart_application 重启以生效"
        
    except Exception as e:
        return f"❌ 删除函数失败: {str(e)}" 