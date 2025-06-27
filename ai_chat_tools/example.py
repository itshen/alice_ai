#!/usr/bin/env python3.11
"""
AI Chat Tools 使用示例
"""
import asyncio
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
    """获取天气信息"""
    # 这里可以调用真实的天气API
    return f"{city}今天天气晴朗，温度25°C，湿度60%"

@register_tool(
    name="file_reader",
    description="读取文件内容"
)
def read_file(filename: str) -> str:
    """读取文件内容"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            return content[:1000] + "..." if len(content) > 1000 else content
    except Exception as e:
        return f"读取文件失败: {str(e)}"

async def main():
    """主函数"""
    print("=== AI Chat Tools 示例 ===\n")
    
    # 创建ChatBot实例（非调试模式）
    bot = ChatBot(provider="qwen", debug=False)
    
    # 创建新会话
    session_id = bot.create_session("示例对话")
    print(f"创建会话: {session_id}\n")
    
    # 示例1: 基础对话
    print("1. 基础对话:")
    result = await bot.chat("你好，请介绍一下你自己", session_id=session_id)
    print(f"AI: {result['message']}\n")
    
    # 示例2: 非调试模式的流式对话
    print("2. 非调试模式 - 查询天气:")
    print("用户: 北京今天天气怎么样？")
    print()
    print("AI实时响应（无调试信息）:")
    
    async for chunk in bot.chat_stream("北京今天天气怎么样？", session_id=session_id):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 50)
    print()
    
    # 示例3: 调试模式的流式对话
    print("3. 调试模式 - 查询天气:")
    print("用户: 上海今天天气怎么样？")
    print()
    print("AI实时响应（包含调试信息）:")
    
    # 切换到调试模式
    bot.debug = True
    
    async for chunk in bot.chat_stream("上海今天天气怎么样？", session_id=session_id):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 50)
    print()
    
    # 示例4: 对比两种模式的多轮对话
    print("4. 模式对比 - 复杂多步骤任务:")
    print()
    
    # 非调试模式
    print("4a. 非调试模式:")
    print("用户: 请先查询当前时间，然后计算50+30")
    print()
    print("AI实时响应（简洁模式）:")
    
    bot.debug = False
    async for chunk in bot.chat_stream("请先查询当前时间，然后计算50+30", session_id=session_id):
        print(chunk, end="", flush=True)
    
    print("\n")
    print("-" * 30)
    print()
    
    # 调试模式
    print("4b. 调试模式:")
    print("用户: 请先查询当前时间，然后计算80+20")
    print()
    print("AI实时响应（调试模式）:")
    
    bot.debug = True
    async for chunk in bot.chat_stream("请先查询当前时间，然后计算80+20", session_id=session_id):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 50)
    print()
    
    # 示例5: 多轮对话 - 计算任务
    print("5. 多轮对话示例 - 数学计算:")
    print("用户: 帮我计算 15 * 23 + 45 等于多少")
    print()
    print("AI实时响应:")
    
    full_response = ""
    async for chunk in bot.chat_stream("帮我计算 15 * 23 + 45 等于多少", session_id=session_id):
        print(chunk, end="", flush=True)
        full_response += chunk
    
    print("\n" + "-" * 50)
    print()
    
    # 示例6: 多轮对话 - 获取时间
    print("6. 多轮对话示例 - 获取时间:")
    print("用户: 现在几点了？")
    print()
    print("AI实时响应:")
    
    full_response = ""
    async for chunk in bot.chat_stream("现在几点了？", session_id=session_id):
        print(chunk, end="", flush=True)
        full_response += chunk
    
    print("\n" + "-" * 50)
    print()
    
    # 示例7: 复杂多轮对话 - 多步骤任务
    print("7. 复杂多轮对话示例 - 多步骤任务:")
    print("用户: 请先查询当前时间，然后计算100+200，最后告诉我结果")
    print()
    print("AI实时响应:")
    
    full_response = ""
    async for chunk in bot.chat_stream("请先查询当前时间，然后计算100+200，最后告诉我结果", session_id=session_id):
        print(chunk, end="", flush=True)
        full_response += chunk
    
    print("\n" + "-" * 50)
    print()
    
    # 示例8: 会话历史总结
    print("8. 会话历史总结:")
    messages = bot.get_session_messages(session_id)
    print(f"本次会话共进行了 {len(messages)} 条消息交换")
    
    # 统计各类消息
    user_msgs = len([m for m in messages if m['role'] == 'user'])
    ai_msgs = len([m for m in messages if m['role'] == 'assistant'])
    tool_calls = sum(1 for m in messages if m.get('tool_calls'))
    
    print(f"- 用户消息: {user_msgs} 条")
    print(f"- AI回复: {ai_msgs} 条")
    print(f"- 工具调用: {tool_calls} 次")
    print()
    
    # 显示最近几条消息
    print("最近的对话:")
    for i, msg in enumerate(messages[-6:], len(messages)-5):
        role = "用户" if msg['role'] == 'user' else "AI"
        content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
        print(f"  {i}. {role}: {content}")
        if msg.get('tool_calls'):
            print(f"     [调用了 {len(msg['tool_calls'])} 个工具]")
    print()
    
    # 显示可用工具
    print("9. 系统可用工具:")
    tools = bot.list_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    print("\n=== 多轮对话示例结束 ===")
    print("通过以上示例可以看到，AI能够：")
    print("1. 理解用户需求")
    print("2. 自动调用相应工具获取信息")
    print("3. 基于工具结果给出完整回答")
    print("4. 支持复杂的多步骤任务处理")

if __name__ == "__main__":
    asyncio.run(main()) 