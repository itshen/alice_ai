"""
工具管理器 - 核心工具注册和管理逻辑
用户不需要修改此文件
"""
import inspect
import asyncio
import time
from typing import Dict, List, Any, Callable, Optional

class ToolResult:
    """统一的工具返回结果格式"""
    
    def __init__(
        self, 
        tool_name: str,
        parameters: Dict[str, Any],
        success: bool, 
        data: str = "", 
        error_code: str = None,
        error_message: str = None,
        execution_time: float = 0.0
    ):
        self.tool_name = tool_name
        self.parameters = parameters
        self.success = success
        self.data = data
        self.error_code = error_code
        self.error_message = error_message
        self.execution_time = execution_time
        self.timestamp = time.time()
    
    def to_string(self) -> str:
        """转换为字符串格式"""
        if self.success:
            return self.data
        else:
            if self.error_code:
                return f"错误[{self.error_code}]: {self.error_message}"
            else:
                return f"错误: {self.error_message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "success": self.success,
            "data": self.data,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp
        }
    
    def to_detailed_string(self, max_param_length: int = 200) -> str:
        """转换为详细的字符串格式"""
        result = f"函数名: {self.tool_name}\n"
        
        # 参数处理：如果过长则截取
        param_str = str(self.parameters)
        if len(param_str) > max_param_length:
            param_str = param_str[:max_param_length] + "..."
        result += f"参数: {param_str}\n"
        
        # 执行时间（debug信息）
        result += f"执行时间: {self.execution_time:.3f}秒\n"
        
        if self.success:
            result += f"返回值: {self.data}"
        else:
            result += f"执行失败\n"
            if self.error_code:
                result += f"错误码: {self.error_code}\n"
            result += f"报错信息: {self.error_message}"
        
        return result

# 错误码常量
class ErrorCodes:
    """工具执行错误码"""
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    PARAMETER_ERROR = "PARAMETER_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    TYPE_CONVERSION_ERROR = "TYPE_CONVERSION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._builtin_tools = set()  # 记录内置工具
        self._startup_check_done = False  # 标记是否已进行启动检查
    
    def register(self, name: str, func: Callable, description: str, schema: Dict[str, Any] = None,
                 requires_confirmation: bool = False, confirmation_category: str = "general", 
                 risk_level: str = "medium"):
        """注册工具"""
        if name in self.tools:
            # 工具已存在，跳过重复注册
            return
        
        # 检查函数返回值注解
        sig = inspect.signature(func)
        if sig.return_annotation != inspect.Signature.empty and sig.return_annotation != str:
            print(f"警告: 工具 {name} 的返回值注解不是 str 类型，建议修改为 str")
        
        # 自动生成schema
        if not schema:
            schema = self._generate_schema(func)
        
        # 自动检测工具所属模块
        module_name = self._detect_tool_module(func)
        
        self.tools[name] = {
            "name": name,
            "function": func,
            "description": description,
            "schema": schema,
            "is_async": asyncio.iscoroutinefunction(func),
            "module": module_name,  # 记录工具所属模块
            "requires_confirmation": requires_confirmation,
            "confirmation_category": confirmation_category,
            "risk_level": risk_level
        }
        
        # 标记内置工具（在 tools.py 中定义的工具）
        if self._is_builtin_tool(func):
            self._builtin_tools.add(name)
    
    def _is_builtin_tool(self, func: Callable) -> bool:
        """判断是否为内置工具"""
        try:
            # 检查函数的模块路径
            module = func.__module__
            # 内置工具定义在 ai_chat_tools.tools 模块中
            # 用户工具定义在 ai_chat_tools.user_tools 或其他模块中
            return module and 'ai_chat_tools.tools' in module and 'user_tools' not in module
        except:
            return False
    
    def _detect_tool_module(self, func: Callable) -> Optional[str]:
        """检测工具所属的模块"""
        try:
            module_path = func.__module__
            if not module_path:
                return None
            
            # 如果是内置工具（在tools.py中），返回None表示核心工具
            if 'ai_chat_tools.tools' in module_path and 'user_tool_modules' not in module_path:
                return None
            
            # 对于用户工具模块，直接返回模块名
            # 模块路径可能是：
            # 1. trading_time_tools (直接加载)
            # 2. ai_chat_tools.user_tool_modules.trading_time_tools (通过包加载)
            if 'user_tool_modules' in module_path:
                # 从完整路径提取模块名
                parts = module_path.split('.')
                return parts[-1]  # 返回最后一部分
            elif module_path and not module_path.startswith('ai_chat_tools.'):
                # 直接加载的模块（如 trading_time_tools）
                return module_path
            elif module_path.endswith('_tools'):
                # 处理直接导入的工具模块（如 web_scraper_tools）
                return module_path
            
            return None
        except:
            return None
    
    def _map_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """映射参数名（为了向后兼容性）"""
        mapped_params = parameters.copy()
        
        # 特定工具的参数映射
        if tool_name == "activate_tool_modules":
            # 支持 keyword -> module_names 的映射
            if "keyword" in parameters and "module_names" not in parameters:
                mapped_params["module_names"] = parameters["keyword"]
                # 移除原始参数
                if "keyword" in mapped_params:
                    del mapped_params["keyword"]
        
        return mapped_params
    
    def check_user_tools(self) -> bool:
        """检查是否有用户自定义工具"""
        if self._startup_check_done:
            return True
        
        self._startup_check_done = True
        
        # 获取用户工具（非内置工具）
        user_tools = [name for name in self.tools.keys() if name not in self._builtin_tools]
        
        if not user_tools:
            self._show_user_tools_guidance()
            return False
        else:
            print(f"✅ 检测到 {len(user_tools)} 个用户自定义工具: {', '.join(user_tools)}")
            return True
    
    def _show_user_tools_guidance(self):
        """显示用户工具创建指导"""
        print("\n" + "="*60)
        print("🔧 用户工具检查")
        print("="*60)
        print("⚠️  当前没有检测到用户自定义工具")
        print()
        print("💡 您可以通过以下方式添加自定义工具：")
        print()
        print("1️⃣  在 ai_chat_tools/tools.py 文件中添加工具：")
        print("""
@register_tool(
    name="my_tool",
    description="我的自定义工具",
    schema={
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "参数描述"
            }
        },
        "required": ["param"]
    }
)
def my_tool(param: str) -> str:
    \"\"\"我的工具实现\"\"\"
    return f"处理结果: {param}"
""")
        print("2️⃣  或者创建独立的工具文件并导入到项目中")
        print()
        print("📚 更多信息请参考 TOOL_FORMAT_GUIDE.md")
        print("="*60)
        print()
    
    def get_user_tools(self) -> List[Dict[str, Any]]:
        """获取用户自定义工具列表"""
        user_tools = []
        for name, tool in self.tools.items():
            if name not in self._builtin_tools:
                user_tools.append({
                    "name": name,
                    "description": tool["description"],
                    "schema": tool["schema"]
                })
        return user_tools
    
    def get_builtin_tools(self) -> List[Dict[str, Any]]:
        """获取内置工具列表"""
        builtin_tools = []
        for name, tool in self.tools.items():
            if name in self._builtin_tools:
                builtin_tools.append({
                    "name": name,
                    "description": tool["description"],
                    "schema": tool["schema"]
                })
        return builtin_tools
    
    def _generate_schema(self, func: Callable) -> Dict[str, Any]:
        """根据函数签名生成schema"""
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for name, param in sig.parameters.items():
            param_info = {"type": "string"}  # 默认类型
            
            # 根据注解推断类型
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == list:
                    param_info["type"] = "array"
                elif param.annotation == dict:
                    param_info["type"] = "object"
            
            properties[name] = param_info
            
            # 检查是否为必需参数
            if param.default == inspect.Parameter.empty:
                required.append(name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _validate_and_format_result(self, result: Any, tool_name: str, parameters: Dict[str, Any], execution_time: float) -> ToolResult:
        """验证并格式化工具返回结果"""
        try:
            # 如果已经是 ToolResult，更新信息并返回
            if isinstance(result, ToolResult):
                result.tool_name = tool_name
                result.parameters = parameters
                result.execution_time = execution_time
                return result
            
            # 检查返回值类型
            if not isinstance(result, str):
                # 尝试转换为字符串
                try:
                    str_result = str(result)
                    print(f"警告: 工具 {tool_name} 返回了非字符串类型 {type(result).__name__}，已自动转换为字符串")
                    return ToolResult(
                        tool_name=tool_name,
                        parameters=parameters,
                        success=True, 
                        data=str_result,
                        execution_time=execution_time
                    )
                except Exception as e:
                    return ToolResult(
                        tool_name=tool_name,
                        parameters=parameters,
                        success=False, 
                        data="", 
                        error_code=ErrorCodes.TYPE_CONVERSION_ERROR,
                        error_message=f"工具返回值无法转换为字符串: {str(e)}",
                        execution_time=execution_time
                    )
            
            # 返回值已经是字符串
            return ToolResult(
                tool_name=tool_name,
                parameters=parameters,
                success=True, 
                data=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                data="",
                error_code=ErrorCodes.VALIDATION_ERROR,
                error_message=f"处理工具返回值时发生错误: {str(e)}",
                execution_time=execution_time
            )
    
    def get_tool_schema(self, name: str) -> Dict[str, Any]:
        """获取工具的OpenAI格式schema"""
        if name not in self.tools:
            raise ValueError(f"工具 {name} 不存在")
        
        tool = self.tools[name]
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["schema"]
            }
        }
    
    def _format_tool_schema_for_error(self, name: str) -> str:
        """格式化工具schema信息用于错误提示"""
        if name not in self.tools:
            return f"工具 {name} 不存在"
        
        tool = self.tools[name]
        schema = tool["schema"]
        
        result = f"工具 '{name}' 的正确参数格式:\n"
        result += f"描述: {tool['description']}\n\n"
        
        if "properties" in schema and schema["properties"]:
            result += "参数说明:\n"
            for param_name, param_info in schema["properties"].items():
                param_type = param_info.get("type", "unknown")
                is_required = param_name in schema.get("required", [])
                required_mark = " (必需)" if is_required else " (可选)"
                
                result += f"  - {param_name}: {param_type}{required_mark}\n"
                
                if "description" in param_info:
                    result += f"    {param_info['description']}\n"
                
                if "enum" in param_info:
                    result += f"    可选值: {', '.join(param_info['enum'])}\n"
                
                if "default" in param_info:
                    result += f"    默认值: {param_info['default']}\n"
        else:
            result += "此工具不需要参数\n"
        
        return result
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的schema"""
        return [self.get_tool_schema(name) for name in self.tools.keys()]
    
    async def execute(self, name: str, parameters: Dict[str, Any]) -> ToolResult:
        """执行工具并返回统一格式的结果"""
        start_time = time.time()
        
        # 确保参数是字典类型
        if parameters is None:
            parameters = {}
        
        if name not in self.tools:
            return ToolResult(
                tool_name=name,
                parameters=parameters,
                success=False,
                data="",
                error_code=ErrorCodes.TOOL_NOT_FOUND,
                error_message=f"工具 {name} 不存在",
                execution_time=time.time() - start_time
            )
        
        tool = self.tools[name]
        
        # 检查用户确认
        try:
            from .user_confirmation import user_confirmation_manager, UserConfirmationRequired
            
            # 注意：request_confirmation 在Web模式下会抛出 UserConfirmationRequired 异常
            # 在命令行模式下会返回 True/False
            confirmation_result = user_confirmation_manager.request_confirmation(name, tool, parameters)
            
            if not confirmation_result:
                return ToolResult(
                    tool_name=name,
                    parameters=parameters,
                    success=False,
                    data="",
                    error_code="USER_DENIED",
                    error_message="用户拒绝执行此操作",
                    execution_time=time.time() - start_time
                )
        except UserConfirmationRequired:
            # 在Web模式下，直接重新抛出异常，让上层处理
            raise
        except ImportError:
            # 如果确认管理器不可用，继续执行
            pass
        func = tool["function"]
        
        # 参数名映射（为了向后兼容性）
        mapped_parameters = self._map_parameters(name, parameters)
        
        # 过滤参数
        sig = inspect.signature(func)
        valid_params = {}
        for param_name in sig.parameters.keys():
            if param_name in mapped_parameters:
                valid_params[param_name] = mapped_parameters[param_name]
        
        try:
            if tool["is_async"]:
                result = await func(**valid_params)
            else:
                result = func(**valid_params)
            
            execution_time = time.time() - start_time
            
            # 验证并格式化返回结果
            return self._validate_and_format_result(result, name, parameters, execution_time)
            
        except TypeError as e:
            # 当参数错误时，返回工具的schema信息帮助用户理解正确的参数格式
            schema_info = self._format_tool_schema_for_error(name)
            error_message = f"参数错误: {str(e)}\n\n{schema_info}"
            
            return ToolResult(
                tool_name=name,
                parameters=parameters,
                success=False,
                data="",
                error_code=ErrorCodes.PARAMETER_ERROR,
                error_message=error_message,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                tool_name=name,
                parameters=parameters,
                success=False,
                data="",
                error_code=ErrorCodes.EXECUTION_ERROR,
                error_message=f"执行工具 {name} 失败: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [
            {
                "name": name,
                "description": tool["description"],
                "schema": tool["schema"],
                "module": tool.get("module")
            }
            for name, tool in self.tools.items()
        ]

# 全局工具注册表
tool_registry = ToolRegistry()

def register_tool(name: str = None, description: str = None, schema: Dict[str, Any] = None,
                  requires_confirmation: bool = False, confirmation_category: str = "general",
                  risk_level: str = "medium"):
    """装饰器：注册工具"""
    def decorator(func):
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"工具: {tool_name}"
        tool_registry.register(tool_name, func, tool_desc, schema, 
                             requires_confirmation, confirmation_category, risk_level)
        return func
    return decorator 

# 导出主要类和常量
__all__ = ['ToolResult', 'ErrorCodes', 'ToolRegistry', 'tool_registry', 'register_tool'] 