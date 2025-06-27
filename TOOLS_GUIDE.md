# AI Chat Tools - 工具开发指南

## 📁 工具系统架构

工具系统采用分离设计，职责清晰：

```
ai_chat_tools/
├── tool_manager.py      # 🔧 工具管理器（核心逻辑，用户不需要修改）
├── tools.py             # 🛠️ 内置工具和示例工具
├── user_tools.py        # 👤 用户自定义工具（推荐在这里添加）
├── config.py            # ⚙️ 系统配置（包含用户确认设置）
└── user_confirmation.py # 🔒 用户确认管理器
```

## 🎯 设计理念

- **`tool_manager.py`**: 包含工具注册、管理、执行的核心逻辑，用户不需要修改
- **`tools.py`**: 包含内置工具和一些示例工具，用户可以参考
- **`user_tools.py`**: 专门用于用户添加自定义工具，保持代码整洁
- **`config.py`**: 系统配置文件，包含用户确认策略设置
- **`user_confirmation.py`**: 用户确认管理器，处理危险操作的确认逻辑

## 🔒 用户确认系统

为了保护用户数据安全，系统内置了用户确认机制。对于可能造成数据损失或系统变更的操作，AI会在执行前请求用户确认。

### 确认策略

系统支持三种确认策略：
- **ask**: 每次都询问用户（默认）
- **allow**: 自动同意执行
- **deny**: 自动拒绝执行

### 确认类别

操作按风险类型分为以下类别：
- **file_write**: 文件写入操作
- **file_delete**: 文件删除操作  
- **file_modify**: 文件修改操作
- **system_command**: 系统命令执行
- **network_request**: 网络请求
- **general**: 一般操作

### 策略优先级

系统按以下优先级应用确认策略：
1. **工具级别策略** - 针对特定工具的设置
2. **类别级别策略** - 针对操作类别的设置
3. **默认策略** - 全局默认设置

### 管理确认设置

使用 `manage_confirmation_settings` 工具来管理确认偏好：

```python
# 查看当前设置
await tool_registry.execute("manage_confirmation_settings", {"action": "show"})

# 设置默认策略为自动同意
await tool_registry.execute("manage_confirmation_settings", {
    "action": "set_default", 
    "strategy": "allow"
})

# 设置文件写入操作为自动拒绝
await tool_registry.execute("manage_confirmation_settings", {
    "action": "set_category",
    "category": "file_write", 
    "strategy": "deny"
})

# 设置特定工具策略
await tool_registry.execute("manage_confirmation_settings", {
    "action": "set_tool",
    "tool_name": "write_file",
    "strategy": "ask"
})

# 重置所有设置
await tool_registry.execute("manage_confirmation_settings", {"action": "reset"})
```

### 确认对话示例

当AI尝试执行需要确认的操作时，会显示如下对话：

```
🔒 用户确认请求

工具: write_file
描述: 写入文件内容
类别: file_write
风险等级: medium

参数:
- filename: important_data.txt
- content: 新的重要数据...

⚠️  此操作可能会覆盖现有文件内容，请谨慎确认。

请选择操作:
  y - 同意执行
  n - 拒绝执行  
  a - 总是同意此类操作
  d - 总是拒绝此类操作

您的选择: 
```

## 🚀 添加工具的三种方式

### 方式1：在 `user_tools.py` 中添加（推荐）

```python
# ai_chat_tools/user_tools.py
from .tool_manager import register_tool

@register_tool(
    name="my_weather",
    description="获取天气信息"
)
def get_weather(city: str) -> str:
    """获取天气信息"""
    # 你的实现代码
    return f"{city}今天天气晴朗，温度25°C"
```

### 方式2：在 `tools.py` 中添加

```python
# ai_chat_tools/tools.py
@register_tool(
    name="my_tool",
    description="我的工具"
)
def my_tool(param: str) -> str:
    return f"处理结果: {param}"
```

### 方式3：在外部文件中添加

```python
# my_custom_tools.py
from ai_chat_tools import register_tool

@register_tool(name="external_tool", description="外部工具")
def external_tool(data: str) -> str:
    return f"外部处理: {data}"

# 然后在主程序中导入
import my_custom_tools
```

## 📝 工具定义语法

### 基础语法

```python
@register_tool(
    name="tool_name",           # 工具名称（必需）
    description="工具描述"       # 工具描述（必需）
)
def my_function(param: str) -> str:  # ⚠️ 必须返回字符串类型
    """函数文档字符串"""
    return "结果"
```

### 带确认机制的工具

```python
@register_tool(
    name="dangerous_tool",
    description="危险操作工具",
    requires_confirmation=True,        # 需要用户确认
    confirmation_category="file_write", # 确认类别
    risk_level="high"                  # 风险等级: low, medium, high
)
def dangerous_tool(filename: str) -> str:
    """执行危险操作的工具"""
    # 这个工具会在执行前请求用户确认
    return f"已执行危险操作: {filename}"
```

### 带Schema的工具

```python
@register_tool(
    name="advanced_tool",
    description="高级工具",
    schema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "参数1描述"
            },
            "param2": {
                "type": "integer",
                "description": "参数2描述",
                "default": 10
            }
        },
        "required": ["param1"]
    }
)
def advanced_tool(param1: str, param2: int = 10) -> str:
    return f"处理 {param1} 和 {param2}"
```

### 异步工具

```python
import asyncio
import httpx

@register_tool(
    name="async_tool",
    description="异步工具"
)
async def async_tool(url: str) -> str:
    """异步HTTP请求"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return f"状态码: {response.status_code}"
```

## ⚠️ 重要：返回值格式要求

### 统一返回字符串
所有工具**必须返回字符串类型**，这是系统的核心要求：

```python
# ✅ 正确的格式
@register_tool(name="good_tool", description="正确的工具")
def good_tool(param: str) -> str:  # 返回类型注解为 str
    return f"处理结果: {param}"    # 返回字符串

# ❌ 不推荐的格式（会显示警告）
@register_tool(name="legacy_tool", description="旧格式工具")
def legacy_tool() -> int:  # 会显示警告
    return 42  # 会自动转换为字符串 "42"
```

### ToolResult 对象
工具执行后会返回 `ToolResult` 对象，包含完整的调用信息：

```python
# 执行工具
result = await tool_registry.execute("calculator", {"expression": "2+3"})

# 获取简洁结果
print(result.to_string())  # "5"

# 检查执行状态
if result.success:
    print(f"计算结果: {result.data}")
    print(f"执行时间: {result.execution_time:.3f}秒")
else:
    print(f"计算失败[{result.error_code}]: {result.error_message}")
```

## 🔧 内置工具列表

当前系统包含以下内置工具：

### 基础工具
- `calculator`: 数学计算器
- `get_time`: 获取当前时间

### 文本处理工具
- `text_length`: 计算文本长度
- `reverse_text`: 反转文本
- `word_count`: 统计单词数量

### 文件管理工具（需要确认）
- `write_file`: 写入文件内容（file_write类别，medium风险）
- `replace_in_file`: 替换文件内容（file_modify类别，high风险）
- `read_file`: 读取文件内容（无需确认）
- `search_in_file`: 搜索文件内容（无需确认）
- `list_files`: 列出文件（无需确认）

### 系统管理工具
- `manage_confirmation_settings`: 管理用户确认设置

## 💡 工具开发最佳实践

### 1. 命名规范
```python
# ✅ 好的命名
@register_tool(name="send_email", description="发送邮件")
@register_tool(name="get_weather", description="获取天气")

# ❌ 避免的命名
@register_tool(name="tool1", description="工具")
@register_tool(name="func", description="函数")
```

### 2. 安全性考虑
```python
# 对于可能造成数据损失的操作，添加确认机制
@register_tool(
    name="delete_files",
    description="批量删除文件",
    requires_confirmation=True,
    confirmation_category="file_delete",
    risk_level="high"
)
def delete_files(pattern: str) -> str:
    """批量删除匹配模式的文件"""
    # 实现删除逻辑
    return f"已删除匹配 {pattern} 的文件"
```

### 3. 错误处理
```python
@register_tool(name="safe_tool", description="安全的工具")
def safe_tool(filename: str) -> str:
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"文件 {filename} 不存在"
    except Exception as e:
        return f"读取失败: {str(e)}"
```

### 4. 参数验证
```python
@register_tool(name="validate_tool", description="验证参数的工具")
def validate_tool(email: str) -> str:
    if "@" not in email:
        return "错误：邮箱格式不正确"
    
    return f"邮箱 {email} 格式正确"
```

### 5. 返回格式
```python
@register_tool(name="format_tool", description="格式化返回的工具")
def format_tool(data: str) -> str:
    # 返回结构化的字符串
    return f"处理结果:\n- 输入: {data}\n- 状态: 成功\n- 时间: {datetime.now()}"
```

### 6. 性能监控
```python
@register_tool(name="monitored_tool", description="监控性能的工具")
def monitored_tool(data: str) -> str:
    import time
    start_time = time.time()
    
    # 处理逻辑
    result = process_data(data)
    
    execution_time = time.time() - start_time
    return f"处理完成，耗时: {execution_time:.3f}秒，结果: {result}"
```

## 🧪 测试工具

### 测试单个工具
```python
import asyncio
from ai_chat_tools.tool_manager import tool_registry

async def test_my_tool():
    result = await tool_registry.execute("my_tool", {"param": "test"})
    print(f"成功: {result.success}")
    print(f"结果: {result.to_string()}")
    print(f"执行时间: {result.execution_time:.3f}秒")

asyncio.run(test_my_tool())
```

### 查看所有工具
```python
from ai_chat_tools.tool_manager import tool_registry

tools = tool_registry.list_tools()
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")
```

### 获取工具Schema
```python
from ai_chat_tools.tool_manager import tool_registry

schema = tool_registry.get_tool_schema("my_tool")
print(schema)
```

### 测试确认设置
```python
import asyncio
from ai_chat_tools.tool_manager import tool_registry

async def test_confirmation():
    # 查看当前确认设置
    result = await tool_registry.execute("manage_confirmation_settings", {"action": "show"})
    print("当前设置:", result.to_string())
    
    # 设置文件写入为自动同意
    result = await tool_registry.execute("manage_confirmation_settings", {
        "action": "set_category",
        "category": "file_write", 
        "strategy": "allow"
    })
    print("设置结果:", result.to_string())

asyncio.run(test_confirmation())
```

## 📚 实际示例

### 示例1：安全的文件操作工具
```python
@register_tool(
    name="secure_file_operations",
    description="安全的文件操作工具",
    requires_confirmation=True,
    confirmation_category="file_modify",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "操作类型: read, write, delete"
            },
            "filename": {
                "type": "string",
                "description": "文件名"
            },
            "content": {
                "type": "string",
                "description": "写入内容（仅write操作需要）"
            }
        },
        "required": ["operation", "filename"]
    }
)
def secure_file_operations(operation: str, filename: str, content: str = "") -> str:
    try:
        if operation == "read":
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        elif operation == "write":
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"已写入文件 {filename}"
        elif operation == "delete":
            import os
            os.remove(filename)
            return f"已删除文件 {filename}"
        else:
            return "不支持的操作类型"
    except Exception as e:
        return f"操作失败: {str(e)}"
```

### 示例2：网络API调用工具
```python
import httpx

@register_tool(
    name="api_call",
    description="调用外部API",
    requires_confirmation=True,
    confirmation_category="network_request",
    risk_level="low",
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "API URL"},
            "method": {"type": "string", "description": "HTTP方法"},
            "data": {"type": "object", "description": "请求数据"}
        },
        "required": ["url", "method"]
    }
)
async def api_call(url: str, method: str = "GET", data: dict = None) -> str:
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            else:
                return f"不支持的HTTP方法: {method}"
            
            return f"状态码: {response.status_code}, 响应: {response.text[:200]}..."
    except Exception as e:
        return f"API调用失败: {str(e)}"
```

## 🔄 错误处理系统

系统定义了标准的错误码：
- `TOOL_NOT_FOUND`: 工具不存在
- `PARAMETER_ERROR`: 参数错误
- `EXECUTION_ERROR`: 执行时异常
- `TYPE_CONVERSION_ERROR`: 类型转换错误
- `VALIDATION_ERROR`: 验证错误
- `USER_DENIED`: 用户拒绝执行

```python
# 错误处理示例
result = await tool_registry.execute("nonexistent", {})
if result.error_code == "TOOL_NOT_FOUND":
    print("工具不存在，请检查工具名称")
elif result.error_code == "USER_DENIED":
    print("用户拒绝执行此操作")
```

## 🔄 重新加载工具

如果你修改了工具文件，需要重启应用程序来加载新的工具：

```bash
# 重启API服务器
python3.11 -m ai_chat_tools.main
```

## 📞 获取帮助

- 查看 `ai_chat_tools/tools.py` 了解内置工具实现
- 查看 `ai_chat_tools/user_tools.py` 了解更多示例
- 运行 `python3.11 test_tools_only.py` 测试工具功能
- 使用 `manage_confirmation_settings` 工具管理安全设置

---

**💡 提示**: 推荐在 `user_tools.py` 中添加你的工具，记住所有工具必须返回字符串类型！对于可能造成数据损失的操作，请添加适当的确认机制。 