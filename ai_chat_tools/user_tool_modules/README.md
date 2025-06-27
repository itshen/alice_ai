# AI聊天工具模块说明文档

这个目录包含了各种用户定义的工具模块，每个模块提供特定的功能集合。

## 已有模块列表

### 1. 网页抓取（联网）工具 (`web_scraping_tools.py`)

**功能描述：** 提供完整的网页抓取和API调用功能

**主要工具：**
- `fetch_webpage_content` - 获取网页纯文本内容（自动过滤JS、CSS、广告等）
- `fetch_webpage_summary` - 获取网页摘要信息（标题、描述、内容片段）
- `extract_webpage_links` - 提取网页中的所有链接
- `check_webpage_status` - 检查网页可访问性和基本信息
- `api_get_request` - 执行GET API请求
- `api_post_request` - 执行POST API请求
- `fetch_json_data` - 获取和分析JSON格式的API数据
- `search_bing` - 使用关键词搜索Bing搜索引擎，获取搜索结果

**使用场景：**
- 获取网页内容用于AI分析（节省上下文长度）
- API数据获取和处理
- 网站链接爬取和分析
- 网页状态监控

**特点：**
- 智能内容提取，自动过滤无关元素
- 支持多种编码自动检测
- 内容长度限制，优化AI上下文使用
- JSON数据自动保存和结构分析
- 支持自定义请求头和参数

## 📚 工具模块概览

| 模块名称 | 类别 | 描述 | 工具数量 |
|---------|------|------|----------|
| [web_scraper_tools](#-网页抓取工具-web_scraper_tools) | web_scraping | 网页内容抓取工具集合 | 6个 |
| [file_manager_tools](#-文件管理工具-file_manager_tools) | file_management | 文件读写、搜索、管理工具 | 5个 |
| [text_processing_tools](#-文本处理工具-text_processing_tools) | text_processing | 文本转换、编码、加密、分析工具 | 30+个 |
| [time_utils_tools](#-时间工具-time_utils_tools) | time_management | 通用时间管理工具 | 15个 |
| [trading_time_tools](#-交易时间工具-trading_time_tools) | trading_time | 金融交易时间管理工具 | 20+个 |
| [woa_notification_tools](#-金山-woa-消息推送工具-woa_notification_tools) | notification | 金山 WOA 消息推送工具集合 | 8个 |

## 🌐 网页抓取工具 (web_scraper_tools)

**模块描述**: 网页内容抓取工具集合，用于获取网页的纯文本内容，过滤掉JS、CSS、样式等无关内容，支持多种内容提取策略，优化上下文长度。

**类别**: web_scraping  
**版本**: 1.0.0  
**作者**: Assistant

### 🔧 包含的工具

#### 1. `fetch_webpage_content` - 获取网页纯文本内容
- **功能**: 获取网页的纯文本内容，自动过滤JS、CSS、广告等无关内容
- **参数**:
  - `url` (必需): 要获取内容的网页URL
  - `timeout` (可选): 请求超时时间（秒），默认10秒
  - `max_length` (可选): 返回内容的最大长度，默认10000字符
- **特点**: 
  - 使用 readability 算法提取主要内容
  - 自动检测编码
  - 过滤广告、导航等无关元素
  - 支持内容长度限制

#### 2. `fetch_webpage_summary` - 获取网页摘要信息
- **功能**: 获取网页内容的摘要信息，包括标题、描述和主要内容片段
- **参数**:
  - `url` (必需): 要获取摘要的网页URL
  - `timeout` (可选): 请求超时时间（秒），默认10秒
  - `summary_length` (可选): 摘要内容的最大长度，默认1000字符
- **特点**:
  - 提取页面标题和meta描述
  - 智能截断，优先在句号处断开
  - 适合快速了解页面内容

#### 3. `extract_webpage_links` - 提取网页链接
- **功能**: 提取网页中的所有链接
- **参数**:
  - `url` (必需): 要提取链接的网页URL
  - `timeout` (可选): 请求超时时间（秒），默认10秒
  - `internal_only` (可选): 是否只返回内部链接（同域名），默认False
  - `max_links` (可选): 返回链接的最大数量，默认50
- **特点**:
  - 自动转换为绝对URL
  - 区分内部和外部链接
  - 自动去重

#### 4. `check_webpage_status` - 检查网页状态
- **功能**: 检查网页的可访问性和基本信息
- **参数**:
  - `url` (必需): 要检查的网页URL
  - `timeout` (可选): 请求超时时间（秒），默认10秒
- **特点**:
  - 检测响应时间和状态码
  - 统计页面元素数量
  - 显示重要HTTP头信息

### 💡 使用示例

```python
# 获取网页内容
fetch_webpage_content(url="https://example.com", max_length=5000)

# 获取网页摘要
fetch_webpage_summary(url="https://example.com", summary_length=500)

# 提取内部链接
extract_webpage_links(url="https://example.com", internal_only=True, max_links=20)

# 检查网页状态
check_webpage_status(url="https://example.com")
```

### 📋 依赖包
- requests>=2.31.0
- beautifulsoup4>=4.12.0
- html2text>=2020.1.16
- readability-lxml>=0.8.1
- chardet>=5.2.0
- lxml>=4.9.0

---

## 📁 文件管理工具 (file_manager_tools)

**模块描述**: 文件管理工具集合，提供文件读写、搜索、管理等功能。

**类别**: file_management  
**版本**: 0.0.1  
**作者**: Luoxiaoshan

### 🔧 包含的工具

#### 1. `read_file` - 读取文件内容
- **功能**: 读取文件内容
- **参数**:
  - `file_path` (必需): 要读取的文件路径
  - `encoding` (可选): 文件编码，默认为 utf-8
- **特点**: 
  - 支持文件大小限制检查
  - 自动编码检测
  - 安全性检查

#### 2. `write_file` - 写入文件内容
- **功能**: 写入内容到文件
- **参数**:
  - `file_path` (必需): 要写入的文件路径
  - `content` (必需): 要写入的内容
  - `encoding` (可选): 文件编码，默认为 utf-8
  - `append` (可选): 是否追加模式，默认为覆盖
- **特点**:
  - 支持追加和覆盖模式
  - 自动创建目录
  - 文件扩展名白名单检查

#### 3. `search_in_file` - 文件内搜索
- **功能**: 在文件中搜索文本
- **参数**:
  - `file_path` (必需): 要搜索的文件路径
  - `pattern` (必需): 搜索模式（支持正则表达式）
  - `case_sensitive` (可选): 是否区分大小写，默认为 False
- **特点**:
  - 支持正则表达式搜索
  - 显示行号和上下文
  - 限制结果数量避免过长输出

#### 4. `replace_in_file` - 文件内替换
- **功能**: 在文件中替换文本
- **参数**:
  - `file_path` (必需): 要处理的文件路径
  - `search_pattern` (必需): 要搜索的模式（支持正则表达式）
  - `replacement` (必需): 替换文本
  - `case_sensitive` (可选): 是否区分大小写，默认为 False
  - `backup` (可选): 是否创建备份文件，默认为 True
- **特点**:
  - 支持正则表达式替换
  - 自动备份原文件
  - 显示替换统计

#### 5. `list_files` - 列出目录文件
- **功能**: 列出目录中的文件
- **参数**:
  - `directory` (可选): 要列出的目录路径，默认为当前目录
  - `pattern` (可选): 文件名匹配模式（支持通配符），如 '*.py'
  - `recursive` (可选): 是否递归搜索子目录，默认为 False
- **特点**:
  - 支持通配符模式匹配
  - 递归目录搜索
  - 显示文件大小和修改时间

### 💡 使用示例

```python
# 读取文件
read_file(file_path="example.txt")

# 写入文件
write_file(file_path="output.txt", content="Hello World")

# 搜索文件内容
search_in_file(file_path="example.txt", pattern="error", case_sensitive=False)

# 替换文件内容
replace_in_file(file_path="example.txt", search_pattern="old", replacement="new")

# 列出Python文件
list_files(directory=".", pattern="*.py", recursive=True)
```

---

## 📝 文本处理工具 (text_processing_tools)

**模块描述**: 文本处理工具集合，提供文本转换、编码解码、加密解密、分析等功能。

**类别**: text_processing  
**版本**: 1.0.0  
**作者**: Assistant

### 🔧 包含的工具

#### 基础文本操作
- `to_uppercase` - 转换为大写
- `to_lowercase` - 转换为小写
- `to_title_case` - 转换为标题格式
- `reverse_text` - 反转文本
- `remove_whitespace` - 移除多余空白字符
- `extract_numbers` - 提取数字
- `extract_letters` - 提取字母

#### 编码解码工具
- `base64_encode` / `base64_decode` - Base64编码/解码
- `url_encode` / `url_decode` - URL编码/解码
- `html_encode` / `html_decode` - HTML实体编码/解码

#### 加密解密工具
- `generate_hash` - 生成哈希值（MD5、SHA1、SHA256、SHA512）
- `caesar_cipher` - 凯撒密码加密/解密
- `simple_xor_encrypt` - 简单XOR加密/解密

#### 格式化工具
- `format_json` - 格式化JSON文本
- `minify_json` - 压缩JSON文本
- `format_xml` - 格式化XML文本
- `csv_to_json` - CSV转JSON
- `json_to_csv` - JSON转CSV

#### 文本分析工具
- `count_words` - 统计单词数
- `find_all_matches` - 查找正则表达式匹配项
- `extract_emails` - 提取邮箱地址
- `extract_urls` - 提取URL链接

#### 生成工具
- `generate_uuid` - 生成UUID或随机ID
- `generate_random_text` - 生成随机文本
- `generate_password` - 生成安全密码

### 💡 使用示例

```python
# 文本转换
to_uppercase(text="hello world")

# Base64编码
base64_encode(text="Hello World")

# 生成MD5哈希
generate_hash(text="password", algorithm="md5")

# 格式化JSON
format_json(json_text='{"name":"John","age":30}', indent=2)

# 提取邮箱
extract_emails(text="联系我们：admin@example.com 或 support@test.org")

# 生成密码
generate_password(length=16, include_symbols=True)
```

---

## ⏰ 时间工具 (time_utils_tools)

**模块描述**: 通用时间管理工具集合，提供时间戳转换、时区处理、时间格式化等功能。

**类别**: time_management  
**版本**: 1.0.0  
**作者**: Assistant

### 🔧 包含的工具

#### 基础时间获取
- `get_current_timestamp` - 获取当前时间戳（支持秒/毫秒/纳秒精度）
- `get_current_time_string` - 获取当前时间字符串
- `get_utc_time` - 获取当前UTC时间

#### 时间转换
- `format_timestamp` - 将时间戳格式化为时间字符串
- `parse_time_string` - 将时间字符串解析为时间戳
- `convert_timezone` - 时区转换
- `convert_time_units` - 时间单位转换

#### 时间计算
- `calculate_time_difference` - 计算两个时间戳的差异
- `get_weekday` - 获取星期几
- `get_day_start_timestamp` - 获取当天0点时间戳

#### 计时器功能
- `start_timer` - 开始计时
- `stop_timer` - 停止计时并获取耗时
- `get_timer_elapsed` - 获取计时器已经过的时间

#### 实用工具
- `generate_timestamp_id` - 生成基于时间戳的唯一ID
- `list_timezones` - 列出常用时区

### 💡 使用示例

```python
# 获取当前时间戳
get_current_timestamp(precision="milliseconds")

# 格式化时间戳
format_timestamp(timestamp=1640995200, format="%Y-%m-%d %H:%M:%S", timezone="Asia/Shanghai")

# 时区转换
convert_timezone(timestamp=1640995200, from_timezone="UTC", to_timezone="Asia/Shanghai")

# 计算时间差
calculate_time_difference(timestamp1=1640995200, timestamp2=1641081600)

# 开始计时
start_timer(timer_name="task1")
# ... 执行任务 ...
stop_timer(timer_name="task1")
```

---

## 📈 交易时间工具 (trading_time_tools)

**模块描述**: 金融交易时间管理工具集合，专门用于AI量化交易的时间管理，提供市场状态判断、交易日计算、K线时间对齐等功能。

**类别**: trading_time  
**版本**: 1.0.0  
**作者**: Assistant

### 🔧 支持的市场

- **CN_A**: 中国A股市场
- **HK**: 香港股市
- **US**: 美股市场
- **EU**: 欧洲股市（伦敦）
- **JP**: 日本股市

### 🔧 包含的工具

#### 市场状态查询
- `get_market_status` - 获取市场当前状态
- `is_market_open` - 判断市场是否开盘
- `get_market_current_time` - 获取市场当前时间
- `list_all_markets` - 列出所有支持的市场

#### 交易日计算
- `get_next_trading_day` - 获取下一个交易日
- `get_previous_trading_day` - 获取上一个交易日
- `get_trading_days_between` - 获取两个日期之间的所有交易日

#### 开盘收盘时间
- `seconds_until_market_open` - 距离市场开盘还有多少秒
- `seconds_until_market_close` - 距离市场收盘还有多少秒

#### K线时间管理
- `align_to_kline_time` - 将时间戳对齐到K线时间
- `generate_kline_timestamps` - 生成K线时间戳序列
- `get_kline_intervals` - 获取支持的K线间隔列表

#### 节假日管理
- `add_holiday` - 添加节假日
- `remove_holiday` - 移除节假日
- `list_holidays` - 列出市场的所有节假日

### 💡 使用示例

```python
# 检查A股市场状态
get_market_status(market_code="CN_A")

# 判断美股是否开盘
is_market_open(market_code="US")

# 获取下一个交易日
get_next_trading_day(market_code="CN_A", date_str="2024-01-01")

# 距离开盘倒计时
seconds_until_market_open(market_code="CN_A")

# K线时间对齐
align_to_kline_time(timestamp=1640995200, interval="1h")

# 生成K线时间序列
generate_kline_timestamps(start_time="2024-01-01 09:30:00", end_time="2024-01-01 15:00:00", interval="5m")
```

---

## 📱 金山 WOA 消息推送工具 (woa_notification_tools)

**模块描述**: 金山 WOA 消息推送工具集合，支持文本、Markdown、链接消息推送，提供完整的企业内部通知和监控报警功能。

**类别**: notification  
**版本**: 1.0.0  
**作者**: Luoxiaoshan

### 🔧 包含的工具

#### Webhook 管理
- `add_woa_webhook` - 添加或更新 WOA 机器人 webhook 配置
- `list_woa_webhooks` - 列出所有已保存的 webhook 配置
- `remove_woa_webhook` - 删除指定的 webhook 配置

#### 消息发送
- `send_woa_text_message` - 发送文本消息（支持@人功能）
- `send_woa_markdown_message` - 发送 Markdown 格式消息
- `send_woa_link_message` - 发送链接消息

#### 快捷模板
- `send_woa_alert_message` - 发送监控报警消息模板

#### 特色功能
- `send_woa_daily_report` - 发送每日数据监控报告模板

### 🔑 主要特性

#### 安全性
- **Key 保护**: Webhook key 本地加密存储，只显示前8位预览
- **频率限制**: 自动控制发送频率（20条/分钟），防止超限
- **内容检查**: 消息内容长度限制（5000字符），避免发送失败

#### 便捷性
- **配置管理**: 支持多个 webhook 配置，命名管理不同群组
- **@人功能**: 支持通过用户ID、邮箱@人，支持@所有人
- **模板消息**: 内置监控报警模板，快速发送格式化消息

#### 可靠性
- **错误处理**: 完善的错误处理和重试机制
- **状态追踪**: 记录最后使用时间，便于管理
- **格式验证**: 自动验证消息格式和参数

### 📋 支持的消息类型

#### 1. 文本消息
```json
{
   "msgtype":"text",
   "text":{
      "content":"每日数据监控报告：\n今日数据统计结果请相关同事注意<at user_id=\"17856\">李三</at><at user_id=\"-1\">所有人</at>"
   }
}
```

#### 2. Markdown 消息
```json
{
    "msgtype": "markdown",
    "markdown": {
        "text":"## KAE监控报警\n\n报警内容：网关入口\n\n> 备注：严重程度中等"
    }
}
```

#### 3. 链接消息
```json
{
    "msgtype": "link",
    "title": "查看详细报告",
    "text": "点击查看完整的监控数据分析报告",
    "messageUrl": "https://example.com/report",
    "btnTitle": "查看报告"
}
```

### 🎯 @人功能支持

- **通过用户ID**: `<at user_id="12345">姓名</at>`
- **通过邮箱**: `<at email="somebody@wps.cn">姓名</at>`
- **@所有人**: `<at user_id="-1">所有人</at>`

### 💡 使用示例

#### 1. 配置 Webhook
```python
# 添加 webhook 配置
add_woa_webhook(
    name="开发群",
    key="xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx",
    description="开发团队群组通知"
)

# 查看所有配置
list_woa_webhooks()
```

#### 2. 发送文本消息
```python
# 普通文本消息
send_woa_text_message(
    webhook_name="开发群",
    content="代码部署完成，请相关同事进行测试"
)

# 带@人的消息
send_woa_text_message(
    webhook_name="开发群",
    content="紧急问题需要处理，请注意",
    at_users=[
        {"type": "id", "value": "12345", "name": "张三"},
        {"type": "all"}
    ]
)
```

#### 3. 发送 Markdown 消息
```python
send_woa_markdown_message(
    webhook_name="开发群",
    markdown_text="""## 📊 每日数据报告

**日期**: 2024-01-15
**状态**: <font color='#00FF00'>正常</font>

### 关键指标
- 用户访问量: **1,234**
- 系统响应时间: **120ms**
- 错误率: **0.01%**

> 所有系统运行正常，无需特别关注
"""
)
```

#### 4. 发送监控报警
```python
send_woa_alert_message(
    webhook_name="运维群",
    alert_title="服务器CPU使用率过高",
    alert_content="服务器 web-01 的CPU使用率达到 85%，请立即检查",
    severity="高",
    at_all=True
)
```

#### 5. 发送链接消息
```python
send_woa_link_message(
    webhook_name="产品群",
    title="新功能上线通知",
    text="用户反馈系统新功能已上线，请查看详细说明文档",
    message_url="https://docs.example.com/new-feature",
    btn_title="查看文档"
)
```

### ⚠️ 使用限制

1. **发送频率**: 每个机器人最多 20 条消息/分钟
2. **消息长度**: 每条消息最多 5000 个字符
3. **按钮标题**: 链接消息的按钮标题最多 12 个字符
4. **Webhook 安全**: 请妥善保管 webhook key，避免泄漏

### 📦 依赖包
- requests>=2.31.0

### 🛡️ 安全提醒

⚠️ **重要**: 
- Webhook key 包含敏感信息，请勿泄漏到 GitHub、博客等公开场所
- 建议定期更换 webhook key
- 使用时注意消息内容的敏感性

---

## 🚀 如何使用工具模块

### 1. 查看可用模块
```python
# AI可以使用这个工具查看所有可用的工具模块
list_tool_modules()
```

### 2. 激活工具模块
```python
# AI可以根据需要激活特定的工具模块
activate_tool_modules(module_names=["web_scraper_tools", "file_manager_tools"])
```

### 3. 获取工具详细信息
```python
# AI可以获取特定工具的详细Schema信息
get_tool_schema(tool_name="read_file")
```

### 4. 查看工具列表
```python
# 查看当前可用的所有工具
list_available_tools()
```

## 📝 开发指南

### 创建新的工具模块

1. **创建模块文件**: 在 `user_tool_modules/` 目录下创建 `.py` 文件
2. **添加模块信息**: 在文件开头添加模块描述注释
3. **实现工具函数**: 使用 `@register_tool` 装饰器注册工具
4. **更新文档**: 在本README中添加模块说明

### 模块信息格式
```python
# MODULE_DESCRIPTION: 模块功能描述
# MODULE_CATEGORY: 模块类别
# MODULE_AUTHOR: 作者名称
# MODULE_VERSION: 版本号
```

### 工具注册示例
```python
@register_tool(
    name="my_tool",
    description="工具描述",
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
    """工具实现"""
    return f"处理结果: {param}"
```

## 🔧 配置说明

工具模块的配置可以在 `config.json` 中进行设置：

```json
{
  "tool_modules": {
    "auto_load": true,
    "interactive_selection": true,
    "default_active": ["file_manager_tools"],
    "module_configs": {
      "file_manager": {
        "max_file_size": 1048576,
        "allowed_extensions": [".txt", ".py", ".json", ".md"]
      }
    }
  }
}
```

## 📋 注意事项

1. **安全性**: 文件操作工具会进行安全检查，避免访问敏感文件
2. **性能**: 大文件操作会有大小限制，避免内存溢出
3. **编码**: 默认使用UTF-8编码，支持自动编码检测
4. **错误处理**: 所有工具都有完善的错误处理机制
5. **依赖管理**: 确保安装了所需的依赖包

## 🆕 更新日志

### v1.0.0 (2024-01-XX)
- ✅ 新增网页抓取工具模块
- ✅ 完善文件管理工具
- ✅ 增强文本处理功能
- ✅ 优化时间管理工具
- ✅ 完善交易时间工具
- 🆕 新增金山 WOA 消息推送工具模块
  - 支持文本、Markdown、链接三种消息类型
  - 完整的 Webhook 配置管理
  - 内置监控报警模板
  - 频率限制和安全保护
  - 支持@人功能

---

*本文档会随着工具模块的更新而持续维护。如有问题或建议，请联系开发团队。* 