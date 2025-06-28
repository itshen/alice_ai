"""
核心ChatBot类 - 整合所有功能
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
from .models import model_manager
from .tool_manager import tool_registry
from .database import db
from .xml_parser import xml_parser
from .user_confirmation import user_confirmation_manager, UserConfirmationRequired

class ChatBot:
    """AI聊天机器人核心类"""
    
    def __init__(self, provider: str | None = None, debug: bool = False, max_turns: Optional[int] = None, web_mode: bool = False):
        """
        初始化聊天机器人
        
        Args:
            provider: 模型提供商 (ollama, qwen, openrouter)，如果为None则使用配置的默认提供商
            debug: 是否启用调试模式，显示工具执行过程信息
            max_turns: 最大对话轮数，如果为None则使用配置文件中的默认值
            web_mode: 是否为Web模式，Web模式下用户确认会通过前端处理
        """
        self.provider = provider or model_manager.get_default_provider_name()
        self.current_session_id = None
        self.debug = debug
        self.max_turns = max_turns  # 保存最大轮数设置
        self.web_mode = web_mode
        
        # 设置用户确认管理器的Web模式
        user_confirmation_manager.set_web_mode(web_mode)
        
        # 如果指定的提供商不可用，使用默认提供商
        if self.provider and self.provider not in model_manager.list_adapters():
            print(f"⚠️  指定的提供商 '{self.provider}' 不可用，使用默认提供商")
            self.provider = model_manager.get_default_provider_name()
    
    def _get_max_turns(self) -> int:
        """获取最大对话轮数"""
        if self.max_turns is not None:
            return self.max_turns
        
        # 从配置中获取默认值
        from .config import config
        return config.get("default_max_turns", 20) or 20
    
    def set_provider(self, provider: str):
        """设置模型提供商"""
        if provider not in model_manager.list_adapters():
            raise ValueError(f"不支持的提供商: {provider}")
        self.provider = provider
        print(f"✅ 已切换到模型提供商: {provider}")
    
    def switch_model(self, provider: str) -> bool:
        """切换模型提供商"""
        try:
            self.set_provider(provider)
            return True
        except ValueError as e:
            print(f"❌ 切换模型失败: {e}")
            return False
    
    def get_current_provider_info(self) -> Dict[str, Any]:
        """获取当前提供商信息"""
        if not self.provider:
            return {"error": "没有可用的模型提供商"}
        
        adapter = self._get_adapter()
        return {
            "provider": self.provider,
            "model": getattr(adapter, 'model', 'unknown'),
            "available_providers": model_manager.list_adapters(),
            "is_default": self.provider == model_manager.get_default_provider_name()
        }
    
    def list_available_models(self) -> Dict[str, Any]:
        """列出所有可用的模型"""
        return model_manager.get_provider_info()
    
    def create_session(self, title: str = "新对话") -> str:
        """创建新会话"""
        session_id = db.create_session(
            title=title,
            model_provider=self.provider or "unknown",
            model_name=self._get_current_model_name()
        )
        self.current_session_id = session_id
        return session_id
    
    def load_session(self, session_id: str):
        """加载会话"""
        session = db.get_session(session_id)
        if not session:
            raise ValueError(f"会话 {session_id} 不存在")
        self.current_session_id = session_id
        # 注意：不自动切换提供商，保持用户当前选择
        # self.provider = session.get('model_provider', self.provider)
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话"""
        return db.get_sessions()
    
    def get_session_messages(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取会话消息"""
        effective_session_id = session_id or self.current_session_id
        if not effective_session_id:
            return []
        return db.get_messages(effective_session_id)
    
    async def chat_stream(self, message: str, session_id: Optional[str] = None, tools: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        """流式聊天"""
        # 确定会话
        if session_id:
            self.load_session(session_id)
        elif not self.current_session_id:
            # 优先使用最近的会话而不是创建新会话
            recent_sessions = db.get_sessions()
            if recent_sessions:
                # 按更新时间排序，使用最近的会话
                recent_sessions.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
                most_recent_session = recent_sessions[0]
                self.load_session(most_recent_session["id"])
                if self.debug:
                    print(f"🔄 自动加载最近会话: {most_recent_session.get('title', '未命名会话')} (ID: {most_recent_session['id']})")
            else:
                # 只有在没有任何会话时才创建新会话
                self.create_session("默认对话")
                if self.debug:
                    print(f"🆕 创建新的默认会话: {self.current_session_id}")
        
        # 获取适配器
        adapter = self._get_adapter()
        
        # 获取工具schema
        tool_schemas = self._get_tool_schemas(tools)
        
        # 保存用户消息
        db.add_message(self.current_session_id, "user", message)
        
        # 多轮对话循环，直到没有工具调用
        # 使用_build_messages_from_history()而不是_build_messages()，避免重复添加刚保存的消息
        current_messages = self._build_messages_from_history()
        max_rounds = 30  # 防止无限循环
        round_count = 0
        
        while round_count < max_rounds:
            round_count += 1
            
            # 流式生成响应
            full_response = ""
            tool_calls_found = []
            response_buffer = ""  # 添加缓冲区
            
            async for chunk in adapter.chat_stream(current_messages, tool_schemas):
                full_response += chunk
                response_buffer += chunk
                
                # 处理thinking标签，合并成一对完整的标签
                if "<thinking>" in chunk:
                    # 开始thinking模式
                    if not hasattr(self, '_thinking_mode'):
                        self._thinking_mode = True
                        self._thinking_content = ""
                        yield "<thinking>"
                    
                    # 提取thinking内容
                    import re
                    thinking_matches = re.findall(r'<thinking>(.*?)</thinking>', chunk, re.DOTALL)
                    for thinking_content in thinking_matches:
                        self._thinking_content += thinking_content
                        yield thinking_content
                    
                    # 移除thinking标签，保留其他内容
                    chunk = re.sub(r'<thinking>.*?</thinking>', '', chunk, flags=re.DOTALL)
                    if chunk.strip():
                        yield chunk
                else:
                    # 如果之前在thinking模式，现在没有thinking标签了，结束thinking
                    if hasattr(self, '_thinking_mode') and self._thinking_mode:
                        yield "</thinking>"
                        self._thinking_mode = False
                        self._thinking_content = ""
                    
                    # 输出正常内容
                    if chunk.strip():
                        yield chunk
                
                # 实时检查是否有完整的工具调用
                # 这样可以更快地检测到工具调用
                if "<tool_call>" in response_buffer and "</tool_call>" in response_buffer:
                    # 尝试提取完整的工具调用
                    temp_calls = xml_parser.extract_tool_calls(response_buffer)
                    if temp_calls and not tool_calls_found:
                        # 找到完整的工具调用，可以提前处理
                        pass
            
            # 检查完整响应中是否包含工具调用
            tool_calls_found = xml_parser.extract_tool_calls(full_response)
            
            # 检查是否刚刚执行过工具调用（避免无限循环）
            recent_messages = current_messages[-3:] if len(current_messages) >= 3 else current_messages
            has_recent_tool_result = any("<TOOL_RESULT>" in msg.get("content", "") for msg in recent_messages)
            
            # 保存助手消息
            db.add_message(self.current_session_id, "assistant", full_response, tool_calls_found if tool_calls_found else None)
            
            # 如果没有工具调用，结束对话
            if not tool_calls_found:
                break
            
            # 执行工具调用
            try:
                print(f"🔧 [DEBUG] 开始执行工具调用: {[tc.get('function', {}).get('name') for tc in tool_calls_found]}")
                tool_results = await self._execute_tool_calls(tool_calls_found)
                print(f"✅ [DEBUG] 工具调用完成，结果数量: {len(tool_results)}")
            except UserConfirmationRequired as e:
                # 在流式模式下，用户确认异常应该向上传播到API层处理
                print(f"🔒 [DEBUG] 捕获到用户确认请求: {e.tool_name}, ID: {e.confirmation_id}")
                raise
            
            # 显示工具调用结果（带分割线和详细格式）
            yield "\n" + "="*20 + " 🔧 AI工具调用 " + "="*20 + "\n"
            
            for tool_call, result in zip(tool_calls_found, tool_results):
                yield f"\n<TOOL_RESULT>\n{result.to_detailed_string()}\n</TOOL_RESULT>\n"
            
            yield "="*20 + " 🔧 调用完成 " + "="*20 + "\n"
            
            # 构建工具结果消息
            tool_result_message = ""
            for tool_call, result in zip(tool_calls_found, tool_results):
                # 使用详细格式的工具结果
                tool_result_message += f"\n<TOOL_RESULT>\n{result.to_detailed_string()}\n</TOOL_RESULT>\n"
            
            # 将工具结果作为用户消息添加到对话历史中
            db.add_message(self.current_session_id, "user", tool_result_message)
            
            # 更新消息历史，准备下一轮对话
            current_messages = self._build_messages_from_history()
        
        if round_count >= max_rounds:
            yield f"\n[达到最大轮次限制 {max_rounds}，对话结束]"
    
    async def chat(self, message: str, session_id: Optional[str] = None, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """非流式聊天"""
        # 确定会话
        if session_id:
            self.load_session(session_id)
        elif not self.current_session_id:
            # 优先使用最近的会话而不是创建新会话
            recent_sessions = db.get_sessions()
            if recent_sessions:
                # 按更新时间排序，使用最近的会话
                recent_sessions.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
                most_recent_session = recent_sessions[0]
                self.load_session(most_recent_session["id"])
                if self.debug:
                    print(f"🔄 自动加载最近会话: {most_recent_session.get('title', '未命名会话')} (ID: {most_recent_session['id']})")
            else:
                # 只有在没有任何会话时才创建新会话
                self.create_session("默认对话")
                if self.debug:
                    print(f"🆕 创建新的默认会话: {self.current_session_id}")
        
        # 获取适配器
        adapter = self._get_adapter()
        
        # 获取工具schema
        tool_schemas = self._get_tool_schemas(tools)
        
        # 保存用户消息
        db.add_message(self.current_session_id, "user", message)
        
        # 多轮对话循环，直到没有工具调用
        # 使用_build_messages_from_history()而不是_build_messages()，避免重复添加刚保存的消息
        current_messages = self._build_messages_from_history()
        max_rounds = 10  # 防止无限循环
        round_count = 0
        final_message = ""
        all_tool_calls = []
        all_tool_results = []
        
        while round_count < max_rounds:
            round_count += 1
            
            # 获取响应
            response = await adapter.chat(current_messages, tool_schemas)
            
            # 解析响应
            assistant_message = self._extract_message_from_response(response)
            final_message += assistant_message
            
            # 检查工具调用
            tool_calls = xml_parser.extract_tool_calls(assistant_message)
            
            # 检查是否刚刚执行过工具调用（避免无限循环）
            recent_messages = current_messages[-3:] if len(current_messages) >= 3 else current_messages
            has_recent_tool_result = any("<TOOL_RESULT>" in msg.get("content", "") for msg in recent_messages)
            
            # 保存助手消息
            db.add_message(self.current_session_id, "assistant", assistant_message, tool_calls if tool_calls else None)
            
            # 如果没有工具调用，结束对话
            if not tool_calls:
                break
            
            # 执行工具调用
            tool_results = await self._execute_tool_calls(tool_calls)
            all_tool_calls.extend(tool_calls)
            all_tool_results.extend(tool_results)
            
            # 构建工具结果消息
            tool_result_message = ""
            for tool_call, result in zip(tool_calls, tool_results):
                # 使用详细格式的工具结果
                tool_result_message += f"\n<TOOL_RESULT>\n{result.to_detailed_string()}\n</TOOL_RESULT>\n"
            
            # 将工具结果作为用户消息添加到对话历史中
            db.add_message(self.current_session_id, "user", tool_result_message)
            
            # 更新消息历史，准备下一轮对话
            current_messages = self._build_messages_from_history()
        
        return {
            "message": final_message,
            "tool_calls": all_tool_calls,
            "tool_results": all_tool_results,
            "session_id": self.current_session_id,
            "rounds": round_count
        }
    
    def _get_adapter(self):
        """获取当前适配器"""
        if not self.provider:
            # 使用模型管理器的默认适配器选择逻辑
            adapter = model_manager.get_default_adapter()
            if adapter:
                self.provider = model_manager.get_default_provider_name()
                return adapter
            else:
                raise ValueError("没有可用的模型适配器")
        
        adapter = model_manager.get_adapter(self.provider)
        if not adapter:
            # 如果当前提供商不可用，尝试使用默认适配器
            print(f"⚠️  提供商 '{self.provider}' 不可用，尝试使用默认提供商")
            adapter = model_manager.get_default_adapter()
            if adapter:
                self.provider = model_manager.get_default_provider_name()
                return adapter
            else:
                raise ValueError(f"适配器 {self.provider} 不可用，且没有可用的备用适配器")
        
        return adapter
    
    def _get_current_model_name(self) -> str:
        """获取当前模型名称"""
        try:
            adapter = self._get_adapter()
            return adapter.model
        except:
            return "unknown"
    
    def _build_messages(self, new_message: str) -> List[Dict[str, Any]]:
        """构建消息历史
        
        注意：此方法会将new_message添加到消息列表中，因此不应该在
        已经通过db.add_message()保存消息后使用，以避免重复。
        如果消息已保存到数据库，请使用_build_messages_from_history()。
        """
        messages = []
        
        # 获取用户偏好记忆
        preference_memory = self._load_user_preferences_memory()
        
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建系统消息，包含记忆内容
        system_content = f"""
我是由洛小山开发的，功能强大的AI应用助手，不仅能够高效解答用户问题，更具备强大的工具调用能力。
通过灵活调用各类工具，精准获取所需信息，从而高效满足用户的多样化需求。

当前时间: {current_time}

当你不知道有什么工具的时候，请你尽快调用 `list_tool_modules` 工具查看所有可用工具模块。

# 工具使用规范

1. 工具调用约束
   - 每次回复只能调用一个工具
   - 工具调用必须在回复的最后
   - 先完成分析和说明，再调用工具

2. 工具调用格式
   - 严格使用XML格式：
   ```
   <tool_call>
   <name>工具名</name>
   <parameters>
   {{
     "参数名": "参数值"
   }}
   </parameters>
   </tool_call>
   ```
   - 参数必须是有效JSON：使用双引号，正确转义特殊字符
   - 确保格式完整，不能分片

3. 基本流程
   - 第一步：如需要特定功能，先用 `list_tool_modules` 查看可用模块
   - 第二步：使用 `activate_tool_modules` 激活所需模块
   - 第三步：调用模块中的具体工具完成任务

4. 核心工具
   - `list_tool_modules` - 查看所有可用工具模块
   - `activate_tool_modules` - 激活指定模块
   - `list_available_tools` - 查看当前可用的所有工具

5. 记忆管理系统
   - `save_memory` - 保存重要信息到用户记忆中
   - `read_all_memories` - 读取所有已保存的用户记忆
   - `find_user_memories` - 通过关键词搜索已保存的记忆
   
   记忆使用指南：
   - 用户提到重要偏好、习惯、项目信息时，主动保存到记忆
   - 对话开始时，可以搜索相关记忆了解用户背景
   - 记忆分类：user_preference(用户偏好)、project_info(项目信息)、task(任务记录)、knowledge(知识积累)、conversation(对话记录)、general(一般信息)、personal_info(个人信息)

6. 错误处理
   - 工具调用失败时，检查模块是否已激活
   - 确认工具名称和参数格式正确
   - 必要时重新激活模块

重要：每次只能调用一个工具，且必须在回复最后！先分析问题，再调用工具！"""

        # 如果有用户偏好记忆，添加到系统消息中
        if preference_memory:
            system_content += preference_memory

        # 添加系统消息
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # 添加历史消息
        if self.current_session_id:
            history = db.get_messages(self.current_session_id)
            for msg in history[-10:]:  # 只取最近10条消息
                if msg['role'] in ['user', 'assistant']:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
        
        # 添加新消息
        messages.append({
            "role": "user",
            "content": new_message
        })
        
        return messages
    
    def _get_tool_schemas(self, tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取工具schemas"""
        if tools:
            # 如果指定了特定工具，返回这些工具的schema
            schemas = []
            for tool_name in tools:
                try:
                    schema = tool_registry.get_tool_schema(tool_name)
                    schemas.append(schema)
                except ValueError:
                    continue  # 忽略不存在的工具
            return schemas
        
        # 返回内置工具 + 激活的模块工具
        schemas = []
        
        # 1. 添加内置工具
        builtin_tools = tool_registry.get_builtin_tools()
        for tool in builtin_tools:
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool['name'],
                    "description": tool['description'],
                    "parameters": tool['schema']
                }
            })
        
        # 2. 添加激活的模块工具
        from .tool_module_manager import tool_module_manager
        active_module_tools = tool_module_manager.get_active_tools()
        
        # 过滤掉内置工具（避免重复）
        builtin_tool_names = {tool['name'] for tool in builtin_tools}
        for tool in active_module_tools:
            if tool['name'] not in builtin_tool_names:
                schemas.append({
                    "type": "function",
                    "function": {
                        "name": tool['name'],
                        "description": tool['description'],
                        "parameters": tool['schema']
                    }
                })
        
        return schemas
    
    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Any]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            try:
                function_info = tool_call.get("function", {})
                tool_name = function_info.get("name")
                arguments_str = function_info.get("arguments", "{}")
                
                # 解析参数
                try:
                    if isinstance(arguments_str, str):
                        arguments = json.loads(arguments_str)
                    else:
                        arguments = arguments_str  # 已经是字典
                except json.JSONDecodeError:
                    arguments = {}
                
                # 执行工具
                tool_result = await tool_registry.execute(tool_name, arguments)
                
                # 直接返回ToolResult对象，保留完整信息
                results.append(tool_result)
                
            except UserConfirmationRequired:
                # 在Web模式下，用户确认异常应该直接向上传播，不在这里处理
                raise
            except Exception as e:
                # 创建错误的ToolResult对象
                from .tool_manager import ToolResult, ErrorCodes
                error_result = ToolResult(
                    tool_name=tool_name or "unknown",
                    parameters=arguments if 'arguments' in locals() else {},
                    success=False,
                    data="",
                    error_code=ErrorCodes.EXECUTION_ERROR,
                    error_message=f"工具调用失败: {str(e)}",
                    execution_time=0.0
                )
                results.append(error_result)
        
        return results
    
    def _extract_message_from_response(self, response: Dict[str, Any]) -> str:
        """从响应中提取消息内容"""
        # 适配不同模型的响应格式
        if "choices" in response:
            # OpenAI格式
            return response["choices"][0]["message"]["content"]
        elif "output" in response:
            # Qwen格式
            message = response["output"]["choices"][0]["message"]
            content = ""
            
            # 处理thinking内容 (通义千问使用reasoning_content字段)
            if message.get("reasoning_content"):
                content += f"<thinking>{message['reasoning_content']}</thinking>\n\n"
            
            # 处理正常内容
            if message.get("content"):
                content += message["content"]
                
            return content
        elif "message" in response:
            # Ollama格式
            return response["message"]["content"]
        else:
            return str(response)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return tool_registry.list_tools()
    
    def list_providers(self) -> List[str]:
        """列出所有可用的模型提供商"""
        return model_manager.list_adapters()
    
    def _build_messages_from_history(self) -> List[Dict[str, Any]]:
        """从历史记录构建消息列表"""
        messages = []
        
        # 获取用户偏好记忆
        preference_memory = self._load_user_preferences_memory()
        
        # 获取当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建系统消息，包含记忆内容
        system_content = f"""
我是由洛小山开发的，功能强大的AI应用助手，不仅能够高效解答用户问题，更具备强大的工具调用能力。
通过灵活调用各类工具，精准获取所需信息，从而高效满足用户的多样化需求。

当前时间: {current_time}

当你不知道有什么工具的时候，请你尽快调用 `list_tool_modules` 工具查看所有可用工具模块。

# 工具使用规范

1. 工具调用约束
   - 每次回复只能调用一个工具
   - 工具调用必须在回复的最后
   - 先完成分析和说明，再调用工具

2. 工具调用格式
   - 严格使用XML格式：
   ```
   <tool_call>
   <name>工具名</name>
   <parameters>
   {{
     "参数名": "参数值"
   }}
   </parameters>
   </tool_call>
   ```
   - 参数必须是有效JSON：使用双引号，正确转义特殊字符
   - 确保格式完整，不能分片

3. 基本流程
   - 第一步：如需要特定功能，先用 `list_tool_modules` 查看可用模块
   - 第二步：使用 `activate_tool_modules` 激活所需模块
   - 第三步：调用模块中的具体工具完成任务

4. 核心工具
   - `list_tool_modules` - 查看所有可用工具模块
   - `activate_tool_modules` - 激活指定模块
   - `list_available_tools` - 查看当前可用的所有工具

5. 记忆管理系统
   - `save_memory` - 保存重要信息到用户记忆中
   - `read_all_memories` - 读取所有已保存的用户记忆
   - `find_user_memories` - 通过关键词搜索已保存的记忆
   
   记忆使用指南：
   - 用户提到重要偏好、习惯、项目信息时，主动保存到记忆
   - 对话开始时，可以搜索相关记忆了解用户背景
   - 记忆分类：user_preference(用户偏好)、project_info(项目信息)、task(任务记录)、knowledge(知识积累)、conversation(对话记录)、general(一般信息)

6. 错误处理
   - 工具调用失败时，检查模块是否已激活
   - 确认工具名称和参数格式正确
   - 必要时重新激活模块

重要：每次只能调用一个工具，且必须在回复最后！先分析问题，再调用工具！"""

        # 如果有用户偏好记忆，添加到系统消息中
        if preference_memory:
            system_content += preference_memory

        # 添加系统消息
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # 添加历史消息
        if self.current_session_id:
            history = db.get_messages(self.current_session_id)
            processed_history = []
            
            # 取最近20条消息，支持更长的对话
            recent_messages = history[-20:] if len(history) > 20 else history
            
            # 过滤处理历史消息
            for i, msg in enumerate(recent_messages):
                if msg['role'] in ['user', 'assistant']:
                    # 从配置获取保留的消息数量
                    from .config import config
                    keep_recent_messages = config.get("token_optimization.keep_recent_messages", 5)
                    
                    # 检查是否是最近几条消息（保持不变）
                    is_recent_message = i >= len(recent_messages) - keep_recent_messages
                    
                    # 过滤工具结果内容
                    filtered_content = self._filter_tool_results_for_token_saving(
                        msg['content'], 
                        is_recent_message
                    )
                    
                    processed_history.append({
                        "role": msg['role'],
                        "content": filtered_content
                    })
            
            messages.extend(processed_history)
        
        return messages
    
    def _filter_tool_results_for_token_saving(self, content: str, is_recent_message: bool) -> str:
        """
        过滤工具结果内容以节省Token
        
        Args:
            content: 原始消息内容
            is_recent_message: 是否是最近几条消息之内
            
        Returns:
            过滤后的消息内容
        """
        # 从配置中获取设置
        from .config import config
        
        # 检查是否启用 Token 优化
        if not config.get("token_optimization.enabled", True):
            return content
        
        # 检查是否启用工具结果过滤
        if not config.get("token_optimization.filter_old_tool_results", True):
            return content
        
        # 如果是最近几条消息，不进行过滤
        if is_recent_message:
            return content
        
        import re
        
        # 从配置获取需要过滤的工具列表和阈值
        filter_tools = config.get("token_optimization.filter_tools", ["list_tool_modules", "list_available_tools"])
        filter_threshold = config.get("token_optimization.filter_threshold", 1000)
        
        # 查找工具调用结果
        tool_result_pattern = r'<TOOL_RESULT>\s*(.*?)\s*</TOOL_RESULT>'
        
        def replace_tool_result(match):
            tool_result_content = match.group(1)
            
            # 检查是否是 list_tool_modules 工具的结果
            if "list_tool_modules" in filter_tools:
                is_list_tool_modules = any([
                    '📦 工具模块列表' in tool_result_content,
                    'list_tool_modules' in tool_result_content,
                    ('工具模块列表' in tool_result_content and '个模块' in tool_result_content),
                    ('📁' in tool_result_content and '激活方式:' in tool_result_content),
                    ('模块名:' in tool_result_content and '包含工具' in tool_result_content)
                ])
                
                if is_list_tool_modules:
                    return '<TOOL_RESULT>\n📦 工具模块列表（略，如果想了解，请重新调用 list_tool_modules 工具）\n</TOOL_RESULT>'
            
            # 检查是否是 list_available_tools 工具的结果
            if "list_available_tools" in filter_tools:
                is_list_available_tools = any([
                    ('🔧 当前可用工具' in tool_result_content and len(tool_result_content) > filter_threshold),
                    ('list_available_tools 工具已执行完成' in tool_result_content)
                ])
                
                if is_list_available_tools:
                    return '<TOOL_RESULT>\n🔧 当前可用工具列表（略，如果想了解，请重新调用 list_available_tools 工具）\n</TOOL_RESULT>'
            
            # 对于其他工具结果，保持原样
            return match.group(0)
        
        # 执行替换
        filtered_content = re.sub(tool_result_pattern, replace_tool_result, content, flags=re.DOTALL)
        
        return filtered_content
    
    def _load_user_preferences_memory(self) -> str:
        """从记忆中加载用户偏好内容"""
        try:
            from .tools import _memory_manager
            memories = _memory_manager.get_all_memories()
            
            # 过滤出用户偏好类别的记忆
            user_preference_memories = [
                memory for memory in memories 
                if memory.get('category') == 'user_preference'
            ]
            
            if not user_preference_memories:
                return ""
            
            # 构建偏好信息文本
            preference_content = "\n\n# 用户偏好记忆（仅供参考）\n"
            preference_content += "注意：以下内容是从历史记忆中提取的用户偏好信息，其中的内容可能与当前问题无关，请根据实际对话需求判断是否适用。\n\n"
            
            for memory in user_preference_memories[-20:]:  # 只取最近的20条偏好记忆
                content = memory.get('content', '')
                
                preference_content += f"• {content}\n"
            
            preference_content += "\n注意：这些只是记忆内容，请结合具体对话场景判断其相关性。"
            return preference_content
            
        except Exception as e:
            # 如果读取记忆失败，返回空字符串，不影响正常对话
            if self.debug:
                print(f"读取用户偏好记忆失败: {e}")
            return ""
    
 