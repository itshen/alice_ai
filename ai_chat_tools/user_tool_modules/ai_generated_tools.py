# MODULE_DESCRIPTION: AI生成的工具函数集合
# MODULE_CATEGORY: ai_generated
# MODULE_AUTHOR: AI Assistant
# MODULE_VERSION: 1.0.0

"""
AI生成工具模块
此模块专门用于存放AI生成的简单工具函数
避免创建过多小模块，集中管理AI生成的功能
"""

import os
import sys
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import re

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# ==================== AI生成的工具函数 ====================
# 此区域用于存放AI生成的工具函数
# 每个函数都应该有@register_tool装饰器

# 示例函数（可以删除）
@register_tool(
    name="example_ai_tool",
    description="示例AI工具函数，可以删除。参数：message(消息内容)。使用示例：example_ai_tool(message='Hello World')。",
    schema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "要处理的消息内容"
            }
        },
        "required": ["message"]
    }
)
def example_ai_tool(message: str) -> str:
    """示例AI工具函数"""
    return f"AI处理结果: {message}"

@register_tool(
    name="calculate_sum",
    description="计算两个数的和",
    schema={
                "type": "object",
                "properties": {
                        "a": {
                                "type": "number",
                                "description": "第一个数"
                        },
                        "b": {
                                "type": "number",
                                "description": "第二个数"
                        }
                },
                "required": [
                        "a",
                        "b"
                ]
        }
)
def calculate_sum(a: float, b: float) -> float:
    """AI生成的工具函数: 计算两个数的和"""
    return a + b

@register_tool(
    name="calculate_factorial",
    description="强大的阶乘计算工具，支持基础阶乘(n!)、双阶乘(n!!)、子阶乘(!n)等多种类型",
    schema={
                "type": "object",
                "properties": {
                        "n": {
                                "type": "integer",
                                "description": "要计算阶乘的数字，必须是非负整数"
                        },
                        "factorial_type": {
                                "type": "string",
                                "description": "阶乘类型：basic(基础阶乘n!)、double(双阶乘n!!)、subfactorial(子阶乘!n)",
                                "default": "basic"
                        }
                },
                "required": [
                        "n"
                ]
        }
)
def calculate_factorial(n: int, factorial_type: str = 'basic') -> str:
    """AI生成的工具函数: 强大的阶乘计算工具，支持基础阶乘(n!)、双阶乘(n!!)、子阶乘(!n)等多种类型"""
    import math

    def factorial_basic(n):
        """基础阶乘计算"""
        if n < 0:
            raise ValueError("阶乘不支持负数")
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    def factorial_double(n):
        """双阶乘计算 (n!! = n*(n-2)*(n-4)*...)"""
        if n < 0:
            raise ValueError("双阶乘不支持负数")
        if n <= 1:
            return 1
        result = 1
        while n > 1:
            result *= n
            n -= 2
        return result

    def subfactorial(n):
        """子阶乘计算 (!n = 错位排列)"""
        if n < 0:
            raise ValueError("子阶乘不支持负数")
        if n == 0:
            return 1
        if n == 1:
            return 0
        result = 0
        for i in range(n + 1):
            result += (-1) ** i / math.factorial(i)
        return int(math.factorial(n) * result)

    # 主函数
    if factorial_type == "basic":
        if not isinstance(n, int) or n < 0:
            return {"error": "基础阶乘需要非负整数"}
        if n > 170:  # 防止溢出
            return {"error": "数字过大，建议使用170以内的数字"}
        result = factorial_basic(n)
        formula = f"{n}! = {' × '.join(str(i) for i in range(1, n + 1)) if n <= 10 else f'1 × 2 × ... × {n}'}"

    elif factorial_type == "double":
        if not isinstance(n, int) or n < 0:
            return {"error": "双阶乘需要非负整数"}
        if n > 100:
            return {"error": "数字过大，建议使用100以内的数字"}
        result = factorial_double(n)
        # 构建双阶乘公式显示
        if n <= 10:
            factors = []
            temp = n
            while temp > 1:
                factors.append(str(temp))
                temp -= 2
            formula = f"{n}!! = {' × '.join(factors) if factors else '1'}"
        else:
            formula = f"{n}!! = {n} × {n-2} × ... × {'2' if n % 2 == 0 else '1'}"

    elif factorial_type == "subfactorial":
        if not isinstance(n, int) or n < 0:
            return {"error": "子阶乘需要非负整数"}
        if n > 20:
            return {"error": "数字过大，建议使用20以内的数字"}
        result = subfactorial(n)
        formula = f"!{n} = 错位排列数"

    else:
        return {"error": f"不支持的阶乘类型: {factorial_type}，支持的类型: basic, double, subfactorial"}

    return {
        "number": n,
        "type": factorial_type,
        "result": result,
        "formula": formula,
        "result_length": len(str(result)),
        "description": {
            "basic": "基础阶乘 (n!) = n × (n-1) × ... × 2 × 1",
            "double": "双阶乘 (n!!) = n × (n-2) × (n-4) × ...", 
            "subfactorial": "子阶乘 (!n) = 错位排列数，表示n个不同元素的错位排列方案数"
        }[factorial_type]
    }

