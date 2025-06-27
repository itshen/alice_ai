"""
FastAPI接口 - 提供HTTP API和SSE流式响应
"""
import json
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core import ChatBot
from .config import config
from .tool_manager import tool_registry
from .tool_module_manager import tool_module_manager

app = FastAPI(
    title="AI Chat Tools",
    description="简化的AI工具调用框架",
    version="1.0.0"
)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局ChatBot实例
# chatbot = ChatBot()

# 请求模型
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    session_id: Optional[str] = None
    tools: Optional[List[str]] = None
    stream: bool = False
    debug: bool = False
    generate_title: bool = False  # 是否生成标题

class SessionRequest(BaseModel):
    title: str = "新对话"
    provider: Optional[str] = None

class ModelSwitchRequest(BaseModel):
    provider: str

class ModelConfigRequest(BaseModel):
    provider: str
    enabled: bool
    api_key: Optional[str] = None
    model: Optional[str] = None
    host: Optional[str] = None

class DefaultModelRequest(BaseModel):
    provider: str
    fallback_providers: Optional[List[str]] = None

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: dict = {}

# API路由
@app.get("/")
async def root():
    """根路径 - 重定向到前端页面"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

@app.post("/chat")
async def chat(request: ChatRequest):
    """聊天接口"""
    try:
        # 为每个请求创建独立的ChatBot实例
        chatbot = ChatBot(provider=request.provider, debug=request.debug)
        
        if request.stream:
            # 流式响应 - 使用SSE格式返回结构化数据
            async def generate():
                try:
                    # 发送开始事件
                    yield f"event: start\ndata: {json.dumps({'type': 'start', 'message': '开始处理请求...'})}\n\n"
                    
                    # 如果需要生成标题，先生成标题
                    session_id_to_use = request.session_id
                    if request.generate_title:
                        yield f"event: title_generating\ndata: {json.dumps({'type': 'title_generating', 'message': '正在生成对话标题...'})}\n\n"
                        
                        # 生成标题
                        title = await generate_conversation_title(request.message, chatbot)
                        
                        # 如果没有会话ID，创建新会话；如果有会话ID，更新会话标题
                        if not request.session_id:
                            session_id_to_use = chatbot.create_session(title)
                        else:
                            session_id_to_use = request.session_id
                            # 更新现有会话的标题
                            from .database import db
                            db.update_session(session_id_to_use, title=title)
                        
                        yield f"event: title_generated\ndata: {json.dumps({'type': 'title_generated', 'title': title, 'session_id': session_id_to_use})}\n\n"
                    
                    # 发送AI思考开始事件
                    yield f"event: thinking\ndata: {json.dumps({'type': 'thinking', 'message': 'AI正在思考...'})}\n\n"
                    
                    # 流式处理聊天 - 使用正确的session_id
                    async for chunk in chatbot.chat_stream(
                        message=request.message,
                        session_id=session_id_to_use,
                        tools=request.tools
                    ):
                        # 检查是否是工具调用分割线
                        if "🔧 AI工具调用" in chunk:
                            yield f"event: tool_start\ndata: {json.dumps({'type': 'tool_start', 'message': '开始执行工具...'})}\n\n"
                        elif "🔧 调用完成" in chunk:
                            yield f"event: tool_end\ndata: {json.dumps({'type': 'tool_end', 'message': '工具执行完成'})}\n\n"
                        elif "<TOOL_RESULT>" in chunk and "</TOOL_RESULT>" in chunk:
                            # 解析工具结果
                            import re
                            tool_result_match = re.search(r'<TOOL_RESULT>\s*(.*?)\s*</TOOL_RESULT>', chunk, re.DOTALL)
                            if tool_result_match:
                                tool_result_content = tool_result_match.group(1)
                                yield f"event: tool_result\ndata: {json.dumps({'type': 'tool_result', 'content': tool_result_content})}\n\n"
                        else:
                            # 普通文本内容
                            if chunk.strip():
                                yield f"event: message\ndata: {json.dumps({'type': 'message', 'content': chunk})}\n\n"
                    
                    # 发送完成事件
                    yield f"event: complete\ndata: {json.dumps({'type': 'complete', 'message': '对话完成'})}\n\n"
                    
                except Exception as e:
                    yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': f'错误: {str(e)}'})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        else:
            # 非流式响应 - 返回分角色的对话内容
            result = await chatbot.chat(
                message=request.message,
                session_id=request.session_id,
                tools=request.tools
            )
            
            # 获取完整的会话消息历史，构建分角色的对话
            if chatbot.current_session_id:
                messages = chatbot.get_session_messages(chatbot.current_session_id)
                
                # 只取最新的几条消息（从用户最后一条消息开始）
                formatted_conversation = []
                user_message_found = False
                
                # 从后往前找到用户的最后一条消息
                for i in range(len(messages) - 1, -1, -1):
                    msg = messages[i]
                    if msg['role'] == 'user' and msg['content'] == request.message:
                        user_message_found = True
                        break
                
                if user_message_found:
                    # 从找到的用户消息开始，收集后续的对话
                    conversation_messages = messages[i:]
                    
                    for msg in conversation_messages:
                        role = msg['role']
                        content = msg['content'].strip()
                        
                        if role == 'user':
                            formatted_conversation.append(f"<<<USER>>>\n{content}\n<<<END_USER>>>")
                        elif role == 'assistant':
                            formatted_conversation.append(f"<<<ASSISTANT>>>\n{content}\n<<<END_ASSISTANT>>>")
                
                # 组合成最终消息
                final_message = "\n\n".join(formatted_conversation)
                return {"message": final_message}
            else:
                # 如果没有会话历史，直接返回结果
                return {"message": f"<<<ASSISTANT>>>\n{result['message']}\n<<<END_ASSISTANT>>>"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_conversation_title(user_message: str, chatbot: ChatBot) -> str:
    """生成对话标题"""
    try:
        # 创建临时会话用于生成标题
        temp_session_id = chatbot.create_session("临时标题生成")
        
        # 构建标题生成提示
        title_prompt = f"""请为以下用户消息生成一个简洁的对话标题（不超过20个字符）：

用户消息：{user_message}

要求：
1. 标题要简洁明了，能概括用户的主要需求
2. 不超过20个字符
3. 不要包含引号或特殊符号
4. 直接返回标题，不要其他解释

标题："""

        # 生成标题
        title_parts = []
        async for chunk in chatbot.chat_stream(message=title_prompt, session_id=temp_session_id):
            # 过滤掉thinking内容，只保留实际的标题内容
            if not chunk.startswith("<thinking>") and "<thinking>" not in chunk:
                title_parts.append(chunk)
        
        # 清理生成的标题
        title = "".join(title_parts).strip()
        
        # 移除thinking标记（如果有残留）
        import re
        title = re.sub(r'<thinking>.*?</thinking>', '', title, flags=re.DOTALL)
        title = re.sub(r'\n\n+', ' ', title)  # 移除多余的换行
        
        # 移除可能的前缀
        if title.startswith("标题："):
            title = title[3:].strip()
        
        # 限制长度
        if len(title) > 20:
            title = title[:20]
        
        # 删除临时会话
        from .database import db
        db.delete_session(temp_session_id)
        
        return title if title else "新对话"
        
    except Exception as e:
        print(f"生成标题失败: {e}")
        return "新对话"

@app.get("/sessions")
async def get_sessions():
    """获取所有会话"""
    try:
        chatbot = ChatBot()
        return {"sessions": chatbot.get_sessions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions")
async def create_session(request: SessionRequest):
    """创建新会话"""
    try:
        chatbot = ChatBot(provider=request.provider)
        session_id = chatbot.create_session(request.title)
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    try:
        chatbot = ChatBot()
        messages = chatbot.get_session_messages(session_id)
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        from .database import db
        db.delete_session(session_id)
        return {"message": "会话已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def get_tools():
    """获取所有已注册的工具"""
    try:
        chatbot = ChatBot()
        return {"tools": chatbot.list_tools()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/active")
async def get_active_tools():
    """获取当前激活的工具（实际传递给AI的工具列表）"""
    try:
        from .tool_module_manager import tool_module_manager
        
        # 获取内置工具
        builtin_tools = tool_registry.get_builtin_tools()
        
        # 获取激活的模块工具
        active_module_tools = tool_module_manager.get_active_tools()
        
        # 合并工具列表，避免重复
        all_active_tools = []
        tool_names_seen = set()
        
        # 添加内置工具
        for tool in builtin_tools:
            if tool['name'] not in tool_names_seen:
                all_active_tools.append(tool)
                tool_names_seen.add(tool['name'])
        
        # 添加激活的模块工具（过滤掉与内置工具同名的）
        for tool in active_module_tools:
            if tool['name'] not in tool_names_seen:
                all_active_tools.append(tool)
                tool_names_seen.add(tool['name'])
        
        return {"tools": all_active_tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/builtin")
async def get_builtin_tools():
    """获取内置工具"""
    try:
        return {"tools": tool_registry.get_builtin_tools()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/user")
async def get_user_tools():
    """获取用户自定义工具"""
    try:
        return {"tools": tool_registry.get_user_tools()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/status")
async def get_tools_status():
    """获取工具状态信息"""
    try:
        builtin_tools = tool_registry.get_builtin_tools()
        user_tools = tool_registry.get_user_tools()
        
        return {
            "total_tools": len(tool_registry.tools),
            "builtin_count": len(builtin_tools),
            "user_count": len(user_tools),
            "has_user_tools": len(user_tools) > 0,
            "builtin_tools": [t["name"] for t in builtin_tools],
            "user_tools": [t["name"] for t in user_tools]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """直接调用工具"""
    try:
        # 检查工具是否存在
        if request.tool_name not in tool_registry.tools:
            return {
                "success": False,
                "tool_name": request.tool_name,
                "error": f"工具 '{request.tool_name}' 不存在"
            }
        
        # 执行工具
        tool_result = await tool_registry.execute(
            request.tool_name, 
            request.parameters
        )
        
        return {
            "success": tool_result.success,
            "tool_name": request.tool_name,
            "parameters": request.parameters,
            "result": tool_result.data if tool_result.success else tool_result.error_message,
            "execution_time": tool_result.execution_time
        }
        
    except Exception as e:
        return {
            "success": False,
            "tool_name": request.tool_name,
            "error": str(e)
        }

@app.get("/providers")
async def get_providers():
    """获取所有可用的模型提供商"""
    try:
        chatbot = ChatBot()
        return {"providers": chatbot.list_providers()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    """获取配置信息"""
    try:
        return {"config": config.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tool-modules")
async def list_tool_modules():
    """列出所有可用的工具模块"""
    try:
        modules = tool_module_manager.list_available_modules()
        return {
            "success": True,
            "modules": modules,
            "total": len(modules),
            "loaded": len([m for m in modules if m['is_loaded']])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tool-modules/load")
async def load_tool_modules_api(request: dict):
    """加载指定的工具模块"""
    try:
        module_names = request.get("modules", [])
        if not module_names:
            return {"success": False, "error": "未指定要加载的模块"}
        
        results = tool_module_manager.load_modules(module_names)
        success_count = sum(1 for success in results.values() if success)
        
        return {
            "success": True,
            "results": results,
            "loaded_count": success_count,
            "total_count": len(module_names)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tool-modules/unload")
async def unload_tool_module_api(request: dict):
    """卸载指定的工具模块"""
    try:
        module_name = request.get("module")
        if not module_name:
            return {"success": False, "error": "未指定要卸载的模块"}
        
        result = tool_module_manager.unload_module(module_name)
        return {"success": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/tool-modules/categories")
async def get_tool_module_categories():
    """获取工具模块类别"""
    try:
        modules = tool_module_manager.list_available_modules()
        categories = {}
        
        for module in modules:
            category = module['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(module)
        
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 模型管理API
@app.get("/models")
async def get_models():
    """获取所有模型信息"""
    try:
        from .models import model_manager
        info = model_manager.get_provider_info()
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/current")
async def get_current_model():
    """获取当前使用的模型"""
    try:
        from .models import model_manager
        default_provider = model_manager.get_default_provider_name()
        if not default_provider:
            raise HTTPException(status_code=404, detail="没有可用的模型")
        
        models_config = config.get('models', {})
        if models_config is None:
            models_config = {}
        
        provider_config = models_config.get(default_provider, {}) if isinstance(models_config, dict) else {}
        
        return {
            "success": True,
            "data": {
                "provider": default_provider,
                "model": provider_config.get('model', 'unknown'),
                "enabled": provider_config.get('enabled', False),
                "host": provider_config.get('host'),
                "has_api_key": bool(provider_config.get('api_key'))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换默认模型"""
    try:
        from .models import model_manager
        
        # 检查提供商是否可用
        available_providers = model_manager.list_adapters()
        if request.provider not in available_providers:
            raise HTTPException(
                status_code=400, 
                detail=f"模型提供商 '{request.provider}' 不可用。可用的提供商: {', '.join(available_providers)}"
            )
        
        # 切换默认提供商
        success = model_manager.switch_default_provider(request.provider)
        if success:
            models_config = config.get('models', {})
            if models_config is None:
                models_config = {}
            
            provider_config = models_config.get(request.provider, {}) if isinstance(models_config, dict) else {}
            model_name = provider_config.get('model', 'unknown') if isinstance(provider_config, dict) else 'unknown'
            
            return {
                "success": True,
                "message": f"已成功切换到模型提供商: {request.provider} (模型: {model_name})",
                "data": {
                    "provider": request.provider,
                    "model": model_name
                }
            }
        else:
            raise HTTPException(status_code=500, detail=f"切换到 '{request.provider}' 失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/models/{provider}/config")
async def update_model_config(provider: str, request: ModelConfigRequest):
    """更新特定模型提供商的配置"""
    try:
        # 验证提供商名称
        valid_providers = ["ollama", "qwen", "openrouter"]
        if provider not in valid_providers:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的提供商: {provider}。支持的提供商: {', '.join(valid_providers)}"
            )
        
        # 更新配置
        config.set(f"models.{provider}.enabled", request.enabled)
        
        if request.api_key is not None:
            config.set(f"models.{provider}.api_key", request.api_key)
        
        if request.model is not None:
            config.set(f"models.{provider}.model", request.model)
        
        if request.host is not None:
            config.set(f"models.{provider}.host", request.host)
        
        # 保存配置
        config.save_config()
        
        # 重新初始化模型管理器
        from .models import model_manager
        model_manager.init_adapters()
        
        return {
            "success": True,
            "message": f"已更新 {provider} 的配置",
            "data": config.get(f"models.{provider}")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/models/default")
async def set_default_model(request: DefaultModelRequest):
    """设置默认模型和备用模型"""
    try:
        from .models import model_manager
        
        # 检查提供商是否可用
        available_providers = model_manager.list_adapters()
        if request.provider not in available_providers:
            raise HTTPException(
                status_code=400, 
                detail=f"模型提供商 '{request.provider}' 不可用。可用的提供商: {', '.join(available_providers)}"
            )
        
        # 设置默认提供商
        config.set_default_provider(request.provider)
        
        # 设置备用提供商（如果提供）
        if request.fallback_providers is not None:
            # 验证备用提供商
            invalid_providers = [p for p in request.fallback_providers if p not in available_providers]
            if invalid_providers:
                raise HTTPException(
                    status_code=400,
                    detail=f"以下备用提供商不可用: {', '.join(invalid_providers)}"
                )
            config.set_fallback_providers(request.fallback_providers)
        
        # 保存配置
        config.save_config()
        
        return {
            "success": True,
            "message": f"已设置默认模型为: {request.provider}",
            "data": {
                "default_provider": request.provider,
                "fallback_providers": request.fallback_providers or config.get_fallback_providers()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_server(host: Optional[str] = None, port: Optional[int] = None):
    """运行服务器"""
    import uvicorn
    
    # 安全地获取配置值
    default_host = config.get('server.host', '0.0.0.0')
    default_port = config.get('server.port', 8000)
    
    # 确保类型正确
    if host is None:
        host = default_host if isinstance(default_host, str) else '0.0.0.0'
    if port is None:
        port = default_port if isinstance(default_port, int) else 8000
    
    print(f"🚀 启动AI Chat Tools服务器: http://{host}:{port}")
    print("📋 可用的API端点:")
    print("  POST /chat - 聊天接口")
    print("  GET  /sessions - 获取会话列表")
    print("  POST /sessions - 创建新会话")
    print("  GET  /tools - 获取所有已注册工具")
    print("  GET  /tools/active - 获取当前激活的工具（传递给AI的工具）")
    print("  GET  /tools/builtin - 获取内置工具")
    print("  GET  /tools/user - 获取用户工具")
    print("  GET  /tools/status - 获取工具状态")
    print("  GET  /providers - 获取模型提供商")
    print("  GET  /tool-modules - 获取工具模块列表")
    print("  POST /tool-modules/load - 加载工具模块")
    print("  POST /tool-modules/unload - 卸载工具模块")
    print("  GET  /tool-modules/categories - 获取工具模块类别")
    print("  GET  /models - 获取所有模型信息")
    print("  GET  /models/current - 获取当前使用的模型")
    print("  POST /models/switch - 切换默认模型")
    print("  PUT  /models/{provider}/config - 更新特定模型提供商的配置")
    print("  PUT  /models/default - 设置默认模型和备用模型")
    print()
    
    # 检查用户工具
    tool_registry.check_user_tools()
    
    uvicorn.run(app, host=host, port=port) 