# AI Chat Tools

一个简化的 AI 工具调用框架，支持多模型、动态工具模块加载和会话管理。

## ✨ 主要特性

- 🤖 **智能对话**：基于 OpenAI GPT 模型的自然语言交互
- 🔧 **工具调用**：支持函数调用，可执行各种实用工具
- 🆕 **动态模块加载**：按需加载工具模块，减少资源占用
- 📦 **模块化设计**：工具按功能分类，便于管理和扩展
- 🎯 **交互式选择**：启动时可选择需要的工具模块
- 🧠 **智能工具管理**：大模型可自主搜索、激活和管理工具模块
- 💭 **AI记忆系统**：智能保存和检索重要信息，持续学习用户偏好
- 🔒 **用户确认机制**：危险操作需要用户确认，保护数据安全
- ⚙️ **配置驱动**：支持配置文件管理默认行为
- 🌐 **API 接口**：提供 HTTP API 支持
- 📱 **流式响应**：实时显示 AI 回复内容
- 📝 **会话管理**：智能会话延续，支持多会话切换和历史查看
- 🚀 **Token 优化**：智能过滤冗长的工具结果，节省 Token 使用

## 🏗️ 工具系统架构

本项目采用**三层工具架构**，满足不同场景的需求：

### 第一层：核心基础工具 ⚡
- **位置**：`ai_chat_tools/tools.py`
- **特点**：系统必需，总是加载
- **包含**：工具管理功能、AI记忆系统、用户确认设置、帮助信息
- **适用**：让大模型具备自主工具管理和学习记忆能力

### 第二层：简单自定义工具 🔨
- **位置**：`ai_chat_tools/user_tools.py`
- **特点**：快速添加单个工具
- **包含**：文本处理、简单计算等
- **适用**：简单的、独立的工具函数

### 第三层：模块化工具 📦
- **位置**：`ai_chat_tools/user_tool_modules/`
- **特点**：按需加载，功能完整
- **包含**：文本编辑工具集、时间管理工具集
- **适用**：复杂的、相关的工具集合

## 🆕 工具模块系统

### 🧠 智能工具管理

大模型现在具备了自主管理工具的能力，可以：

- **🔍 搜索工具模块**：根据关键词查找相关功能模块
- **📋 列出可用工具**：查看当前激活的所有工具
- **📦 管理模块状态**：动态激活或取消激活工具模块
- **🎯 按需加载**：根据任务需求自动选择合适的工具

**示例对话：**
```
用户：我想处理一些文本文件
AI：我来帮你搜索相关的工具模块...
    [搜索并激活文本编辑工具模块]
    现在我可以帮你读取、编辑、搜索文本文件了！

用户：我还需要管理一些任务
AI：让我激活时间管理工具模块...
    [激活时间管理工具模块]
    现在我可以帮你添加任务、设置提醒了！
```

### 💭 AI记忆系统

AI现在具备了持久记忆能力，可以智能地保存和检索重要信息：

- **🧠 智能记忆**：自动识别并保存重要信息
- **🏷️ 分类管理**：支持标签和类别系统
- **🔍 模糊搜索**：根据关键词快速找到相关记忆
- **📅 时间排序**：按时间顺序管理记忆信息

#### 核心功能

**1. 自动记忆保存**
AI会在以下情况下自动保存记忆：
- 用户偏好设置（语言、系统环境等）
- 项目配置信息（文件路径、架构等）
- 重要任务和决策记录
- 学习到的新知识和解决方案

**2. 记忆类别系统**
- `user_preference`: 用户偏好
- `project_info`: 项目信息
- `task`: 任务记录
- `knowledge`: 知识积累
- `conversation`: 对话记录
- `general`: 一般信息

**3. 记忆检索**
- **查看所有记忆**: 按时间倒序显示
- **类别过滤**: 按特定类别查看记忆
- **关键词搜索**: 在内容、标签、类别中搜索
- **标签系统**: 使用标签快速分类和查找

#### 使用示例

```
用户：我的系统是macOS，喜欢用中文
AI：[保存记忆] 我已经记住您的偏好：系统macOS，语言中文
    以后我会按照您的偏好来回答问题。

用户：这个项目的配置文件在哪里？
AI：[搜索记忆] 让我查看一下项目相关的记忆...
    根据之前的记录，配置文件在 config.json 中。

用户：我之前问过什么问题？
AI：[读取记忆] 让我查看一下您的对话记录...
    您之前询问过关于工具系统、记忆功能和API使用等问题。
```

#### 记忆数据存储

- **存储位置**: `ai_memory.json`（项目根目录）
- **数据格式**: JSON格式，包含ID、内容、标签、类别、时间戳
- **自动管理**: 自动创建文件、分配ID、记录时间

### 🔒 用户确认机制

为保护用户数据安全，系统内置了智能确认机制：

- **🛡️ 危险操作保护**：文件写入、删除、网络请求等需要确认
- **📋 策略管理**：支持三种策略（询问、允许、拒绝）
- **🎯 多级配置**：工具级别、类别级别、默认级别
- **💾 记忆功能**：记住用户选择，减少重复确认

#### 确认类别

- `file_write`: 文件写入操作
- `file_delete`: 文件删除操作
- `file_modify`: 文件修改操作
- `system_command`: 系统命令执行
- `network_request`: 网络请求
- `general`: 一般操作

#### 管理确认设置

**注意**: 确认设置管理工具（`manage_confirmation_settings`）仅限用户在控制台或API中操作，AI无法自主修改安全设置。

```bash
# 查看当前确认设置
python3.11 -c "
import asyncio
from ai_chat_tools.tool_manager import tool_registry
result = asyncio.run(tool_registry.execute('manage_confirmation_settings', {'action': 'show'}))
print(result.to_string())
"

# 设置默认策略为自动允许
python3.11 -c "
import asyncio
from ai_chat_tools.tool_manager import tool_registry
result = asyncio.run(tool_registry.execute('manage_confirmation_settings', {
    'action': 'set_default', 
    'policy': 'allow'
}))
print(result.to_string())
"
```

### 可用模块

### 📁 文件管理工具 (file_manager_tools)

提供文件操作和文本处理功能：

- `read_file`: 读取文件内容
- `write_file`: 写入文件内容
- `search_in_file`: 在文件中搜索文本
- `replace_in_file`: 替换文件中的文本
- `list_files`: 列出目录中的文件

### 模块加载方式

**1. 交互式选择（推荐）**
```bash
python3.11 main.py
# 启动时会显示可用模块列表，可以选择需要的模块
```

**2. 指定模块加载**
```bash
python3.11 main.py --modules file_manager_tools
```

**3. 跳过模块加载**
```bash
python3.11 main.py --skip-modules
```

**4. 配置文件管理**
在 `config.json` 中设置：
```json
{
  "tool_modules": {
    "auto_load": ["file_manager_tools"],
    "interactive_selection": true
  }
}
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置模型
创建 `config.json` 文件：
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
      "enabled": true,
      "api_key": "your-api-key-here",
      "model": "qwen-plus-latest"
    }
  }
}
```

### 3. 选择模型并启动

**方式1：使用启动脚本**
```bash
# Python版本
python3.11 run.py
# 选择选项 4: 列出可用模型
# 选择选项 5: 选择模型启动对话

# Bash版本  
./run.sh
# 选择相应的模型管理选项
```

**方式2：直接命令行**
```bash
# 列出所有可用模型
python3.11 main.py --list-models

# 指定模型启动
python3.11 main.py --model qwen
python3.11 main.py --model ollama

# 交互式选择（当有多个可用模型时会自动提示）
python3.11 main.py
```

### 4. 开始对话
```
你: 你现在有哪些工具可以用？
AI: 我来查看一下当前可用的工具...
[使用工具管理功能] 目前我有工具管理相关的核心工具，可以帮你搜索和激活其他功能模块。

你: 切换到ollama模型
AI: [切换模型] ✅ 已成功切换到模型提供商: ollama (模型: qwen3:8b)

你: 帮我找找文本处理相关的工具
AI: 我来搜索文本相关的工具模块...
[搜索工具模块] 找到了文本编辑工具模块！我来激活它...
[激活工具模块] 现在我可以帮你读取、编辑、搜索文本文件了！
```

## 📝 会话管理

### 智能会话延续

系统自动保持对话连续性，避免上下文丢失：

- **自动延续**：启动时自动加载最近的会话
- **智能切换**：只有在用户主动操作时才创建新会话
- **历史保护**：所有对话历史安全保存，随时可查看

### 命令行会话管理

在聊天界面中直接输入以下命令：

#### 基本会话操作

```bash
# 创建新会话
new_session                    # 创建默认标题的新会话
new_session IU研究专用会话      # 创建带标题的新会话

# 查看会话列表  
list_sessions                  # 列出所有会话（显示ID、标题、消息数）
sessions                      # 简写形式

# 切换会话
switch_session <会话ID>        # 切换到指定会话

# 查看历史
show_history                  # 显示当前会话的消息历史
history                       # 简写形式
```

#### 使用示例

```bash
你: new_session IU最新资讯研究
✅ 已创建新会话: IU最新资讯研究
🆔 会话ID: abc123...

你: 搜索IU的最新消息
AI: 我来帮你搜索IU的最新资讯...
[执行搜索工具]

你: list_sessions
📝 对话会话列表 (共 3 个):
==================================================
1. IU最新资讯研究 📍 当前
   ID: abc123...
   创建时间: 2024-01-15 10:30:00
   消息数: 3

2. 默认对话
   ID: def456...
   创建时间: 2024-01-15 09:15:00
   消息数: 15

你: show_history
📝 会话历史: IU最新资讯研究
🆔 会话ID: abc123...
==================================================
1. 👤 USER
   ⏰ 2024-01-15 10:30:15
   💬 搜索IU的最新消息

2. 🤖 ASSISTANT  
   ⏰ 2024-01-15 10:30:45
   💬 我来帮你搜索IU的最新资讯...
```

### API接口会话管理

除了命令行，也可以通过API管理会话：

```bash
# 获取所有会话
curl http://localhost:8000/sessions

# 创建新会话
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "我的新会话"}'

# 获取特定会话详情
curl http://localhost:8000/sessions/{session_id}

# 删除会话
curl -X DELETE http://localhost:8000/sessions/{session_id}

# 在指定会话中聊天
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好",
    "session_id": "abc123...",
    "provider": "ollama"
  }'
```

### 会话管理最佳实践

**1. 按主题组织会话**
```bash
new_session 项目开发讨论
new_session 学习笔记整理  
new_session 日常问题咨询
```

**2. 定期查看历史**
```bash
list_sessions              # 查看所有会话概览
switch_session <old_id>    # 切换到旧会话
show_history              # 回顾历史对话
```

## 🚀 Token 优化

### 智能消息过滤

为了节省 Token 使用，系统内置了智能过滤机制，自动压缩冗长的工具调用结果：

#### 核心特性

- **🎯 智能识别**：自动识别大型工具结果（如 `list_tool_modules`、`list_available_tools`）
- **📝 保留关键信息**：保留最近 5 条消息的完整内容，确保 AI 能正常工作
- **🔄 按需重调用**：过滤后的工具结果提示用户可重新调用获取最新信息
- **⚙️ 可配置**：支持通过配置文件自定义过滤行为

#### 过滤效果示例

**过滤前：**
```
<TOOL_RESULT>
📦 工具模块列表 (10 个):
💡 提示：此列表仅显示工具名称和描述，不包含详细参数...
📁 FILE_MANAGER:
  • FILE_MANAGER (模块名: file_manager_tools) - 文件操作工具集合...
  [500+ 字符的详细列表]
</TOOL_RESULT>
```

**过滤后：**
```
<TOOL_RESULT>
📦 工具模块列表（略，如果想了解，请重新调用 list_tool_modules 工具）
</TOOL_RESULT>
```

**Token 节省：** 从 525 个字符压缩到 75 个字符，节省约 86%

#### 配置选项

在 `config.json` 中可以自定义过滤行为：

```json
{
  "token_optimization": {
    "enabled": true,                    // 是否启用 Token 优化
    "filter_old_tool_results": true,   // 是否过滤旧的工具结果
    "keep_recent_messages": 5,         // 保留最近几条消息不过滤
    "filter_tools": [                  // 需要过滤的工具列表
      "list_tool_modules",
      "list_available_tools"
    ],
    "filter_threshold": 1000           // 工具结果超过多少字符时进行过滤
  }
}
```

#### 工作原理

1. **消息历史处理**：构建对话历史时检查每条消息
2. **新旧区分**：保留最近N条消息（默认5条）的完整内容
3. **智能过滤**：对较旧消息中的大型工具结果进行压缩
4. **提示保留**：用简短提示替换冗长内容，保持上下文连贯

#### 使用建议

- **默认启用**：建议保持功能开启，可大幅节省 Token 使用
- **长对话友好**：特别适合需要频繁调用工具的长时间对话
- **无感知操作**：用户和 AI 都无需关心过滤过程，自动运行
- **灵活控制**：可通过配置文件按需调整过滤策略```

**3. 工作流示例**
```bash
# 早上开始工作
python3.11 main.py
# 系统自动加载昨天的工作会话

# 开始新的研究主题
new_session 新技术调研

# 工作中途需要查看其他内容
list_sessions
switch_session <另一个会话ID>

# 工作结束前查看今天的讨论
show_history
```

## 🛠️ 可用工具模块

## ⚙️ 配置

在 `config.json` 中配置默认行为：

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
      "enabled": true,
      "api_key": "your-api-key-here",
      "model": "qwen-plus-latest"
    },
    "openrouter": {
      "enabled": false,
      "api_key": "",
      "model": "anthropic/claude-sonnet-4"
    }
  },
  "tool_modules": {
    "auto_load": true,
    "interactive_selection": true,
    "default_modules": ["file_manager_tools"],
    "module_configs": {
      "file_manager": {
        "max_file_size": 1048576,
        "allowed_extensions": [".txt", ".md", ".py"]
      }
    }
  }
}
```

## 🤖 模型管理

### 支持的模型提供商

- **Ollama**: 本地部署的开源模型
- **通义千问 (Qwen)**: 阿里云的大语言模型服务
- **OpenRouter**: 提供多种AI模型的统一API

### 模型切换方式

#### 1. 启动时选择模型

```bash
# 列出所有可用模型
python3.11 main.py --list-models

# 指定模型启动
python3.11 main.py --model ollama
python3.11 main.py --model qwen

# 交互式选择（当有多个可用模型时会自动提示）
python3.11 main.py
```

#### 2. 通过聊天命令切换

```bash
# 查看当前模型
get_current_model

# 列出所有可用模型
list_models

# 切换模型
switch_model ollama

# 查看详细配置
show_model_config
```

#### 3. 通过聊天命令配置模型

```bash
# 启用/禁用模型
configure_model ollama enabled=true

# 设置API密钥
configure_model qwen api_key="your-api-key" enabled=true


# 设置本地服务地址
configure_model ollama host="http://localhost:11434" enabled=true

# 设置默认模型和备用模型
set_default_model ollama "qwen,openrouter"
```

#### 4. 通过API接口管理

```bash
# 获取所有模型信息
curl http://localhost:8000/models

# 获取当前使用的模型
curl http://localhost:8000/models/current

# 切换默认模型
curl -X POST http://localhost:8000/models/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "ollama"}'

# 更新模型配置
curl -X PUT http://localhost:8000/models/ollama/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "enabled": true,
    "model": "qwen3:8b",
    "host": "http://localhost:11434"
  }'

# 设置默认模型和备用模型
curl -X PUT http://localhost:8000/models/default \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "fallback_providers": ["qwen", "openrouter"]
  }'
```

### 模型配置说明

#### Ollama 配置
```json
{
  "ollama": {
    "enabled": true,
    "host": "http://localhost:11434",  // Ollama服务地址
    "model": "qwen3:8b"                // 模型名称
  }
}
```

#### 通义千问 配置
```json
{
  "qwen": {
    "enabled": true,
    "api_key": "your-dashscope-api-key",  // DashScope API密钥
    "model": "qwen-plus-latest"           // 模型版本
  }
}
```

#### OpenRouter 配置
```json
{
  "openrouter": {
    "enabled": true,
    "api_key": "your-openrouter-api-key",      // OpenRouter API密钥
    "model": "anthropic/claude-sonnet-4"     // 模型名称
  }
}
```

## 🌐 API 使用

### 聊天接口

```bash
# 发送消息
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我读取 README.md 文件", "stream": false}'

# 流式聊天
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "当前时间是什么？", "stream": true}'
```

### 工具模块管理

```bash
# 获取工具模块列表
curl http://localhost:8000/tool-modules

# 加载工具模块
curl -X POST http://localhost:8000/tool-modules/load \
  -H "Content-Type: application/json" \
  -d '{"modules": ["file_manager_tools"]}'

# 获取模块类别
curl http://localhost:8000/tool-modules/categories
```

## 📚 使用场景

### 场景1：文档处理

```bash
# 只加载文件管理工具
python3.11 -m ai_chat_tools.main --load-modules file_manager_tools
```

然后可以使用 AI 来：
- 读取和分析文档
- 搜索和替换文本
- 批量处理文件

### 场景2：文档处理

```bash
# 只加载文件管理工具
python3.11 -m ai_chat_tools.main --load-modules file_manager_tools
```

然后可以使用 AI 来：
- 读取和分析文档
- 搜索和替换文本
- 批量处理文件

### 场景3：全功能使用

```bash
# 加载所有工具模块
python3.11 -m ai_chat_tools.main --load-modules file_manager_tools
```

## 🔧 自定义工具模块

### 创建新模块

1. 在 `ai_chat_tools/user_tool_modules/` 目录下创建 Python 文件
2. 添加模块信息注释
3. 定义工具函数

```python
# ai_chat_tools/user_tool_modules/my_tools.py

# MODULE_DESCRIPTION: 我的自定义工具集合
# MODULE_CATEGORY: custom
# MODULE_AUTHOR: Your Name
# MODULE_VERSION: 1.0.0

from ..tool_manager import register_tool

@register_tool(
    name="my_tool",
    description="我的工具描述",
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
    """我的工具实现"""
    return f"处理结果: {param}"
```

### 配置模块

在 `config.json` 中添加模块配置：

```json
{
  "tool_modules": {
    "default_modules": ["my_tools"],
    "module_configs": {
      "my_tools": {
        "custom_setting": "value"
      }
    }
  }
}
```

## 📖 API 文档

启动服务后，访问 http://localhost:8000/docs 查看完整的 API 文档。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**提示**: 这个框架设计为模块化和可扩展的，你可以根据需要加载不同的工具模块，也可以轻松创建自己的工具模块。

## 🛠️ 自定义工具

### 添加简单工具

对于简单的、单个的工具，可以在 `ai_chat_tools/user_tools.py` 中添加：

```python
@register_tool(
    name="text_length",
    description="计算文本长度",
    schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要计算长度的文本"
            }
        },
        "required": ["text"]
    }
)
def text_length(text: str) -> str:
    """计算文本长度"""
    return f"文本长度: {len(text)} 个字符"
```

### 🆕 创建工具模块

对于复杂的、相关的工具集合，建议创建工具模块：

**1. 创建模块文件**
在 `ai_chat_tools/user_tool_modules/` 目录下创建新的 `.py` 文件，例如 `my_tools.py`：

```python
# MODULE_DESCRIPTION: 我的自定义工具集合
# MODULE_CATEGORY: 自定义工具
# MODULE_VERSION: 1.0.0
# MODULE_AUTHOR: 你的名字

from ..tool_manager import register_tool

@register_tool(
    name="tool1",
    description="工具1的描述"
)
def tool1() -> str:
    return "工具1的结果"

@register_tool(
    name="tool2", 
    description="工具2的描述"
)
def tool2() -> str:
    return "工具2的结果"
```

**2. 模块配置**
在 `config.json` 中添加模块特定配置：

```json
{
  "tool_modules": {
    "auto_load": ["my_tools"],
    "module_configs": {
      "my_tools": {
        "setting1": "value1",
        "setting2": "value2"
      }
    }
  }
}
```

**3. 使用模块配置**
在工具函数中获取配置：

```python
from ..config import get_tool_module_config

@register_tool(...)
def my_tool():
    config = get_tool_module_config('my_tools')
    setting = config.get('setting1', 'default_value')
    return f"使用配置: {setting}"
```

### 工具开发最佳实践

- **简单工具** → `user_tools.py`：适合单一功能的工具
- **工具模块** → `user_tool_modules/`：适合功能完整的工具集合
- **核心工具** → `tools.py`：仅用于系统级功能（谨慎修改）

**注意事项：**
- 所有工具函数必须返回字符串类型
- 使用清晰的工具名称和描述
- 提供完整的 JSON Schema 参数定义
- 相关工具放在同一模块中 