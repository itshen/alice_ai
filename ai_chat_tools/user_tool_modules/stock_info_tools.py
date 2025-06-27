# MODULE_DESCRIPTION: 全面的证券交易市场信息工具集合，提供股票基本面分析、技术分析、实时资讯和市场排行榜等功能
# MODULE_CATEGORY: stock_info
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 2.0.0

"""
证券交易市场信息工具模块
提供完整的金融市场数据获取和分析功能，包括：

📊 基本面分析：
- 获取公司概况信息（美股、港股、A股）
- 获取财务指标数据（盈利能力、成长性、偿债能力、营运能力等）
- 获取利润表数据（营业收入、成本、净利润等损益项目）
- 获取资产负债表数据（资产、负债、股东权益等财务状况）

📈 技术分析：
- 获取实时股价和K线数据
- 计算技术指标（MACD、KDJ、布林带、SAR、移动平均线等）
- 提供专业的技术分析摘要和投资建议

📰 市场资讯：
- 获取股票相关新闻资讯，支持并发获取完整内容
- 智能关键词搜索和中英文股票名称转换
- 提供丰富的市场信息用于投资决策

📊 市场排行榜：
- 实时涨幅榜、跌幅榜、成交量榜、成交额榜
- 支持美股、港股、A股三大市场
- 用于市场热点分析和投资机会发现

🔧 工具特性：
- 支持批量查询和自动市场类型检测
- 智能股票代码格式识别和标准化
- 专业的数据分析和可视化输出
- 专门用于AI量化交易和投资分析
"""

import os
import json
import re
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# 使用绝对导入避免相对导入问题
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# 导入web抓取工具的管理器
try:
    from ai_chat_tools.user_tool_modules.web_scraping_tools import _web_scraper, WebScraperManager
    WEB_SCRAPER_AVAILABLE = True
except ImportError:
    WEB_SCRAPER_AVAILABLE = False
    _web_scraper = None
    WebScraperManager = None

# ==================== 数据结构定义 ====================

class MarketType(Enum):
    """市场类型枚举"""
    US = "us"           # 美股
    HK = "hk"           # 港股
    CN = "cn"           # A股
    UK = "uk"           # 英股
    JP = "jp"           # 日股

@dataclass
class CompanyInfo:
    """公司基本信息"""
    symbol: str                         # 股票代码
    org_name_cn: Optional[str] = None   # 中文公司名称
    org_name_en: Optional[str] = None   # 英文公司名称
    org_short_name_cn: Optional[str] = None  # 中文简称
    org_short_name_en: Optional[str] = None  # 英文简称
    main_operation_business: Optional[str] = None  # 主营业务
    org_introduction: Optional[str] = None  # 公司介绍
    established_date: Optional[str] = None  # 成立日期
    listed_date: Optional[str] = None       # 上市日期
    staff_num: Optional[int] = None         # 员工数量
    website: Optional[str] = None           # 公司网站
    chairman: Optional[str] = None          # 董事长
    market_type: Optional[str] = None       # 市场类型
    trading_market: Optional[str] = None    # 交易所

# ==================== 股票信息管理器 ====================

class StockInfoManager:
    """股票信息管理器"""
    
    def __init__(self):
        self.base_urls = {
            MarketType.US: "https://stock.xueqiu.com/v5/stock/f10/us/company.json",
            MarketType.HK: "https://stock.xueqiu.com/v5/stock/f10/hk/company.json", 
            MarketType.CN: "https://stock.xueqiu.com/v5/stock/f10/cn/company.json"
        }
        
        # 财务指标API URLs
        self.finance_urls = {
            MarketType.US: "https://stock.xueqiu.com/v5/stock/finance/us/indicator.json",
            MarketType.HK: "https://stock.xueqiu.com/v5/stock/finance/hk/indicator.json",
            MarketType.CN: "https://stock.xueqiu.com/v5/stock/finance/cn/indicator.json"
        }
        
        # 利润表API URLs  
        self.income_urls = {
            MarketType.US: "https://stock.xueqiu.com/v5/stock/finance/us/income.json",
            MarketType.HK: "https://stock.xueqiu.com/v5/stock/finance/hk/income.json",
            MarketType.CN: "https://stock.xueqiu.com/v5/stock/finance/cn/income.json"
        }
        
        # 雪球API需要的请求头
        self.xueqiu_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,ko;q=0.8,en-US;q=0.7,en;q=0.6',
            'cache-control': 'no-cache',
            'origin': 'https://xueqiu.com',
            'referer': 'https://xueqiu.com/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'cookie': 's=be12bcx3pb; cookiesu=971748192631827; device_id=afda57cfe6697001d99fa8895d7a8922; u=971748192631827; Hm_lvt_1db88642e346389874251b5a1eded6e3=1748192633,1749565221; HMACCOUNT=73EFE7072B2EF8EE; xq_a_token=b7259d09435458cc3f1a963479abb270a1a016ce; xqat=b7259d09435458cc3f1a963479abb270a1a016ce; xq_r_token=28108bfa1d92ac8a46bbb57722633746218621a3; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTc1MjU0MTk4OCwiY3RtIjoxNzQ5OTk0MzEyODE0LCJjaWQiOiJkOWQwbjRBWnVwIn0.jNWjZYg_wpiX1GgMAlx7hE9ZE8pTjQg6V5NgsM7O2vSbzM_yE4np01eywM_aKem3L0sh3bMqgbpZT8IG0L61oJ7yEV84aO6wajvfSgP8NOtkNJxDk6ljYG57-fgau9Ig1Vpi49_Md-fM4BXQeza0sgHXnBLnvv7LyVks5Z1puo4mr_pGIyKYr_o5MtWRFGNZBRpDtTQ0SgYn8pQWJ9ceu9EojXvYeelq4hny4Gocgj6yvnaInlyimJA3own6mb5d0a067ypFnZ9YP3UG_jcBndeXn5OX1wNmeBcHgGTwH_vN33bo6vjb1Nqhu7v2Hb4WpLrjyK8POAFUjivQ7THdkA; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1749994377; ssxmod_itna=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45aY5D/zG7eDZDG9dDqx0ErXQA7Tthe9G7gqpPfl0Y4hkW80GSYaYQI=RxYifUzSc65c7eGImDG2DYoDCqDS0DD9R2GrDYYfDBYD74G+DDeDixbDGuuP2DDFRWbdclNQiW+PueDE000a0DDgjPD1QPWrulNqla4D0LWDfR0WleqxxY=DQwOQFoTDjR9W7KGyQeGWi8RjuKGuSZixphuNqPqU=RDSzCLxW7eM+BxPfA6hznGxngxNAD4EsPYs3AxYA4qY5=nQkxDic5Kb2rBqK4U2atq1UriXYAm=e52YI6DKrUxr/Dgpw1nwKAG5mDIA03iiGGDK3X3YD; ssxmod_itna2=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45a7eDAQf7G+C=fQD03qe8G3TPDBMpP4WMYZ5y53fY=RcKkBFEhWq3m+7DHhYA+sYgERHupq29iQ4YMLxWw6Hebfu80DRAbQh+CiujLr2fkrnKe4DpCXx5W5eWj3lSf+Xzeh4wO0HQG2K8Gj5m8rZ7MhW=TQkrYc5K0rk57fPvfhSzTF8yQcKnL4Qwg6EgbUU7Zxipai6Kpi2uZxNLUdu2UiCM8g4T/C=cR18=7m5covxo0sEYGiCmxnrZ0pV/bDNuqzir9GE+bZKGEQRY9GPLAtQDNfGNW0qbD40BPsiKPD'
        }
        
        # 创建数据存储目录
        self.data_dir = os.path.join(os.getcwd(), "stock_data")
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _detect_market_type(self, symbol: str) -> MarketType:
        """根据股票代码自动检测市场类型"""
        symbol = symbol.upper().strip()
        
        # A股判断
        if symbol.startswith(('SH', 'SZ')):
            return MarketType.CN
        if re.match(r'^[036]\d{5}$', symbol):  # 6位数字，0/3/6开头
            return MarketType.CN
            
        # 港股判断
        if re.match(r'^0\d{4}$', symbol):  # 5位数字，0开头
            return MarketType.HK
        if symbol.startswith('HK'):
            return MarketType.HK
            
        # 美股判断（默认）
        return MarketType.US
    
    def _normalize_symbol(self, symbol: str, market_type: MarketType) -> str:
        """标准化股票代码格式"""
        symbol = symbol.upper().strip()
        
        if market_type == MarketType.CN:
            # A股代码处理
            if symbol.startswith(('SH', 'SZ')):
                return symbol
            elif symbol.startswith('6'):
                return f'SH{symbol}'
            elif symbol.startswith(('0', '3')):
                return f'SZ{symbol}'
        elif market_type == MarketType.HK:
            # 港股代码处理
            if symbol.startswith('HK'):
                symbol = symbol[2:]
            if len(symbol) < 5:
                symbol = symbol.zfill(5)
        
        return symbol
    
    def _format_timestamp(self, timestamp: Optional[Union[int, float]]) -> Optional[str]:
        """格式化时间戳为日期字符串"""
        if timestamp is None:
            return None
        try:
            # 处理毫秒时间戳
            if timestamp > 1e10:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            return None
    
    def _extract_company_info(self, data: Dict[str, Any], symbol: str, market_type: MarketType) -> CompanyInfo:
        """从API响应中提取公司信息"""
        company_data = data.get('data', {}).get('company', {})
        
        return CompanyInfo(
            symbol=symbol,
            org_name_cn=company_data.get('org_name_cn'),
            org_name_en=company_data.get('org_name_en'),
            org_short_name_cn=company_data.get('org_short_name_cn'),
            org_short_name_en=company_data.get('org_short_name_en'),
            main_operation_business=company_data.get('main_operation_business'),
            org_introduction=company_data.get('org_cn_introduction') or company_data.get('org_en_introduction'),
            established_date=self._format_timestamp(company_data.get('established_date')),
            listed_date=self._format_timestamp(company_data.get('listed_date')),
            staff_num=company_data.get('staff_num'),
            website=company_data.get('org_website'),
            chairman=company_data.get('chairman'),
            market_type=market_type.value,
            trading_market=company_data.get('td_mkt')
        )
    
    def get_company_overview(self, symbol: str, market_type: Optional[str] = None, 
                           save_data: bool = False) -> Dict[str, Any]:
        """获取公司概况信息"""
        if not WEB_SCRAPER_AVAILABLE:
            return {
                'success': False,
                'error': 'Web抓取工具不可用，请确保web_scraping_tools模块正常导入'
            }
        
        try:
            # 确定市场类型
            if market_type:
                try:
                    market_enum = MarketType(market_type.lower())
                except ValueError:
                    market_enum = self._detect_market_type(symbol)
            else:
                market_enum = self._detect_market_type(symbol)
            
            # 标准化股票代码
            normalized_symbol = self._normalize_symbol(symbol, market_enum)
            
            # 构建API URL
            if market_enum not in self.base_urls:
                return {
                    'success': False,
                    'error': f'暂不支持的市场类型: {market_enum.value}'
                }
            
            api_url = f"{self.base_urls[market_enum]}?symbol={normalized_symbol}"
            
            # 设置referer
            headers = self.xueqiu_headers.copy()
            headers['referer'] = f'https://xueqiu.com/snowman/S/{normalized_symbol}/detail'
            
            # 使用web_scraper发送API请求
            if _web_scraper is None:
                return {
                    'success': False,
                    'error': 'Web抓取工具实例不可用'
                }
            
            result = _web_scraper.api_request(
                url=api_url,
                method="GET",
                headers=headers,
                timeout=30
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'API请求失败: {result["error"]}'
                }
            
            if not result['is_json']:
                return {
                    'success': False,
                    'error': '响应不是JSON格式'
                }
            
            # 检查API响应状态
            api_data = result['json']
            if api_data.get('error_code', 0) != 0:
                return {
                    'success': False,
                    'error': f'API返回错误: {api_data.get("error_description", "未知错误")}'
                }
            
            # 提取公司信息
            company_info = self._extract_company_info(api_data, normalized_symbol, market_enum)
            
            # 保存数据（如果需要）
            filepath = None
            if save_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"company_overview_{normalized_symbol}_{timestamp}.json"
                filepath = os.path.join(self.data_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(api_data, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'data': {
                    'company_info': company_info,
                    'raw_data': api_data,
                    'api_url': api_url,
                    'market_type': market_enum.value,
                    'normalized_symbol': normalized_symbol
                },
                'filepath': filepath
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取公司概况失败: {str(e)}'
            }
    
    def get_financial_indicators(self, symbol: str, market_type: Optional[str] = None, 
                               count: int = 5, save_data: bool = False) -> Dict[str, Any]:
        """获取财务指标数据"""
        if not WEB_SCRAPER_AVAILABLE:
            return {
                'success': False,
                'error': 'Web抓取工具不可用，请确保web_scraping_tools模块正常导入'
            }
        
        try:
            # 确定市场类型
            if market_type:
                try:
                    market_enum = MarketType(market_type.lower())
                except ValueError:
                    market_enum = self._detect_market_type(symbol)
            else:
                market_enum = self._detect_market_type(symbol)
            
            # 标准化股票代码
            normalized_symbol = self._normalize_symbol(symbol, market_enum)
            
            # 构建API URL
            if market_enum not in self.finance_urls:
                return {
                    'success': False,
                    'error': f'暂不支持的市场类型: {market_enum.value}'
                }
            
            # 构建财务指标API参数
            import time
            timestamp = int(time.time() * 1000)  # 毫秒时间戳
            
            params = {
                'symbol': normalized_symbol,
                'type': 'all',
                'is_detail': 'true',
                'count': str(count),
                'timestamp': str(timestamp)
            }
            
            api_url = self.finance_urls[market_enum]
            
            # 设置referer
            headers = self.xueqiu_headers.copy()
            headers['referer'] = f'https://xueqiu.com/snowman/S/{normalized_symbol}/detail'
            
            # 使用web_scraper发送API请求
            if _web_scraper is None:
                return {
                    'success': False,
                    'error': 'Web抓取工具实例不可用'
                }
            
            result = _web_scraper.api_request(
                url=api_url,
                method="GET",
                headers=headers,
                data=params,
                timeout=30
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'API请求失败: {result["error"]}'
                }
            
            if not result['is_json']:
                return {
                    'success': False,
                    'error': '响应不是JSON格式'
                }
            
            # 检查API响应状态
            api_data = result['json']
            if api_data.get('error_code', 0) != 0:
                return {
                    'success': False,
                    'error': f'API返回错误: {api_data.get("error_description", "未知错误")}'
                }
            
            # 保存数据（如果需要）
            filepath = None
            if save_data:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"financial_indicators_{normalized_symbol}_{timestamp_str}.json"
                filepath = os.path.join(self.data_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(api_data, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'data': {
                    'raw_data': api_data,
                    'api_url': f"{api_url}?{result['url'].split('?')[1] if '?' in result['url'] else ''}",
                    'market_type': market_enum.value,
                    'normalized_symbol': normalized_symbol
                },
                'filepath': filepath
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取财务指标失败: {str(e)}'
            }
    
    def get_income_statement(self, symbol: str, market_type: Optional[str] = None, 
                           count: int = 5, save_data: bool = False) -> Dict[str, Any]:
        """获取利润表数据"""
        if not WEB_SCRAPER_AVAILABLE:
            return {
                'success': False,
                'error': 'Web抓取工具不可用，请确保web_scraping_tools模块正常导入'
            }
        
        try:
            # 确定市场类型
            if market_type:
                try:
                    market_enum = MarketType(market_type.lower())
                except ValueError:
                    market_enum = self._detect_market_type(symbol)
            else:
                market_enum = self._detect_market_type(symbol)
            
            # 标准化股票代码
            normalized_symbol = self._normalize_symbol(symbol, market_enum)
            
            # 构建API URL
            if market_enum not in self.income_urls:
                return {
                    'success': False,
                    'error': f'暂不支持的市场类型: {market_enum.value}'
                }
            
            # 构建利润表API参数
            import time
            timestamp = int(time.time() * 1000)  # 毫秒时间戳
            
            params = {
                'symbol': normalized_symbol,
                'type': 'all',
                'is_detail': 'true',
                'count': str(count),
                'timestamp': str(timestamp)
            }
            
            api_url = self.income_urls[market_enum]
            
            # 设置referer
            headers = self.xueqiu_headers.copy()
            headers['referer'] = f'https://xueqiu.com/snowman/S/{normalized_symbol}/detail'
            
            # 使用web_scraper发送API请求
            if _web_scraper is None:
                return {
                    'success': False,
                    'error': 'Web抓取工具实例不可用'
                }
            
            result = _web_scraper.api_request(
                url=api_url,
                method="GET",
                headers=headers,
                data=params,
                timeout=30
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'API请求失败: {result["error"]}'
                }
            
            if not result['is_json']:
                return {
                    'success': False,
                    'error': '响应不是JSON格式'
                }
            
            # 检查API响应状态
            api_data = result['json']
            if api_data.get('error_code', 0) != 0:
                return {
                    'success': False,
                    'error': f'API返回错误: {api_data.get("error_description", "未知错误")}'
                }
            
            # 保存数据（如果需要）
            filepath = None
            if save_data:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"income_statement_{normalized_symbol}_{timestamp_str}.json"
                filepath = os.path.join(self.data_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(api_data, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'data': {
                    'raw_data': api_data,
                    'api_url': f"{api_url}?{result['url'].split('?')[1] if '?' in result['url'] else ''}",
                    'market_type': market_enum.value,
                    'normalized_symbol': normalized_symbol
                },
                'filepath': filepath
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取利润表失败: {str(e)}'
            }

# 创建全局实例
_stock_manager = StockInfoManager()

# ==================== 工具函数定义 ====================

@register_tool(
    name="get_company_overview",
    description="获取上市公司的详细概况信息，包括公司中英文名称、主营业务描述、公司简介、成立日期、上市日期、员工数量、官方网站、董事长信息、交易所信息等。支持美股、港股、A股三大市场，自动识别股票代码所属市场。",
    schema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，支持美股(如TSLA)、港股(如00700)、A股(如SH688111或688111)"
            },
            "market_type": {
                "type": "string",
                "description": "市场类型，可选值: us(美股), hk(港股), cn(A股)。不指定则自动检测",
                "enum": ["us", "hk", "cn"]
            },
            "save_data": {
                "type": "boolean",
                "description": "是否保存原始数据到本地文件，默认False",
                "default": False
            }
        },
        "required": ["symbol"]
    }
)
def get_company_overview(symbol: str, market_type: Optional[str] = None, save_data: bool = False) -> str:
    """获取上市公司的概况信息"""
    try:
        result = _stock_manager.get_company_overview(symbol, market_type, save_data)
        
        if not result['success']:
            return f"[错误] {result['error']}"
        
        data = result['data']
        company = data['company_info']
        
        # 构建输出信息
        output = f"[成功] 公司概况信息获取完成\n"
        output += f"股票代码: {company.symbol} ({data['market_type'].upper()})\n"
        output += f"API地址: {data['api_url']}\n"
        
        if result['filepath']:
            output += f"数据文件: {result['filepath']}\n"
        
        output += f"{'=' * 60}\n\n"
        
        # 直接显示所有原始API返回的公司数据
        company_data = data['raw_data'].get('data', {}).get('company', {})
        
        output += f"📊 完整公司信息\n"
        for key, value in company_data.items():
            if value is not None and value != "":
                # 时间戳转换为日期
                if key in ['established_date', 'listed_date'] and isinstance(value, (int, float)):
                    if value > 1e10:  # 毫秒时间戳
                        value = value / 1000
                    try:
                        formatted_date = datetime.fromtimestamp(value).strftime('%Y-%m-%d')
                        output += f"{key}: {formatted_date} (时间戳: {value})\n"
                    except:
                        output += f"{key}: {value}\n"
                else:
                    output += f"{key}: {value}\n"
        
        # 附加信息提示
        if result['filepath']:
            output += f"\n💾 完整数据已保存到: {result['filepath']}"
        
        return output
        
    except Exception as e:
        return f"[错误] 获取公司概况失败: {str(e)}"

@register_tool(
    name="detect_stock_market",
    description="智能识别股票代码所属的市场类型。支持识别美股（如TSLA、AAPL）、港股（如00700、02318）、A股（如688111、000001、SH600000、SZ000002）等不同市场的股票代码格式，返回对应的市场类型标识。",
    schema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码"
            }
        },
        "required": ["symbol"]
    }
)
def detect_stock_market(symbol: str) -> str:
    """自动检测股票代码所属的市场类型"""
    try:
        market_type = _stock_manager._detect_market_type(symbol)
        normalized_symbol = _stock_manager._normalize_symbol(symbol, market_type)
        
        market_names = {
            MarketType.US: "美股 (NASDAQ/NYSE)",
            MarketType.HK: "港股 (HKEX)",
            MarketType.CN: "A股 (沪深交易所)"
        }
        
        output = f"[成功] 股票市场检测完成\n"
        output += f"原始代码: {symbol}\n"
        output += f"标准化代码: {normalized_symbol}\n"
        output += f"市场类型: {market_type.value.upper()}\n"
        output += f"市场名称: {market_names.get(market_type, '未知')}\n"
        
        return output
        
    except Exception as e:
        return f"[错误] 股票市场检测失败: {str(e)}"

@register_tool(
    name="get_multiple_company_overview",
    description="批量获取多个上市公司的概况信息，支持一次性查询多只股票的基本信息。可以混合查询不同市场的股票（美股、港股、A股），自动识别每个股票代码的市场类型，返回汇总的公司概况报告。适用于投资组合分析和多股票对比研究。",
    schema={
        "type": "object",
        "properties": {
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "股票代码列表，如['TSLA', '00700', 'SH688111']"
            },
            "include_details": {
                "type": "boolean",
                "description": "是否包含详细信息，默认True",
                "default": True
            }
        },
        "required": ["symbols"]
    }
)
def get_multiple_company_overview(symbols: List[str], include_details: bool = True) -> str:
    """批量获取多个公司的概况信息"""
    try:
        if not symbols:
            return "[错误] 股票代码列表不能为空"
        
        if len(symbols) > 10:
            return "[错误] 一次最多查询10只股票"
        
        results = []
        for symbol in symbols:
            result = _stock_manager.get_company_overview(symbol.strip())
            results.append((symbol, result))
        
        # 统计结果
        successful = sum(1 for _, r in results if r['success'])
        failed = len(results) - successful
        
        output = f"[批量查询] 公司概况信息获取完成\n"
        output += f"查询股票: {len(symbols)} 只\n"
        output += f"成功: {successful} 只，失败: {failed} 只\n"
        output += f"{'=' * 60}\n\n"
        
        for i, (symbol, result) in enumerate(results, 1):
            output += f"【{i}】{symbol.upper()}\n"
            
            if not result['success']:
                output += f"❌ 获取失败: {result['error']}\n\n"
                continue
            
            # 直接显示原始API返回的所有公司数据
            company_data = result['data']['raw_data'].get('data', {}).get('company', {})
            market_type = result['data']['market_type'].upper()
            output += f"✅ {market_type}市场\n"
            
            # 直接遍历所有键值对
            for key, value in company_data.items():
                if value is not None and value != "":
                    # 时间戳转换为日期
                    if key in ['established_date', 'listed_date'] and isinstance(value, (int, float)):
                        if value > 1e10:  # 毫秒时间戳
                            value = value / 1000
                        try:
                            value = datetime.fromtimestamp(value).strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    output += f"{key}: {value}\n"
            
            output += f"\n"
        
        return output
        
    except Exception as e:
        return f"[错误] 批量获取公司概况失败: {str(e)}"

@register_tool(
    name="get_financial_indicators",
    description="获取上市公司的核心财务指标数据，包括盈利能力指标（ROE、ROA、净利润率等）、成长性指标（营收增长率、净利润增长率等）、偿债能力指标（资产负债率、流动比率等）、营运能力指标（总资产周转率、存货周转率等）。支持多期数据对比分析，用于财务健康状况评估和投资决策。",
    schema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，支持美股(如TSLA)、港股(如00700)、A股(如SH688111或688111)"
            },
            "market_type": {
                "type": "string",
                "description": "市场类型，可选值: us(美股), hk(港股), cn(A股)。不指定则自动检测",
                "enum": ["us", "hk", "cn"]
            },
            "count": {
                "type": "integer",
                "description": "返回的报告期数量，默认5期",
                "default": 5,
                "minimum": 1,
                "maximum": 20
            },
            "save_data": {
                "type": "boolean",
                "description": "是否保存原始数据到本地文件，默认False",
                "default": False
            }
        },
        "required": ["symbol"]
    }
)
def get_financial_indicators(symbol: str, market_type: Optional[str] = None, 
                           count: int = 5, save_data: bool = False) -> str:
    """获取公司财务指标数据"""
    try:
        result = _stock_manager.get_financial_indicators(symbol, market_type, count, save_data)
        
        if not result['success']:
            return f"[错误] {result['error']}"
        
        data = result['data']
        raw_data = data['raw_data']
        
        # 构建输出信息
        output = f"[成功] 财务指标数据获取完成\n"
        output += f"股票代码: {data['normalized_symbol']} ({data['market_type'].upper()})\n"
        output += f"API地址: {data['api_url']}\n"
        
        if result['filepath']:
            output += f"数据文件: {result['filepath']}\n"
        
        # 基本信息
        finance_data = raw_data.get('data', {})
        quote_name = finance_data.get('quote_name', '未知')
        currency_name = finance_data.get('currency_name', '未知')
        last_report_name = finance_data.get('last_report_name', '未知')
        
        output += f"公司名称: {quote_name}\n"
        output += f"货币单位: {currency_name}\n"
        output += f"最新报告期: {last_report_name}\n"
        output += f"{'=' * 80}\n\n"
        
        # 财务指标列表
        indicator_list = finance_data.get('list', [])
        
        if not indicator_list:
            output += "📊 无财务指标数据\n"
            return output
        
        # 显示每个报告期的所有指标
        for i, period_data in enumerate(indicator_list, 1):
            report_date = period_data.get('report_date')
            report_name = period_data.get('report_name', '未知')
            ctime = period_data.get('ctime')
            
            # 转换时间戳
            if report_date:
                try:
                    if report_date > 1e10:
                        report_date = report_date / 1000
                    formatted_date = datetime.fromtimestamp(report_date).strftime('%Y-%m-%d')
                except:
                    formatted_date = str(report_date)
            else:
                formatted_date = "未知"
            
            if ctime:
                try:
                    if ctime > 1e10:
                        ctime = ctime / 1000
                    formatted_ctime = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_ctime = str(ctime)
            else:
                formatted_ctime = "未知"
            
            output += f"📊 【{i}】{report_name} ({formatted_date})\n"
            output += f"发布时间: {formatted_ctime}\n"
            output += f"{'-' * 60}\n"
            
            # 显示所有指标
            for key, value in period_data.items():
                if key not in ['report_date', 'report_name', 'ctime']:
                    # 处理数组类型的值（通常是 [当前值, 同比变化率]）
                    if isinstance(value, list) and len(value) >= 2:
                        current_value = value[0]
                        change_rate = value[1]
                        
                        # 格式化变化率为百分比
                        if isinstance(change_rate, (int, float)):
                            if abs(change_rate) < 1:  # 小数形式的变化率
                                change_rate_str = f"{change_rate * 100:.2f}%"
                            else:  # 已经是百分比形式
                                change_rate_str = f"{change_rate:.2f}%"
                        else:
                            change_rate_str = str(change_rate)
                        
                        output += f"{key}: {current_value} (同比: {change_rate_str})\n"
                    else:
                        output += f"{key}: {value}\n"
            
            output += f"\n"
        
        # 附加信息提示
        if result['filepath']:
            output += f"💾 完整数据已保存到: {result['filepath']}"
        
        return output
        
    except Exception as e:
        return f"[错误] 获取财务指标失败: {str(e)}"

@register_tool(
    name="get_income_statement",
    description="获取上市公司的利润表（损益表）详细数据，包括营业收入、营业成本、毛利润、营业利润、利润总额、净利润、每股收益等核心损益项目。支持多个报告期的历史数据查询，用于分析公司盈利能力变化趋势和经营业绩表现。",
    schema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，支持美股(如TSLA)、港股(如00700)、A股(如SH688111或688111)"
            },
            "market_type": {
                "type": "string",
                "description": "市场类型，可选值: us(美股), hk(港股), cn(A股)。不指定则自动检测",
                "enum": ["us", "hk", "cn"]
            },
            "count": {
                "type": "integer",
                "description": "返回的报告期数量，默认5期",
                "default": 5,
                "minimum": 1,
                "maximum": 20
            },
            "save_data": {
                "type": "boolean",
                "description": "是否保存原始数据到本地文件，默认False",
                "default": False
            }
        },
        "required": ["symbol"]
    }
)
def get_income_statement(symbol: str, market_type: Optional[str] = None, 
                        count: int = 5, save_data: bool = False) -> str:
    """获取公司利润表数据"""
    try:
        result = _stock_manager.get_income_statement(symbol, market_type, count, save_data)
        
        if not result['success']:
            return f"[错误] {result['error']}"
        
        data = result['data']
        raw_data = data['raw_data']
        
        # 构建输出信息
        output = f"[成功] 利润表数据获取完成\n"
        output += f"股票代码: {data['normalized_symbol']} ({data['market_type'].upper()})\n"
        output += f"API地址: {data['api_url']}\n"
        
        if result['filepath']:
            output += f"数据文件: {result['filepath']}\n"
        
        # 基本信息
        finance_data = raw_data.get('data', {})
        quote_name = finance_data.get('quote_name', '未知')
        currency_name = finance_data.get('currency_name', '未知')
        last_report_name = finance_data.get('last_report_name', '未知')
        
        output += f"公司名称: {quote_name}\n"
        output += f"货币单位: {currency_name}\n"
        output += f"最新报告期: {last_report_name}\n"
        output += f"{'=' * 80}\n\n"
        
        # 利润表列表
        income_list = finance_data.get('list', [])
        
        if not income_list:
            output += "📊 无利润表数据\n"
            return output
        
        # 显示每个报告期的所有利润表项目
        for i, period_data in enumerate(income_list, 1):
            report_date = period_data.get('report_date')
            report_name = period_data.get('report_name', '未知')
            ctime = period_data.get('ctime')
            
            # 转换时间戳
            if report_date:
                try:
                    if report_date > 1e10:
                        report_date = report_date / 1000
                    formatted_date = datetime.fromtimestamp(report_date).strftime('%Y-%m-%d')
                except:
                    formatted_date = str(report_date)
            else:
                formatted_date = "未知"
            
            if ctime:
                try:
                    if ctime > 1e10:
                        ctime = ctime / 1000
                    formatted_ctime = datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_ctime = str(ctime)
            else:
                formatted_ctime = "未知"
            
            output += f"📊 【{i}】{report_name} ({formatted_date})\n"
            output += f"发布时间: {formatted_ctime}\n"
            output += f"{'-' * 60}\n"
            
            # 显示所有利润表项目
            for key, value in period_data.items():
                if key not in ['report_date', 'report_name', 'ctime']:
                    # 处理数组类型的值（通常是 [当前值, 同比变化率]）
                    if isinstance(value, list) and len(value) >= 2:
                        current_value = value[0]
                        change_rate = value[1]
                        
                        # 格式化金额（如果是大数字）
                        if isinstance(current_value, (int, float)) and abs(current_value) > 1000000:
                            if abs(current_value) > 1e8:
                                current_value_str = f"{current_value/1e8:.2f}亿"
                            elif abs(current_value) > 1e4:
                                current_value_str = f"{current_value/1e4:.2f}万"
                            else:
                                current_value_str = str(current_value)
                        else:
                            current_value_str = str(current_value)
                        
                        # 格式化变化率为百分比
                        if isinstance(change_rate, (int, float)):
                            if abs(change_rate) < 1:  # 小数形式的变化率
                                change_rate_str = f"{change_rate * 100:.2f}%"
                            else:  # 已经是百分比形式
                                change_rate_str = f"{change_rate:.2f}%"
                        else:
                            change_rate_str = str(change_rate)
                        
                        output += f"{key}: {current_value_str} (同比: {change_rate_str})\n"
                    else:
                        # 单个值，也尝试格式化金额
                        if isinstance(value, (int, float)) and abs(value) > 1000000:
                            if abs(value) > 1e8:
                                value_str = f"{value/1e8:.2f}亿"
                            elif abs(value) > 1e4:
                                value_str = f"{value/1e4:.2f}万"
                            else:
                                value_str = str(value)
                        else:
                            value_str = str(value)
                        
                        output += f"{key}: {value_str}\n"
            
            output += f"\n"
        
        # 附加信息提示
        if result['filepath']:
            output += f"💾 完整数据已保存到: {result['filepath']}"
        
        return output
        
    except Exception as e:
        return f"[错误] 获取利润表失败: {str(e)}"

@register_tool(
    name="list_supported_markets",
    description="列出当前工具支持的所有股票市场类型及其详细说明，包括市场代码、市场名称、支持的股票代码格式示例等信息。帮助用户了解可以查询哪些市场的股票数据。",
    schema={
        "type": "object",
        "properties": {}
    }
)
def list_supported_markets() -> str:
    """列出支持的股票市场类型"""
    try:
        output = f"[成功] 支持的股票市场类型\n"
        output += f"{'=' * 40}\n\n"
        
        markets = [
            {
                "code": "us",
                "name": "美股",
                "description": "美国纳斯达克、纽约证券交易所",
                "example": "TSLA, AAPL, MSFT"
            },
            {
                "code": "hk", 
                "name": "港股",
                "description": "香港交易所",
                "example": "00700, 00941, 09988"
            },
            {
                "code": "cn",
                "name": "A股",
                "description": "上海、深圳证券交易所",
                "example": "SH600036, SZ000001, 688111"
            }
        ]
        
        for market in markets:
            output += f"🏢 {market['name']} ({market['code'].upper()})\n"
            output += f"   交易所: {market['description']}\n"
            output += f"   代码示例: {market['example']}\n\n"
        
        output += f"💡 使用说明:\n"
        output += f"- 大部分情况下可以自动检测市场类型，无需手动指定\n"
        output += f"- A股支持带前缀(SH/SZ)和不带前缀的格式\n"
        output += f"- 港股代码通常为5位数字，以0开头\n"
        output += f"- 美股代码为字母组合，如TSLA、AAPL等\n"
        
        return output
        
    except Exception as e:
        return f"[错误] 获取市场列表失败: {str(e)}"

@register_tool(
    name="get_balance_sheet",
    description="获取上市公司的资产负债表详细数据，包括总资产、流动资产、非流动资产、总负债、流动负债、非流动负债、股东权益等核心财务状况指标。支持多个报告期的历史数据查询，用于分析公司资产结构、负债水平和财务稳定性。",
    schema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，如 TSLA、688111、00700"
            },
            "count": {
                "type": "integer",
                "description": "获取期数，默认5期",
                "default": 5
            },
            "save_to_file": {
                "type": "boolean",
                "description": "是否保存到文件",
                "default": False
            },
            "file_path": {
                "type": "string",
                "description": "保存文件路径（需要save_to_file=True）"
            }
        },
        "required": ["symbol"]
    }
)
def get_balance_sheet(symbol: str, count: int = 5, save_to_file: bool = False, file_path: Optional[str] = None) -> str:
    """获取公司资产负债表数据"""
    try:
        # 检测市场类型并标准化代码
        market_type = _stock_manager._detect_market_type(symbol)
        normalized_symbol = _stock_manager._normalize_symbol(symbol, market_type)
        
        market_map = {
            MarketType.US: "us",
            MarketType.HK: "hk", 
            MarketType.CN: "cn"
        }
        market = market_map[market_type]
        
        # 构造API URL
        timestamp = int(time.time() * 1000)
        url = f"https://stock.xueqiu.com/v5/stock/finance/{market}/balance.json"
        
        params = {
            'symbol': normalized_symbol,
            'type': 'all',
            'is_detail': 'true',
            'count': str(count),
            'timestamp': str(timestamp)
        }
        
        # 设置请求头
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,ko;q=0.8,en-US;q=0.7,en;q=0.6',
            'cache-control': 'no-cache',
            'origin': 'https://xueqiu.com',
            'referer': f'https://xueqiu.com/snowman/S/{normalized_symbol}/detail',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'cookie': 's=be12bcx3pb; cookiesu=971748192631827; device_id=afda57cfe6697001d99fa8895d7a8922; u=971748192631827; Hm_lvt_1db88642e346389874251b5a1eded6e3=1748192633,1749565221; HMACCOUNT=73EFE7072B2EF8EE; xq_a_token=b7259d09435458cc3f1a963479abb270a1a016ce; xqat=b7259d09435458cc3f1a963479abb270a1a016ce; xq_r_token=28108bfa1d92ac8a46bbb57722633746218621a3; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTc1MjU0MTk4OCwiY3RtIjoxNzQ5OTk0MzEyODE0LCJjaWQiOiJkOWQwbjRBWnVwIn0.jNWjZYg_wpiX1GgMAlx7hE9ZE8pTjQg6V5NgsM7O2vSbzM_yE4np01eywM_aKem3L0sh3bMqgbpZT8IG0L61oJ7yEV84aO6wajvfSgP8NOtkNJxDk6ljYG57-fgau9Ig1Vpi49_Md-fM4BXQeza0sgHXnBLnvv7LyVks5Z1puo4mr_pGIyKYr_o5MtWRFGNZBRpDtTQ0SgYn8pQWJ9ceu9EojXvYeelq4hny4Gocgj6yvnaInlyimJA3own6mb5d0a067ypFnZ9YP3UG_jcBndeXn5OX1wNmeBcHgGTwH_vN33bo6vjb1Nqhu7v2Hb4WpLrjyK8POAFUjivQ7THdkA; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1749994377; ssxmod_itna=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45aY5D/zG7eDZDG9dDqx0ErXQA7Tthe9G7gqpPfl0Y4hkW80GSYaYQI=RxYifUzSc65c7eGImDG2DYoDCqDS0DD9R2GrDYYfDBYD74G+DDeDixbDGuuP2DDFRWbdclNQiW+PueDE000a0DDgjPD1QPWrulNqla4D0LWDfR0WleqxxY=DQwOQFoTDjR9W7KGyQeGWi8RjuKGuSZixphuNqPqU=RDSzCLxW7eM+BxPfA6hznGxngxNAD4EsPYs3AxYA4qY5=nQkxDic5Kb2rBqK4U2atq1UriXYAm=e52YI6DKrUxr/Dgpw1nwKAG5mDIA03iiGGDK3X3YD; ssxmod_itna2=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45a7eDAQf7G+C=fQD03qe8G3TPDBMpP4WMYZ5y53fY=RcKkBFEhWq3m+7DHhYA+sYgERHupq29iQ4YMLxWw6Hebfu80DRAbQh+CiujLr2fkrnKe4DpCXx5W5eWj3lSf+Xzeh4wO0HQG2K8Gj5m8rZ7MhW=TQkrYc5K0rk57fPvfhSzTF8yQcKnL4Qwg6EgbUU7Zxipai6Kpi2uZxNLUdu2UiCM8g4T/C=cR18=7m5covxo0sEYGiCmxnrZ0pV/bDNuqzir9GE+bZKGEQRY9GPLAtQDNfGNW0qbD40BPsiKPD'
        }
        
                # 使用web_scraper发送API请求
        if _web_scraper is None:
            return f"[错误] Web抓取工具实例不可用"
        
        # 直接构造完整URL
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"
        
        result = _web_scraper.api_request(
            url=full_url,
            method="GET",
            headers=headers,
            timeout=30
        )
        
        if not result['success']:
            return f"[错误] API请求失败: {result['error']}\nURL: {full_url}"
        
        if not result['is_json']:
            return f"[错误] 响应不是JSON格式\n响应内容: {result.get('content', '')[:500]}"
        
        data = result['json']
        
        # 检查API返回的错误
        if 'error_code' in data and data.get('error_code') != 0:
            return f"[错误] API返回错误: {data.get('error_description', '未知错误')}"
        
        quote_data = data.get('data', {})
        company_name = quote_data.get('quote_name', '未知公司')
        currency = quote_data.get('currency_name', '未知币种')
        balance_list = quote_data.get('list', [])
        
        if not balance_list:
            return f"[错误] 未获取到{symbol}的资产负债表数据"
        
        result = f"📊 {company_name}({symbol}) 资产负债表\n"
        result += f"💱 币种: {currency}\n"
        result += f"📈 期数: {len(balance_list)}\n"
        result += "=" * 60 + "\n\n"
        
        for i, period_data in enumerate(balance_list):
            report_name = period_data.get('report_name', '未知期间')
            report_timestamp = period_data.get('report_date')
            
            result += f"📅 【{report_name}】"
            if report_timestamp:
                report_date = datetime.fromtimestamp(report_timestamp / 1000).strftime('%Y-%m-%d')
                result += f" ({report_date})"
            result += "\n"
            result += "-" * 40 + "\n"
            
            # 显示所有原始数据
            for key, value in period_data.items():
                if key in ['report_date', 'report_name', 'ctime']:
                    continue
                    
                if isinstance(value, list) and len(value) >= 2:
                    amount, change_rate = value[0], value[1]
                    if amount is not None:
                        # 格式化金额
                        if abs(amount) >= 1e8:
                            formatted_amount = f"{amount/1e8:.2f}亿"
                        elif abs(amount) >= 1e4:
                            formatted_amount = f"{amount/1e4:.2f}万"
                        else:
                            formatted_amount = f"{amount:.2f}"
                        
                        # 格式化变化率
                        if change_rate is not None:
                            change_str = f" (同比{'+' if change_rate > 0 else ''}{change_rate*100:.2f}%)"
                        else:
                            change_str = ""
                        
                        result += f"  {key}: {formatted_amount}{change_str}\n"
                    else:
                        result += f"  {key}: 无数据\n"
                else:
                    if value is not None:
                        result += f"  {key}: {value}\n"
                    else:
                        result += f"  {key}: 无数据\n"
            
            result += "\n"
        
        # 保存到文件
        if save_to_file:
            if not file_path:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"{symbol}_balance_sheet_{timestamp_str}.txt"
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                result += f"\n💾 数据已保存至: {file_path}"
            except Exception as e:
                result += f"\n❌ 保存文件失败: {str(e)}"
        
        return result
        
    except Exception as e:
        return f"[错误] 获取资产负债表失败: {str(e)}"

@register_tool(
    name="get_multiple_balance_sheet", 
    description="批量获取多个上市公司的资产负债表数据，支持一次性查询多只股票的财务状况。可以混合查询不同市场的股票，自动识别市场类型，返回汇总的资产负债表分析报告。适用于投资组合的财务健康状况对比分析和风险评估。",
    schema={
        "type": "object",
        "properties": {
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "股票代码列表，如['TSLA', '00700', 'SH688111']"
            },
            "count": {
                "type": "integer", 
                "description": "每只股票获取的期数，默认3期",
                "default": 3
            },
            "include_details": {
                "type": "boolean",
                "description": "是否包含详细数据，默认False（仅显示关键指标）",
                "default": False
            }
        },
        "required": ["symbols"]
    }
)
def get_multiple_balance_sheet(symbols: List[str], count: int = 3, include_details: bool = False) -> str:
    """批量获取多个公司的资产负债表数据"""
    try:
        if not symbols:
            return "[错误] 请提供至少一个股票代码"
        
        results = []
        success_count = 0
        
        for symbol in symbols:
            try:
                # 检测市场类型并标准化代码
                market_type = _stock_manager._detect_market_type(symbol)
                normalized_symbol = _stock_manager._normalize_symbol(symbol, market_type)
                
                market_map = {
                    MarketType.US: "us",
                    MarketType.HK: "hk",
                    MarketType.CN: "cn"
                }
                market = market_map[market_type]
                
                # 构造API URL
                timestamp = int(time.time() * 1000)
                url = f"https://stock.xueqiu.com/v5/stock/finance/{market}/balance.json"
                
                params = {
                    'symbol': normalized_symbol,
                    'type': 'all',
                    'is_detail': 'true',
                    'count': str(count),
                    'timestamp': str(timestamp)
                }
                
                # 设置请求头
                headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'zh-CN,zh;q=0.9,ko;q=0.8,en-US;q=0.7,en;q=0.6',
                    'cache-control': 'no-cache',
                    'origin': 'https://xueqiu.com',
                    'referer': f'https://xueqiu.com/snowman/S/{normalized_symbol}/detail',
                    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
                    'cookie': 's=be12bcx3pb; cookiesu=971748192631827; device_id=afda57cfe6697001d99fa8895d7a8922; u=971748192631827; Hm_lvt_1db88642e346389874251b5a1eded6e3=1748192633,1749565221; HMACCOUNT=73EFE7072B2EF8EE; xq_a_token=b7259d09435458cc3f1a963479abb270a1a016ce; xqat=b7259d09435458cc3f1a963479abb270a1a016ce; xq_r_token=28108bfa1d92ac8a46bbb57722633746218621a3; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTc1MjU0MTk4OCwiY3RtIjoxNzQ5OTk0MzEyODE0LCJjaWQiOiJkOWQwbjRBWnVwIn0.jNWjZYg_wpiX1GgMAlx7hE9ZE8pTjQg6V5NgsM7O2vSbzM_yE4np01eywM_aKem3L0sh3bMqgbpZT8IG0L61oJ7yEV84aO6wajvfSgP8NOtkNJxDk6ljYG57-fgau9Ig1Vpi49_Md-fM4BXQeza0sgHXnBLnvv7LyVks5Z1puo4mr_pGIyKYr_o5MtWRFGNZBRpDtTQ0SgYn8pQWJ9ceu9EojXvYeelq4hny4Gocgj6yvnaInlyimJA3own6mb5d0a067ypFnZ9YP3UG_jcBndeXn5OX1wNmeBcHgGTwH_vN33bo6vjb1Nqhu7v2Hb4WpLrjyK8POAFUjivQ7THdkA; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1749994377; ssxmod_itna=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45aY5D/zG7eDZDG9dDqx0ErXQA7Tthe9G7gqpPfl0Y4hkW80GSYaYQI=RxYifUzSc65c7eGImDG2DYoDCqDS0DD9R2GrDYYfDBYD74G+DDeDixbDGuuP2DDFRWbdclNQiW+PueDE000a0DDgjPD1QPWrulNqla4D0LWDfR0WleqxxY=DQwOQFoTDjR9W7KGyQeGWi8RjuKGuSZixphuNqPqU=RDSzCLxW7eM+BxPfA6hznGxngxNAD4EsPYs3AxYA4qY5=nQkxDic5Kb2rBqK4U2atq1UriXYAm=e52YI6DKrUxr/Dgpw1nwKAG5mDIA03iiGGDK3X3YD; ssxmod_itna2=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45a7eDAQf7G+C=fQD03qe8G3TPDBMpP4WMYZ5y53fY=RcKkBFEhWq3m+7DHhYA+sYgERHupq29iQ4YMLxWw6Hebfu80DRAbQh+CiujLr2fkrnKe4DpCXx5W5eWj3lSf+Xzeh4wO0HQG2K8Gj5m8rZ7MhW=TQkrYc5K0rk57fPvfhSzTF8yQcKnL4Qwg6EgbUU7Zxipai6Kpi2uZxNLUdu2UiCM8g4T/C=cR18=7m5covxo0sEYGiCmxnrZ0pV/bDNuqzir9GE+bZKGEQRY9GPLAtQDNfGNW0qbD40BPsiKPD'
                }
                
                # 使用web_scraper发送API请求
                if _web_scraper is None:
                    results.append(f"❌ {symbol}: Web抓取工具实例不可用")
                    continue
                
                result = _web_scraper.api_request(
                    url=url,
                    method="GET",
                    headers=headers,
                    data=params,
                    timeout=30
                )
                
                if not result['success']:
                    results.append(f"❌ {symbol}: API请求失败 - {result['error']}")
                    continue
                
                if not result['is_json']:
                    results.append(f"❌ {symbol}: 响应不是JSON格式")
                    continue
                
                data = result['json']
                
                if data.get('error_code') != 0:
                    results.append(f"❌ {symbol}: {data.get('error_description', '未知错误')}")
                    continue
                
                quote_data = data.get('data', {})
                company_name = quote_data.get('quote_name', '未知公司')
                currency = quote_data.get('currency_name', '未知币种')
                balance_list = quote_data.get('list', [])
                
                if not balance_list:
                    results.append(f"❌ {symbol}: 未获取到资产负债表数据")
                    continue
                
                # 处理资产负债表数据
                company_result = f"📊 {company_name}({symbol}) - {currency}\n"
                company_result += "-" * 50 + "\n"
                
                # 只获取最新期的数据
                period_data = balance_list[0]
                report_name = period_data.get('report_name', '未知期间')
                report_timestamp = period_data.get('report_date')
                
                period_title = f"📅 {report_name}"
                if report_timestamp:
                    report_date = datetime.fromtimestamp(report_timestamp / 1000).strftime('%Y-%m-%d')
                    period_title += f" ({report_date})"
                
                company_result += f"{period_title}\n"
                
                # 显示所有原始数据
                for key, value in period_data.items():
                    if key in ['report_date', 'report_name', 'ctime']:
                        continue
                        
                    if isinstance(value, list) and len(value) >= 2:
                        amount, change_rate = value[0], value[1]
                        if amount is not None:
                            # 格式化金额
                            if abs(amount) >= 1e8:
                                formatted_amount = f"{amount/1e8:.2f}亿"
                            elif abs(amount) >= 1e4:
                                formatted_amount = f"{amount/1e4:.2f}万"
                            else:
                                formatted_amount = f"{amount:.2f}"
                            
                            # 格式化变化率
                            if change_rate is not None:
                                change_str = f" (同比{'+' if change_rate > 0 else ''}{change_rate*100:.2f}%)"
                            else:
                                change_str = ""
                            
                            company_result += f"  {key}: {formatted_amount}{change_str}\n"
                        else:
                            company_result += f"  {key}: 无数据\n"
                    else:
                        if value is not None:
                            company_result += f"  {key}: {value}\n"
                        else:
                            company_result += f"  {key}: 无数据\n"
                
                results.append(company_result)
                success_count += 1
                
                # 添加延迟避免请求过快
                time.sleep(0.5)
                
            except Exception as e:
                results.append(f"❌ {symbol}: 处理失败 - {str(e)}")
        
        # 生成汇总结果
        output = f"📈 批量资产负债表查询结果\n"
        output += f"{'=' * 60}\n"
        output += f"总计: {len(symbols)}只股票, 成功: {success_count}只, 失败: {len(symbols) - success_count}只\n\n"
        
        for result in results:
            output += result + "\n"
        
        return output
        
    except Exception as e:
        return f"[错误] 批量获取资产负债表失败: {str(e)}"

@register_tool(
    name="get_stock_price_and_technical_analysis",
    description="获取股票的实时股价信息和全面的技术指标分析。包括当前股价、涨跌幅、成交量等基础数据，以及移动平均线系统（MA5/10/20/60）、MACD指标、KDJ随机指标、布林带（BOLL）、SAR抛物线指标等多种技术分析工具。提供专业的技术分析摘要和投资参考建议，支持美股、港股、A股市场。",
    schema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，如 TSLA、688111、00700"
            },
            "days": {
                "type": "integer",
                "description": "获取多少天的K线数据，默认365天",
                "default": 365,
                "minimum": 30,
                "maximum": 1000
            }
        },
        "required": ["symbol"]
    }
)
def get_technical_analysis(symbol: str, days: int = 365) -> str:
    """获取股票技术分析数据"""
    try:
        # 检测市场类型并标准化代码
        market_type = _stock_manager._detect_market_type(symbol)
        normalized_symbol = _stock_manager._normalize_symbol(symbol, market_type)
        
        # 获取开始时间戳（120天前）
        import time as time_module
        current_timestamp = int(time_module.time() * 1000)  # 毫秒时间戳
        
        # 构造API URL
        url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
        
        params = {
            'symbol': normalized_symbol,
            'begin': str(current_timestamp),
            'period': 'day',
            'type': 'before',
            'count': f'-{days}',
            'indicator': 'kline,pe,pb,ps,pcf,market_capital,agt,ggt,balance'
        }
        
        # 设置请求头（根据您的curl测试）
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,ko;q=0.8,en-US;q=0.7,en;q=0.6',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Cookie': 's=be12bcx3pb; cookiesu=971748192631827; device_id=afda57cfe6697001d99fa8895d7a8922; u=971748192631827; Hm_lvt_1db88642e346389874251b5a1eded6e3=1748192633,1749565221; HMACCOUNT=73EFE7072B2EF8EE; xq_a_token=b7259d09435458cc3f1a963479abb270a1a016ce; xqat=b7259d09435458cc3f1a963479abb270a1a016ce; xq_r_token=28108bfa1d92ac8a46bbb57722633746218621a3; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTc1MjU0MTk4OCwiY3RtIjoxNzQ5OTk0MzEyODE0LCJjaWQiOiJkOWQwbjRBWnVwIn0.jNWjZYg_wpiX1GgMAlx7hE9ZE8pTjQg6V5NgsM7O2vSbzM_yE4np01eywM_aKem3L0sh3bMqgbpZT8IG0L61oJ7yEV84aO6wajvfSgP8NOtkNJxDk6ljYG57-fgau9Ig1Vpi49_Md-fM4BXQeza0sgHXnBLnvv7LyVks5Z1puo4mr_pGIyKYr_o5MtWRFGNZBRpDtTQ0SgYn8pQWJ9ceu9EojXvYeelq4hny4Gocgj6yvnaInlyimJA3own6mb5d0a067ypFnZ9YP3UG_jcBndeXn5OX1wNmeBcHgGTwH_vN33bo6vjb1Nqhu7v2Hb4WpLrjyK8POAFUjivQ7THdkA; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1749994377; ssxmod_itna=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45aY5D/zG7eDZDG9dDqx0ErXQA7Tthe9G7gqpPfl0Y4hkW80GSYaYQI=RxYifUzSc65c7eGImDG2DYoDCqDS0DD9R2GrDYYfDBYD74G+DDeDixbDGuuP2DDFRWbdclNQiW+PueDE000a0DDgjPD1QPWrulNqla4D0LWDfR0WleqxxY=DQwOQFoTDjR9W7KGyQeGWi8RjuKGuSZixphuNqPqU=RDSzCLxW7eM+BxPfA6hznGxngxNAD4EsPYs3AxYA4qY5=nQkxDic5Kb2rBqK4U2atq1UriXYAm=e52YI6DKrUxr/Dgpw1nwKAG5mDIA03iiGGDK3X3YD; ssxmod_itna2=YqUxnDcDBC0QiQ=i7NitYiOqDQK4ijKQDXDUqMq7tDRDFqApxDH8mrF5stfB=8YKnDG=45a7eDAQf7G+C=fQD03qe8G3TPDBMpP4WMYZ5y53fY=RcKkBFEhWq3m+7DHhYA+sYgERHupq29iQ4YMLxWw6Hebfu80DRAbQh+CiujLr2fkrnKe4DpCXx5W5eWj3lSf+Xzeh4wO0HQG2K8Gj5m8rZ7MhW=TQkrYc5K0rk57fPvfhSzTF8yQcKnL4Qwg6EgbUU7Zxipai6Kpi2uZxNLUdu2UiCM8g4T/C=cR18=7m5covxo0sEYGiCmxnrZ0pV/bDNuqzir9GE+bZKGEQRY9GPLAtQDNfGNW0qbD40BPsiKPD'
        }
        
        # 使用web_scraper发送API请求
        if _web_scraper is None:
            return f"[错误] Web抓取工具实例不可用"
        
        result = _web_scraper.api_request(
            url=url,
            method="GET",
            headers=headers,
            data=params,
            timeout=30
        )
        
        if not result['success']:
            return f"[错误] API请求失败: {result['error']}"
        
        if not result['is_json']:
            return f"[错误] 响应不是JSON格式"
        
        data = result['json']
        
        if data.get('error_code') != 0:
            return f"[错误] API返回错误: {data.get('error_description', '未知错误')}"
        
        # 解析K线数据
        chart_data = data.get('data', {})
        symbol_name = chart_data.get('symbol', symbol)
        columns = chart_data.get('column', [])
        items = chart_data.get('item', [])
        
        if not items:
            return f"[错误] 未获取到{symbol}的K线数据\n数据结构: {list(data.keys())}\nchart_data: {chart_data}"
        
        # 解析数据列
        timestamp_idx = columns.index('timestamp')
        volume_idx = columns.index('volume')
        open_idx = columns.index('open')
        high_idx = columns.index('high')
        low_idx = columns.index('low')
        close_idx = columns.index('close')
        
        # 提取价格数据
        prices = []
        for item in items:
            if len(item) > max(timestamp_idx, volume_idx, open_idx, high_idx, low_idx, close_idx):
                prices.append({
                    'timestamp': item[timestamp_idx],
                    'open': item[open_idx],
                    'high': item[high_idx], 
                    'low': item[low_idx],
                    'close': item[close_idx],
                    'volume': item[volume_idx]
                })
        
        if len(prices) < 26:  # MACD需要至少26个数据点
            return f"[错误] 数据不足，无法计算技术指标（需要至少26个数据点，当前{len(prices)}个）"
        
        # 计算技术指标
        analysis = _calculate_technical_indicators(prices, symbol_name)
        
        return analysis
        
    except Exception as e:
        return f"[错误] 获取技术分析失败: {str(e)}"


def _calculate_technical_indicators(prices: list, symbol_name: str) -> str:
    """计算技术指标并返回分析摘要"""
    try:
        # 最新数据
        latest = prices[-1]
        previous = prices[-2] if len(prices) > 1 else latest
        
        # 基本价格信息
        current_price = latest['close']
        prev_close = previous['close']
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        
        # 最高最低价分析
        recent_7_days = prices[-7:] if len(prices) >= 7 else prices
        recent_30_days = prices[-30:] if len(prices) >= 30 else prices
        
        high_7d = max([p['high'] for p in recent_7_days])
        low_7d = min([p['low'] for p in recent_7_days])
        high_30d = max([p['high'] for p in recent_30_days])
        low_30d = min([p['low'] for p in recent_30_days])
        
        # 计算移动平均线
        ma5 = _calculate_ma([p['close'] for p in prices], 5)
        ma10 = _calculate_ma([p['close'] for p in prices], 10)
        ma20 = _calculate_ma([p['close'] for p in prices], 20)
        ma60 = _calculate_ma([p['close'] for p in prices], 60)
        
        # 计算SMA（简单移动平均线）
        sma5 = _calculate_sma([p['close'] for p in prices], 5)
        sma20 = _calculate_sma([p['close'] for p in prices], 20)
        
        # 计算MACD
        macd_data = _calculate_macd([p['close'] for p in prices])
        
        # 计算KDJ
        kdj_data = _calculate_kdj(prices)
        
        # 计算BOLL
        boll_data = _calculate_boll([p['close'] for p in prices])
        
        # 计算SAR
        sar_data = _calculate_sar(prices)
        
        # 构建技术分析报告
        analysis = f"📈 {symbol_name} 技术分析报告\n"
        analysis += "=" * 60 + "\n\n"
        
        # 股价信息
        analysis += f"📊 股价信息\n"
        analysis += f"当前股价: {current_price:.2f}\n"
        analysis += f"涨跌幅: {change:+.2f} ({change_pct:+.2f}%)\n"
        analysis += f"昨收: {prev_close:.2f}\n"
        analysis += f"昨开: {previous['open']:.2f}\n"
        analysis += f"最高: {latest['high']:.2f}\n"
        analysis += f"最低: {latest['low']:.2f}\n\n"
        
        # 阶段最值
        analysis += "📈 阶段最值\n"
        analysis += f"近7天最高: {high_7d:.2f}\n"
        analysis += f"近7天最低: {low_7d:.2f}\n"
        analysis += f"近30天最高: {high_30d:.2f}\n"
        analysis += f"近30天最低: {low_30d:.2f}\n\n"
        
        # 移动平均线
        analysis += "📈 均线系统\n"
        if ma5 and ma10 and ma20 and ma60:
            ma5_latest = ma5[-1] if ma5 else 0
            ma10_latest = ma10[-1] if ma10 else 0
            ma20_latest = ma20[-1] if ma20 else 0
            ma60_latest = ma60[-1] if ma60 else 0
            analysis += f"MA5: {ma5_latest:.2f}\n"
            analysis += f"MA10: {ma10_latest:.2f}\n"
            analysis += f"MA20: {ma20_latest:.2f}\n"
            analysis += f"MA60: {ma60_latest:.2f}\n"
            
            # 均线排列判断
            if ma5_latest > ma10_latest > ma20_latest > ma60_latest:
                analysis += "均线排列: 完美多头排列 🔴🔴\n"
            elif ma5_latest > ma20_latest:
                analysis += "均线排列: 多头排列 🔴\n"
            else:
                analysis += "均线排列: 空头排列 🔵\n"
        
        # SMA分析
        analysis += "\n📈 SMA简单移动平均\n"
        if sma5 and sma20:
            sma5_latest = sma5[-1] if sma5 else 0
            sma20_latest = sma20[-1] if sma20 else 0
            analysis += f"SMA5: {sma5_latest:.2f}\n"
            analysis += f"SMA20: {sma20_latest:.2f}\n"
            
            if sma5_latest > sma20_latest:
                analysis += "SMA趋势: 上升趋势 📈\n"
            else:
                analysis += "SMA趋势: 下降趋势 📉\n"
        analysis += "\n"
        
        # MACD分析
        analysis += "📈 MACD分析\n"
        if macd_data:
            recent_macd = macd_data[-7:] if len(macd_data) >= 7 else macd_data
            analysis += f"近7天MACD值: {[f'{x:.3f}' for x in [m['macd'] for m in recent_macd]]}\n"
            
            # 金叉银叉判断
            if len(macd_data) >= 2:
                current_macd = macd_data[-1]
                previous_macd = macd_data[-2]
                
                if (current_macd['dif'] > current_macd['dea'] and 
                    previous_macd['dif'] <= previous_macd['dea']):
                    analysis += "MACD状态: 金叉 🟡\n"
                elif (current_macd['dif'] < current_macd['dea'] and 
                      previous_macd['dif'] >= previous_macd['dea']):
                    analysis += "MACD状态: 死叉 ⚫\n"
                else:
                    if current_macd['dif'] > current_macd['dea']:
                        analysis += "MACD状态: 多头趋势\n"
                    else:
                        analysis += "MACD状态: 空头趋势\n"
        analysis += "\n"
        
        # KDJ分析
        analysis += "📈 KDJ分析\n"
        if kdj_data:
            recent_kdj = kdj_data[-7:] if len(kdj_data) >= 7 else kdj_data
            analysis += f"近7天K值: {[f'{x:.1f}' for x in [k['k'] for k in recent_kdj]]}\n"
            analysis += f"近7天D值: {[f'{x:.1f}' for x in [k['d'] for k in recent_kdj]]}\n"
            analysis += f"近7天J值: {[f'{x:.1f}' for x in [k['j'] for k in recent_kdj]]}\n"
            
            # 金叉银叉判断
            if len(kdj_data) >= 2:
                current_kdj = kdj_data[-1]
                previous_kdj = kdj_data[-2]
                
                if (current_kdj['k'] > current_kdj['d'] and 
                    previous_kdj['k'] <= previous_kdj['d']):
                    analysis += "KDJ状态: 金叉 🟡\n"
                elif (current_kdj['k'] < current_kdj['d'] and 
                      previous_kdj['k'] >= previous_kdj['d']):
                    analysis += "KDJ状态: 死叉 ⚫\n"
                else:
                    if current_kdj['k'] > current_kdj['d']:
                        analysis += "KDJ状态: 多头趋势\n"
                    else:
                        analysis += "KDJ状态: 空头趋势\n"
                
                # 超买超卖判断
                if current_kdj['k'] > 80:
                    analysis += "KDJ提示: 超买区域，注意回调风险\n"
                elif current_kdj['k'] < 20:
                    analysis += "KDJ提示: 超卖区域，可能反弹\n"
        analysis += "\n"
        
        # BOLL分析
        analysis += "📈 布林带分析\n"
        if boll_data:
            latest_boll = boll_data[-1]
            analysis += f"上轨: {latest_boll['upper']:.2f}\n"
            analysis += f"中轨: {latest_boll['middle']:.2f}\n"
            analysis += f"下轨: {latest_boll['lower']:.2f}\n"
            
            # 位置分析
            if current_price > latest_boll['upper']:
                analysis += "布林带位置: 上轨之上，可能回调\n"
            elif current_price < latest_boll['lower']:
                analysis += "布林带位置: 下轨之下，可能反弹\n"
            elif current_price > latest_boll['middle']:
                analysis += "布林带位置: 中轨之上，偏强势\n"
            else:
                analysis += "布林带位置: 中轨之下，偏弱势\n"
        analysis += "\n"
        
        # SAR分析
        analysis += "📈 SAR抛物线指标\n"
        if sar_data:
            recent_sar = sar_data[-7:] if len(sar_data) >= 7 else sar_data
            latest_sar = sar_data[-1]
            analysis += f"当前SAR: {latest_sar['sar']:.2f}\n"
            sar_values = [f'{x.get("sar", 0):.2f}' for x in recent_sar]
            analysis += f"近7天SAR: {sar_values}\n"
            
            # SAR信号判断
            if current_price > latest_sar['sar']:
                analysis += "SAR信号: 看涨信号 🟢\n"
            else:
                analysis += "SAR信号: 看跌信号 🔴\n"
            
            # SAR转向判断
            if len(sar_data) >= 2:
                prev_sar = sar_data[-2]
                if (current_price > latest_sar['sar'] and 
                    previous['close'] <= prev_sar['sar']):
                    analysis += "SAR状态: 刚刚转为看涨 ⬆️\n"
                elif (current_price < latest_sar['sar'] and 
                      previous['close'] >= prev_sar['sar']):
                    analysis += "SAR状态: 刚刚转为看跌 ⬇️\n"
        
        analysis += "\n📝 注意：技术指标仅供参考，投资有风险，决策需谨慎！"
        
        return analysis
        
    except Exception as e:
        return f"[错误] 计算技术指标失败: {str(e)}"


def _calculate_ma(prices: list, period: int) -> list:
    """计算移动平均线"""
    if len(prices) < period:
        return []
    
    ma_values = []
    for i in range(period - 1, len(prices)):
        ma = sum(prices[i - period + 1:i + 1]) / period
        ma_values.append(ma)
    
    return ma_values


def _calculate_macd(prices: list, fast=12, slow=26, signal=9) -> list:
    """计算MACD指标"""
    if len(prices) < slow:
        return []
    
    # 计算EMA
    def calculate_ema(data, period):
        k = 2 / (period + 1)
        ema = [data[0]]
        for i in range(1, len(data)):
            ema.append(data[i] * k + ema[-1] * (1 - k))
        return ema
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    # 计算DIF
    dif = []
    for i in range(len(ema_slow)):
        if i < len(ema_fast):
            dif.append(ema_fast[i] - ema_slow[i])
    
    # 计算DEA (DIF的EMA)
    dea = calculate_ema(dif, signal)
    
    # 计算MACD
    macd_data = []
    for i in range(len(dea)):
        if i < len(dif):
            macd_value = (dif[i] - dea[i]) * 2
            macd_data.append({
                'dif': dif[i],
                'dea': dea[i],
                'macd': macd_value
            })
    
    return macd_data


def _calculate_kdj(prices: list, period=9) -> list:
    """计算KDJ指标"""
    if len(prices) < period:
        return []
    
    kdj_data = []
    k_values = []
    d_values = []
    
    for i in range(period - 1, len(prices)):
        # 获取period天内的最高最低价
        period_data = prices[i - period + 1:i + 1]
        highest = max([p['high'] for p in period_data])
        lowest = min([p['low'] for p in period_data])
        
        current_close = prices[i]['close']
        
        # 计算RSV
        if highest != lowest:
            rsv = (current_close - lowest) / (highest - lowest) * 100
        else:
            rsv = 50
        
        # 计算K值 (3日移动平均)
        if not k_values:
            k = rsv
        else:
            k = (2 * k_values[-1] + rsv) / 3
        
        k_values.append(k)
        
        # 计算D值 (K值的3日移动平均)
        if not d_values:
            d = k
        else:
            d = (2 * d_values[-1] + k) / 3
        
        d_values.append(d)
        
        # 计算J值
        j = 3 * k - 2 * d
        
        kdj_data.append({
            'k': k,
            'd': d, 
            'j': j
        })
    
    return kdj_data


def _calculate_boll(prices: list, period=20, std_dev=2) -> list:
    """计算布林带指标"""
    if len(prices) < period:
        return []
    
    boll_data = []
    
    for i in range(period - 1, len(prices)):
        period_prices = prices[i - period + 1:i + 1]
        
        # 计算中轨（移动平均线）
        middle = sum(period_prices) / period
        
        # 计算标准差
        variance = sum([(p - middle) ** 2 for p in period_prices]) / period
        std = variance ** 0.5
        
        # 计算上下轨
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        boll_data.append({
            'upper': upper,
            'middle': middle,
            'lower': lower
        })
    
    return boll_data


def _calculate_sma(prices: list, period: int) -> list:
    """计算简单移动平均线（SMA）"""
    if len(prices) < period:
        return []
    
    sma_values = []
    for i in range(period - 1, len(prices)):
        sma = sum(prices[i - period + 1:i + 1]) / period
        sma_values.append(sma)
    
    return sma_values


def _calculate_sar(prices: list, af_start=0.02, af_increment=0.02, af_max=0.2) -> list:
    """计算SAR抛物线指标"""
    if len(prices) < 2:
        return []
    
    sar_data = []
    
    # 初始化
    trend = 1  # 1为上升趋势，-1为下降趋势
    af = af_start  # 加速因子
    ep = prices[0]['high']  # 极值点
    sar = prices[0]['low']  # SAR值
    
    for i in range(1, len(prices)):
        current = prices[i]
        
        # 计算新的SAR值
        new_sar = sar + af * (ep - sar)
        
        # 上升趋势
        if trend == 1:
            # 检查是否需要转向
            if current['low'] <= new_sar:
                trend = -1
                sar = ep
                ep = current['low']
                af = af_start
            else:
                sar = new_sar
                # 更新极值点
                if current['high'] > ep:
                    ep = current['high']
                    af = min(af + af_increment, af_max)
                
                # SAR不能高于前两日的最低价
                if i >= 2:
                    sar = min(sar, prices[i-1]['low'], prices[i-2]['low'])
        
        # 下降趋势
        else:
            # 检查是否需要转向
            if current['high'] >= new_sar:
                trend = 1
                sar = ep
                ep = current['high']
                af = af_start
            else:
                sar = new_sar
                # 更新极值点
                if current['low'] < ep:
                    ep = current['low']
                    af = min(af + af_increment, af_max)
                
                # SAR不能低于前两日的最高价
                if i >= 2:
                    sar = max(sar, prices[i-1]['high'], prices[i-2]['high'])
        
        sar_data.append({
            'sar': sar,
            'trend': trend,
            'af': af,
            'ep': ep
        })
    
    return sar_data

@register_tool(
    name="get_stock_news",
    description="获取股票相关的最新资讯新闻，支持智能关键词搜索和并发获取完整新闻内容。可以获取新闻标题、发布时间、来源、摘要和完整正文内容。支持中英文股票名称自动转换（如TSLA→特斯拉），提供丰富的市场资讯用于投资决策参考。默认获取10篇新闻，支持1-50篇范围调整。",
    schema={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，如 TSLA、688111、00700"
            },
            "count": {
                "type": "integer",
                "description": "获取新闻数量，默认10条",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            },
            "include_summary": {
                "type": "boolean",
                "description": "是否包含新闻摘要，默认True",
                "default": True
            },
            "fetch_full_content": {
                "type": "boolean",
                "description": "是否并发获取完整新闻内容，默认False",
                "default": False
            },
            "max_content_length": {
                "type": "integer",
                "description": "每篇新闻内容最大长度，默认5000字符",
                "default": 5000,
                "minimum": 200,
                "maximum": 10000
            }
        },
        "required": ["symbol"]
    }
)
def get_stock_news(symbol: str, count: int = 10, include_summary: bool = True, 
                  fetch_full_content: bool = False, max_content_length: int = 5000) -> str:
    """获取股票相关资讯新闻"""
    try:
        # 检测市场类型并标准化代码
        market_type = _stock_manager._detect_market_type(symbol)
        normalized_symbol = _stock_manager._normalize_symbol(symbol, market_type)
        
        # 根据股票代码确定搜索关键词
        if market_type == MarketType.US:
            # 美股使用股票代码
            if symbol.upper() == 'TSLA':
                keyword = '特斯拉'  # 使用中文名称搜索更准确
            else:
                keyword = symbol.upper()
        elif market_type == MarketType.HK:
            # 港股使用公司中文名称
            if symbol in ['00700', '0700']:
                keyword = '腾讯'
            else:
                keyword = symbol
        elif market_type == MarketType.CN:
            # A股使用公司名称
            if symbol in ['688111', 'SH688111']:
                keyword = '金山办公'
            else:
                keyword = symbol
        else:
            keyword = symbol
        
        # 构造东方财富搜索API
        import json
        import urllib.parse
        import time
        import random
        
        # 生成随机的jQuery回调函数名和时间戳
        callback = f"jQuery{random.randint(10000000000000000000, 99999999999999999999)}_{int(time.time() * 1000)}"
        timestamp = int(time.time() * 1000)
        
        # 构造搜索参数
        search_param = {
            "uid": "",
            "keyword": keyword,
            "type": ["cmsArticleWebOld"],
            "client": "web",
            "clientType": "web", 
            "clientVersion": "curr",
            "param": {
                "cmsArticleWebOld": {
                    "searchScope": "default",
                    "sort": "default",
                    "pageIndex": 1,
                    "pageSize": min(count, 20),  # 限制最大20条
                    "preTag": "<em>",
                    "postTag": "</em>"
                }
            }
        }
        
        # URL编码参数
        param_str = urllib.parse.quote(json.dumps(search_param, ensure_ascii=False))
        
        # 构造完整URL
        api_url = f"https://search-api-web.eastmoney.com/search/jsonp?cb={callback}&param={param_str}&_={timestamp}"
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://so.eastmoney.com/',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        # 使用web_scraper发送请求
        if _web_scraper is None:
            return f"[错误] Web抓取工具实例不可用"
        
        result = _web_scraper.api_request(
            url=api_url,
            method="GET",
            headers=headers,
            timeout=60  # 增加超时时间
        )
        
        if not result['success']:
            return f"[错误] 东方财富API请求失败: {result['error']}"
        
        # 调试信息
        print(f"搜索关键词: {keyword}")
        
        # 解析JSONP响应
        news_items = _parse_eastmoney_response(result['content'], callback, count)
        
        if not news_items:
            return f"[提示] 未找到关于'{keyword}'的相关新闻"
        
        # 如果需要获取完整内容，并发获取新闻页面内容
        if fetch_full_content:
            print(f"正在并发获取 {len(news_items)} 篇新闻的完整内容...")
            news_items = _fetch_news_content_concurrent(news_items, max_content_length)
        
        # 构建新闻报告
        analysis = f"📰 {symbol} ({keyword}) 股票资讯\n"
        analysis += "=" * 60 + "\n\n"
        
        for i, item in enumerate(news_items, 1):
            analysis += f"📄 新闻 {i}\n"
            analysis += f"标题: {item['title']}\n"
            analysis += f"发布时间: {item['pub_date']}\n"
            analysis += f"来源: {item.get('source', '东方财富')}\n"
            
            # 显示内容（优先显示完整内容，其次是摘要）
            if fetch_full_content and item.get('full_content'):
                analysis += f"完整内容: {item['full_content']}\n"
            elif include_summary and item.get('content'):
                # 清理HTML标签
                content = _clean_html_tags(item['content'])
                if content:
                    analysis += f"摘要: {content[:200]}{'...' if len(content) > 200 else ''}\n"
            
            if item.get('url'):
                analysis += f"链接: {item['url']}\n"
            
            analysis += "\n" + "-" * 50 + "\n\n"
        
        analysis += f"📊 共获取到 {len(news_items)} 条相关新闻\n"
        if fetch_full_content:
            analysis += "📖 已获取完整新闻内容\n"
        analysis += "📝 注意：新闻内容仅供参考，投资决策请谨慎！"
        
        return analysis
        
    except Exception as e:
        return f"[错误] 获取股票资讯失败: {str(e)}"


def _parse_eastmoney_response(response: str, callback: str, max_count: int) -> list:
    """解析东方财富API响应"""
    try:
        import json
        import re
        
        # 使用正则表达式匹配JSONP格式: jQuery回调函数名(JSON数据);
        jsonp_pattern = r'jQuery\d+_\d+\((.*)\);?$'
        match = re.search(jsonp_pattern, response, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            # 如果正则匹配失败，尝试手动查找
            start_idx = response.find('(')
            end_idx = response.rfind(');')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx + 1:end_idx]
            else:
                return []
        
        # 解析JSON
        data = json.loads(json_str)
        
        # 检查API返回状态
        if data.get('code') != 0:
            return []
        
        # 提取新闻列表
        result_data = data.get('result', {})
        news_list = result_data.get('cmsArticleWebOld', [])
        
        if not news_list:
            return []
        
        # 只提取需要的字段
        news_items = []
        for news in news_list:
            title = news.get('title', '')
            pub_date = news.get('date', '')
            source = news.get('mediaName', '东方财富')
            url = news.get('url', '')
            content = news.get('content', '')
            
            if title:
                news_items.append({
                    'title': title,
                    'pub_date': pub_date,
                    'source': source,
                    'url': url,
                    'content': content
                })
            
            if len(news_items) >= max_count:
                break
        
        return news_items
        
    except Exception as e:
        print(f"解析东方财富API响应失败: {str(e)}")
        return []


def _clean_html_tags(text: str) -> str:
    """清理HTML标签"""
    try:
        import re
        if not text:
            return ""
        
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 移除多余的空白字符
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        # 解码HTML实体
        clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
        
        return clean_text
        
    except Exception:
        return text or ""


def _fetch_news_content_concurrent(news_items: list, max_content_length: int = 5000) -> list:
    """并发获取新闻页面的完整内容"""
    try:
        import concurrent.futures
        from urllib.parse import urlparse
        
        def fetch_single_news_content(index_and_news):
            """获取单个新闻的完整内容，保持索引"""
            index, news_item = index_and_news
            try:
                url = news_item.get('url', '')
                if not url:
                    return index, news_item
                
                # 检查URL是否有效
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    return index, news_item
                
                # 使用web_scraper获取页面内容
                if _web_scraper is None:
                    return index, news_item
                
                result = _web_scraper.fetch_page(url, timeout=10)
                
                if not result['success']:
                    print(f"获取新闻内容失败: {url} - {result.get('error', '未知错误')}")
                    return index, news_item
                
                # 提取主要内容
                full_content = _web_scraper.extract_main_content(result['content'], url)
                
                if full_content:
                    # 清理和截断内容
                    clean_content = _clean_html_tags(full_content)
                    if len(clean_content) > max_content_length:
                        clean_content = clean_content[:max_content_length] + "..."
                    
                    # 创建新的新闻项，包含完整内容
                    updated_news_item = news_item.copy()
                    updated_news_item['full_content'] = clean_content
                    print(f"✓ 成功获取新闻内容: {news_item.get('title', 'Unknown')[:50]}...")
                    return index, updated_news_item
                else:
                    print(f"✗ 无法提取新闻内容: {url}")
                    return index, news_item
                
            except Exception as e:
                print(f"获取新闻内容异常: {news_item.get('url', 'Unknown')} - {str(e)}")
                return index, news_item
        
        # 使用线程池并发获取新闻内容
        max_workers = min(5, len(news_items))  # 最多5个并发线程
        results = [None] * len(news_items)  # 预分配结果数组
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务，包含索引信息
            futures = [
                executor.submit(fetch_single_news_content, (i, news_item))
                for i, news_item in enumerate(news_items)
            ]
            
            # 收集结果并按原始顺序排列
            for future in concurrent.futures.as_completed(futures, timeout=60):
                try:
                    index, updated_news_item = future.result()
                    results[index] = updated_news_item
                except Exception as e:
                    print(f"处理新闻失败: {str(e)}")
                    # 如果失败，保持原始新闻项
                    for i, news_item in enumerate(news_items):
                        if results[i] is None:
                            results[i] = news_item
                            break
        
        # 确保所有位置都有值（防止None）
        final_results = []
        for i, result in enumerate(results):
            if result is not None:
                final_results.append(result)
            else:
                final_results.append(news_items[i])
        
        success_count = sum(1 for item in final_results if item.get('full_content'))
        print(f"并发获取完成，成功获取 {success_count} 篇完整内容")
        return final_results
        
    except Exception as e:
        print(f"并发获取新闻内容失败: {str(e)}")
        return news_items


# ==================== 股票排行榜功能 ====================

@register_tool(
    name="get_stock_ranking",
    description="获取实时股票市场排行榜数据，支持多种排行榜类型和三大主要市场。包括涨幅榜（当日涨幅最大的股票）、跌幅榜（当日跌幅最大的股票）、成交量榜（当日成交量最大的股票）、成交额榜（当日成交金额最大的股票）。覆盖美股、港股、A股三大市场，提供股票代码、名称、当前价格、涨跌幅、涨跌额、成交量、成交额等详细信息，用于市场热点分析和投资机会发现。",
    schema={
        "type": "object",
        "properties": {
            "market": {
                "type": "string",
                "description": "目标市场类型：US=美股市场（纳斯达克、纽交所等），HK=港股市场（香港交易所），CN=A股市场（上交所、深交所、北交所）",
                "enum": ["US", "HK", "CN"],
                "default": "CN"
            },
            "ranking_type": {
                "type": "string", 
                "description": "排行榜类型：rise=涨幅榜（按涨跌幅降序），fall=跌幅榜（按涨跌幅升序），volume=成交量榜（按成交量降序），turnover=成交额榜（按成交金额降序）",
                "enum": ["rise", "fall", "volume", "turnover"],
                "default": "rise"
            },
            "count": {
                "type": "integer",
                "description": "返回的股票数量，范围1-50只，默认20只。数量越多查询时间越长",
                "default": 20,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["market"]
    }
)
def get_stock_ranking(market: str = "CN", ranking_type: str = "rise", count: int = 20) -> str:
    """获取股票排行榜"""
    try:
        import json
        import urllib.parse
        import time
        import random
        
        # 生成随机的jQuery回调函数名和时间戳
        callback = f"jQuery{random.randint(10000000000000000000, 99999999999999999999)}_{int(time.time() * 1000)}"
        timestamp = int(time.time() * 1000)
        
        # 根据市场类型设置参数
        if market == "US":
            # 美股市场
            fs_param = "m:105,m:106,m:107"
            fields = "f12,f13,f14,f1,f2,f4,f3,f152,f17,f28,f15,f16,f18,f20,f115"
            market_name = "美股"
        elif market == "HK":
            # 港股市场
            fs_param = "m:128+t:3"
            fields = "f12,f13,f14,f19,f1,f2,f4,f3,f152,f17,f18,f15,f16,f5,f6"
            market_name = "港股"
        elif market == "CN":
            # A股市场
            fs_param = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
            fields = "f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f23"
            market_name = "A股"
        else:
            return f"[错误] 不支持的市场类型: {market}"
        
        # 根据排行榜类型设置排序字段
        if ranking_type == "rise":
            fid = "f3"  # 按涨跌幅排序
            po = "1"    # 降序
            ranking_name = "涨幅榜"
        elif ranking_type == "fall":
            fid = "f3"  # 按涨跌幅排序
            po = "0"    # 升序
            ranking_name = "跌幅榜"
        elif ranking_type == "volume":
            fid = "f5"  # 按成交量排序
            po = "1"    # 降序
            ranking_name = "成交量榜"
        elif ranking_type == "turnover":
            fid = "f6"  # 按成交额排序
            po = "1"    # 降序
            ranking_name = "成交额榜"
        else:
            return f"[错误] 不支持的排行榜类型: {ranking_type}，仅支持rise、fall、volume、turnover"
        
        # 构造API URL
        base_url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "np": "1",
            "fltt": "1", 
            "invt": "2",
            "cb": callback,
            "fs": fs_param,
            "fields": fields,
            "fid": fid,
            "pn": "1",
            "pz": str(min(count, 50)),
            "po": po,
            "dect": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "wbp2u": "|0|0|0|web",
            "_": str(timestamp)
        }
        
        # 构造完整URL
        api_url = f"{base_url}?" + "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://quote.eastmoney.com/center/gridlist.html',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        # 使用web_scraper发送请求
        if _web_scraper is None:
            return f"[错误] Web抓取工具实例不可用"
        
        result = _web_scraper.api_request(
            url=api_url,
            method="GET",
            headers=headers,
            timeout=60
        )
        
        if not result['success']:
            return f"[错误] 东方财富排行榜API请求失败: {result['error']}"
        
        # 解析JSONP响应
        ranking_data = _parse_ranking_response(result['content'], callback, count)
        
        if not ranking_data:
            return f"[提示] 未获取到{market_name}{ranking_name}数据"
        
        # 构建排行榜报告
        analysis = f"📊 {market_name}{ranking_name}\n"
        analysis += "=" * 60 + "\n\n"
        
        for i, stock in enumerate(ranking_data, 1):
            analysis += f"🏆 第{i}名\n"
            analysis += f"股票代码: {stock['code']}\n"
            analysis += f"股票名称: {stock['name']}\n"
            analysis += f"当前价格: {stock['price']}\n"
            analysis += f"涨跌幅: {stock['change_percent']}\n"
            analysis += f"涨跌额: {stock['change_amount']}\n"
            
            if market == "CN":
                analysis += f"成交量: {stock.get('volume', 'N/A')}\n"
                analysis += f"成交额: {stock.get('turnover', 'N/A')}\n"
            elif market == "US":
                analysis += f"成交量: {stock.get('volume', 'N/A')}\n"
            
            analysis += "\n" + "-" * 50 + "\n\n"
        
        analysis += f"📈 共获取到 {len(ranking_data)} 只股票\n"
        analysis += "📝 注意：排行榜数据仅供参考，投资决策请谨慎！"
        
        return analysis
        
    except Exception as e:
        return f"[错误] 获取股票排行榜失败: {str(e)}"


def _parse_ranking_response(response: str, callback: str, max_count: int) -> list:
    """解析东方财富排行榜API响应"""
    try:
        import json
        import re
        
        # 使用正则表达式匹配JSONP格式
        jsonp_pattern = r'jQuery\d+_\d+\((.*)\);?$'
        match = re.search(jsonp_pattern, response, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            # 如果正则匹配失败，尝试手动查找
            start_idx = response.find('(')
            end_idx = response.rfind(');')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx + 1:end_idx]
            else:
                return []
        
        # 解析JSON
        data = json.loads(json_str)
        
        # 检查API返回状态
        if data.get('rc') != 0:
            return []
        
        # 提取股票列表
        stock_list = data.get('data', {}).get('diff', [])
        
        if not stock_list:
            return []
        
        # 解析股票数据
        ranking_items = []
        for stock in stock_list:
            code = stock.get('f12', '')
            name = stock.get('f14', '')
            price = stock.get('f2', 0)
            change_percent = stock.get('f3', 0)
            change_amount = stock.get('f4', 0)
            volume = stock.get('f5', 0)
            turnover = stock.get('f6', 0)
            
            if code and name:
                # 格式化数据
                price_str = f"{price/100:.2f}" if price else "N/A"
                change_percent_str = f"{change_percent/100:+.2f}%" if change_percent else "N/A"
                change_amount_str = f"{change_amount/100:+.2f}" if change_amount else "N/A"
                
                # 格式化成交量和成交额
                volume_str = _format_volume(volume) if volume else "N/A"
                turnover_str = _format_turnover(turnover) if turnover else "N/A"
                
                ranking_items.append({
                    'code': code,
                    'name': name,
                    'price': price_str,
                    'change_percent': change_percent_str,
                    'change_amount': change_amount_str,
                    'volume': volume_str,
                    'turnover': turnover_str
                })
            
            if len(ranking_items) >= max_count:
                break
        
        return ranking_items
        
    except Exception as e:
        print(f"解析东方财富排行榜API响应失败: {str(e)}")
        return []


def _format_volume(volume):
    """格式化成交量"""
    if volume >= 100000000:  # 亿
        return f"{volume/100000000:.2f}亿手"
    elif volume >= 10000:  # 万
        return f"{volume/10000:.2f}万手"
    else:
        return f"{volume}手"


def _format_turnover(turnover):
    """格式化成交额"""
    if turnover >= 100000000:  # 亿
        return f"{turnover/100000000:.2f}亿元"
    elif turnover >= 10000:  # 万
        return f"{turnover/10000:.2f}万元"
    else:
        return f"{turnover:.2f}元"


if __name__ == "__main__":
    # 测试股票信息工具
    print("=== 股票信息工具测试 ===\n")
    
    # 测试股票代码
    test_symbols = ['TSLA', '688111', '00700']
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"测试股票: {symbol}")
        print(f"{'='*60}")
        
        # 1. 测试技术分析
        print(f"\n📈 获取 {symbol} 技术分析:")
        try:
            tech_analysis = get_technical_analysis(symbol)
            print(tech_analysis)
        except Exception as e:
            print(f"技术分析获取失败: {e}")
        
        # 2. 测试股票资讯（东方财富API）
        print(f"\n📰 获取 {symbol} 股票资讯:")
        try:
            news_result = get_stock_news(symbol, count=3)
            print(news_result)
        except Exception as e:
            print(f"股票资讯获取失败: {e}")
        
        print(f"\n{'-'*60}")
        print("等待2秒后继续下一个股票...")
        import time
        time.sleep(2)
    
    # 测试并发获取完整新闻内容功能
    print(f"\n{'='*60}")
    print("测试并发获取完整新闻内容功能")
    print(f"{'='*60}")
    
    print(f"\n📖 获取 TSLA 的完整新闻内容（并发模式）:")
    try:
        full_news_result = get_stock_news("TSLA", count=2, fetch_full_content=True, max_content_length=500)
        print(full_news_result)
    except Exception as e:
        print(f"获取 TSLA 完整新闻内容失败: {e}")
    
    print(f"\n{'-'*60}")
    import time
    time.sleep(2)
    
    # 3. 测试股票排行榜功能
    print(f"\n{'='*60}")
    print("测试股票排行榜功能")
    print(f"{'='*60}")
    
    ranking_tests = [
        ("CN", "rise", "A股涨幅榜"),
        ("US", "rise", "美股涨幅榜"),
        ("HK", "rise", "港股涨幅榜"),
        ("CN", "fall", "A股跌幅榜"),
        ("CN", "volume", "A股成交量榜")
    ]
    
    for market, ranking_type, name in ranking_tests:
        print(f"\n📊 获取 {name}:")
        try:
            ranking_result = get_stock_ranking(market, ranking_type, 3)
            print(ranking_result)
        except Exception as e:
            print(f"{name}获取失败: {e}")
        
        print(f"\n{'-'*40}")
        import time
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("所有测试完成！")
    print(f"{'='*60}")