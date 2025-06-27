# README for Cursor AI

这是一个 AI 工具调用框架的说明文档，专门为 Cursor AI 编写，帮助快速理解项目结构和进行代码修改。

## 🎯 项目概述

**AI Chat Tools** 是一个简化的 AI 工具调用框架，支持：
- 多模型适配（Ollama、Qwen、OpenRouter）
- 统一的工具注册和调用机制
- **🆕 动态工具模块加载系统**
- **🧠 智能工具管理**：大模型可自主搜索、激活和管理工具模块
- **💭 AI记忆系统**：智能保存和检索重要信息，持续学习用户偏好
- **🔒 用户确认机制**：危险操作需要用户确认，保护数据安全
- **📝 智能会话管理**：自动延续对话上下文，支持多会话切换
- SQLite 持久化会话管理
- FastAPI HTTP 接口
- 流式和非流式响应

## 📁 核心文件结构

```
ai_chat_tools/
├── __init__.py              # 模块入口，导入核心组件
├── core.py                  # ChatBot 核心类，处理对话逻辑
├── tool_manager.py          # 工具管理器，统一工具注册和执行
├── tool_module_manager.py   # 🆕 工具模块管理器，动态加载工具模块
├── tools.py                 # 内置工具定义（含模型管理、记忆管理、确认设置工具）
├── user_confirmation.py     # 🔒 用户确认管理器，处理危险操作确认
├── config.py                # 配置管理（含模型、记忆、确认配置）
├── user_tools.py            # 用户自定义工具（示例都被注释）
├── user_tool_modules/       # 🆕 用户工具模块目录
│   ├── file_manager_tools.py # 文件管理工具模块（带确认机制）
│   └── web_scraper_tools.py  # 网页抓取和API调用工具模块
├── api.py                   # FastAPI 接口定义（含模型管理API）
├── models.py                # 模型适配器（支持Ollama、Qwen、OpenRouter）
├── database.py              # SQLite 数据库操作
├── config.py                # 配置管理（含模型配置）
├── xml_parser.py            # XML 工具调用解析
└── main.py                  # 主启动文件（含模型选择功能）
```

## 🔧 核心概念

### 1. 工具系统 (tool_manager.py)

**关键类：**
- `ToolResult`: 统一的工具返回格式，包含完整的调用上下文
- `ToolRegistry`: 工具注册表，管理所有工具
- `ErrorCodes`: 标准化错误码

**工具注册装饰器：**
```python
@register_tool(
    name="tool_name",
    description="工具描述",
    schema={...}  # JSON Schema 定义参数
)
def my_tool(param: str) -> str:  # 必须返回 str
    return "结果"
```

**工具分类：**
- 内置工具：定义在 `tools.py` 中
- 用户工具：定义在 `user_tools.py` 或其他模块中
- **🆕 模块化工具：定义在 `user_tool_modules/` 目录中**

### 2. 🆕 动态工具模块系统 (tool_module_manager.py)

**核心特性：**
- 按需加载工具模块（文本编辑、时间管理等）
- 交互式模块选择界面
- 配置文件管理默认加载模块
- API 接口支持动态管理

**ToolModuleManager 类：**
- `load_module()`: 加载指定模块
- `list_available_modules()`: 列出可用模块
- `interactive_module_selection()`: 交互式选择

### 3. 🏗️ 三层工具架构

**工具系统现在采用三层架构设计：**

#### 第一层：核心基础工具 (`tools.py`)
- **作用**：系统必需的基础工具，总是被加载
- **包含**：工具管理功能、AI记忆系统、用户确认设置、帮助信息
- **特点**：让大模型具备自主工具管理和学习记忆能力
- **适用**：智能工具管理、记忆保存检索、系统安全设置

#### 第二层：简单自定义工具 (`user_tools.py`)
- **作用**：用户快速添加简单的、单个的工具
- **包含**：文本处理、简单计算等单一功能工具
- **特点**：直接注册，无需模块化
- **适用**：简单的、独立的工具函数

#### 第三层：模块化工具 (`user_tool_modules/`)
- **作用**：复杂的、相关的工具集合，按需加载
- **包含**：文本编辑工具集、时间管理工具集等
- **特点**：支持配置、分类管理、动态加载
- **适用**：功能完整的工具模块

### 4. 聊天系统 (core.py)

**ChatBot 类：**
- 管理会话状态
- 处理多轮对话
- 执行工具调用
- 支持流式和非流式响应

**关键方法：**
- `chat()`: 非流式聊天
- `chat_stream()`: 流式聊天
- `_execute_tool_calls()`: 执行工具调用

### 5. API 接口 (api.py)

**流式响应：** 直接返回纯文本流
**非流式响应：** 返回格式化的分角色对话

**关键端点：**
- `POST /chat`: 聊天接口
- `GET /tools/*`: 工具相关接口
- `GET /sessions/*`: 会话管理
- **🆕 `GET /tool-modules`**: 获取工具模块列表
- **🆕 `POST /tool-modules/load`**: 加载工具模块
- **🆕 `GET /tool-modules/categories`**: 获取模块类别
- **🆕 `GET /models`**: 获取所有模型信息
- **🆕 `POST /models/switch`**: 切换默认模型
- **🆕 `PUT /models/{provider}/config`**: 更新模型配置
- **🆕 `PUT /models/default`**: 设置默认模型

## 🤖 模型管理系统

### 1. 支持的模型提供商

**Ollama (本地模型)**:
- 优点: 免费、隐私性好、响应快
- 缺点: 需要本地安装、占用系统资源
- 配置: host, model

**通义千问 (Qwen)**:
- 优点: 中文能力强、官方支持
- 缺点: 需要API密钥、有使用成本
- 配置: api_key, model

**OpenRouter**:
- 优点: 支持多种知名模型、统一接口
- 缺点: 需要API密钥、有使用成本
- 配置: api_key, model

### 2. 模型配置结构 (config.py)

```json
{
  "default_model": {
    "provider": "ollama",
    "fallback_providers": ["qwen", "openrouter"]
  },
  "models": {
    "ollama": {
      "enabled": true,
      "host": "http://localhost:11434",
      "model": "qwen3:8b"
    },
    "qwen": {
      "enabled": false,
      "api_key": "",
      "model": "qwen-plus-latest"
    },
    "openrouter": {
      "enabled": false,
      "api_key": "",
      "model": "anthropic/claude-sonnet-4"
    }
  }
}
```

### 3. 模型管理工具 (tools.py)

**内置模型管理工具：**
- `list_models`: 列出所有可用模型
- `get_current_model`: 获取当前使用的模型
- `switch_model`: 切换默认模型
- `configure_model`: 配置模型参数
- `set_default_model`: 设置默认和备用模型
- `show_model_config`: 显示详细配置

**💭 AI记忆管理工具：**
- `save_memory`: 保存重要信息到AI记忆
- `read_all_memories`: 读取所有已保存的记忆
- `find_user_memories`: 根据关键词搜索记忆

**🔒 用户确认设置工具：**
- `manage_confirmation_settings`: 管理用户确认偏好（仅限用户操作）

### 4. 启动时模型选择 (main.py)

**命令行参数：**
- `--list-models`: 列出所有可用模型
- `--model [provider]`: 指定使用的模型

## 📝 会话管理系统

### 1. 智能会话延续

**核心逻辑 (core.py:99-115)：**
```python
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
    else:
        # 只有在没有任何会话时才创建新会话
        self.create_session("默认对话")
```

**关键特性：**
- **自动延续**：启动时自动加载最近会话，避免上下文丢失
- **智能切换**：只有用户主动操作时才创建新会话
- **历史保护**：所有对话安全保存，随时可查看

### 2. 命令行会话管理 (main.py:203-322)

**在聊天界面中直接输入命令：**

```python
# 创建新会话
if user_input.lower().startswith(('new_session', 'new session')):
    parts = user_input.split(' ', 1)
    title = parts[1].strip() if len(parts) > 1 else "新对话"
    session_id = bot.create_session(title)

# 列出会话
elif user_input.lower() in ['list_sessions', 'list sessions', 'sessions']:
    sessions = bot.get_sessions()
    # 显示会话列表，包含当前会话标记

# 切换会话  
elif user_input.lower().startswith(('switch_session', 'switch session')):
    session_id = parts[2].strip()
    bot.load_session(session_id)

# 查看历史
elif user_input.lower() in ['show_history', 'show history', 'history']:
    messages = bot.get_session_messages()
    # 显示最近10条消息
```

**支持的命令：**
- `new_session [标题]` - 创建新会话
- `list_sessions` - 列出所有会话 
- `switch_session <ID>` - 切换会话
- `show_history` - 显示当前会话历史
- `help` - 显示帮助信息

### 3. API会话管理 (api.py)

**已有的会话接口：**
```python
@app.get("/sessions")                    # 获取所有会话
@app.post("/sessions")                   # 创建新会话
@app.get("/sessions/{session_id}")       # 获取会话详情  
@app.delete("/sessions/{session_id}")    # 删除会话
```

**聊天接口支持session_id：**
```python
@app.post("/chat")
async def chat(request: ChatRequest):
    # 自动创建或加载会话
    chatbot = ChatBot(provider=request.provider, debug=request.debug)
    
    # 如果指定session_id则使用，否则自动延续最近会话
    response = await chatbot.chat_stream(
        message=request.message,
        session_id=request.session_id,
        tools=request.tools
    )
```

### 4. 数据库会话存储 (database.py)

**会话表结构：**
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TEXT,
    updated_at TEXT
)

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,
    content TEXT,
    timestamp TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
)
```

**核心方法：**
- `create_session()` - 创建新会话
- `get_sessions()` - 获取所有会话  
- `get_session()` - 获取特定会话
- `get_messages()` - 获取会话消息
- `add_message()` - 添加消息到会话

### 5. 最佳实践

**工作流建议：**
1. **日常使用**：直接启动，系统自动延续昨天的对话
2. **新主题**：`new_session 主题名称` 创建专门会话
3. **查看历史**：定期使用 `list_sessions` 和 `show_history`
4. **项目切换**：为不同项目创建不同会话

**Cursor AI 开发建议：**
- 会话逻辑主要在 `core.py` 的 `chat_stream()` 方法
- 命令处理在 `main.py` 的主循环中
- API接口已经完整，可直接使用
- 数据库操作封装在 `database.py` 中
- 交互式选择: 多个模型可用时自动提示

**启动流程：**
```python
# 1. 解析命令行参数
args = parse_args()

# 2. 处理模型选择
if args.model:
    selected_provider = args.model
elif 多个可用模型:
    selected_provider = select_model_interactively()

# 3. 创建ChatBot实例
bot = ChatBot(provider=selected_provider)
```

## 💭 AI记忆系统 (tools.py)

### 核心类：MemoryManager

**文件存储：** `ai_memory.json`（项目根目录）

**核心方法：**
```python
class MemoryManager:
    def add_memory(self, content: str, tags: List[str] = None, category: str = "general") -> str
    def get_all_memories(self) -> List[Dict]
    def find_user_memories(self, keyword: str) -> List[Dict]
```

**记忆数据结构：**
```python
{
    "id": 1,
    "content": "记忆内容",
    "tags": ["标签1", "标签2"],
    "category": "user_preference",
    "timestamp": "2025-06-10T14:28:19.327274",
    "created_date": "2025-06-10 14:28:19"
}
```

**记忆类别：**
- `user_preference`: 用户偏好
- `project_info`: 项目信息  
- `task`: 任务记录
- `knowledge`: 知识积累
- `conversation`: 对话记录
- `general`: 一般信息

### 使用记忆系统

**在工具中集成记忆：**
```python
@register_tool(...)
def my_tool(param: str) -> str:
    # 保存重要信息到记忆
    from .tools import _memory_manager
    _memory_manager.add_memory(
        content=f"用户执行了操作: {param}",
        tags=["用户操作"],
        category="conversation"
    )
    return "处理完成"
```

## 🔒 用户确认机制 (user_confirmation.py)

### 核心类：UserConfirmationManager

**配置文件：** 在 `config.json` 的 `user_confirmation` 节点

**确认策略：**
- `ask`: 每次询问用户（默认）
- `allow`: 自动同意执行
- `deny`: 自动拒绝执行

**确认类别：**
- `file_write`: 文件写入操作
- `file_delete`: 文件删除操作
- `file_modify`: 文件修改操作
- `system_command`: 系统命令执行
- `network_request`: 网络请求
- `general`: 一般操作

### 在工具中添加确认机制

**工具注册时添加确认参数：**
```python
@register_tool(
    name="dangerous_tool",
    description="危险操作工具",
    requires_confirmation=True,        # 需要用户确认
    confirmation_category="file_write", # 确认类别
    risk_level="high",                 # 风险等级：low, medium, high
    schema={...}
)
def dangerous_tool(param: str) -> str:
    # 这个工具会在执行前请求用户确认
    return f"执行危险操作: {param}"
```

**确认配置结构：**
```python
"user_confirmation": {
    "default_policy": "ask",
    "tool_policies": {
        "specific_tool": "allow"
    },
    "category_policies": {
        "file_write": "ask",
        "network_request": "allow"
    },
    "remember_choices": True,
    "session_memory": {}
}
```

## 🛠️ 常见修改场景

### 1. 添加新工具模块

**创建新的工具模块文件：**
```python
# ai_chat_tools/user_tool_modules/my_tools.py

# MODULE_DESCRIPTION: 我的工具模块描述
# MODULE_CATEGORY: custom
# MODULE_AUTHOR: Your Name
# MODULE_VERSION: 1.0.0

from ..tool_manager import register_tool
from ..config import config

@register_tool(
    name="my_new_tool",
    description="新工具描述",
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
def my_new_tool(param: str) -> str:
    """新工具实现"""
    # 获取模块配置
    module_config = config.get_tool_module_config("my_tools")
    
    # 处理逻辑
    return f"处理结果: {param}"
```

**模块信息注释格式：**
```python
# MODULE_DESCRIPTION: 模块功能描述
# MODULE_CATEGORY: 模块类别（如 text_processing, time_management, custom）
# MODULE_AUTHOR: 作者名称
# MODULE_VERSION: 版本号
```

### 2. 添加新的模型提供商

**步骤1: 在 models.py 中创建适配器**
```python
class NewProviderAdapter(ModelAdapter):
    def __init__(self, api_key: str, model: str, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model = model
    
    async def chat_stream(self, messages: List[Dict], tools: List[Dict] = None, **kwargs):
        # 实现流式聊天
        pass
    
    async def chat(self, messages: List[Dict], tools: List[Dict] = None, **kwargs):
        # 实现非流式聊天
        pass
```

**步骤2: 在 ModelManager.init_adapters() 中注册**
```python
# 在 init_adapters 方法中添加
if models_config.get('new_provider', {}).get('enabled'):
    new_provider_config = models_config['new_provider']
    if new_provider_config.get('api_key'):
        self.adapters['new_provider'] = NewProviderAdapter(
            api_key=new_provider_config['api_key'],
            model=new_provider_config['model']
        )
```

**步骤3: 更新默认配置**
```python
# 在 config.py 的 default_config 中添加
"new_provider": {
    "enabled": False,
    "api_key": "",
    "model": "new-model-name"
}
```

### 3. 添加模型管理相关的API接口

**在 api.py 中添加新接口：**
```python
@app.get("/models/stats")
async def get_model_stats():
    """获取模型使用统计"""
    try:
        from .models import model_manager
        # 实现统计逻辑
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. 添加模型管理工具

**在 tools.py 中添加新的模型管理工具：**
```python
@register_tool(
    name="model_health_check",
    description="检查模型连接状态"
)
def model_health_check() -> str:
    """检查所有模型的连接状态"""
    from .models import model_manager
    
    results = []
    for provider in model_manager.list_adapters():
        try:
            # 测试连接
            adapter = model_manager.get_adapter(provider)
            # 执行健康检查
            status = "✅ 正常"
        except Exception as e:
            status = f"❌ 错误: {str(e)}"
        
        results.append(f"  {provider}: {status}")
    
    return "🔍 **模型健康检查**\n\n" + "\n".join(results)
```

## 🔍 关键设计模式

### 1. 模块化工具加载

**工具模块扫描：**
```python
def _scan_tool_modules(self):
    """扫描 user_tool_modules/ 目录下的 .py 文件"""
    user_modules_dir = os.path.join(os.path.dirname(__file__), "user_tool_modules")
    if os.path.exists(user_modules_dir):
        self._scan_directory(user_modules_dir, "user")
```

**动态导入模块：**
```python
def load_module(self, module_name: str) -> bool:
    """使用 importlib 动态加载模块"""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
```

### 2. 配置驱动的模块管理

**配置结构：**
```python
"tool_modules": {
    "auto_load": True,              # 是否自动加载
    "interactive_selection": True,   # 是否交互式选择
    "default_modules": [],          # 默认加载的模块
    "module_configs": {}            # 各模块的特定配置
}
```

### 3. 统一返回格式

所有工具执行都返回 `ToolResult` 对象：
```python
ToolResult(
    tool_name="工具名",
    parameters={"参数": "值"},
    success=True/False,
    data="结果数据",
    error_code="错误码",
    error_message="错误信息",
    execution_time=0.001,
    timestamp=1234567890
)
```

## 📝 修改指南

### 添加功能时：

1. **新工具模块**: 在 `user_tool_modules/` 中创建 `.py` 文件
2. **新 API**: 在 `api.py` 中添加端点
3. **新配置**: 在 `config.py` 中添加配置项
4. **新启动选项**: 在 `main.py` 中添加命令行参数

### 调试技巧：

1. **模块调试**: 使用 `tool_module_manager.load_module()` 直接测试
2. **工具调试**: 使用 `tool_registry.execute()` 直接测试
3. **API 调试**: 查看 FastAPI 自动生成的文档 `/docs`
4. **配置调试**: 使用 `config.get()` 检查配置值

## ⚠️ 重要约束

1. **工具返回值**: 必须是 `str` 类型
2. **模块信息**: 必须在文件开头添加 `# MODULE_*` 注释
3. **异步支持**: 工具可以是同步或异步函数
4. **错误处理**: 使用标准错误码，不要抛出未捕获异常
5. **配置管理**: 所有配置都通过 `config.py` 管理
6. **模块卸载**: Python 中模块卸载有限制，需要重启程序

## 🚀 快速开始修改

1. **添加工具模块**:
   ```bash
   # 创建新模块文件
   touch ai_chat_tools/user_tool_modules/my_tools.py
   # 添加模块信息和工具函数
   ```

2. **配置默认加载**:
   ```json
   # 在 config.json 中添加
   "tool_modules": {
     "default_modules": ["file_manager_tools", "my_tools"]
   }
   ```

3. **测试模块加载**:
   ```bash
   python3.11 -m ai_chat_tools.main --load-modules file_manager_tools my_tools
   ```

## 📚 内置工具模块

### 文件管理工具 (file_manager_tools.py)
**包含确认机制的文件操作工具：**
- `read_file` - 读取文件内容（无需确认）
- `write_file` - 写入文件内容（需要确认，file_write类别，medium风险）
- `search_in_file` - 文件内搜索（无需确认）
- `replace_in_file` - 文件内替换（需要确认，file_modify类别，high风险）
- `list_files` - 列出目录文件（无需确认）

### 网页抓取工具 (web_scraper_tools.py)
**包含网络请求确认机制的工具：**
- `fetch_webpage_content` - 获取网页纯文本内容
- `fetch_webpage_summary` - 获取网页摘要信息
- `extract_webpage_links` - 提取网页链接
- `check_webpage_status` - 检查网页状态
- `fetch_json_data` - 获取JSON数据并保存（需要确认，network_request类别，medium风险）
- `api_get_request` - 执行GET请求（需要确认，network_request类别，low风险）
- `api_post_request` - 执行POST请求（需要确认，network_request类别，medium风险）

**可用模块：**
- file_manager_tools: 文件管理工具（带安全确认）
- web_scraper_tools: 网页抓取和API调用工具（带安全确认）

创建自定义模块：