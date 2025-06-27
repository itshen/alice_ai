# AI Chat Tools API 测试指南

本文档提供了完整的API测试CURL命令，方便在Postman或命令行中测试AI Chat Tools的各种功能。

## 🚀 快速开始

### 启动API服务器
```bash
python3.11 run.py
# 选择选项 7 (快速启动)
# 或者直接运行:
python3.11 -m ai_chat_tools.main --port 8000
```

## 📡 API端点测试

### 1. **基础信息**

#### 根路径
```bash
curl -X GET "http://localhost:8000/"
```

#### 获取可用工具
```bash
curl -X GET "http://localhost:8000/tools"
```

#### 获取可用模型提供商
```bash
curl -X GET "http://localhost:8000/providers"
```

#### 获取配置信息
```bash
curl -X GET "http://localhost:8000/config"
```

### 2. **会话管理**

#### 创建新会话
```bash
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试会话",
    "provider": "qwen"
  }'
```

#### 获取会话列表
```bash
curl -X GET "http://localhost:8000/sessions"
```

#### 获取会话详情
```bash
curl -X GET "http://localhost:8000/sessions/{session_id}"
```

#### 删除会话
```bash
curl -X DELETE "http://localhost:8000/sessions/{session_id}"
```

### 3. **聊天功能**

#### 数学计算工具测试 (非流式)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我计算 100 * 25 + 50",
    "provider": "qwen",
    "stream": false,
    "debug": false
  }'
```

**返回格式 (分角色版):**
```json
{
  "message": "<<<USER>>>\n帮我计算 100 * 25 + 50\n<<<END_USER>>>\n\n<<<ASSISTANT>>>\n我来帮你计算 100 * 25 + 50。\n\n<tool_call>\n<name>calculate</name>\n<parameters>\n{\"expression\": \"100 * 25 + 50\"}\n</parameters>\n</tool_call>\n<<<END_ASSISTANT>>>\n\n<<<USER>>>\n\n工具 calculate 的执行结果: 2550\n\n<<<END_USER>>>\n\n<<<ASSISTANT>>>\n计算结果是：2550\n<<<END_ASSISTANT>>>"
}
```

**格式说明:**
- `<<<USER>>>` ... `<<<END_USER>>>` - 用户消息段
- `<<<ASSISTANT>>>` ... `<<<END_ASSISTANT>>>` - AI助手消息段  
- `<<<TOOL_RESULT>>>` ... `<<<END_TOOL_RESULT>>>` - 工具执行结果段
- 使用ANSI安全字符，避免与正常文本冲突
- 按对话时间顺序排列，完整展现多轮交互过程

**工具结果包含信息:**
- 工具调用名称
- 调用参数
- 执行时间（秒）
- 执行状态（成功/失败）
- 返回结果或错误信息
- 错误码（如果失败）

#### 数学计算工具测试 (调试模式)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "计算一下 (100 + 200) * 3",
    "provider": "qwen", 
    "stream": false,
    "debug": true
  }'
```

#### 时间查询工具测试 (流式)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "现在几点了？",
    "provider": "qwen",
    "stream": true,
    "debug": false
  }' \
  --no-buffer
```

**流式返回格式:**
- 直接返回纯文本内容，无JSON包装
- 适合直接拼接到对话消息列表中
- 包含工具调用过程和最终回答

#### 时间查询工具测试 (流式调试模式)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "告诉我当前时间",
    "provider": "qwen",
    "stream": true,
    "debug": true
  }' \
  --no-buffer
```

#### 文本处理工具测试 (调试模式)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我计算这段文本的长度：Hello World",
    "provider": "qwen",
    "stream": true,
    "debug": true
  }' \
  --no-buffer
```

#### 文本反转工具测试
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请反转这个文本：AI Chat Tools",
    "provider": "qwen",
    "stream": false,
    "debug": true
  }'
```

#### 单词统计工具测试
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "统计这段话的单词数：This is a test sentence for word counting",
    "provider": "qwen",
    "stream": false,
    "debug": true
  }'
```

#### 复杂多工具调用 (调试模式)
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "先查询当前时间，然后计算100+200，最后统计文本长度：Hello AI",
    "provider": "qwen",
    "stream": true,
    "debug": true
  }' \
  --no-buffer
```

#### 指定会话ID聊天
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "继续之前的对话",
    "provider": "qwen",
    "session_id": "你的会话ID",
    "stream": false,
    "debug": true
  }'
```

#### 指定特定工具聊天
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我计算一下数学题",
    "provider": "qwen",
    "tools": ["calculator"],
    "stream": false,
    "debug": true
  }'
```

#### 多个工具组合使用
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我处理文本相关任务",
    "provider": "qwen",
    "tools": ["text_length", "reverse_text", "word_count"],
    "stream": false,
    "debug": true
  }'
```

## 📋 Postman集合导入

你可以直接复制以下JSON到Postman导入完整的测试集合：

```json
{
  "info": {
    "name": "AI Chat Tools API",
    "description": "AI工具调用框架API测试集合",
    "version": "1.0.0"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000"
    }
  ],
  "item": [
    {
      "name": "基础信息",
      "item": [
        {
          "name": "根路径",
          "request": {
            "method": "GET",
            "url": "{{baseUrl}}/"
          }
        },
        {
          "name": "获取工具列表",
          "request": {
            "method": "GET",
            "url": "{{baseUrl}}/tools"
          }
        },
        {
          "name": "获取模型提供商",
          "request": {
            "method": "GET",
            "url": "{{baseUrl}}/providers"
          }
        }
      ]
    },
    {
      "name": "会话管理",
      "item": [
        {
          "name": "创建会话",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"title\": \"测试会话\",\n  \"provider\": \"qwen\"\n}"
            },
            "url": "{{baseUrl}}/sessions"
          }
        },
        {
          "name": "获取会话列表",
          "request": {
            "method": "GET",
            "url": "{{baseUrl}}/sessions"
          }
        }
      ]
    },
    {
      "name": "工具测试",
      "item": [
        {
          "name": "计算器工具(普通)",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"message\": \"帮我计算 100 * 25 + 50\",\n  \"provider\": \"qwen\",\n  \"stream\": false,\n  \"debug\": false\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        },
        {
          "name": "计算器工具(调试)",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"message\": \"计算一下 (100 + 200) * 3\",\n  \"provider\": \"qwen\",\n  \"stream\": false,\n  \"debug\": true\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        },
        {
          "name": "时间查询工具",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"message\": \"现在几点了？\",\n  \"provider\": \"qwen\",\n  \"stream\": true,\n  \"debug\": true\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        },
        {
          "name": "文本长度计算",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw", 
              "raw": "{\n  \"message\": \"帮我计算这段文本的长度：Hello World\",\n  \"provider\": \"qwen\",\n  \"stream\": false,\n  \"debug\": true\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        },
        {
          "name": "文本反转工具",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"message\": \"请反转这个文本：AI Chat Tools\",\n  \"provider\": \"qwen\",\n  \"stream\": false,\n  \"debug\": true\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        },
        {
          "name": "单词统计工具",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"message\": \"统计这段话的单词数：This is a test sentence for word counting\",\n  \"provider\": \"qwen\",\n  \"stream\": false,\n  \"debug\": true\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        },
        {
          "name": "多工具组合调用",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"message\": \"先查询当前时间，然后计算100+200，最后统计文本长度：Hello AI\",\n  \"provider\": \"qwen\",\n  \"stream\": true,\n  \"debug\": true\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        },
        {
          "name": "指定工具使用",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"message\": \"帮我处理文本相关任务\",\n  \"provider\": \"qwen\",\n  \"tools\": [\"text_length\", \"reverse_text\", \"word_count\"],\n  \"stream\": false,\n  \"debug\": true\n}"
            },
            "url": "{{baseUrl}}/chat"
          }
        }
      ]
    },
    {
      "name": "模型管理",
      "item": [
        {
          "name": "获取所有模型信息",
          "request": {
            "method": "GET",
            "url": "{{baseUrl}}/models"
          }
        },
        {
          "name": "获取当前使用的模型",
          "request": {
            "method": "GET",
            "url": "{{baseUrl}}/models/current"
          }
        },
        {
          "name": "切换默认模型",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"provider\": \"qwen\"\n}"
            },
            "url": "{{baseUrl}}/models/switch"
          }
        },
        {
          "name": "更新模型配置 - Ollama",
          "request": {
            "method": "PUT",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"provider\": \"ollama\",\n  \"enabled\": true,\n  \"model\": \"qwen3:8b\",\n  \"host\": \"http://localhost:11434\"\n}"
            },
            "url": "{{baseUrl}}/models/ollama/config"
          }
        },
        {
          "name": "更新模型配置 - Qwen",
          "request": {
            "method": "PUT",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"provider\": \"qwen\",\n  \"enabled\": true,\n  \"api_key\": \"your-api-key-here\",\n  \"model\": \"qwen-plus-latest\"\n}"
            },
            "url": "{{baseUrl}}/models/qwen/config"
          }
        },
        {
          "name": "设置默认模型和备用模型",
          "request": {
            "method": "PUT",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"provider\": \"ollama\",\n  \"fallback_providers\": [\"qwen\", \"openrouter\"]\n}"
            },
            "url": "{{baseUrl}}/models/default"
          }
        }
      ]
    }
  ]
}
```

## 🔧 参数说明

### 聊天接口参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | ✅ | 用户消息内容 |
| `provider` | string | ❌ | 模型提供商 (`qwen`, `ollama`, `openrouter`) |
| `stream` | boolean | ❌ | 是否流式输出，默认 `false` |
| `debug` | boolean | ❌ | 是否显示调试信息，默认 `false` |
| `session_id` | string | ❌ | 指定会话ID，不指定则创建新会话 |
| `tools` | array | ❌ | 指定使用的工具列表，不指定则使用所有工具 |

### 会话创建参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ❌ | 会话标题，默认"新对话" |
| `provider` | string | ❌ | 模型提供商 |

## 🛠️ 可用工具列表

根据 `tools.py` 文件，当前系统包含以下内置工具：

### 1. **calculator** - 计算器
- **描述**: 执行数学计算
- **参数**: `expression` (string) - 数学表达式，如 '2 + 3 * 4'
- **示例**: "帮我计算 100 * 25 + 50"

### 2. **get_time** - 时间查询
- **描述**: 获取当前时间
- **参数**: 无参数
- **示例**: "现在几点了？"

### 3. **text_length** - 文本长度计算
- **描述**: 计算文本长度
- **参数**: `text` (string) - 要计算长度的文本
- **示例**: "计算这段文本的长度：Hello World"

### 4. **reverse_text** - 文本反转
- **描述**: 反转文本
- **参数**: `text` (string) - 要反转的文本
- **示例**: "反转这个文本：AI Chat Tools"

### 5. **word_count** - 单词统计
- **描述**: 统计单词数量
- **参数**: `text` (string) - 要统计的文本
- **示例**: "统计这段话的单词数：This is a test"

## 🎯 测试重点

### 1. **Debug模式对比**
- 测试 `debug: true` 和 `debug: false` 的输出差异
- 调试模式会显示工具的实际返回值：
  ```
  [工具执行结果]
  🔧 calculator: 2550
  [继续生成回答...]
  ```

### 2. **流式vs非流式**
- 非流式：一次性返回完整结果
- 流式：实时输出，使用SSE格式

### 3. **多工具调用**
- 测试复杂任务的工具链调用
- 观察AI如何自动选择和组合工具

### 4. **工具参数验证**
- 测试各工具的参数验证和错误处理
- 例如：给计算器传入无效表达式

### 5. **会话管理**
- 测试会话创建、查询、删除
- 验证会话历史记录功能

## 🚨 注意事项

1. **端口检查**：确保API服务器在正确端口运行
2. **工具注册**：当前可用工具已在 `tools.py` 中注册
3. **流式测试**：在Postman中测试流式接口时，注意观察实时响应
4. **错误处理**：注意观察各种错误情况的API响应
5. **计算器安全**：计算器工具有安全限制，不允许执行危险操作

## 🔍 常见问题

### Q: 工具调用失败？
A: 检查工具是否正确注册，可以先调用 `/tools` 接口查看可用工具。当前可用工具：
- `calculator` - 数学计算
- `get_time` - 获取时间
- `text_length` - 文本长度
- `reverse_text` - 文本反转
- `word_count` - 单词统计

### Q: 流式响应看不到实时效果？
A: 确保使用 `--no-buffer` 参数，或在Postman中观察响应流

### Q: 会话ID从哪里获取？
A: 调用 `/sessions` 接口获取会话列表，或创建会话时返回的ID

### Q: 如何测试不同模型？
A: 修改 `provider` 参数为 `ollama` 或 `openrouter`（需要相应配置）

### Q: 计算器不能执行某些操作？
A: 为了安全，计算器限制了可用字符和操作，不允许 import、exec、eval 等危险操作

---

🎉 现在你可以在Postman中愉快地测试AI Chat Tools的所有功能了！ 