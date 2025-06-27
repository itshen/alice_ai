# MODULE_DESCRIPTION: 金融交易时间管理工具集合，专门用于AI量化交易的时间管理
# MODULE_CATEGORY: trading_time
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 1.0.0

"""
金融交易时间管理工具模块
专门用于AI量化交易的时间管理，提供市场状态判断、交易日计算、K线时间对齐等功能
"""

import os
import time
import datetime
import pytz
from typing import Dict, List, Tuple, Optional, Union, NamedTuple
from enum import Enum
from dataclasses import dataclass
from functools import lru_cache

# 使用绝对导入避免相对导入问题
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# ==================== 数据结构定义 ====================

class MarketStatus(Enum):
    """市场状态枚举"""
    CLOSED = "closed"           # 休市
    PRE_MARKET = "pre_market"   # 盘前
    OPEN = "open"               # 开盘中
    POST_MARKET = "post_market" # 盘后
    HOLIDAY = "holiday"         # 节假日

class TradingSession(NamedTuple):
    """交易时段"""
    name: str           # 时段名称
    start_time: str     # 开始时间 (HH:MM:SS)
    end_time: str       # 结束时间 (HH:MM:SS)
    timezone: str       # 时区

@dataclass
class MarketInfo:
    """市场信息"""
    name: str                           # 市场名称
    code: str                           # 市场代码
    timezone: str                       # 时区
    trading_sessions: List[TradingSession]  # 交易时段
    holidays: Optional[List[str]] = None    # 节假日列表 (YYYY-MM-DD格式)
    weekend_days: Tuple[int, int] = (5, 6)  # 周末 (5=周六, 6=周日)

# ==================== 全局管理器 ====================

class TradingTimeManager:
    """交易时间管理器"""
    
    def __init__(self):
        self.markets = self._init_markets()
        self._holidays_cache = {}
    
    def _init_markets(self) -> Dict[str, MarketInfo]:
        """初始化市场信息"""
        markets = {}
        
        # 中国A股市场
        markets['CN_A'] = MarketInfo(
            name="中国A股",
            code="CN_A",
            timezone="Asia/Shanghai",
            trading_sessions=[
                TradingSession("上午盘", "09:30:00", "11:30:00", "Asia/Shanghai"),
                TradingSession("下午盘", "13:00:00", "15:00:00", "Asia/Shanghai"),
            ],
            weekend_days=(5, 6)
        )
        
        # 香港股市
        markets['HK'] = MarketInfo(
            name="香港股市",
            code="HK",
            timezone="Asia/Hong_Kong",
            trading_sessions=[
                TradingSession("上午盘", "09:30:00", "12:00:00", "Asia/Hong_Kong"),
                TradingSession("下午盘", "13:00:00", "16:00:00", "Asia/Hong_Kong"),
            ],
            weekend_days=(5, 6)
        )
        
        # 美股市场
        markets['US'] = MarketInfo(
            name="美股",
            code="US",
            timezone="US/Eastern",
            trading_sessions=[
                TradingSession("盘前", "04:00:00", "09:30:00", "US/Eastern"),
                TradingSession("正常交易", "09:30:00", "16:00:00", "US/Eastern"),
                TradingSession("盘后", "16:00:00", "20:00:00", "US/Eastern"),
            ],
            weekend_days=(5, 6)
        )
        
        # 欧洲股市 (以伦敦为例)
        markets['EU'] = MarketInfo(
            name="欧洲股市",
            code="EU",
            timezone="Europe/London",
            trading_sessions=[
                TradingSession("正常交易", "08:00:00", "16:30:00", "Europe/London"),
            ],
            weekend_days=(5, 6)
        )
        
        # 日本股市
        markets['JP'] = MarketInfo(
            name="日本股市",
            code="JP",
            timezone="Asia/Tokyo",
            trading_sessions=[
                TradingSession("上午盘", "09:00:00", "11:30:00", "Asia/Tokyo"),
                TradingSession("下午盘", "12:30:00", "15:00:00", "Asia/Tokyo"),
            ],
            weekend_days=(5, 6)
        )
        
        return markets
    
    @lru_cache(maxsize=128)
    def _get_market_datetime(self, market_code: str, timestamp: Optional[float] = None) -> datetime.datetime:
        """获取市场当地时间"""
        market = self.markets.get(market_code)
        if not market:
            raise ValueError(f"未知的市场代码: {market_code}")
        
        if timestamp is None:
            timestamp = time.time()
        
        tz = pytz.timezone(market.timezone)
        return datetime.datetime.fromtimestamp(timestamp, tz)

# 创建全局实例
_trading_manager = TradingTimeManager()

# ==================== K线时间管理器 ====================

class KLineTimeManager:
    """K线时间管理器"""
    
    @staticmethod
    def get_kline_intervals() -> Dict[str, int]:
        """获取常用K线间隔"""
        return {
            '1m': 60,           # 1分钟
            '3m': 180,          # 3分钟
            '5m': 300,          # 5分钟
            '15m': 900,         # 15分钟
            '30m': 1800,        # 30分钟
            '1h': 3600,         # 1小时
            '2h': 7200,         # 2小时
            '4h': 14400,        # 4小时
            '6h': 21600,        # 6小时
            '8h': 28800,        # 8小时
            '12h': 43200,       # 12小时
            '1d': 86400,        # 1天
            '3d': 259200,       # 3天
            '1w': 604800,       # 1周
        }
    
    @staticmethod
    def align_to_kline_time(timestamp: float, interval_seconds: int) -> int:
        """将时间戳对齐到K线时间"""
        return int(timestamp // interval_seconds) * interval_seconds

_kline_manager = KLineTimeManager()

# ==================== 市场状态查询工具 ====================

@register_tool(
    name="get_market_status",
    description="获取市场当前状态",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            },
            "timestamp": {
                "type": "number",
                "description": "指定时间戳，不提供则使用当前时间"
            }
        },
        "required": ["market_code"]
    }
)
def get_market_status(market_code: str, timestamp: Optional[float] = None) -> str:
    """获取市场当前状态"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        dt = _trading_manager._get_market_datetime(market_code, timestamp)
        
        # 检查是否为周末
        weekday = dt.weekday()  # 0=周一, 6=周日
        if weekday in market.weekend_days:
            status = MarketStatus.CLOSED
        else:
            # 检查是否为节假日
            date_str = dt.strftime('%Y-%m-%d')
            if market.holidays and date_str in market.holidays:
                status = MarketStatus.HOLIDAY
            else:
                # 检查交易时段
                current_time = dt.time()
                status = MarketStatus.CLOSED
                
                for session in market.trading_sessions:
                    start_time = datetime.time.fromisoformat(session.start_time)
                    end_time = datetime.time.fromisoformat(session.end_time)
                    
                    if start_time <= current_time <= end_time:
                        if session.name in ["盘前", "pre_market"]:
                            status = MarketStatus.PRE_MARKET
                        elif session.name in ["盘后", "post_market"]:
                            status = MarketStatus.POST_MARKET
                        else:
                            status = MarketStatus.OPEN
                        break
        
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        status_desc = {
            MarketStatus.CLOSED: "休市",
            MarketStatus.PRE_MARKET: "盘前交易",
            MarketStatus.OPEN: "开盘中",
            MarketStatus.POST_MARKET: "盘后交易",
            MarketStatus.HOLIDAY: "节假日"
        }
        
        return f"[成功] {market.name}市场状态:\n时间: {time_str} ({market.timezone})\n状态: {status_desc[status]} ({status.value})"
    except Exception as e:
        return f"[错误] 获取市场状态失败: {str(e)}"

@register_tool(
    name="is_market_open",
    description="判断市场是否开盘",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            },
            "timestamp": {
                "type": "number",
                "description": "指定时间戳，不提供则使用当前时间"
            }
        },
        "required": ["market_code"]
    }
)
def is_market_open(market_code: str, timestamp: Optional[float] = None) -> str:
    """判断市场是否开盘"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        dt = _trading_manager._get_market_datetime(market_code, timestamp)
        
        # 检查是否为周末
        weekday = dt.weekday()
        if weekday in market.weekend_days:
            is_open = False
        else:
            # 检查是否为节假日
            date_str = dt.strftime('%Y-%m-%d')
            if market.holidays and date_str in market.holidays:
                is_open = False
            else:
                # 检查是否在正常交易时段
                current_time = dt.time()
                is_open = False
                
                for session in market.trading_sessions:
                    if session.name not in ["盘前", "pre_market", "盘后", "post_market"]:
                        start_time = datetime.time.fromisoformat(session.start_time)
                        end_time = datetime.time.fromisoformat(session.end_time)
                        
                        if start_time <= current_time <= end_time:
                            is_open = True
                            break
        
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        result = "开盘中" if is_open else "未开盘"
        
        return f"[成功] {market.name}开盘状态:\n时间: {time_str} ({market.timezone})\n状态: {result}"
    except Exception as e:
        return f"[错误] 判断市场开盘状态失败: {str(e)}"

@register_tool(
    name="get_market_current_time",
    description="获取市场当前时间",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            }
        },
        "required": ["market_code"]
    }
)
def get_market_current_time(market_code: str) -> str:
    """获取市场当前时间"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        dt = _trading_manager._get_market_datetime(market_code)
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        return f"[成功] {market.name}当前时间:\n{time_str} ({market.timezone})"
    except Exception as e:
        return f"[错误] 获取市场时间失败: {str(e)}"

@register_tool(
    name="list_all_markets",
    description="列出所有支持的市场",
    schema={
        "type": "object",
        "properties": {}
    }
)
def list_all_markets() -> str:
    """列出所有支持的市场"""
    try:
        result = "[成功] 支持的市场列表:\n\n"
        
        for code, market in _trading_manager.markets.items():
            result += f"代码: {code}\n"
            result += f"名称: {market.name}\n"
            result += f"时区: {market.timezone}\n"
            result += f"交易时段:\n"
            for session in market.trading_sessions:
                result += f"  {session.name}: {session.start_time} - {session.end_time}\n"
            result += "\n"
        
        return result
    except Exception as e:
        return f"[错误] 获取市场列表失败: {str(e)}"

# ==================== 交易日计算工具 ====================

@register_tool(
    name="get_next_trading_day",
    description="获取下一个交易日",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            },
            "date_str": {
                "type": "string",
                "description": "起始日期 (YYYY-MM-DD)，不提供则使用今天"
            }
        },
        "required": ["market_code"]
    }
)
def get_next_trading_day(market_code: str, date_str: Optional[str] = None) -> str:
    """获取下一个交易日"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        if date_str is None:
            dt = _trading_manager._get_market_datetime(market_code)
        else:
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        
        # 从明天开始查找
        dt += datetime.timedelta(days=1)
        
        # 最多查找30天
        for _ in range(30):
            current_date_str = dt.strftime('%Y-%m-%d')
            weekday = dt.weekday()
            
            # 检查是否为工作日且非节假日
            if (weekday not in market.weekend_days and 
                (not market.holidays or current_date_str not in market.holidays)):
                start_date = date_str or _trading_manager._get_market_datetime(market_code).strftime('%Y-%m-%d')
                return f"[成功] {market.name}下一个交易日:\n起始日期: {start_date}\n下一个交易日: {current_date_str}"
            
            dt += datetime.timedelta(days=1)
        
        return f"[错误] 无法找到下一个交易日（查找范围：30天）"
    except Exception as e:
        return f"[错误] 获取下一个交易日失败: {str(e)}"

@register_tool(
    name="get_previous_trading_day",
    description="获取上一个交易日",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            },
            "date_str": {
                "type": "string",
                "description": "起始日期 (YYYY-MM-DD)，不提供则使用今天"
            }
        },
        "required": ["market_code"]
    }
)
def get_previous_trading_day(market_code: str, date_str: Optional[str] = None) -> str:
    """获取上一个交易日"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        if date_str is None:
            dt = _trading_manager._get_market_datetime(market_code)
        else:
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        
        # 从昨天开始查找
        dt -= datetime.timedelta(days=1)
        
        # 最多查找30天
        for _ in range(30):
            current_date_str = dt.strftime('%Y-%m-%d')
            weekday = dt.weekday()
            
            # 检查是否为工作日且非节假日
            if (weekday not in market.weekend_days and 
                (not market.holidays or current_date_str not in market.holidays)):
                start_date = date_str or _trading_manager._get_market_datetime(market_code).strftime('%Y-%m-%d')
                return f"[成功] {market.name}上一个交易日:\n起始日期: {start_date}\n上一个交易日: {current_date_str}"
            
            dt -= datetime.timedelta(days=1)
        
        return f"[错误] 无法找到上一个交易日（查找范围：30天）"
    except Exception as e:
        return f"[错误] 获取上一个交易日失败: {str(e)}"

@register_tool(
    name="get_trading_days_between",
    description="获取两个日期之间的所有交易日",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            },
            "start_date": {
                "type": "string",
                "description": "开始日期 (YYYY-MM-DD)"
            },
            "end_date": {
                "type": "string",
                "description": "结束日期 (YYYY-MM-DD)"
            }
        },
        "required": ["market_code", "start_date", "end_date"]
    }
)
def get_trading_days_between(market_code: str, start_date: str, end_date: str) -> str:
    """获取两个日期之间的所有交易日"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_dt > end_dt:
            return f"[错误] 开始日期不能晚于结束日期"
        
        trading_days = []
        current_dt = start_dt
        
        while current_dt <= end_dt:
            current_date_str = current_dt.strftime('%Y-%m-%d')
            weekday = current_dt.weekday()
            
            # 检查是否为工作日且非节假日
            if (weekday not in market.weekend_days and 
                (not market.holidays or current_date_str not in market.holidays)):
                trading_days.append(current_date_str)
            
            current_dt += datetime.timedelta(days=1)
        
        result = f"[成功] {market.name}交易日列表:\n"
        result += f"日期范围: {start_date} 到 {end_date}\n"
        result += f"交易日总数: {len(trading_days)}\n\n"
        
        if trading_days:
            result += "交易日列表:\n"
            for day in trading_days:
                result += f"  {day}\n"
        else:
            result += "该日期范围内没有交易日"
        
        return result
    except Exception as e:
        return f"[错误] 获取交易日列表失败: {str(e)}"

# ==================== 开盘收盘时间工具 ====================

@register_tool(
    name="seconds_until_market_open",
    description="距离市场开盘还有多少秒",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            }
        },
        "required": ["market_code"]
    }
)
def seconds_until_market_open(market_code: str) -> str:
    """距离市场开盘还有多少秒"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        current_time = _trading_manager._get_market_datetime(market_code)
        
        # 检查是否已经开盘
        current_time_only = current_time.time()
        is_open = False
        
        for session in market.trading_sessions:
            if session.name not in ["盘前", "pre_market", "盘后", "post_market"]:
                start_time = datetime.time.fromisoformat(session.start_time)
                end_time = datetime.time.fromisoformat(session.end_time)
                
                if start_time <= current_time_only <= end_time:
                    is_open = True
                    break
        
        if is_open:
            return f"[结果] {market.name}已经开盘\n当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 查找下一个开盘时间
        today_str = current_time.strftime('%Y-%m-%d')
        
        # 先尝试今天的开盘时间
        for session in market.trading_sessions:
            if session.name not in ["盘前", "pre_market", "盘后", "post_market"]:
                open_time_str = f"{today_str} {session.start_time}"
                open_time = datetime.datetime.strptime(open_time_str, '%Y-%m-%d %H:%M:%S')
                open_time = pytz.timezone(market.timezone).localize(open_time)
                
                if open_time > current_time:
                    # 检查今天是否为交易日
                    weekday = current_time.weekday()
                    if (weekday not in market.weekend_days and 
                        (not market.holidays or today_str not in market.holidays)):
                        seconds_left = int((open_time - current_time).total_seconds())
                        hours, remainder = divmod(seconds_left, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        return f"[成功] {market.name}距离开盘:\n当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n开盘时间: {open_time.strftime('%Y-%m-%d %H:%M:%S')}\n剩余时间: {hours}小时{minutes}分{seconds}秒 ({seconds_left}秒)"
        
        # 查找下一个交易日的开盘时间
        next_day = current_time + datetime.timedelta(days=1)
        for _ in range(30):  # 最多查找30天
            next_day_str = next_day.strftime('%Y-%m-%d')
            weekday = next_day.weekday()
            
            if (weekday not in market.weekend_days and 
                (not market.holidays or next_day_str not in market.holidays)):
                # 找到下一个交易日
                for session in market.trading_sessions:
                    if session.name not in ["盘前", "pre_market", "盘后", "post_market"]:
                        open_time_str = f"{next_day_str} {session.start_time}"
                        open_time = datetime.datetime.strptime(open_time_str, '%Y-%m-%d %H:%M:%S')
                        open_time = pytz.timezone(market.timezone).localize(open_time)
                        
                        seconds_left = int((open_time - current_time).total_seconds())
                        hours, remainder = divmod(seconds_left, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        return f"[成功] {market.name}距离开盘:\n当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n下次开盘: {open_time.strftime('%Y-%m-%d %H:%M:%S')}\n剩余时间: {hours}小时{minutes}分{seconds}秒 ({seconds_left}秒)"
            
            next_day += datetime.timedelta(days=1)
        
        return f"[错误] 无法找到下次开盘时间（查找范围：30天）"
    except Exception as e:
        return f"[错误] 计算开盘倒计时失败: {str(e)}"

@register_tool(
    name="seconds_until_market_close",
    description="距离市场收盘还有多少秒",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            }
        },
        "required": ["market_code"]
    }
)
def seconds_until_market_close(market_code: str) -> str:
    """距离市场收盘还有多少秒"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        current_time = _trading_manager._get_market_datetime(market_code)
        current_time_only = current_time.time()
        
        # 查找当前正在进行的交易时段
        current_session = None
        for session in market.trading_sessions:
            if session.name not in ["盘前", "pre_market", "盘后", "post_market"]:
                start_time = datetime.time.fromisoformat(session.start_time)
                end_time = datetime.time.fromisoformat(session.end_time)
                
                if start_time <= current_time_only <= end_time:
                    current_session = session
                    break
        
        if not current_session:
            return f"[结果] {market.name}当前未开盘\n当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 计算距离收盘的时间
        today_str = current_time.strftime('%Y-%m-%d')
        close_time_str = f"{today_str} {current_session.end_time}"
        close_time = datetime.datetime.strptime(close_time_str, '%Y-%m-%d %H:%M:%S')
        close_time = pytz.timezone(market.timezone).localize(close_time)
        
        seconds_left = int((close_time - current_time).total_seconds())
        
        if seconds_left <= 0:
            return f"[结果] {market.name}已经收盘\n当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        hours, remainder = divmod(seconds_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"[成功] {market.name}距离收盘:\n当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n收盘时间: {close_time.strftime('%Y-%m-%d %H:%M:%S')}\n剩余时间: {hours}小时{minutes}分{seconds}秒 ({seconds_left}秒)"
    except Exception as e:
        return f"[错误] 计算收盘倒计时失败: {str(e)}"

# ==================== K线时间管理工具 ====================

@register_tool(
    name="align_to_kline_time",
    description="将时间戳对齐到K线时间",
    schema={
        "type": "object",
        "properties": {
            "timestamp": {
                "type": "number",
                "description": "原始时间戳"
            },
            "interval": {
                "type": "string",
                "description": "K线间隔",
                "enum": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
            }
        },
        "required": ["timestamp", "interval"]
    }
)
def align_to_kline_time(timestamp: float, interval: str) -> str:
    """将时间戳对齐到K线时间"""
    try:
        intervals = _kline_manager.get_kline_intervals()
        if interval not in intervals:
            return f"[错误] 不支持的K线间隔: {interval}"
        
        interval_seconds = intervals[interval]
        aligned_timestamp = _kline_manager.align_to_kline_time(timestamp, interval_seconds)
        
        original_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        aligned_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(aligned_timestamp))
        
        return f"[成功] K线时间对齐 ({interval}):\n原始时间: {original_time} ({timestamp})\n对齐时间: {aligned_time} ({aligned_timestamp})"
    except Exception as e:
        return f"[错误] K线时间对齐失败: {str(e)}"

@register_tool(
    name="generate_kline_timestamps",
    description="生成K线时间戳序列",
    schema={
        "type": "object",
        "properties": {
            "start_time": {
                "type": "string",
                "description": "开始时间，支持时间戳或时间字符串 (YYYY-MM-DD HH:mm:ss)"
            },
            "end_time": {
                "type": "string",
                "description": "结束时间，支持时间戳或时间字符串 (YYYY-MM-DD HH:mm:ss)"
            },
            "interval": {
                "type": "string",
                "description": "K线间隔",
                "enum": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
            }
        },
        "required": ["start_time", "end_time", "interval"]
    }
)
def generate_kline_timestamps(start_time: str, end_time: str, interval: str) -> str:
    """生成K线时间戳序列"""
    try:
        intervals = _kline_manager.get_kline_intervals()
        if interval not in intervals:
            return f"[错误] 不支持的K线间隔: {interval}"
        
        interval_seconds = intervals[interval]
        
        # 解析开始和结束时间
        try:
            start_timestamp = float(start_time)
        except ValueError:
            # 尝试解析时间字符串
            import re
            patterns = [
                r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2}):(\d{1,2})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d{1,2})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})'
            ]
            
            parsed = False
            for pattern in patterns:
                match = re.match(pattern, start_time.strip())
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        year, month, day = groups
                        hour = minute = second = 0
                    else:
                        year, month, day, hour, minute, second = groups
                    
                    dt = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                    start_timestamp = dt.timestamp()
                    parsed = True
                    break
            
            if not parsed:
                return f"[错误] 无法解析开始时间: {start_time}"
        
        try:
            end_timestamp = float(end_time)
        except ValueError:
            # 尝试解析时间字符串
            parsed = False
            for pattern in patterns:
                match = re.match(pattern, end_time.strip())
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        year, month, day = groups
                        hour = minute = second = 0
                    else:
                        year, month, day, hour, minute, second = groups
                    
                    dt = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                    end_timestamp = dt.timestamp()
                    parsed = True
                    break
            
            if not parsed:
                return f"[错误] 无法解析结束时间: {end_time}"
        
        # 对齐开始时间
        aligned_start = _kline_manager.align_to_kline_time(start_timestamp, interval_seconds)
        
        # 生成时间戳序列
        timestamps = []
        current_timestamp = aligned_start
        
        while current_timestamp <= end_timestamp:
            timestamps.append(int(current_timestamp))
            current_timestamp += interval_seconds
        
        if len(timestamps) > 100:
            # 如果时间戳太多，只显示前10个和后10个
            result = f"[成功] 生成K线时间戳序列 ({interval}):\n"
            result += f"时间范围: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_timestamp))} 到 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_timestamp))}\n"
            result += f"总数量: {len(timestamps)}\n\n"
            result += "前10个时间戳:\n"
            for i, ts in enumerate(timestamps[:10]):
                result += f"  {i+1}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))} ({ts})\n"
            result += "...\n"
            result += "后10个时间戳:\n"
            for i, ts in enumerate(timestamps[-10:], len(timestamps)-9):
                result += f"  {i}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))} ({ts})\n"
        else:
            result = f"[成功] 生成K线时间戳序列 ({interval}):\n"
            result += f"时间范围: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_timestamp))} 到 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_timestamp))}\n"
            result += f"总数量: {len(timestamps)}\n\n"
            for i, ts in enumerate(timestamps, 1):
                result += f"  {i}: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))} ({ts})\n"
        
        return result
    except Exception as e:
        return f"[错误] 生成K线时间戳序列失败: {str(e)}"

@register_tool(
    name="get_kline_intervals",
    description="获取支持的K线间隔列表",
    schema={
        "type": "object",
        "properties": {}
    }
)
def get_kline_intervals() -> str:
    """获取支持的K线间隔列表"""
    try:
        intervals = _kline_manager.get_kline_intervals()
        
        result = "[成功] 支持的K线间隔:\n\n"
        for interval, seconds in intervals.items():
            if seconds < 3600:
                desc = f"{seconds//60}分钟"
            elif seconds < 86400:
                desc = f"{seconds//3600}小时"
            else:
                desc = f"{seconds//86400}天"
            
            result += f"{interval}: {desc} ({seconds}秒)\n"
        
        return result
    except Exception as e:
        return f"[错误] 获取K线间隔列表失败: {str(e)}"

# ==================== 节假日管理工具 ====================

@register_tool(
    name="add_holiday",
    description="添加节假日",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            },
            "date_str": {
                "type": "string",
                "description": "节假日日期 (YYYY-MM-DD)"
            }
        },
        "required": ["market_code", "date_str"]
    }
)
def add_holiday(market_code: str, date_str: str) -> str:
    """添加节假日"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        # 验证日期格式
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return f"[错误] 无效的日期格式，请使用 YYYY-MM-DD 格式"
        
        if market.holidays is None:
            market.holidays = []
        
        if date_str in market.holidays:
            return f"[结果] {market.name}的节假日 {date_str} 已存在"
        
        market.holidays.append(date_str)
        market.holidays.sort()  # 保持排序
        
        return f"[成功] 已添加{market.name}节假日: {date_str}\n当前节假日总数: {len(market.holidays)}"
    except Exception as e:
        return f"[错误] 添加节假日失败: {str(e)}"

@register_tool(
    name="remove_holiday",
    description="移除节假日",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            },
            "date_str": {
                "type": "string",
                "description": "节假日日期 (YYYY-MM-DD)"
            }
        },
        "required": ["market_code", "date_str"]
    }
)
def remove_holiday(market_code: str, date_str: str) -> str:
    """移除节假日"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        if not market.holidays or date_str not in market.holidays:
            return f"[结果] {market.name}的节假日 {date_str} 不存在"
        
        market.holidays.remove(date_str)
        
        return f"[成功] 已移除{market.name}节假日: {date_str}\n当前节假日总数: {len(market.holidays)}"
    except Exception as e:
        return f"[错误] 移除节假日失败: {str(e)}"

@register_tool(
    name="list_holidays",
    description="列出市场的所有节假日",
    schema={
        "type": "object",
        "properties": {
            "market_code": {
                "type": "string",
                "description": "市场代码",
                "enum": ["CN_A", "HK", "US", "EU", "JP"]
            }
        },
        "required": ["market_code"]
    }
)
def list_holidays(market_code: str) -> str:
    """列出市场的所有节假日"""
    try:
        market = _trading_manager.markets.get(market_code)
        if not market:
            return f"[错误] 未知的市场代码: {market_code}"
        
        if not market.holidays:
            return f"[结果] {market.name}暂无设置节假日"
        
        result = f"[成功] {market.name}节假日列表 (共{len(market.holidays)}个):\n\n"
        for holiday in sorted(market.holidays):
            # 计算是星期几
            try:
                dt = datetime.datetime.strptime(holiday, '%Y-%m-%d')
                weekday = dt.weekday()
                weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                weekday_str = weekdays[weekday]
                result += f"  {holiday} ({weekday_str})\n"
            except:
                result += f"  {holiday}\n"
        
        return result
    except Exception as e:
        return f"[错误] 获取节假日列表失败: {str(e)}" 