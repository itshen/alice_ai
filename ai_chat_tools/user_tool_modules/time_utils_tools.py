# MODULE_DESCRIPTION: 通用时间管理工具集合，提供时间戳转换、时区处理、时间格式化等功能
# MODULE_CATEGORY: time_management
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 1.0.0

"""
通用时间管理工具模块
提供时间戳转换、时区处理、时间格式化、性能计时等功能
"""

import os
import time
import datetime
import pytz
import re
import random
import string
from typing import Union, Tuple, Optional
from functools import lru_cache

# 使用绝对导入避免相对导入问题
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# 默认时区配置
DEFAULT_TIMEZONE = 'Asia/Shanghai'

# 全局时间工具实例
class TimeUtils:
    """通用时间管理工具类"""
    
    def __init__(self, default_timezone: str = DEFAULT_TIMEZONE):
        self.default_timezone = default_timezone
    
    @lru_cache(maxsize=32)
    def _get_timezone(self, timezone_name: str) -> pytz.BaseTzInfo:
        """缓存时区对象，避免重复创建"""
        return pytz.timezone(timezone_name)

# 创建全局实例
_time_utils = TimeUtils()

# ==================== 基础时间获取工具 ====================

@register_tool(
    name="get_current_timestamp",
    description="获取当前时间戳",
    schema={
        "type": "object",
        "properties": {
            "precision": {
                "type": "string",
                "description": "时间戳精度",
                "enum": ["seconds", "milliseconds", "nanoseconds"],
                "default": "seconds"
            }
        }
    }
)
def get_current_timestamp(precision: str = "seconds") -> str:
    """获取当前时间戳"""
    try:
        if precision == "seconds":
            timestamp = time.time()
            return f"[成功] 当前时间戳(秒): {timestamp}"
        elif precision == "milliseconds":
            timestamp = int(time.time() * 1000)
            return f"[成功] 当前时间戳(毫秒): {timestamp}"
        elif precision == "nanoseconds":
            timestamp = time.time_ns()
            return f"[成功] 当前时间戳(纳秒): {timestamp}"
        else:
            return f"[错误] 不支持的精度: {precision}"
    except Exception as e:
        return f"[错误] 获取时间戳失败: {str(e)}"

@register_tool(
    name="get_current_time_string",
    description="获取当前时间字符串",
    schema={
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "时间格式",
                "default": "%Y-%m-%d %H:%M:%S"
            },
            "timezone": {
                "type": "string",
                "description": "时区名称",
                "default": "Asia/Shanghai"
            }
        }
    }
)
def get_current_time_string(format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "Asia/Shanghai") -> str:
    """获取当前时间字符串"""
    try:
        if timezone == "local":
            time_str = time.strftime(format, time.localtime())
            return f"[成功] 当前本地时间: {time_str}"
        else:
            tz = _time_utils._get_timezone(timezone)
            dt = datetime.datetime.now(tz)
            time_str = dt.strftime(format)
            return f"[成功] 当前{timezone}时间: {time_str}"
    except Exception as e:
        return f"[错误] 获取时间字符串失败: {str(e)}"

@register_tool(
    name="get_utc_time",
    description="获取当前UTC时间",
    schema={
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "时间格式",
                "default": "%Y-%m-%d %H:%M:%S"
            }
        }
    }
)
def get_utc_time(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前UTC时间"""
    try:
        utc_dt = datetime.datetime.now(pytz.utc)
        time_str = utc_dt.strftime(format)
        return f"[成功] 当前UTC时间: {time_str}"
    except Exception as e:
        return f"[错误] 获取UTC时间失败: {str(e)}"

# ==================== 时间转换工具 ====================

@register_tool(
    name="format_timestamp",
    description="将时间戳格式化为时间字符串",
    schema={
        "type": "object",
        "properties": {
            "timestamp": {
                "type": "number",
                "description": "时间戳"
            },
            "format": {
                "type": "string",
                "description": "时间格式",
                "default": "%Y-%m-%d %H:%M:%S"
            },
            "timezone": {
                "type": "string",
                "description": "时区名称",
                "default": "local"
            }
        },
        "required": ["timestamp"]
    }
)
def format_timestamp(timestamp: float, format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "local") -> str:
    """将时间戳格式化为时间字符串"""
    try:
        if timezone == "local":
            time_str = time.strftime(format, time.localtime(timestamp))
            return f"[成功] 格式化时间戳 {timestamp}:\n{time_str}"
        else:
            tz = _time_utils._get_timezone(timezone)
            dt = datetime.datetime.fromtimestamp(timestamp, tz)
            time_str = dt.strftime(format)
            return f"[成功] 格式化时间戳 {timestamp} ({timezone}):\n{time_str}"
    except Exception as e:
        return f"[错误] 格式化时间戳失败: {str(e)}"

@register_tool(
    name="parse_time_string",
    description="将时间字符串解析为时间戳",
    schema={
        "type": "object",
        "properties": {
            "time_string": {
                "type": "string",
                "description": "时间字符串，支持格式: yyyy-MM-DD, yyyy-MM-DD HH:mm:ss, yyyy-MM-DDThh:mm:ss"
            }
        },
        "required": ["time_string"]
    }
)
def parse_time_string(time_string: str) -> str:
    """将时间字符串解析为时间戳"""
    try:
        # 无效时间字符串列表
        invalid_strings = {
            '未知', '0000-00-00 00:00:00', '0000-00-00', '0000-00-00T00:00:00',
            '0000-00-00T00:00:00Z', 'unknown', '', None
        }
        
        if time_string in invalid_strings:
            return f"[结果] 无效时间字符串，返回时间戳: 0"
        
        # 时间格式正则表达式
        patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',  # yyyy-MM-DD HH:mm:ss
            r'(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d{1,2})',   # yyyy-MM-DDTHH:mm:ss
            r'(\d{4})-(\d{1,2})-(\d{1,2})',                                   # yyyy-MM-DD
        ]
        
        for pattern in patterns:
            match = re.match(pattern, time_string.strip())
            if match:
                groups = match.groups()
                if len(groups) == 3:  # 只有日期
                    year, month, day = groups
                    hour = minute = second = 0
                else:  # 包含时间
                    year, month, day, hour, minute, second = groups
                
                dt = datetime.datetime(
                    int(year), int(month), int(day),
                    int(hour), int(minute), int(second)
                )
                
                # 检查年份有效性
                if int(year) < 1970:
                    return f"[结果] 年份小于1970，返回时间戳: 0"
                
                timestamp = dt.timestamp()
                return f"[成功] 解析时间字符串 '{time_string}':\n时间戳: {timestamp}"
        
        return f"[错误] 无法解析的时间字符串格式: {time_string}"
        
    except ValueError as e:
        return f"[错误] 时间字符串解析失败: {str(e)}"
    except Exception as e:
        return f"[错误] 解析失败: {str(e)}"

@register_tool(
    name="convert_timezone",
    description="时区转换",
    schema={
        "type": "object",
        "properties": {
            "timestamp": {
                "type": "number",
                "description": "时间戳"
            },
            "from_timezone": {
                "type": "string",
                "description": "源时区",
                "default": "Asia/Shanghai"
            },
            "to_timezone": {
                "type": "string",
                "description": "目标时区",
                "default": "US/Eastern"
            },
            "format": {
                "type": "string",
                "description": "输出格式",
                "default": "%Y-%m-%d %H:%M:%S"
            }
        },
        "required": ["timestamp"]
    }
)
def convert_timezone(timestamp: float, from_timezone: str = "Asia/Shanghai", 
                    to_timezone: str = "US/Eastern", format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """时区转换"""
    try:
        from_tz = _time_utils._get_timezone(from_timezone)
        to_tz = _time_utils._get_timezone(to_timezone)
        
        dt = datetime.datetime.fromtimestamp(timestamp)
        dt_with_tz = from_tz.localize(dt)
        dt_converted = dt_with_tz.astimezone(to_tz)
        
        result = dt_converted.strftime(format)
        return f"[成功] 时区转换 ({from_timezone} -> {to_timezone}):\n{result}"
    except pytz.exceptions.UnknownTimeZoneError as e:
        return f"[错误] 未知的时区名称: {str(e)}"
    except Exception as e:
        return f"[错误] 时区转换失败: {str(e)}"

# ==================== 时间计算工具 ====================

@register_tool(
    name="calculate_time_difference",
    description="计算两个时间戳的差异",
    schema={
        "type": "object",
        "properties": {
            "timestamp1": {
                "type": "number",
                "description": "第一个时间戳"
            },
            "timestamp2": {
                "type": "number",
                "description": "第二个时间戳"
            },
            "show_direction": {
                "type": "boolean",
                "description": "是否显示方向（前/后）",
                "default": True
            }
        },
        "required": ["timestamp1", "timestamp2"]
    }
)
def calculate_time_difference(timestamp1: float, timestamp2: float, show_direction: bool = True) -> str:
    """计算两个时间戳的差异"""
    try:
        diff_seconds = int(timestamp2 - timestamp1)
        is_negative = diff_seconds < 0
        abs_seconds = abs(diff_seconds)
        
        # 计算各个时间单位
        days, remainder = divmod(abs_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)
        
        # 构建结果字符串
        parts = []
        if days:
            parts.append(f'{days}天')
        if hours:
            parts.append(f'{hours}小时')
        if minutes:
            parts.append(f'{minutes}分')
        if secs or not parts:
            parts.append(f'{secs}秒')
        
        result = ''.join(parts)
        
        if show_direction and diff_seconds != 0:
            result += '前' if is_negative else '后'
        
        time1_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp1))
        time2_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp2))
        
        return f"[成功] 时间差计算:\n时间1: {time1_str}\n时间2: {time2_str}\n差异: {result}"
    except Exception as e:
        return f"[错误] 时间差计算失败: {str(e)}"

@register_tool(
    name="get_weekday",
    description="获取时间戳对应的星期几",
    schema={
        "type": "object",
        "properties": {
            "timestamp": {
                "type": "number",
                "description": "时间戳，不提供则使用当前时间"
            },
            "language": {
                "type": "string",
                "description": "语言",
                "enum": ["chinese", "english", "number"],
                "default": "chinese"
            }
        }
    }
)
def get_weekday(timestamp: Optional[float] = None, language: str = "chinese") -> str:
    """获取时间戳对应的星期几"""
    try:
        if timestamp is None:
            timestamp = time.time()
        
        dt = datetime.datetime.fromtimestamp(timestamp)
        weekday = dt.weekday()  # 0=周一, 6=周日
        
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        if language == "chinese":
            weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            result = weekdays[weekday]
        elif language == "english":
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            result = weekdays[weekday]
        elif language == "number":
            result = str(weekday)
        else:
            return f"[错误] 不支持的语言: {language}"
        
        return f"[成功] 星期几查询:\n时间: {time_str}\n星期: {result}"
    except Exception as e:
        return f"[错误] 星期几查询失败: {str(e)}"

@register_tool(
    name="get_day_start_timestamp",
    description="获取指定时间戳当天0点的时间戳",
    schema={
        "type": "object",
        "properties": {
            "timestamp": {
                "type": "number",
                "description": "时间戳，不提供则使用当前时间"
            }
        }
    }
)
def get_day_start_timestamp(timestamp: Optional[float] = None) -> str:
    """获取指定时间戳当天0点的时间戳"""
    try:
        if timestamp is None:
            timestamp = time.time()
        
        dt = datetime.datetime.fromtimestamp(timestamp)
        day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        start_timestamp = int(day_start.timestamp())
        
        original_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        start_time = day_start.strftime("%Y-%m-%d %H:%M:%S")
        
        return f"[成功] 当天0点时间戳:\n原始时间: {original_time}\n当天0点: {start_time}\n0点时间戳: {start_timestamp}"
    except Exception as e:
        return f"[错误] 获取当天0点时间戳失败: {str(e)}"

# ==================== 时间单位转换工具 ====================

@register_tool(
    name="convert_time_units",
    description="时间单位转换",
    schema={
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
                "description": "要转换的数值"
            },
            "from_unit": {
                "type": "string",
                "description": "源单位",
                "enum": ["nanoseconds", "microseconds", "milliseconds", "seconds", "minutes", "hours", "days"]
            },
            "to_unit": {
                "type": "string",
                "description": "目标单位",
                "enum": ["nanoseconds", "microseconds", "milliseconds", "seconds", "minutes", "hours", "days"]
            }
        },
        "required": ["value", "from_unit", "to_unit"]
    }
)
def convert_time_units(value: float, from_unit: str, to_unit: str) -> str:
    """时间单位转换"""
    try:
        # 转换系数（相对于秒）
        unit_factors = {
            "nanoseconds": 1e-9,
            "microseconds": 1e-6,
            "milliseconds": 1e-3,
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }
        
        if from_unit not in unit_factors or to_unit not in unit_factors:
            return f"[错误] 不支持的时间单位"
        
        # 先转换为秒，再转换为目标单位
        seconds = value * unit_factors[from_unit]
        result = seconds / unit_factors[to_unit]
        
        return f"[成功] 时间单位转换:\n{value} {from_unit} = {result} {to_unit}"
    except Exception as e:
        return f"[错误] 时间单位转换失败: {str(e)}"

# ==================== 性能计时工具 ====================

# 全局计时器存储
_timers = {}

@register_tool(
    name="start_timer",
    description="开始计时",
    schema={
        "type": "object",
        "properties": {
            "timer_name": {
                "type": "string",
                "description": "计时器名称",
                "default": "default"
            }
        }
    }
)
def start_timer(timer_name: str = "default") -> str:
    """开始计时"""
    try:
        _timers[timer_name] = time.time_ns()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return f"[成功] 计时器 '{timer_name}' 已启动\n启动时间: {current_time}"
    except Exception as e:
        return f"[错误] 启动计时器失败: {str(e)}"

@register_tool(
    name="stop_timer",
    description="停止计时并获取耗时",
    schema={
        "type": "object",
        "properties": {
            "timer_name": {
                "type": "string",
                "description": "计时器名称",
                "default": "default"
            }
        }
    }
)
def stop_timer(timer_name: str = "default") -> str:
    """停止计时并获取耗时"""
    try:
        if timer_name not in _timers:
            return f"[错误] 计时器 '{timer_name}' 未启动"
        
        start_time = _timers[timer_name]
        end_time = time.time_ns()
        elapsed_ns = end_time - start_time
        elapsed_ms = elapsed_ns / 1_000_000
        elapsed_s = elapsed_ns / 1_000_000_000
        
        # 清除计时器
        del _timers[timer_name]
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        return f"[成功] 计时器 '{timer_name}' 已停止\n停止时间: {current_time}\n耗时: {elapsed_ms:.4f} 毫秒 ({elapsed_s:.6f} 秒)"
    except Exception as e:
        return f"[错误] 停止计时器失败: {str(e)}"

@register_tool(
    name="get_timer_elapsed",
    description="获取计时器已经过的时间（不停止计时器）",
    schema={
        "type": "object",
        "properties": {
            "timer_name": {
                "type": "string",
                "description": "计时器名称",
                "default": "default"
            }
        }
    }
)
def get_timer_elapsed(timer_name: str = "default") -> str:
    """获取计时器已经过的时间（不停止计时器）"""
    try:
        if timer_name not in _timers:
            return f"[错误] 计时器 '{timer_name}' 未启动"
        
        start_time = _timers[timer_name]
        current_time = time.time_ns()
        elapsed_ns = current_time - start_time
        elapsed_ms = elapsed_ns / 1_000_000
        elapsed_s = elapsed_ns / 1_000_000_000
        
        return f"[成功] 计时器 '{timer_name}' 已运行:\n耗时: {elapsed_ms:.4f} 毫秒 ({elapsed_s:.6f} 秒)"
    except Exception as e:
        return f"[错误] 获取计时器耗时失败: {str(e)}"

# ==================== 实用工具 ====================

@register_tool(
    name="generate_timestamp_id",
    description="生成基于时间戳的唯一ID",
    schema={
        "type": "object",
        "properties": {
            "prefix": {
                "type": "string",
                "description": "ID前缀",
                "default": ""
            },
            "suffix": {
                "type": "string",
                "description": "ID后缀",
                "default": ""
            },
            "random_length": {
                "type": "integer",
                "description": "随机字符长度",
                "default": 6
            },
            "use_milliseconds": {
                "type": "boolean",
                "description": "是否使用毫秒时间戳",
                "default": False
            }
        }
    }
)
def generate_timestamp_id(prefix: str = "", suffix: str = "", random_length: int = 6, use_milliseconds: bool = False) -> str:
    """生成基于时间戳的唯一ID"""
    try:
        # 生成时间戳部分
        if use_milliseconds:
            timestamp_part = str(int(time.time() * 1000))
        else:
            timestamp_part = str(int(time.time()))
        
        # 生成随机字符串
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=random_length))
        
        # 组合ID
        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(timestamp_part)
        parts.append(random_chars)
        if suffix:
            parts.append(suffix)
        
        unique_id = '_'.join(parts)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        return f"[成功] 生成唯一ID:\nID: {unique_id}\n生成时间: {current_time}"
    except Exception as e:
        return f"[错误] 生成ID失败: {str(e)}"

@register_tool(
    name="list_timezones",
    description="列出常用时区",
    schema={
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "地区筛选",
                "enum": ["all", "asia", "america", "europe", "africa", "australia"],
                "default": "all"
            }
        }
    }
)
def list_timezones(region: str = "all") -> str:
    """列出常用时区"""
    try:
        common_timezones = {
            "asia": [
                "Asia/Shanghai", "Asia/Hong_Kong", "Asia/Tokyo", "Asia/Seoul",
                "Asia/Singapore", "Asia/Bangkok", "Asia/Mumbai", "Asia/Dubai"
            ],
            "america": [
                "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
                "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
                "America/Toronto", "America/Sao_Paulo"
            ],
            "europe": [
                "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome",
                "Europe/Madrid", "Europe/Amsterdam", "Europe/Zurich", "Europe/Moscow"
            ],
            "africa": [
                "Africa/Cairo", "Africa/Johannesburg", "Africa/Lagos", "Africa/Nairobi"
            ],
            "australia": [
                "Australia/Sydney", "Australia/Melbourne", "Australia/Perth", "Australia/Brisbane"
            ]
        }
        
        if region == "all":
            result = "[成功] 常用时区列表:\n\n"
            for reg, zones in common_timezones.items():
                result += f"{reg.upper()}:\n"
                for zone in zones:
                    result += f"  {zone}\n"
                result += "\n"
        elif region in common_timezones:
            zones = common_timezones[region]
            result = f"[成功] {region.upper()}地区时区:\n"
            for zone in zones:
                result += f"  {zone}\n"
        else:
            return f"[错误] 不支持的地区: {region}"
        
        return result
    except Exception as e:
        return f"[错误] 获取时区列表失败: {str(e)}" 