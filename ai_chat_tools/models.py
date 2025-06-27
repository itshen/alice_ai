"""
模型适配器
"""
import json
import httpx
import asyncio
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from .config import config

class ModelAdapter(ABC):
    """模型适配器基类"""
    
    def __init__(self, **kwargs):
        self.config = kwargs
    
    @abstractmethod
    async def chat_stream(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> AsyncGenerator[str, None]:
        """流式聊天"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> Dict[str, Any]:
        """非流式聊天"""
        pass

class OllamaAdapter(ModelAdapter):
    """Ollama适配器"""
    
    def __init__(self, host: str, model: str, **kwargs):
        super().__init__(**kwargs)
        self.host = host.rstrip('/')
        self.model = model
    
    async def chat_stream(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Ollama流式聊天"""
        url = f"{self.host}/api/chat"
        
        # 构建请求数据
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        # 禁用原生工具支持，强制使用XML格式
        # if tools:
        #     data["tools"] = tools
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            if chunk.get("message", {}).get("content"):
                                yield chunk["message"]["content"]
                            
                            # 不输出原生工具调用，强制使用XML格式
                            
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
    
    async def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> Dict[str, Any]:
        """Ollama非流式聊天"""
        url = f"{self.host}/api/chat"
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        # 禁用原生工具支持，强制使用XML格式
        # if tools:
        #     data["tools"] = tools
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()

class QwenAdapter(ModelAdapter):
    """通义千问适配器"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    async def chat_stream(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Qwen流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        # 处理工具信息 - 拼接到prompt中
        processed_messages = self._process_messages_with_tools(messages, tools)
        
        data = {
            "model": self.model,
            "input": {"messages": processed_messages},
            "parameters": {
                "result_format": "message",
                "incremental_output": True,
                "stream": True,
                "enable_thinking": True
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.base_url, json=data, headers=headers) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        line_data = line[5:].strip()
                        if line_data == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(line_data)
                            
                            if chunk_data.get("output", {}).get("choices"):
                                choice = chunk_data["output"]["choices"][0]
                                message = choice.get("message", {})
                                
                                # 处理thinking内容 (通义千问使用reasoning_content字段)
                                if message.get("reasoning_content"):
                                    thinking_content = message['reasoning_content']
                                    yield f"<thinking>{thinking_content}</thinking>"
                                
                                # 处理正常内容
                                if message.get("content"):
                                    yield message["content"]
                        except json.JSONDecodeError:
                            continue
    
    async def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> Dict[str, Any]:
        """Qwen非流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 处理工具信息 - 拼接到prompt中
        processed_messages = self._process_messages_with_tools(messages, tools)
        
        data = {
            "model": self.model,
            "input": {"messages": processed_messages},
            "parameters": {
                "result_format": "message",
                "enable_thinking": True
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.base_url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
    
    def _process_messages_with_tools(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> List[Dict]:
        """将工具信息拼接到消息中"""
        if not tools:
            return messages
        
        # 构建详细的工具描述（包含完整schema）
        tools_description = f"\n\n📋 当前可用工具 ({len(tools)} 个)：\n"
        
        def format_tool_with_schema(tool):
            """格式化工具信息，包含完整schema"""
            func = tool["function"]
            tool_desc = f"\n🔧 {func['name']}\n"
            tool_desc += f"   描述: {func['description']}\n"
            
            # 添加参数schema信息
            schema = func.get('parameters', {})
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            if properties:
                tool_desc += f"   参数:\n"
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '无描述')
                    is_required = param_name in required
                    required_mark = "必需" if is_required else "可选"
                    
                    # 显示枚举值
                    if 'enum' in param_info:
                        enum_values = ', '.join(map(str, param_info['enum']))
                        tool_desc += f"     - {param_name} ({param_type}, {required_mark}): {param_desc}\n       可选值: [{enum_values}]\n"
                    # 显示默认值
                    elif 'default' in param_info:
                        default_val = param_info['default']
                        tool_desc += f"     - {param_name} ({param_type}, {required_mark}): {param_desc}\n       默认值: {default_val}\n"
                    else:
                        tool_desc += f"     - {param_name} ({param_type}, {required_mark}): {param_desc}\n"
                    
                    # 显示数组元素类型
                    if param_type == 'array' and 'items' in param_info:
                        items_type = param_info['items'].get('type', 'string')
                        tool_desc += f"       数组元素类型: {items_type}\n"
                    
                    # 显示数值范围
                    if param_type in ['integer', 'number']:
                        if 'minimum' in param_info:
                            tool_desc += f"       最小值: {param_info['minimum']}\n"
                        if 'maximum' in param_info:
                            tool_desc += f"       最大值: {param_info['maximum']}\n"
            else:
                tool_desc += f"   参数: 无需参数\n"
            
            return tool_desc
        
        for tool in tools:
            tools_description += format_tool_with_schema(tool)
        
        tools_description += "\n🔧 工具调用格式：<tool_call><name>工具名称</name><parameters>参数JSON</parameters></tool_call>\n"
        tools_description += "💡 请根据上述schema正确传递参数，确保参数类型和必需性符合要求\n"
        
        # 复制消息列表
        processed_messages = messages.copy()
        
        # 如果第一条是系统消息，追加工具信息
        if processed_messages and processed_messages[0].get("role") == "system":
            processed_messages[0]["content"] += tools_description
        else:
            
            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 否则插入新的系统消息
            system_message = {
                "role": "system",
                "content": f""""
我是由洛小山开发的，功能强大的AI应用助手，不仅能够高效解答用户问题，更具备强大的工具调用能力。
通过灵活调用各类工具，精准获取所需信息，从而高效满足用户的多样化需求。

当前时间: {current_time}

当你不知道有什么工具的时候，请你尽快调用 `list_tool_modules` 工具查看所有可用工具模块。

# 回答要求  
1. 用户需求识别
当用户提出任务需求时，我会首先判断是否需要调用工具：  
  - 直接回答：若需求可通过知识库或基础能力解决，直接响应。  
  - 工具调用：若需外部数据或复杂操作，启动工具调用流程。  
  **流程图示**  
    - 用户需求 → 判断是否需工具 → 发现工具模块 → 激活模块 → 调用工具完成任务  
2. 发现与使用工具
   - 使用以下工具定位可用模块：  
     - `list_tool_modules`：列出所有工具模块（包括功能分类和描述）。  
     - `get_tool_schema`：通过工具名获取工具的详细Schema信息。  
   - 若发现新模块需启用：  
     - `activate_tool_modules`：激活指定模块，确保其功能可被调用。  
   - 然后，根据需求选择合适工具完成任务（如：数据查询、API调用、文件处理等）.
   例如：<tool_call><name>工具名</name><parameters>参数</parameters></tool_call>
   {tools_description}"""
            }
            processed_messages.insert(0, system_message)
        
        return processed_messages

class OpenRouterAdapter(ModelAdapter):
    """OpenRouter适配器"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def chat_stream(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> AsyncGenerator[str, None]:
        """OpenRouter流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 处理工具信息 - 拼接到prompt中
        processed_messages = self._process_messages_with_tools(messages, tools)
        
        data = {
            "model": self.model,
            "messages": processed_messages,
            "stream": True
        }
        
        # 禁用原生工具支持，强制使用XML格式
        # if tools:
        #     data["tools"] = tools
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", self.base_url, json=data, headers=headers) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line_data = line[6:]
                        if line_data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(line_data)
                            if chunk.get("choices"):
                                delta = chunk["choices"][0].get("delta", {})
                                if delta.get("content"):
                                    yield delta["content"]
                                
                                # 不输出原生工具调用，强制使用XML格式
                        except json.JSONDecodeError:
                            continue
    
    async def chat(self, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> Dict[str, Any]:
        """OpenRouter非流式聊天"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 处理工具信息 - 拼接到prompt中
        processed_messages = self._process_messages_with_tools(messages, tools)
        
        data = {
            "model": self.model,
            "messages": processed_messages
        }
        
        # 禁用原生工具支持，强制使用XML格式
        # if tools:
        #     data["tools"] = tools
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.base_url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
    
    def _process_messages_with_tools(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> List[Dict]:
        """将工具信息拼接到消息中"""
        if not tools:
            return messages
        
        # 构建详细的工具描述（包含完整schema）
        tools_description = f"\n\n📋 当前可用工具 ({len(tools)} 个)：\n"
        
        def format_tool_with_schema(tool):
            """格式化工具信息，包含完整schema"""
            func = tool["function"]
            tool_desc = f"\n🔧 {func['name']}\n"
            tool_desc += f"   描述: {func['description']}\n"
            
            # 添加参数schema信息
            schema = func.get('parameters', {})
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            if properties:
                tool_desc += f"   参数:\n"
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '无描述')
                    is_required = param_name in required
                    required_mark = "必需" if is_required else "可选"
                    
                    # 显示枚举值
                    if 'enum' in param_info:
                        enum_values = ', '.join(map(str, param_info['enum']))
                        tool_desc += f"     - {param_name} ({param_type}, {required_mark}): {param_desc}\n       可选值: [{enum_values}]\n"
                    # 显示默认值
                    elif 'default' in param_info:
                        default_val = param_info['default']
                        tool_desc += f"     - {param_name} ({param_type}, {required_mark}): {param_desc}\n       默认值: {default_val}\n"
                    else:
                        tool_desc += f"     - {param_name} ({param_type}, {required_mark}): {param_desc}\n"
                    
                    # 显示数组元素类型
                    if param_type == 'array' and 'items' in param_info:
                        items_type = param_info['items'].get('type', 'string')
                        tool_desc += f"       数组元素类型: {items_type}\n"
                    
                    # 显示数值范围
                    if param_type in ['integer', 'number']:
                        if 'minimum' in param_info:
                            tool_desc += f"       最小值: {param_info['minimum']}\n"
                        if 'maximum' in param_info:
                            tool_desc += f"       最大值: {param_info['maximum']}\n"
            else:
                tool_desc += f"   参数: 无需参数\n"
            
            return tool_desc
        
        for tool in tools:
            tools_description += format_tool_with_schema(tool)
        
        tools_description += "\n🔧 工具调用格式：<tool_call><name>工具名称</name><parameters>参数JSON</parameters></tool_call>\n"
        tools_description += "💡 请根据上述schema正确传递参数，确保参数类型和必需性符合要求\n"
        
        # 复制消息列表
        processed_messages = messages.copy()
        
        # 如果第一条是系统消息，追加工具信息
        if processed_messages and processed_messages[0].get("role") == "system":
            processed_messages[0]["content"] += tools_description
        else:
            # 否则插入新的系统消息
            
            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            system_message = {
                "role": "system",
                "content": f""""
我是由洛小山开发的，功能强大的AI应用助手，不仅能够高效解答用户问题，更具备强大的工具调用能力。
通过灵活调用各类工具，精准获取所需信息，从而高效满足用户的多样化需求。

当前时间: {current_time}

当你不知道有什么工具的时候，请你尽快调用 `list_tool_modules` 工具查看所有可用工具模块。


# 回答要求  
1. 用户需求识别
当用户提出任务需求时，我会首先判断是否需要调用工具：  
  - 直接回答：若需求可通过知识库或基础能力解决，直接响应。  
  - 工具调用：若需外部数据或复杂操作，启动工具调用流程。  
  **流程图示**  
    - 用户需求 → 判断是否需工具 → 发现工具模块 → 激活模块 → 调用工具完成任务  
2. 发现与使用工具
   - 使用以下工具定位可用模块：  
     - `list_tool_modules`：列出所有工具模块（包括功能分类和描述）。  
     - `get_tool_schema`：通过工具名获取工具的详细Schema信息。  
   - 若发现新模块需启用：  
     - `activate_tool_modules`：激活指定模块，确保其功能可被调用。  
   - 然后，根据需求选择合适工具完成任务（如：数据查询、API调用、文件处理等）.
   例如：<tool_call><name>工具名</name><parameters>参数</parameters></tool_call>
   {tools_description}"""
            }
            processed_messages.insert(0, system_message)
        
        return processed_messages

class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, ModelAdapter] = {}
        self.init_adapters()
    
    def init_adapters(self):
        """初始化适配器"""
        models_config = config.get('models', {}) or {}
        
        # Ollama
        ollama_config = models_config.get('ollama', {})
        if ollama_config and ollama_config.get('enabled'):
            self.adapters['ollama'] = OllamaAdapter(
                host=ollama_config['host'],
                model=ollama_config['model']
            )
        
        # Qwen
        qwen_config = models_config.get('qwen', {})
        if qwen_config and qwen_config.get('enabled') and qwen_config.get('api_key'):
            self.adapters['qwen'] = QwenAdapter(
                api_key=qwen_config['api_key'],
                model=qwen_config['model']
            )
        
        # OpenRouter
        openrouter_config = models_config.get('openrouter', {})
        if openrouter_config and openrouter_config.get('enabled') and openrouter_config.get('api_key'):
            self.adapters['openrouter'] = OpenRouterAdapter(
                api_key=openrouter_config['api_key'],
                model=openrouter_config['model']
            )
    
    def get_adapter(self, provider: str) -> Optional[ModelAdapter]:
        """获取适配器"""
        return self.adapters.get(provider)
    
    def list_adapters(self) -> List[str]:
        """列出可用适配器"""
        return list(self.adapters.keys())
    
    def get_default_adapter(self) -> Optional[ModelAdapter]:
        """获取默认适配器，按照配置的优先级选择"""
        # 首先尝试配置的默认提供商
        default_provider = config.get_default_provider()
        if default_provider in self.adapters:
            return self.adapters[default_provider]
        
        # 如果默认提供商不可用，尝试备用提供商
        fallback_providers = config.get_fallback_providers()
        for provider in fallback_providers:
            if provider in self.adapters:
                return self.adapters[provider]
        
        # 如果都不可用，返回第一个可用的适配器
        if self.adapters:
            return list(self.adapters.values())[0]
        
        return None
    
    def get_default_provider_name(self) -> Optional[str]:
        """获取默认提供商名称"""
        # 首先尝试配置的默认提供商
        default_provider = config.get_default_provider()
        if default_provider in self.adapters:
            return default_provider
        
        # 如果默认提供商不可用，尝试备用提供商
        fallback_providers = config.get_fallback_providers()
        for provider in fallback_providers:
            if provider in self.adapters:
                return provider
        
        # 如果都不可用，返回第一个可用的适配器名称
        if self.adapters:
            return list(self.adapters.keys())[0]
        
        return None
    
    def switch_default_provider(self, provider: str) -> bool:
        """切换默认提供商"""
        if provider not in self.adapters:
            return False
        
        config.set_default_provider(provider)
        config.save_config()
        return True
    
    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        info = {
            "available_providers": list(self.adapters.keys()),
            "default_provider": self.get_default_provider_name(),
            "fallback_providers": config.get_fallback_providers(),
            "provider_details": {}
        }
        
        # 获取每个提供商的详细信息
        models_config = config.get('models', {}) or {}
        for provider in self.adapters.keys():
            provider_config = models_config.get(provider, {}) or {}
            info["provider_details"][provider] = {
                "model": provider_config.get("model", "unknown"),
                "enabled": provider_config.get("enabled", False)
            }
        
        return info

# 全局模型管理器
model_manager = ModelManager() 