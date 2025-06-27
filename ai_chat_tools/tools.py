"""
核心基础工具 - 系统必需的基础工具
这些工具总是被加载，不依赖于工具模块系统
"""
from .tool_manager import register_tool
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# ==================== 记忆管理系统 ====================

class MemoryManager:
    """记忆管理器 - 用于存储和检索AI的记忆"""
    
    def __init__(self):
        self.memory_file = os.path.join(os.getcwd(), "ai_memory.json")
        self._ensure_memory_file()
    
    def _ensure_memory_file(self):
        """确保记忆文件存在"""
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({"memories": [], "metadata": {"created": datetime.now().isoformat()}}, f, ensure_ascii=False, indent=2)
    
    def add_memory(self, content: str, tags: List[str] = [], category: str = "general") -> str:
        """添加记忆"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            memory_entry = {
                "id": len(data["memories"]) + 1,
                "content": content,
                "tags": tags or [],
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            data["memories"].append(memory_entry)
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return f"✅ 记忆已保存 (ID: {memory_entry['id']})"
            
        except Exception as e:
            return f"❌ 保存记忆失败: {str(e)}"
    
    def get_all_memories(self) -> List[Dict]:
        """获取所有记忆"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("memories", [])
        except Exception:
            return []
    
    def find_user_memories(self, keyword: str) -> List[Dict]:
        """模糊搜索记忆"""
        memories = self.get_all_memories()
        keyword_lower = keyword.lower()
        
        matching_memories = []
        for memory in memories:
            # 在内容、标签、类别中搜索
            if (keyword_lower in memory.get("content", "").lower() or
                any(keyword_lower in tag.lower() for tag in memory.get("tags", [])) or
                keyword_lower in memory.get("category", "").lower()):
                matching_memories.append(memory)
        
        return matching_memories
    
    def update_memory(self, memory_id: int, content: Optional[str] = None, tags: Optional[List[str]] = None, category: Optional[str] = None) -> str:
        """更新记忆"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 查找要更新的记忆
            memory_index = None
            for i, memory in enumerate(data["memories"]):
                if memory.get("id") == memory_id:
                    memory_index = i
                    break
            
            if memory_index is None:
                return f"❌ 未找到ID为 {memory_id} 的记忆"
            
            # 更新记忆内容
            memory = data["memories"][memory_index]
            updated_fields = []
            
            if content is not None:
                memory["content"] = content
                updated_fields.append("内容")
            
            if tags is not None:
                memory["tags"] = tags
                updated_fields.append("标签")
            
            if category is not None:
                memory["category"] = category
                updated_fields.append("类别")
            
            # 更新时间戳
            memory["updated_at"] = datetime.now().isoformat()
            memory["updated_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return f"✅ 记忆已更新 (ID: {memory_id})\n🔄 更新字段: {', '.join(updated_fields)}"
            
        except Exception as e:
            return f"❌ 更新记忆失败: {str(e)}"
    
    def delete_memory(self, memory_id: int) -> str:
        """删除记忆"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 查找要删除的记忆
            memory_index = None
            memory_content = None
            for i, memory in enumerate(data["memories"]):
                if memory.get("id") == memory_id:
                    memory_index = i
                    memory_content = memory.get("content", "")[:50] + "..." if len(memory.get("content", "")) > 50 else memory.get("content", "")
                    break
            
            if memory_index is None:
                return f"❌ 未找到ID为 {memory_id} 的记忆"
            
            # 删除记忆
            del data["memories"][memory_index]
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return f"✅ 记忆已删除 (ID: {memory_id})\n📝 内容预览: {memory_content}"
            
        except Exception as e:
            return f"❌ 删除记忆失败: {str(e)}"
    
    def get_memory_by_id(self, memory_id: int) -> Dict:
        """根据ID获取单个记忆"""
        memories = self.get_all_memories()
        for memory in memories:
            if memory.get("id") == memory_id:
                return memory
        return {}

# 创建全局记忆管理器实例
_memory_manager = MemoryManager()

@register_tool(
    name="save_memory",
    description="保存对话过程中的关键信息到AI记忆库。保存的记忆会带有唯一ID，方便后续引用、修改或删除",
    schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要保存的记忆内容"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "记忆标签，便于分类和搜索（可选）",
                "default": []
            },
            "category": {
                "type": "string",
                "description": "记忆类别",
                "enum": ["general", "user_preference", "project_info", "task", "knowledge", "conversation", "personal_info"],
                "default": "general"
            }
        },
        "required": ["content"]
    }
)
def save_memory(content: str, tags: List[str] = [], category: str = "general") -> str:
    """保存重要信息到AI记忆"""
    return _memory_manager.add_memory(content, tags, category)

@register_tool(
    name="read_all_memories",
    description="读取所有已保存的AI记忆，每条记忆都包含唯一ID便于后续操作。返回的记忆信息包含ID、时间、内容等完整信息",
    schema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "按类别过滤记忆（可选）",
                "enum": ["general", "user_preference", "project_info", "task", "knowledge", "conversation", "personal_info"],
                "default": ""
            },
            "limit": {
                "type": "integer",
                "description": "限制返回的记忆数量，默认返回所有",
                "default": 0,
                "minimum": 0
            }
        }
    }
)
def read_all_memories(category: str = "", limit: int = 0) -> str:
    """读取所有已保存的记忆"""
    try:
        memories = _memory_manager.get_all_memories()
        
        if not memories:
            return "💭 暂无保存的用户记忆"
        
        # 按类别过滤
        if category:
            memories = [m for m in memories if m.get("category", "") == category]
        
        # 按时间倒序排列（最新的在前）
        memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 限制数量
        if limit > 0:
            memories = memories[:limit]
        
        result = f"💭 AI记忆库 (共 {len(memories)} 条记忆)\n"
        result += "=" * 50 + "\n\n"
        
        for memory in memories:
            result += f"🆔 ID: {memory.get('id', 'N/A')}\n"
            result += f"📅 时间: {memory.get('created_date', 'N/A')}\n"
            result += f"📂 类别: {memory.get('category', 'general')}\n"
            
            tags = memory.get('tags', [])
            if tags:
                result += f"🏷️  标签: {', '.join(tags)}\n"
            
            result += f"📝 内容: {memory.get('content', '')}\n"
            result += "-" * 30 + "\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ 读取记忆失败: {str(e)}"

@register_tool(
    name="find_user_memories",
    description="通过关键词模糊搜索已保存的AI记忆。搜索范围包括记忆内容、标签和类别。返回结果包含记忆ID，便于后续修改或删除操作",
    schema={
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "搜索关键词"
            },
            "limit": {
                "type": "integer",
                "description": "限制返回的结果数量，默认20",
                "default": 20,
                "minimum": 1,
                "maximum": 100
            }
        },
        "required": ["keyword"]
    }
)
def find_user_memories(keyword: str, limit: int = 20) -> str:
    """根据关键词搜索记忆"""
    try:
        matching_memories = _memory_manager.find_user_memories(keyword)
        
        if not matching_memories:
            return f"🔍 没有找到包含关键词 '{keyword}' 的记忆"
        
        # 按时间倒序排列
        matching_memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 限制结果数量
        if len(matching_memories) > limit:
            matching_memories = matching_memories[:limit]
            truncated_note = f"\n💡 注意: 搜索结果已限制为前 {limit} 条，共找到 {len(_memory_manager.find_user_memories(keyword))} 条匹配记录"
        else:
            truncated_note = ""
        
        result = f"🔍 搜索结果 (关键词: '{keyword}', 找到 {len(matching_memories)} 条)\n"
        result += "=" * 50 + "\n\n"
        
        for memory in matching_memories:
            result += f"🆔 ID: {memory.get('id', 'N/A')}\n"
            result += f"📅 时间: {memory.get('created_date', 'N/A')}\n"
            result += f"📂 类别: {memory.get('category', 'general')}\n"
            
            tags = memory.get('tags', [])
            if tags:
                result += f"🏷️  标签: {', '.join(tags)}\n"
            
            content = memory.get('content', '')
            # 高亮关键词（简单实现）
            highlighted_content = content.replace(keyword, f"**{keyword}**")
            result += f"📝 内容: {highlighted_content}\n"
            result += "-" * 30 + "\n\n"
        
        result += truncated_note
        return result
        
    except Exception as e:
        return f"❌ 搜索记忆失败: {str(e)}"

@register_tool(
    name="update_memory",
    description="根据记忆ID修改已保存的AI记忆内容、标签或类别。可以单独更新其中一个或多个字段",
    schema={
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "integer",
                "description": "要修改的记忆ID",
                "minimum": 1
            },
            "content": {
                "type": "string",
                "description": "新的记忆内容（可选，不提供则不修改）"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "新的记忆标签列表（可选，不提供则不修改）"
            },
            "category": {
                "type": "string",
                "description": "新的记忆类别（可选，不提供则不修改）",
                "enum": ["general", "user_preference", "project_info", "task", "knowledge", "conversation", "personal_info"]
            }
        },
        "required": ["memory_id"]
    }
)
def update_memory(memory_id: int, content: Optional[str] = None, tags: Optional[List[str]] = None, category: Optional[str] = None) -> str:
    """修改已保存的记忆"""
    return _memory_manager.update_memory(memory_id, content, tags, category)

@register_tool(
    name="delete_memory",
    description="根据记忆ID删除已保存的AI记忆。删除操作不可恢复，请谨慎使用",
    schema={
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "integer",
                "description": "要删除的记忆ID",
                "minimum": 1
            }
        },
        "required": ["memory_id"]
    }
)
def delete_memory(memory_id: int) -> str:
    """删除指定的记忆"""
    return _memory_manager.delete_memory(memory_id)

@register_tool(
    name="get_memory",
    description="根据记忆ID获取单条记忆的详细信息",
    schema={
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "integer",
                "description": "要获取的记忆ID",
                "minimum": 1
            }
        },
        "required": ["memory_id"]
    }
)
def get_memory(memory_id: int) -> str:
    """获取单条记忆的详细信息"""
    try:
        memory = _memory_manager.get_memory_by_id(memory_id)
        
        if not memory:
            return f"❌ 未找到ID为 {memory_id} 的记忆"
        
        result = f"🧠 记忆详情 (ID: {memory_id})\n"
        result += "=" * 40 + "\n\n"
        result += f"📝 内容: {memory.get('content', '')}\n"
        result += f"📂 类别: {memory.get('category', 'general')}\n"
        
        tags = memory.get('tags', [])
        if tags:
            result += f"🏷️  标签: {', '.join(tags)}\n"
        else:
            result += f"🏷️  标签: 无\n"
        
        result += f"📅 创建时间: {memory.get('created_date', 'N/A')}\n"
        
        if memory.get('updated_date'):
            result += f"🔄 更新时间: {memory.get('updated_date')}\n"
        
        return result
        
    except Exception as e:
        return f"❌ 获取记忆失败: {str(e)}"

@register_tool(
    name="get_memories_for_context",
    description="获取格式化的记忆信息，用于在对话上下文中提供AI记忆参考。返回包含ID的记忆摘要，便于后续操作",
    schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "限制返回的记忆数量，默认10条",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            },
            "category": {
                "type": "string",
                "description": "按类别过滤记忆（可选）",
                "enum": ["general", "user_preference", "project_info", "task", "knowledge", "conversation", "personal_info"],
                "default": ""
            },
            "keyword": {
                "type": "string",
                "description": "关键词过滤（可选）",
                "default": ""
            }
        }
    }
)
def get_memories_for_context(limit: int = 10, category: str = "", keyword: str = "") -> str:
    """获取格式化的记忆信息，用于对话上下文"""
    try:
        memories = _memory_manager.get_all_memories()
        
        if not memories:
            return "📝 暂无AI记忆"
        
        # 过滤记忆
        filtered_memories = memories
        
        # 按类别过滤
        if category:
            filtered_memories = [m for m in filtered_memories if m.get("category", "") == category]
        
        # 按关键词过滤
        if keyword:
            keyword_lower = keyword.lower()
            filtered_memories = [m for m in filtered_memories if 
                                keyword_lower in m.get("content", "").lower() or
                                any(keyword_lower in tag.lower() for tag in m.get("tags", [])) or
                                keyword_lower in m.get("category", "").lower()]
        
        # 按时间倒序排列（最新的在前）
        filtered_memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 限制数量
        if len(filtered_memories) > limit:
            filtered_memories = filtered_memories[:limit]
        
        if not filtered_memories:
            filter_desc = []
            if category:
                filter_desc.append(f"类别: {category}")
            if keyword:
                filter_desc.append(f"关键词: {keyword}")
            
            filter_str = f" ({', '.join(filter_desc)})" if filter_desc else ""
            return f"📝 没有找到匹配的AI记忆{filter_str}"
        
        result = f"🧠 AI记忆上下文 (最近 {len(filtered_memories)} 条)\n"
        
        for memory in filtered_memories:
            memory_id = memory.get('id', 'N/A')
            content = memory.get('content', '')
            category_name = memory.get('category', 'general')
            tags = memory.get('tags', [])
            created_date = memory.get('created_date', 'N/A')
            
            # 内容摘要（限制长度）
            if len(content) > 100:
                content_summary = content[:100] + "..."
            else:
                content_summary = content
            
            result += f"\n[ID:{memory_id}] {content_summary}"
            if tags:
                result += f" [标签: {', '.join(tags)}]"
            result += f" [类别: {category_name}] [{created_date}]"
        
        return result
        
    except Exception as e:
        return f"❌ 获取记忆上下文失败: {str(e)}"

# ==================== 工具管理工具 ====================
# 让大模型具备自主管理工具的能力

@register_tool(
    name="list_available_tools",
    description="列出当前可用的所有工具（包括系统工具和当前已添加的模块工具）",
    schema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "按类别过滤工具（可选）",
                "default": ""
            }
        }
    }
)
def list_available_tools(category: str = "") -> str:
    """列出当前可用的所有工具"""
    from .tool_manager import tool_registry
    from .tool_module_manager import tool_module_manager
    
    def format_tool_with_params(tool_info):
        """格式化工具信息，包含参数说明"""
        tool_desc = f"    • {tool_info['name']}: {tool_info['description']}\n"
        
        # 添加参数信息
        schema = tool_info.get('schema', {})
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        if properties:
            tool_desc += f"      参数:\n"
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'string')
                param_desc = param_info.get('description', '无描述')
                is_required = param_name in required
                required_mark = "必需" if is_required else "可选"
                
                # 显示枚举值
                if 'enum' in param_info:
                    enum_values = ', '.join(param_info['enum'])
                    tool_desc += f"        - {param_name} ({param_type}, {required_mark}): {param_desc} [可选值: {enum_values}]\n"
                # 显示默认值
                elif 'default' in param_info:
                    default_val = param_info['default']
                    tool_desc += f"        - {param_name} ({param_type}, {required_mark}): {param_desc} [默认: {default_val}]\n"
                else:
                    tool_desc += f"        - {param_name} ({param_type}, {required_mark}): {param_desc}\n"
        else:
            tool_desc += f"      参数: 无需参数\n"
        
        return tool_desc
    
    # 获取内置工具（始终可用）
    builtin_tools = tool_registry.get_builtin_tools()
    
    # 获取激活的模块工具
    module_tools = tool_module_manager.get_active_tools()
    
    # 过滤掉内置工具（避免重复）
    module_tools = [tool for tool in module_tools if tool['name'] not in [bt['name'] for bt in builtin_tools]]
    
    all_tools_count = len(builtin_tools) + len(module_tools)
    result = f"🔧 当前可用工具 ({all_tools_count} 个):\n"
    result += "⚠️ 注意：list_available_tools 工具已执行完成，请勿重复调用此工具\n"
    result += "💡 以下是完整的工具列表及详细参数说明，请根据需要选择合适的工具执行任务\n\n"
    
    # 按功能分类显示内置工具（排除当前正在执行的工具）
    result += "📌 核心工具:\n"
    
    # 工具管理功能
    management_tools = [t for t in builtin_tools if t['name'] in [
        'list_available_tools', 'list_tool_modules', 'activate_tool_modules', 
        'deactivate_tool_modules', 'get_tool_schema'
    ]]
    if management_tools:
        result += "  🔧 工具管理:\n"
        for tool in management_tools:
            result += format_tool_with_params(tool)
    
    # 记忆管理功能
    memory_tools = [t for t in builtin_tools if t['name'] in [
        'save_memory', 'read_all_memories', 'find_user_memories', 'update_memory', 'delete_memory', 'get_memory', 'get_memories_for_context'
    ]]
    if memory_tools:
        result += "  🧠 记忆管理:\n"
        for tool in memory_tools:
            result += format_tool_with_params(tool)
    
    # 帮助和系统功能
    system_tools = [t for t in builtin_tools if t['name'] in [
        'help', 'manage_confirmation_settings', 'switch_session', 'show_session_history', 'delete_session',
        'send_notification', 'send_notification_advanced', 'test_notification_system', 
        'get_notification_platform_info', 'send_smart_notification'
    ]]
    if system_tools:
        result += "  ⚙️ 系统功能:\n"
        for tool in system_tools:
            result += format_tool_with_params(tool)
    
    result += "\n"
    
    # 显示模块工具（仅在有激活的模块时）
    if module_tools:
        result += "📦 模块工具:\n"
        for tool in module_tools:
            result += format_tool_with_params(tool)
    else:
        result += "💡 没有激活的模块工具。使用 'list_tool_modules' 查看可用模块，用 'activate_tool_modules' 激活模块。\n"
    
    return result

def _get_module_tools(module_name: str) -> List[Dict[str, str]]:
    """获取指定模块中的工具列表"""
    from .tool_manager import tool_registry
    
    module_tools = []
    for tool_name, tool_info in tool_registry.tools.items():
        # 检查工具是否属于指定模块
        if tool_info.get('module') == module_name:
            module_tools.append({
                'name': tool_name,
                'description': tool_info['description']
            })
    
    return sorted(module_tools, key=lambda x: x['name'])

@register_tool(
    name="list_tool_modules",
    description="列出所有可用的工具模块。注意：此工具仅显示模块中工具的名称和描述，不包含工具的详细参数说明。要获取工具的完整参数信息，需要先使用 activate_tool_modules 激活模块，然后调用 list_available_tools 查看详细的工具参数说明",
    schema={
        "type": "object",
        "properties": {
            "show_details": {
                "type": "boolean",
                "description": "是否显示详细信息",
                "default": False
            },
            "show_tools": {
                "type": "boolean",
                "description": "是否显示每个模块包含的工具列表",
                "default": True
            }
        }
    }
)
def list_tool_modules(show_details: bool = False, show_tools: bool = True) -> str:
    """列出所有可用的工具模块"""
    from .tool_module_manager import tool_module_manager
    
    # 按需扫描模块（只在第一次调用时或模块列表为空时）
    if not tool_module_manager.available_modules:
        tool_module_manager.scan_and_load_all_modules()
    
    modules = tool_module_manager.list_available_modules()
    
    if not modules:
        return "❌ 没有找到可用的工具模块"
    
    result = f"📦 工具模块列表 ({len(modules)} 个):\n"
    result += "💡 提示：此列表仅显示工具名称和描述，不包含详细参数。要查看工具的完整参数说明，请：\n"
    result += "  1. 使用 activate_tool_modules 激活需要的模块\n"
    result += "  2. 然后调用 list_available_tools 查看详细的工具参数和使用方法\n\n"
    
    # 按类别分组
    categories = {}
    for module in modules:
        category = module['category'].upper()
        if category not in categories:
            categories[category] = []
        categories[category].append(module)
    
    for category, category_modules in categories.items():
        result += f"📁 {category}:\n"
        for module in category_modules:
            status = "✅ 已激活" if module['active'] else "⭕ 未激活"
            # 显示类别名作为主要激活方式，模块名作为备选方式
            result += f"  • {category} (模块名: {module['name']}) - {module['description']} [{status}]\n"
            
            if show_details:
                result += f"    版本: {module['version']}, 作者: {module['author']}\n"
                result += f"    激活方式: activate_tool_modules(\"{category}\") 或 activate_tool_modules(\"{module['name']}\")\n"
            
            # 显示模块中的工具列表
            if show_tools:
                module_tools = _get_module_tools(module['name'])
                if module_tools:
                    result += f"    🔧 包含工具 ({len(module_tools)} 个):\n"
                    for tool in module_tools:
                        result += f"      - {tool['name']}: {tool['description']}\n"
                else:
                    result += f"    🔧 包含工具: 暂无或未加载\n"
        result += "\n"
    
    return result

@register_tool(
    name="activate_tool_modules",
    description="激活指定的工具模块",
    schema={
        "type": "object",
        "properties": {
            "module_names": {
                "type": "string",
                "description": "要激活的模块名称，多个用逗号分隔"
            }
        },
        "required": ["module_names"]
    }
)
def activate_tool_modules(module_names) -> str:
    """激活指定的工具模块"""
    from .tool_module_manager import tool_module_manager
    
    # 处理AI传递的参数格式
    if isinstance(module_names, dict):
        # AI可能传递 {"module_names": "value"} 或 {"keyword": "value"} 格式
        if "module_names" in module_names:
            module_names = module_names["module_names"]
        elif "keyword" in module_names:
            # 向后兼容：支持 keyword 参数
            module_names = module_names["keyword"]
        else:
            return f"❌ 字典参数格式错误：缺少 'module_names' 或 'keyword' 键，实际收到: {module_names}"
    
    # 解析模块名称 - 支持字符串和列表两种格式
    if isinstance(module_names, str):
        modules = [name.strip() for name in module_names.split(',')]
    elif isinstance(module_names, list):
        modules = [str(name).strip() for name in module_names]
    else:
        return f"❌ 参数格式错误：module_names 应该是字符串或列表，实际收到: {type(module_names)}"
    
    # 获取可用模块信息
    available_modules_info = tool_module_manager.list_available_modules()
    available_modules = {m['name'] for m in available_modules_info}
    
    # 创建类别名到模块名的映射（支持一个类别对应多个模块）
    category_to_modules = {}
    for module_info in available_modules_info:
        category = module_info['category'].upper()
        if category not in category_to_modules:
            category_to_modules[category] = []
        category_to_modules[category].append(module_info['name'])
    
    # 转换模块名称：如果是类别名称，转换为模块名称
    converted_modules = []
    for module in modules:
        if module in available_modules:
            # 直接是模块名
            converted_modules.append(module)
        elif module.upper() in category_to_modules:
            # 是类别名，添加该类别下的所有模块
            category_modules = category_to_modules[module.upper()]
            converted_modules.extend(category_modules)
        else:
            # 既不是模块名也不是类别名
            converted_modules.append(module)
    
    # 检查转换后的模块是否存在
    invalid_modules = [m for m in converted_modules if m not in available_modules]
    
    if invalid_modules:
        result = f"❌ 以下模块不存在: {', '.join(invalid_modules)}\n\n"
        result += f"📦 可用模块列表:\n"
        
        # 按类别显示可用模块
        modules_info = tool_module_manager.list_available_modules()
        categories = {}
        for module in modules_info:
            category = module['category'].upper()
            if category not in categories:
                categories[category] = []
            categories[category].append(module)
        
        for category, category_modules in categories.items():
            result += f"\n{category}:\n"
            for module in category_modules:
                status = "✅ 已激活" if module['active'] else "⭕ 未激活"
                result += f"  • {category} (模块名: {module['name']}) - {module['description']} [{status}]\n"
        
        return result
    
    # 检查哪些模块在激活前已经是激活状态
    already_active_before = [m for m in converted_modules if m in tool_module_manager.active_modules]
    
    # 激活模块
    success = tool_module_manager.activate_modules(converted_modules)
    
    if success:
        # 检查哪些是新激活的
        newly_activated = [m for m in converted_modules if m not in already_active_before]
        already_active = already_active_before
        
        result = ""
        if newly_activated:
            result += f"✅ 成功激活模块: {', '.join(newly_activated)}\n"
        if already_active:
            result += f"ℹ️ 以下模块已处于激活状态: {', '.join(already_active)}\n"
        
        if not newly_activated and already_active:
            result += f"💡 所有请求的模块都已激活，无需重复操作\n"
        
        result += "\n💡 提示：模块激活后，您可以使用以下命令：\n"
        result += "  • list_available_tools - 查看所有可用工具\n"
        result += "  • help - 查看帮助信息\n"
        
        return result
    else:
        return f"⚠️ 部分模块激活失败。请检查模块是否存在。"

@register_tool(
    name="deactivate_tool_modules",
    description="取消激活指定的工具模块",
    schema={
        "type": "object",
        "properties": {
            "module_names": {
                "type": "string",
                "description": "要取消激活的模块名称，多个用逗号分隔"
            }
        },
        "required": ["module_names"]
    }
)
def deactivate_tool_modules(module_names) -> str:
    """取消激活指定的工具模块"""
    from .tool_module_manager import tool_module_manager
    
    # 解析模块名称 - 支持字符串和列表两种格式
    if isinstance(module_names, str):
        modules = [name.strip() for name in module_names.split(',')]
    elif isinstance(module_names, list):
        modules = [str(name).strip() for name in module_names]
    else:
        return f"❌ 参数格式错误：module_names 应该是字符串或列表"
    
    # 取消激活模块
    success = tool_module_manager.deactivate_modules(modules)
    
    if success:
        return f"✅ 成功取消激活模块: {', '.join(modules)}"
    else:
        return f"❌ 取消激活模块失败"

@register_tool(
    name="get_tool_schema",
    description="通过工具名获取工具的详细Schema信息，包括参数说明、类型和使用方法",
    schema={
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "要获取Schema的工具名称"
            },
            "format": {
                "type": "string",
                "description": "返回格式：'detailed'(详细格式)或'json'(JSON格式)",
                "enum": ["detailed", "json"],
                "default": "detailed"
            }
        },
        "required": ["tool_name"]
    }
)
def get_tool_schema(tool_name: str, format: str = "detailed") -> str:
    """通过工具名获取工具的Schema信息"""
    from .tool_manager import tool_registry
    
    # 检查工具是否存在
    if tool_name not in tool_registry.tools:
        available_tools = list(tool_registry.tools.keys())
        result = f"❌ 工具 '{tool_name}' 不存在\n\n"
        result += "📋 可用工具列表:\n"
        
        # 分类显示可用工具
        builtin_tools = [name for name in available_tools if name in ['list_available_tools', 'list_tool_modules', 'activate_tool_modules', 'deactivate_tool_modules', 'get_tool_schema', 'save_memory', 'read_all_memories', 'find_user_memories', 'help', 'manage_confirmation_settings']]
        
        from .tool_module_manager import tool_module_manager
        module_tools = []
        for name in available_tools:
            if name not in builtin_tools:
                module_tools.append(name)
    
        if builtin_tools:
            result += "🔧 系统工具:\n"
            for tool in sorted(builtin_tools):
                result += f"  • {tool}\n"
        
        if module_tools:
            result += "\n📦 模块工具:\n"
            for tool in sorted(module_tools):
                result += f"  • {tool}\n"
        
        result += f"\n💡 提示：使用 get_tool_schema(tool_name=\"具体工具名\") 获取工具详细信息"
        return result
    
    tool_info = tool_registry.tools[tool_name]
    
    if format == "json":
        # 返回JSON格式的Schema
        import json
        schema = tool_registry.get_tool_schema(tool_name)
        return f"✅ 工具 '{tool_name}' 的Schema (JSON格式):\n\n```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```"
    
    # 返回详细格式的Schema
    result = f"🔧 工具信息: {tool_name}\n"
    result += "=" * 50 + "\n\n"
    
    # 基本信息
    result += f"📝 描述: {tool_info['description']}\n"
    
    # 模块信息
    module = tool_info.get('module')
    if module:
        result += f"📦 所属模块: {module}\n"
    else:
        result += f"📦 所属模块: 系统内置工具\n"
    
    # 确认机制信息
    requires_confirmation = tool_info.get('requires_confirmation', False)
    if requires_confirmation:
        category = tool_info.get('confirmation_category', 'general')
        risk_level = tool_info.get('risk_level', 'medium')
        result += f"⚠️  需要用户确认: 是 (类别: {category}, 风险级别: {risk_level})\n"
    else:
        result += f"✅ 需要用户确认: 否\n"
    
    result += f"🔄 异步执行: {'是' if tool_info['is_async'] else '否'}\n\n"
    
    # 参数信息
    schema = tool_info['schema']
    if "properties" in schema and schema["properties"]:
        result += "📋 参数说明:\n"
        required_params = schema.get("required", [])
        
        for param_name, param_info in schema["properties"].items():
            param_type = param_info.get("type", "unknown")
            is_required = param_name in required_params
            required_mark = " ⭐" if is_required else " (可选)"
            
            result += f"\n  🔹 {param_name} ({param_type}){required_mark}\n"
            
            if "description" in param_info:
                result += f"     📖 说明: {param_info['description']}\n"
            
            if "enum" in param_info:
                result += f"     🎯 可选值: {', '.join(map(str, param_info['enum']))}\n"
            
            if "default" in param_info:
                result += f"     🔧 默认值: {param_info['default']}\n"
            
            if "minimum" in param_info:
                result += f"     📏 最小值: {param_info['minimum']}\n"
            
            if "maximum" in param_info:
                result += f"     📏 最大值: {param_info['maximum']}\n"
    else:
        result += "📋 参数说明: 此工具不需要参数\n"
    
    # 使用示例
    result += "\n💡 调用示例:\n"
    if "properties" in schema and schema["properties"]:
        # 生成示例参数
        example_params = {}
        for param_name, param_info in schema["properties"].items():
            param_type = param_info.get("type", "string")
            if "default" in param_info:
                example_params[param_name] = param_info["default"]
            elif "enum" in param_info:
                example_params[param_name] = param_info["enum"][0]
            elif param_type == "string":
                example_params[param_name] = "示例文本"
            elif param_type == "integer":
                example_params[param_name] = 1
            elif param_type == "boolean":
                example_params[param_name] = True
            elif param_type == "array":
                example_params[param_name] = ["示例项目"]
        
        result += f"```\n{tool_name}("
        param_strs = []
        for key, value in example_params.items():
            if isinstance(value, str):
                param_strs.append(f'{key}="{value}"')
            else:
                param_strs.append(f'{key}={value}')
        result += ", ".join(param_strs)
        result += ")\n```"
    else:
        result += f"```\n{tool_name}()\n```"
    
    return result

# ==================== 帮助工具 ====================

@register_tool(
    name="help",
    description="获取帮助信息",
    schema={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "帮助主题（可选）",
                "default": "general"
            }
        }
    }
)
def help(topic: str = "general") -> str:
    """获取帮助信息"""
    help_info = {
        "general": """
🤖 AI Chat Tools 帮助

工具管理：
- list_available_tools: 列出当前可用工具
- list_tool_modules: 列出所有工具模块
- activate_tool_modules: 激活工具模块
- deactivate_tool_modules: 取消激活工具模块
- get_tool_schema: 获取工具详细Schema信息

使用方法：
1. 直接描述你想做的事情
2. AI 会自动选择合适的工具
3. 查看工具执行结果

更多信息请访问项目文档。
        """,
        "modules": """
📦 工具模块系统：

动态加载：
- 启动时选择需要的工具模块
- 按需加载，减少资源占用
- 模块化管理不同功能

可用模块：
- file_manager_tools: 文件管理工具

创建自定义模块：
1. 在 user_tool_modules/ 目录创建 .py 文件
2. 添加 MODULE_* 注释
3. 使用 @register_tool 装饰器定义工具
        """
    }
    
    return help_info.get(topic, help_info["general"])

@register_tool(
    name="manage_confirmation_settings",
    description="管理用户确认偏好设置（仅限用户操作）",
    requires_confirmation=True,
    confirmation_category="system_command",
    risk_level="high",
    schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "操作类型",
                "enum": ["show", "set_default", "set_tool", "set_category", "clear_session", "reset"]
            },
            "policy": {
                "type": "string",
                "description": "确认策略",
                "enum": ["ask", "allow", "deny"]
            },
            "tool_name": {
                "type": "string",
                "description": "工具名称（用于设置特定工具策略）"
            },
            "category": {
                "type": "string",
                "description": "操作类别",
                "enum": ["file_write", "file_delete", "file_modify", "system_command", "network_request", "general"]
            }
        },
        "required": ["action"]
    }
)
def manage_confirmation_settings(action: str, policy: str = "", tool_name: str = "", category: str = "") -> str:
    """管理用户确认偏好设置"""
    try:
        from .config import config
        
        if action == "show":
            # 显示当前设置
            result = "🔒 用户确认偏好设置\n"
            result += "=" * 40 + "\n\n"
            
            # 默认策略
            default_policy = config.get_confirmation_policy()
            result += f"📋 默认策略: {default_policy}\n\n"
            
            # 类别策略
            categories = ["file_write", "file_delete", "file_modify", "system_command", "network_request"]
            result += "📂 类别策略:\n"
            for cat in categories:
                cat_policy = config.get_confirmation_policy(category=cat)
                result += f"  • {cat}: {cat_policy}\n"
            
            # 工具级别策略
            tool_policies = config.get("user_confirmation.tool_policies", {})
            if tool_policies:
                result += "\n🔧 工具级别策略:\n"
                for tool, pol in tool_policies.items():
                    result += f"  • {tool}: {pol}\n"
            
            # 会话记忆
            session_memory = config.get("user_confirmation.session_memory", {})
            if session_memory:
                result += "\n💭 当前会话记忆:\n"
                for key, value in session_memory.items():
                    result += f"  • {key}: {value}\n"
            
            return result
            
        elif action == "set_default":
            if not policy:
                return "❌ 设置默认策略需要提供 policy 参数"
            
            config.set_confirmation_policy(policy)
            config.save()
            return f"✅ 已设置默认确认策略为: {policy}"
            
        elif action == "set_tool":
            if not tool_name or not policy:
                return "❌ 设置工具策略需要提供 tool_name 和 policy 参数"
            
            config.set_confirmation_policy(policy, tool_name=tool_name)
            config.save()
            return f"✅ 已设置工具 '{tool_name}' 的确认策略为: {policy}"
            
        elif action == "set_category":
            if not category or not policy:
                return "❌ 设置类别策略需要提供 category 和 policy 参数"
            
            config.set_confirmation_policy(policy, category=category)
            config.save()
            return f"✅ 已设置类别 '{category}' 的确认策略为: {policy}"
            
        elif action == "clear_session":
            config.clear_session_memory()
            return "✅ 已清除当前会话的确认记忆"
            
        elif action == "reset":
            # 重置所有确认设置
            config.set("user_confirmation", {
                "default_policy": "ask",
                "tool_policies": {},
                "category_policies": {
                    "file_write": "ask",
                    "file_delete": "ask", 
                    "file_modify": "ask",
                    "system_command": "ask",
                    "network_request": "allow"
                },
                "remember_choices": True,
                "session_memory": {}
            })
            config.save()
            return "✅ 已重置所有确认设置为默认值"
            
        else:
            return f"❌ 未知操作: {action}"
            
    except Exception as e:
        return f"❌ 管理确认设置失败: {str(e)}"

@register_tool(
    name="switch_session",
    description="切换到指定的对话会话",
    schema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "要切换到的会话ID"
            }
        },
        "required": ["session_id"]
    }
)
def switch_session(session_id: str) -> str:
    """切换会话"""
    try:
        from .database import db
        
        # 验证会话是否存在
        session = db.get_session(session_id)
        if not session:
            return f"❌ 会话 {session_id} 不存在\n\n💡 使用 'list_sessions' 查看所有可用会话"
        
        # 获取会话信息
        title = session.get("title", "未命名会话")
        created_at = session.get("created_at", "")
        message_count = len(db.get_messages(session_id))
        
        # 注意：实际的会话切换需要在ChatBot实例中处理
        # 这里只是提供信息，真正的切换会在下次对话时生效
        
        return f"✅ 会话切换成功\n🆔 会话ID: {session_id}\n📋 标题: {title}\n📅 创建时间: {created_at}\n💬 消息数: {message_count}\n\n💡 后续对话将在此会话中进行"
        
    except Exception as e:
        return f"❌ 切换会话失败: {str(e)}"

@register_tool(
    name="show_session_history",
    description="显示当前会话或指定会话的对话历史",
    schema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "会话ID，如果不指定则显示当前会话历史",
                "default": ""
            },
            "limit": {
                "type": "integer",
                "description": "限制显示的消息数量，默认显示最近20条",
                "default": 20,
                "minimum": 1,
                "maximum": 100
            },
            "include_tool_calls": {
                "type": "boolean",
                "description": "是否包含工具调用信息",
                "default": True
            }
        }
    }
)
def show_session_history(session_id: str = "", limit: int = 20, include_tool_calls: bool = True) -> str:
    """显示会话历史"""
    try:
        from .database import db
        
        # 如果没有指定session_id，尝试使用当前会话
        if not session_id:
            # 由于这是静态函数，无法直接获取当前会话ID
            # 需要从最近的会话中选择
            sessions = db.get_sessions()
            if not sessions:
                return "📝 暂无对话会话\n\n💡 使用 'new_session' 工具创建新会话"
            
            # 选择最近更新的会话
            sessions.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
            session_id = sessions[0]["id"]
            session_title = sessions[0].get("title", "未命名会话")
        else:
            # 验证指定的会话是否存在
            session = db.get_session(session_id)
            if not session:
                return f"❌ 会话 {session_id} 不存在\n\n💡 使用 'list_sessions' 查看所有可用会话"
            session_title = session.get("title", "未命名会话")
        
        # 获取消息历史
        messages = db.get_messages(session_id)
        
        if not messages:
            return f"📝 会话 '{session_title}' 暂无消息历史\n🆔 会话ID: {session_id}"
        
        # 限制消息数量（取最近的消息）
        if len(messages) > limit:
            messages = messages[-limit:]
            truncated_note = f"\n💡 注意: 只显示最近 {limit} 条消息，该会话共有 {len(db.get_messages(session_id))} 条消息"
        else:
            truncated_note = ""
        
        result = f"📝 会话历史: {session_title}\n"
        result += f"🆔 会话ID: {session_id}\n"
        result += f"💬 显示消息: {len(messages)} 条\n"
        result += "=" * 50 + "\n\n"
        
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            tool_calls = msg.get("tool_calls", [])
            
            # 角色图标
            role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(role, "❓")
            
            result += f"{i}. {role_icon} {role.upper()}\n"
            if timestamp:
                result += f"   ⏰ {timestamp}\n"
            
            # 内容预览（避免过长）
            if len(content) > 300:
                content_preview = content[:300] + "..."
            else:
                content_preview = content
            
            result += f"   💬 {content_preview}\n"
            
            # 显示工具调用信息
            if include_tool_calls and tool_calls:
                result += f"   🔧 工具调用: {len(tool_calls)} 个\n"
                for j, tool_call in enumerate(tool_calls[:3]):  # 最多显示3个工具调用
                    tool_name = tool_call.get("function", {}).get("name", "unknown")
                    result += f"      {j+1}. {tool_name}\n"
                if len(tool_calls) > 3:
                    result += f"      ... 还有 {len(tool_calls) - 3} 个工具调用\n"
            
            result += "-" * 30 + "\n\n"
        
        result += truncated_note
        
        return result
        
    except Exception as e:
        return f"❌ 获取会话历史失败: {str(e)}"

@register_tool(
    name="delete_session",
    description="删除指定的对话会话（谨慎操作）",
    requires_confirmation=True,
    confirmation_category="general",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "要删除的会话ID"
            },
            "confirm": {
                "type": "boolean",
                "description": "确认删除操作",
                "default": False
            }
        },
        "required": ["session_id"]
    }
)
def delete_session(session_id: str, confirm: bool = False) -> str:
    """删除会话"""
    try:
        from .database import db
        
        # 验证会话是否存在
        session = db.get_session(session_id)
        if not session:
            return f"❌ 会话 {session_id} 不存在"
        
        if not confirm:
            title = session.get("title", "未命名会话")
            message_count = len(db.get_messages(session_id))
            return f"⚠️ 确认删除会话吗？\n🆔 会话ID: {session_id}\n📋 标题: {title}\n💬 消息数: {message_count}\n\n💡 请在参数中设置 confirm=true 来确认删除操作"
        
        # 执行删除
        db.delete_session(session_id)
        title = session.get("title", "未命名会话")
        
        return f"✅ 会话已删除\n🆔 会话ID: {session_id}\n📋 标题: {title}"
        
    except Exception as e:
        return f"❌ 删除会话失败: {str(e)}"

# ==================== 消息提醒工具 ====================

@register_tool(
    name="send_notification",
    description="发送系统桌面通知消息，用于AI推送重要信息给用户",
    schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "通知标题"
            },
            "message": {
                "type": "string",
                "description": "通知消息内容"
            },
            "timeout": {
                "type": "integer",
                "description": "通知显示时长（秒），默认10秒",
                "default": 10,
                "minimum": 1,
                "maximum": 60
            }
        },
        "required": ["title", "message"]
    }
)
def send_notification(title: str, message: str, timeout: int = 10) -> str:
    """发送桌面通知"""
    try:
        try:
            from plyer import notification
        except ImportError:
            return "❌ 发送通知失败: 缺少 plyer 库\n💡 请运行: pip install plyer"
        
        # 发送通知
        notification.notify(  # type: ignore
            title=title,
            message=message,
            timeout=timeout
        )
        
        return f"✅ 通知已发送\n📋 标题: {title}\n💬 内容: {message}\n⏰ 显示时长: {timeout}秒"
        
    except Exception as e:
        return f"❌ 发送通知失败: {str(e)}"

@register_tool(
    name="send_notification_advanced",
    description="发送高级桌面通知，支持更多自定义选项",
    schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "通知标题"
            },
            "message": {
                "type": "string",
                "description": "通知消息内容"
            },
            "timeout": {
                "type": "integer",
                "description": "通知显示时长（秒），默认10秒",
                "default": 10,
                "minimum": 1,
                "maximum": 300
            },
            "app_name": {
                "type": "string",
                "description": "应用名称，默认为'Alice '",
                "default": "Alice "
            },
            "app_icon": {
                "type": "string",
                "description": "应用图标路径（可选）",
                "default": ""
            },
            "urgency": {
                "type": "string",
                "description": "通知紧急程度",
                "enum": ["low", "normal", "critical"],
                "default": "normal"
            }
        },
        "required": ["title", "message"]
    }
)
def send_notification_advanced(title: str, message: str, timeout: int = 10, 
                             app_name: str = "Alice ", app_icon: str = "", 
                             urgency: str = "normal") -> str:
    """发送高级桌面通知"""
    try:
        try:
            from plyer import notification
        except ImportError:
            return "❌ 发送通知失败: 缺少 plyer 库\n💡 请运行: pip install plyer"
        
        import os
        
        # 准备通知参数
        notify_kwargs = {
            "title": title,
            "message": message,
            "timeout": timeout,
            "app_name": app_name
        }
        
        # 添加图标（如果提供且文件存在）
        if app_icon and os.path.exists(app_icon):
            notify_kwargs["app_icon"] = app_icon
        
        # 发送通知
        notification.notify(**notify_kwargs)  # type: ignore
        
        result = f"✅ 高级通知已发送\n"
        result += f"📋 标题: {title}\n"
        result += f"💬 内容: {message}\n"
        result += f"⏰ 显示时长: {timeout}秒\n"
        result += f"📱 应用名称: {app_name}\n"
        result += f"🚨 紧急程度: {urgency}\n"
        
        if app_icon and os.path.exists(app_icon):
            result += f"🖼️ 图标: {app_icon}\n"
        
        return result
        
    except Exception as e:
        return f"❌ 发送通知失败: {str(e)}"

@register_tool(
    name="test_notification_system",
    description="测试通知系统是否正常工作",
    schema={
        "type": "object",
        "properties": {
            "test_type": {
                "type": "string",
                "description": "测试类型",
                "enum": ["basic", "advanced", "both"],
                "default": "basic"
            }
        }
    }
)
def test_notification_system(test_type: str = "basic") -> str:
    """测试通知系统"""
    try:
        try:
            from plyer import notification
        except ImportError:
            return "❌ 通知系统测试失败: 缺少 plyer 库\n💡 请运行: pip install plyer"
        
        import datetime
        
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        if test_type in ["basic", "both"]:
            # 测试基本通知
            notification.notify(  # type: ignore
                title="🧪 通知系统测试",
                message=f"基本通知测试成功！时间: {current_time}",
                timeout=5
            )
            
            if test_type == "basic":
                return f"✅ 基本通知测试完成\n⏰ 测试时间: {current_time}\n💡 如果您看到了桌面通知，说明系统工作正常"
        
        if test_type in ["advanced", "both"]:
            # 测试高级通知
            notification.notify(  # type: ignore
                title="🚀 高级通知测试",
                message=f"高级通知功能测试成功！时间: {current_time}",
                timeout=8,
                app_name="AI通知测试"
            )
            
            if test_type == "advanced":
                return f"✅ 高级通知测试完成\n⏰ 测试时间: {current_time}\n💡 如果您看到了桌面通知，说明系统工作正常"
        
        if test_type == "both":
            return f"✅ 通知系统全面测试完成\n⏰ 测试时间: {current_time}\n📋 已测试: 基本通知 + 高级通知\n💡 如果您看到了两个桌面通知，说明系统工作正常"
        
        # 默认返回值（如果没有匹配的test_type）
        return f"❌ 未知的测试类型: {test_type}\n💡 支持的类型: basic, advanced, both"
        
    except Exception as e:
        return f"❌ 通知系统测试失败: {str(e)}"

@register_tool(
    name="get_notification_platform_info",
    description="获取当前平台的通知系统信息和支持情况",
    schema={
        "type": "object",
        "properties": {}
    }
)
def get_notification_platform_info() -> str:
    """获取平台通知信息"""
    try:
        import platform
        import sys
        
        system = platform.system()
        version = platform.version()
        python_version = sys.version
        
        result = f"🖥️ 平台通知系统信息\n"
        result += "=" * 40 + "\n\n"
        result += f"💻 操作系统: {system}\n"
        result += f"📋 系统版本: {version}\n"
        result += f"🐍 Python版本: {python_version}\n\n"
        
        # 检查plyer库
        try:
            from plyer import notification
            result += f"✅ plyer库: 已安装\n"
            
            # 尝试获取平台特定信息
            if system == "Windows":
                result += f"🪟 Windows通知: 支持Windows 10/11原生通知\n"
                result += f"📦 依赖: plyer (已安装)\n"
                result += f"🔧 通知方式: Windows Toast通知\n"
                
            elif system == "Darwin":  # macOS
                result += f"🍎 macOS通知: 支持原生通知中心\n"
                result += f"📦 依赖: plyer + pyobjus\n"
                
                # 检查pyobjus
                try:
                    import pyobjus
                    result += f"✅ pyobjus: 已安装 (macOS通知支持)\n"
                except ImportError:
                    result += f"⚠️ pyobjus: 未安装 (建议安装以获得更好的macOS支持)\n"
                    result += f"💡 安装命令: pip install pyobjus\n"
                
                result += f"🔧 通知方式: macOS通知中心\n"
                
            elif system == "Linux":
                result += f"🐧 Linux通知: 支持libnotify/D-Bus通知\n"
                result += f"📦 依赖: plyer + libnotify\n"
                result += f"🔧 通知方式: D-Bus桌面通知\n"
                result += f"💡 可能需要安装: sudo apt-get install libnotify-bin (Ubuntu/Debian)\n"
                
            else:
                result += f"❓ 未知系统: {system}\n"
                result += f"🔧 通知方式: plyer会尝试自动检测\n"
            
        except ImportError:
            result += f"❌ plyer库: 未安装\n"
            result += f"💡 安装命令: pip install plyer\n"
            
            if system == "Darwin":
                result += f"💡 macOS额外依赖: pip install pyobjus\n"
        
        result += f"\n🌐 跨平台支持:\n"
        result += f"  • Windows 10/11: ✅ 原生Toast通知\n"
        result += f"  • macOS: ✅ 通知中心集成\n"
        result += f"  • Linux: ✅ libnotify/D-Bus通知\n"
        result += f"  • 其他平台: ⚠️ 有限支持\n"
        
        return result
        
    except Exception as e:
        return f"❌ 获取平台信息失败: {str(e)}"

@register_tool(
    name="send_smart_notification",
    description="发送智能跨平台通知，自动适配不同操作系统的最佳通知方式",
    schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "通知标题"
            },
            "message": {
                "type": "string",
                "description": "通知消息内容"
            },
            "timeout": {
                "type": "integer",
                "description": "通知显示时长（秒），默认10秒",
                "default": 10,
                "minimum": 1,
                "maximum": 300
            },
            "priority": {
                "type": "string",
                "description": "通知优先级",
                "enum": ["low", "normal", "high", "urgent"],
                "default": "normal"
            },
            "app_name": {
                "type": "string",
                "description": "应用名称，默认为'Alice '",
                "default": "Alice "
            }
        },
        "required": ["title", "message"]
    }
)
def send_smart_notification(title: str, message: str, timeout: int = 10, 
                          priority: str = "normal", app_name: str = "Alice ") -> str:
    """发送智能跨平台通知"""
    try:
        try:
            from plyer import notification
        except ImportError:
            return "❌ 发送通知失败: 缺少 plyer 库\n💡 请运行: pip install plyer"
        
        import platform
        import os
        
        system = platform.system()
        
        # 准备基础通知参数
        notify_kwargs = {
            "title": title,
            "message": message,
            "timeout": timeout,
            "app_name": app_name
        }
        
        # 根据平台和优先级调整参数
        if system == "Windows":
            # Windows特定优化
            if priority == "urgent":
                notify_kwargs["timeout"] = min(timeout * 2, 60)  # 紧急通知显示更久
            
        elif system == "Darwin":  # macOS
            # macOS特定优化
            try:
                import pyobjus
                # 如果有pyobjus，可以使用更高级的macOS通知功能
                if priority in ["high", "urgent"]:
                    # 高优先级通知可能需要特殊处理
                    pass
            except ImportError:
                pass
                
        elif system == "Linux":
            # Linux特定优化
            if priority == "urgent":
                # Linux上可以设置urgency级别
                try:
                    # 某些Linux发行版支持urgency参数
                    notify_kwargs["urgency"] = "critical"
                except:
                    pass
        
        # 发送通知
        notification.notify(**notify_kwargs)  # type: ignore
        
        # 构建返回信息
        result = f"✅ 智能通知已发送\n"
        result += f"🖥️ 平台: {system}\n"
        result += f"📋 标题: {title}\n"
        result += f"💬 内容: {message}\n"
        result += f"⏰ 显示时长: {timeout}秒\n"
        result += f"📱 应用名称: {app_name}\n"
        result += f"🚨 优先级: {priority}\n"
        
        # 平台特定提示
        if system == "Windows":
            result += f"🪟 Windows: 使用原生Toast通知\n"
        elif system == "Darwin":
            result += f"🍎 macOS: 使用通知中心\n"
        elif system == "Linux":
            result += f"🐧 Linux: 使用D-Bus通知\n"
        
        return result
        
    except Exception as e:
        return f"❌ 发送智能通知失败: {str(e)}\n💡 请检查平台兼容性或运行 get_notification_platform_info 获取详细信息"

 