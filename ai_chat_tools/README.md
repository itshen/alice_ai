# AI Chat Tools

简化的AI工具调用框架，支持多模型、工具调用、SQLite持久化。

## 特性

- 🤖 **多模型支持**: Ollama、通义千问、OpenRouter
- 🛠️ **工具调用**: 简单的装饰器注册工具
- 💾 **SQLite持久化**: 自动保存对话历史
- 🌊 **流式响应**: 支持SSE实时流式输出
- 🔧 **XML解析**: 智能解析AI输出中的工具调用
- 📡 **HTTP API**: 简洁的REST接口

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置模型

创建 `config.json` 文件：

```json
{
  "models": {
    "ollama": {
      "enabled": true,
      "host": "http://localhost:11434",
      "model": "qwen2.5:7b"
    },
    "qwen": {
      "enabled": false,
      "api_key": "your_qwen_api_key",
      "model": "qwen-plus"
    },
    "openrouter": {
      "enabled": false,
      "api_key": "your_openrouter_api_key",
      "model": "anthropic/claude-sonnet-4"
    }
  }
}
```

### 3. 启动服务

```bash
python3.11 -m ai_chat_tools.main
```

或者：

```bash
python3.11 -m ai_chat_tools.main --host 0.0.0.0 --port 8000
```

## 使用方法

### 编程接口

```python
from ai_chat_tools import ChatBot, register_tool

# 注册自定义工具
@register_tool(
    name="weather",
    description="获取天气信息",
    schema={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"]
    }
)
def get_weather(city: str) -> str:
    return f"{city}今天天气晴朗，温度25°C"

# 使用ChatBot
bot = ChatBot(provider="ollama")

# 创建会话
session_id = bot.create_session("天气查询")

# 流式聊天
async for chunk in bot.chat_stream("北京天气怎么样？", session_id=session_id):
    print(chunk, end="")

# 非流式聊天
result = await bot.chat("上海天气如何？", session_id=session_id)
print(result["message"])
```

### HTTP API

#### 聊天接口

```bash
# 非流式
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "计算 2 + 3 * 4",
    "provider": "ollama",
    "stream": false
  }'

# 流式 (SSE)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "现在几点了？",
    "stream": true
  }'
```

#### 会话管理

```bash
# 获取会话列表
curl "http://localhost:8000/sessions"

# 创建新会话
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"title": "新对话"}'

# 获取会话详情
curl "http://localhost:8000/sessions/{session_id}"
```

#### 工具和模型

```bash
# 获取可用工具
curl "http://localhost:8000/tools"

# 获取可用模型
curl "http://localhost:8000/providers"
```

## 添加自定义工具

### 方法1：装饰器注册

```python
from ai_chat_tools import register_tool

@register_tool(
    name="file_reader",
    description="读取文件内容"
)
def read_file(filename: str) -> str:
    """读取文件内容"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"
```

### 方法2：手动注册

```python
from ai_chat_tools import ToolRegistry

def my_tool(param1: str, param2: int = 10) -> dict:
    return {"result": f"{param1} processed {param2} times"}

# 获取全局注册表
from ai_chat_tools.tools import tool_registry

tool_registry.register(
    name="my_tool",
    func=my_tool,
    description="我的自定义工具",
    schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1"},
            "param2": {"type": "integer", "description": "参数2", "default": 10}
        },
        "required": ["param1"]
    }
)
```

## 项目结构

```
ai_chat_tools/
├── __init__.py          # 包初始化
├── config.py            # 配置管理
├── database.py          # SQLite数据库
├── models.py            # 模型适配器
├── tools.py             # 工具注册系统
├── xml_parser.py        # XML解析器
├── core.py              # 核心ChatBot类
├── api.py               # FastAPI接口
├── main.py              # 启动文件
├── requirements.txt     # 依赖文件
└── README.md            # 说明文档
```

## 内置工具

- `calculator`: 数学计算器
- `get_time`: 获取当前时间

## 配置选项

```json
{
  "models": {
    "ollama": {
      "enabled": true,
      "host": "http://localhost:11434",
      "model": "qwen2.5:7b"
    },
    "qwen": {
      "enabled": false,
      "api_key": "",
      "model": "qwen-plus"
    },
    "openrouter": {
      "enabled": false,
      "api_key": "",
      "model": "anthropic/claude-sonnet-4"
    }
  },
  "database": {
    "path": "chat_history.db"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

## 许可证

MIT License 