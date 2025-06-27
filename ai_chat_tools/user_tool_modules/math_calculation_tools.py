# MODULE_DESCRIPTION: 数学计算工具模块，提供基础数学运算、统计分析、几何计算等功能
# MODULE_CATEGORY: calculation
# MODULE_AUTHOR: AI Assistant
# MODULE_VERSION: 1.0.0

import math
import statistics
from typing import List, Union, Dict, Any
from ..tool_manager import register_tool


@register_tool(
    name="basic_calculate",
    description="执行基础数学运算，支持加减乘除、幂运算、开方等",
    schema={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如：'2 + 3 * 4', 'sqrt(16)', 'pow(2, 3)', 'sin(pi/2)'"
            }
        },
        "required": ["expression"]
    }
)
def basic_calculate(expression: str) -> str:
    """执行基础数学运算"""
    try:
        # 安全的数学函数映射
        safe_dict = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
            "ceil": math.ceil,
            "floor": math.floor,
            "factorial": math.factorial,
            "degrees": math.degrees,
            "radians": math.radians
        }
        
        # 计算表达式
        result = eval(expression, safe_dict)
        
        return f"🧮 **数学计算结果**\n\n表达式: `{expression}`\n结果: **{result}**"
        
    except Exception as e:
        return f"❌ **计算错误**\n\n表达式: `{expression}`\n错误: {str(e)}\n\n💡 请检查表达式格式是否正确"


@register_tool(
    name="statistics_calculate",
    description="对数据集进行统计分析，计算平均值、中位数、标准差等",
    schema={
        "type": "object",
        "properties": {
            "numbers": {
                "type": "array",
                "items": {"type": "number"},
                "description": "数字列表，如：[1, 2, 3, 4, 5]"
            },
            "analysis_type": {
                "type": "string",
                "enum": ["all", "mean", "median", "mode", "stdev", "variance", "range"],
                "description": "分析类型：all(全部)、mean(平均值)、median(中位数)、mode(众数)、stdev(标准差)、variance(方差)、range(极差)",
                "default": "all"
            }
        },
        "required": ["numbers"]
    }
)
def statistics_calculate(numbers: List[float], analysis_type: str = "all") -> str:
    """统计分析计算"""
    try:
        if not numbers:
            return "❌ **错误**: 数据列表不能为空"
        
        results = []
        
        if analysis_type in ["all", "mean"]:
            mean_val = statistics.mean(numbers)
            results.append(f"平均值 (Mean): **{mean_val:.4f}**")
        
        if analysis_type in ["all", "median"]:
            median_val = statistics.median(numbers)
            results.append(f"中位数 (Median): **{median_val}**")
        
        if analysis_type in ["all", "mode"]:
            try:
                mode_val = statistics.mode(numbers)
                results.append(f"众数 (Mode): **{mode_val}**")
            except statistics.StatisticsError:
                results.append("众数 (Mode): **无唯一众数**")
        
        if analysis_type in ["all", "stdev"] and len(numbers) > 1:
            stdev_val = statistics.stdev(numbers)
            results.append(f"标准差 (Standard Deviation): **{stdev_val:.4f}**")
        
        if analysis_type in ["all", "variance"] and len(numbers) > 1:
            var_val = statistics.variance(numbers)
            results.append(f"方差 (Variance): **{var_val:.4f}**")
        
        if analysis_type in ["all", "range"]:
            range_val = max(numbers) - min(numbers)
            results.append(f"极差 (Range): **{range_val}**")
            results.append(f"最小值 (Min): **{min(numbers)}**")
            results.append(f"最大值 (Max): **{max(numbers)}**")
        
        data_info = f"数据个数: {len(numbers)}\n数据: {numbers}"
        
        return f"📊 **统计分析结果**\n\n{data_info}\n\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ **统计计算错误**: {str(e)}"


@register_tool(
    name="geometry_calculate",
    description="几何图形计算，包括圆形、矩形、三角形等的面积和周长",
    schema={
        "type": "object",
        "properties": {
            "shape": {
                "type": "string",
                "enum": ["circle", "rectangle", "triangle", "square"],
                "description": "图形类型：circle(圆形)、rectangle(矩形)、triangle(三角形)、square(正方形)"
            },
            "parameters": {
                "type": "object",
                "description": "图形参数，根据图形类型不同：圆形需要radius，矩形需要width和height，三角形需要a、b、c三边长，正方形需要side"
            }
        },
        "required": ["shape", "parameters"]
    }
)
def geometry_calculate(shape: str, parameters: Dict[str, float]) -> str:
    """几何图形计算"""
    try:
        results = []
        
        if shape == "circle":
            radius = parameters.get("radius")
            if not radius or radius <= 0:
                return "❌ **错误**: 圆形需要正数半径 (radius)"
            
            area = math.pi * radius ** 2
            circumference = 2 * math.pi * radius
            results.append(f"半径: **{radius}**")
            results.append(f"面积: **{area:.4f}**")
            results.append(f"周长: **{circumference:.4f}**")
            shape_name = "圆形"
            
        elif shape == "rectangle":
            width = parameters.get("width")
            height = parameters.get("height")
            if not width or not height or width <= 0 or height <= 0:
                return "❌ **错误**: 矩形需要正数宽度 (width) 和高度 (height)"
            
            area = width * height
            perimeter = 2 * (width + height)
            results.append(f"宽度: **{width}**")
            results.append(f"高度: **{height}**")
            results.append(f"面积: **{area:.4f}**")
            results.append(f"周长: **{perimeter:.4f}**")
            shape_name = "矩形"
            
        elif shape == "square":
            side = parameters.get("side")
            if not side or side <= 0:
                return "❌ **错误**: 正方形需要正数边长 (side)"
            
            area = side ** 2
            perimeter = 4 * side
            results.append(f"边长: **{side}**")
            results.append(f"面积: **{area:.4f}**")
            results.append(f"周长: **{perimeter:.4f}**")
            shape_name = "正方形"
            
        elif shape == "triangle":
            a = parameters.get("a")
            b = parameters.get("b") 
            c = parameters.get("c")
            if a is None or b is None or c is None or a <= 0 or b <= 0 or c <= 0:
                return "❌ **错误**: 三角形需要三个正数边长 (a, b, c)"
            
            # 检查三角形不等式
            if not (a + b > c and a + c > b and b + c > a):
                return "❌ **错误**: 三边长不能构成三角形"
            
            # 使用海伦公式计算面积
            s = (a + b + c) / 2
            area = math.sqrt(s * (s - a) * (s - b) * (s - c))
            perimeter = a + b + c
            
            results.append(f"边长 a: **{a}**")
            results.append(f"边长 b: **{b}**")
            results.append(f"边长 c: **{c}**")
            results.append(f"面积: **{area:.4f}**")
            results.append(f"周长: **{perimeter:.4f}**")
            shape_name = "三角形"
        
        else:
            return f"❌ **错误**: 不支持的图形类型 '{shape}'"
        
        return f"📐 **{shape_name}计算结果**\n\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ **几何计算错误**: {str(e)}"


@register_tool(
    name="number_conversion",
    description="数字进制转换，支持二进制、八进制、十进制、十六进制之间的转换",
    schema={
        "type": "object",
        "properties": {
            "number": {
                "type": "string",
                "description": "要转换的数字"
            },
            "from_base": {
                "type": "integer",
                "enum": [2, 8, 10, 16],
                "description": "源进制：2(二进制)、8(八进制)、10(十进制)、16(十六进制)"
            },
            "to_base": {
                "type": "integer", 
                "enum": [2, 8, 10, 16],
                "description": "目标进制：2(二进制)、8(八进制)、10(十进制)、16(十六进制)"
            }
        },
        "required": ["number", "from_base", "to_base"]
    }
)
def number_conversion(number: str, from_base: int, to_base: int) -> str:
    """数字进制转换"""
    try:
        # 先转换为十进制
        if from_base == 10:
            decimal_num = int(number)
        elif from_base == 2:
            decimal_num = int(number, 2)
        elif from_base == 8:
            decimal_num = int(number, 8)
        elif from_base == 16:
            decimal_num = int(number, 16)
        else:
            return f"❌ **错误**: 不支持的源进制 {from_base}"
        
        # 从十进制转换到目标进制
        if to_base == 10:
            result = str(decimal_num)
        elif to_base == 2:
            result = bin(decimal_num)[2:]  # 去掉 '0b' 前缀
        elif to_base == 8:
            result = oct(decimal_num)[2:]  # 去掉 '0o' 前缀
        elif to_base == 16:
            result = hex(decimal_num)[2:].upper()  # 去掉 '0x' 前缀，转大写
        else:
            return f"❌ **错误**: 不支持的目标进制 {to_base}"
        
        base_names = {2: "二进制", 8: "八进制", 10: "十进制", 16: "十六进制"}
        
        return f"🔢 **进制转换结果**\n\n" \
               f"原数字: **{number}** ({base_names[from_base]})\n" \
               f"转换结果: **{result}** ({base_names[to_base]})\n" \
               f"十进制值: **{decimal_num}**"
        
    except ValueError as e:
        return f"❌ **转换错误**: 数字格式不正确 - {str(e)}"
    except Exception as e:
        return f"❌ **转换错误**: {str(e)}"


@register_tool(
    name="solve_equation",
    description="求解简单的一元二次方程 ax² + bx + c = 0",
    schema={
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
                "description": "二次项系数 a (不能为0)"
            },
            "b": {
                "type": "number", 
                "description": "一次项系数 b"
            },
            "c": {
                "type": "number",
                "description": "常数项 c"
            }
        },
        "required": ["a", "b", "c"]
    }
)
def solve_equation(a: float, b: float, c: float) -> str:
    """求解一元二次方程"""
    try:
        if a == 0:
            if b == 0:
                if c == 0:
                    return "📝 **方程求解结果**\n\n方程: **0 = 0**\n结果: **所有实数都是解**"
                else:
                    return f"📝 **方程求解结果**\n\n方程: **{c} = 0**\n结果: **无解**"
            else:
                # 一次方程 bx + c = 0
                x = -c / b
                return f"📝 **方程求解结果**\n\n方程: **{b}x + {c} = 0**\n解: **x = {x:.4f}**"
        
        # 一元二次方程 ax² + bx + c = 0
        discriminant = b**2 - 4*a*c
        
        equation_str = f"{a}x² + {b}x + {c} = 0"
        if a == 1:
            equation_str = f"x² + {b}x + {c} = 0"
        elif a == -1:
            equation_str = f"-x² + {b}x + {c} = 0"
        
        results = [f"方程: **{equation_str}**"]
        results.append(f"判别式 Δ = b² - 4ac = {b}² - 4×{a}×{c} = **{discriminant:.4f}**")
        
        if discriminant > 0:
            x1 = (-b + math.sqrt(discriminant)) / (2*a)
            x2 = (-b - math.sqrt(discriminant)) / (2*a)
            results.append("**两个不同的实数解:**")
            results.append(f"x₁ = **{x1:.4f}**")
            results.append(f"x₂ = **{x2:.4f}**")
        elif discriminant == 0:
            x = -b / (2*a)
            results.append("**一个重根:**")
            results.append(f"x = **{x:.4f}**")
        else:
            real_part = -b / (2*a)
            imaginary_part = math.sqrt(-discriminant) / (2*a)
            results.append("**两个复数解:**")
            results.append(f"x₁ = **{real_part:.4f} + {imaginary_part:.4f}i**")
            results.append(f"x₂ = **{real_part:.4f} - {imaginary_part:.4f}i**")
        
        return f"📝 **方程求解结果**\n\n" + "\n".join(results)
        
    except Exception as e:
        return f"❌ **方程求解错误**: {str(e)}"


@register_tool(
    name="percentage_calculate",
    description="百分比计算，包括求百分比、百分比增减、比例计算等",
    schema={
        "type": "object",
        "properties": {
            "calculation_type": {
                "type": "string",
                "enum": ["percentage_of", "percentage_change", "find_total", "find_percentage"],
                "description": "计算类型：percentage_of(求百分比)、percentage_change(变化百分比)、find_total(求总数)、find_percentage(求百分率)"
            },
            "value1": {
                "type": "number",
                "description": "第一个数值"
            },
            "value2": {
                "type": "number", 
                "description": "第二个数值"
            }
        },
        "required": ["calculation_type", "value1", "value2"]
    }
)
def percentage_calculate(calculation_type: str, value1: float, value2: float) -> str:
    """百分比计算"""
    try:
        if calculation_type == "percentage_of":
            # 计算 value1 是 value2 的百分之几
            if value2 == 0:
                return "❌ **错误**: 除数不能为0"
            percentage = (value1 / value2) * 100
            return f"📊 **百分比计算结果**\n\n{value1} 是 {value2} 的 **{percentage:.2f}%**"
            
        elif calculation_type == "percentage_change":
            # 计算从 value1 到 value2 的变化百分比
            if value1 == 0:
                return "❌ **错误**: 原始值不能为0"
            change = value2 - value1
            percentage_change = (change / value1) * 100
            change_type = "增长" if change > 0 else "减少"
            return f"📊 **百分比变化结果**\n\n从 {value1} 到 {value2}\n变化: **{abs(change):.2f}** ({change_type})\n变化率: **{abs(percentage_change):.2f}%**"
            
        elif calculation_type == "find_total":
            # 已知 value1 是总数的 value2%，求总数
            if value2 == 0:
                return "❌ **错误**: 百分比不能为0"
            total = value1 / (value2 / 100)
            return f"📊 **求总数结果**\n\n如果 {value1} 是总数的 {value2}%\n那么总数是: **{total:.2f}**"
            
        elif calculation_type == "find_percentage":
            # 已知总数是 value2，部分是 value1，求百分比
            if value2 == 0:
                return "❌ **错误**: 总数不能为0"
            percentage = (value1 / value2) * 100
            return f"📊 **求百分比结果**\n\n{value1} 占 {value2} 的: **{percentage:.2f}%**"
            
        else:
            return f"❌ **错误**: 不支持的计算类型 '{calculation_type}'"
            
    except Exception as e:
        return f"❌ **百分比计算错误**: {str(e)}" 