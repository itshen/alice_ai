# MODULE_DESCRIPTION: 金山 WOA 消息推送工具集合，支持文本、Markdown、链接消息推送
# MODULE_CATEGORY: notification
# MODULE_AUTHOR: Luoxiaoshan
# MODULE_VERSION: 1.0.0

"""
金山 WOA 消息推送工具模块
提供完整的金山 WOA 机器人消息推送功能，包括：
- 文本消息推送（支持@人功能）
- Markdown 格式消息推送
- 链接消息推送
- Webhook Key 管理
- 消息频率限制保护
专门用于企业内部通知和监控报警
"""

import os
import json
import time
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import threading

# 使用绝对导入避免相对导入问题
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_chat_tools.tool_manager import register_tool
from ai_chat_tools.config import config

# ==================== WOA 推送管理器 ====================

class WOANotificationManager:
    """金山 WOA 消息推送管理器"""
    
    def __init__(self):
        # 创建数据存储目录
        self.data_dir = os.path.join(os.getcwd(), "woa_data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Webhook 配置文件路径
        self.config_file = os.path.join(self.data_dir, "woa_webhooks.json")
        
        # 消息发送频率限制（20条/分钟）
        self.rate_limit_lock = threading.Lock()
        self.message_history = []
        self.max_messages_per_minute = 20
        
        # 加载已保存的 webhook 配置
        self.webhooks = self._load_webhooks()
    
    def _load_webhooks(self) -> Dict[str, Any]:
        """加载保存的 webhook 配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _save_webhooks(self):
        """保存 webhook 配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.webhooks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"保存 webhook 配置失败: {str(e)}")
    
    def add_webhook(self, name: str, key: str, description: str = "") -> bool:
        """添加或更新 webhook 配置"""
        try:
            # 验证 key 格式
            if not key or len(key) < 10:
                raise ValueError("Webhook key 格式无效")
            
            # 构建完整的 webhook URL
            webhook_url = f"https://xz.wps.cn/api/v1/webhook/send?key={key}"
            
            # 保存配置
            self.webhooks[name] = {
                'key': key,
                'url': webhook_url,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'last_used': None
            }
            
            self._save_webhooks()
            return True
            
        except Exception as e:
            raise Exception(f"添加 webhook 失败: {str(e)}")
    
    def remove_webhook(self, name: str) -> bool:
        """删除 webhook 配置"""
        if name in self.webhooks:
            del self.webhooks[name]
            self._save_webhooks()
            return True
        return False
    
    def list_webhooks(self) -> Dict[str, Dict]:
        """列出所有 webhook 配置"""
        # 返回不包含敏感信息的配置列表
        safe_webhooks = {}
        for name, config in self.webhooks.items():
            safe_webhooks[name] = {
                'description': config.get('description', ''),
                'created_at': config.get('created_at', ''),
                'last_used': config.get('last_used', ''),
                'key_preview': config['key'][:8] + '...' if len(config['key']) > 8 else config['key']
            }
        return safe_webhooks
    
    def _check_rate_limit(self) -> bool:
        """检查消息发送频率限制"""
        with self.rate_limit_lock:
            now = datetime.now()
            # 清理超过1分钟的历史记录
            self.message_history = [
                timestamp for timestamp in self.message_history 
                if now - timestamp < timedelta(minutes=1)
            ]
            
            # 检查是否超过频率限制
            if len(self.message_history) >= self.max_messages_per_minute:
                return False
            
            # 记录当前消息时间
            self.message_history.append(now)
            return True
    
    def _send_message(self, webhook_name: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息到指定的 webhook"""
        try:
            # 检查 webhook 是否存在
            if webhook_name not in self.webhooks:
                return {
                    'success': False,
                    'error': f"Webhook '{webhook_name}' 不存在，请先添加配置"
                }
            
            # 检查频率限制
            if not self._check_rate_limit():
                return {
                    'success': False,
                    'error': f"消息发送频率超限，每分钟最多发送 {self.max_messages_per_minute} 条消息"
                }
            
            # 验证消息内容长度（5000字符限制）
            content_length = len(json.dumps(message_data, ensure_ascii=False))
            if content_length > 5000:
                return {
                    'success': False,
                    'error': f"消息内容过长 ({content_length} 字符)，最大支持 5000 字符"
                }
            
            webhook_config = self.webhooks[webhook_name]
            webhook_url = webhook_config['url']
            
            # 发送 HTTP POST 请求
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            response = requests.post(
                webhook_url,
                data=json.dumps(message_data, ensure_ascii=False).encode('utf-8'),
                headers=headers,
                timeout=30
            )
            
            # 更新最后使用时间
            webhook_config['last_used'] = datetime.now().isoformat()
            self._save_webhooks()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'webhook_name': webhook_name,
                    'message_type': message_data.get('msgtype', 'unknown'),
                    'response': response.text
                }
            else:
                return {
                    'success': False,
                    'error': f"发送失败，状态码: {response.status_code}, 响应: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"发送消息失败: {str(e)}"
            }

# 创建全局实例
_woa_manager = WOANotificationManager()

# ==================== Webhook 管理工具 ====================

@register_tool(
    name="add_woa_webhook",
    description="添加或更新金山 WOA 机器人 webhook 配置",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Webhook 配置名称（用于标识不同的群组或机器人）"
            },
            "key": {
                "type": "string",
                "description": "Webhook 的 key 参数（从 webhook URL 中提取）"
            },
            "description": {
                "type": "string",
                "description": "可选的描述信息",
                "default": ""
            }
        },
        "required": ["name", "key"]
    }
)
def add_woa_webhook(name: str, key: str, description: str = "") -> str:
    """添加或更新 WOA webhook 配置"""
    try:
        success = _woa_manager.add_webhook(name, key, description)
        if success:
            return f"[成功] Webhook '{name}' 配置已保存\n描述: {description}\nKey: {key[:8]}...\n\n⚠️ 重要提醒：请妥善保管 webhook key，避免泄漏到公开场所！"
        else:
            return f"[错误] 添加 webhook 配置失败"
    except Exception as e:
        return f"[错误] {str(e)}"

@register_tool(
    name="list_woa_webhooks",
    description="列出所有已保存的 WOA webhook 配置",
    schema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_woa_webhooks() -> str:
    """列出所有 webhook 配置"""
    try:
        webhooks = _woa_manager.list_webhooks()
        if not webhooks:
            return "[提示] 暂无保存的 webhook 配置，请先使用 add_woa_webhook 添加"
        
        result = "[成功] 已保存的 WOA Webhook 配置:\n\n"
        for name, config in webhooks.items():
            result += f"📍 **{name}**\n"
            result += f"   描述: {config['description'] or '无'}\n"
            result += f"   Key 预览: {config['key_preview']}\n"
            result += f"   创建时间: {config['created_at']}\n"
            result += f"   最后使用: {config['last_used'] or '从未使用'}\n\n"
        
        return result
    except Exception as e:
        return f"[错误] 获取 webhook 配置失败: {str(e)}"

@register_tool(
    name="remove_woa_webhook",
    description="删除指定的 WOA webhook 配置",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "要删除的 webhook 配置名称"
            }
        },
        "required": ["name"]
    }
)
def remove_woa_webhook(name: str) -> str:
    """删除 webhook 配置"""
    try:
        success = _woa_manager.remove_webhook(name)
        if success:
            return f"[成功] Webhook '{name}' 配置已删除"
        else:
            return f"[错误] Webhook '{name}' 不存在"
    except Exception as e:
        return f"[错误] 删除 webhook 配置失败: {str(e)}"

# ==================== 消息发送工具 ====================

@register_tool(
    name="send_woa_text_message",
    description="发送文本消息到金山 WOA 群组",
    requires_confirmation=True,
    confirmation_category="notification",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "webhook_name": {
                "type": "string",
                "description": "使用的 webhook 配置名称"
            },
            "content": {
                "type": "string",
                "description": "消息内容（支持 @人 标签）"
            },
            "at_users": {
                "type": "array",
                "description": "要 @的用户列表，格式: [{'type': 'id', 'value': '12345', 'name': '张三'}, {'type': 'email', 'value': 'user@wps.cn', 'name': '李四'}]",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["id", "email", "all"]},
                        "value": {"type": "string"},
                        "name": {"type": "string"}
                    },
                    "required": ["type"]
                },
                "default": []
            }
        },
        "required": ["webhook_name", "content"]
    }
)
def send_woa_text_message(webhook_name: str, content: str, at_users: Optional[List[Dict[str, str]]] = None) -> str:
    """发送文本消息"""
    try:
        # 处理 @人 标签
        if at_users:
            for user in at_users:
                user_type = user.get('type')
                if user_type == 'all':
                    at_tag = '<at user_id="-1">所有人</at>'
                elif user_type == 'id':
                    user_id = user.get('value', '')
                    name = user.get('name', '')
                    at_tag = f'<at user_id="{user_id}">{name}</at>'
                elif user_type == 'email':
                    email = user.get('value', '')
                    name = user.get('name', '')
                    at_tag = f'<at email="{email}">{name}</at>'
                else:
                    continue
                
                content += f" {at_tag}"
        
        # 构建消息数据
        message_data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        # 发送消息
        result = _woa_manager._send_message(webhook_name, message_data)
        
        if result['success']:
            return f"[成功] 文本消息发送完成\nWebhook: {webhook_name}\n内容预览: {content[:100]}{'...' if len(content) > 100 else ''}"
        else:
            return f"[错误] 消息发送失败: {result['error']}"
            
    except Exception as e:
        return f"[错误] 发送文本消息失败: {str(e)}"

@register_tool(
    name="send_woa_markdown_message",
    description="发送 Markdown 格式消息到金山 WOA 群组",
    requires_confirmation=True,
    confirmation_category="notification",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "webhook_name": {
                "type": "string",
                "description": "使用的 webhook 配置名称"
            },
            "markdown_text": {
                "type": "string",
                "description": "Markdown 格式的消息内容（支持标题、加粗、链接、列表等）"
            }
        },
        "required": ["webhook_name", "markdown_text"]
    }
)
def send_woa_markdown_message(webhook_name: str, markdown_text: str) -> str:
    """发送 Markdown 消息"""
    try:
        # 构建消息数据
        message_data = {
            "msgtype": "markdown",
            "markdown": {
                "text": markdown_text
            }
        }
        
        # 发送消息
        result = _woa_manager._send_message(webhook_name, message_data)
        
        if result['success']:
            return f"[成功] Markdown 消息发送完成\nWebhook: {webhook_name}\n内容预览: {markdown_text[:100]}{'...' if len(markdown_text) > 100 else ''}"
        else:
            return f"[错误] 消息发送失败: {result['error']}"
            
    except Exception as e:
        return f"[错误] 发送 Markdown 消息失败: {str(e)}"

@register_tool(
    name="send_woa_link_message",
    description="发送链接消息到金山 WOA 群组",
    requires_confirmation=True,
    confirmation_category="notification",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "webhook_name": {
                "type": "string",
                "description": "使用的 webhook 配置名称"
            },
            "title": {
                "type": "string",
                "description": "链接标题"
            },
            "text": {
                "type": "string",
                "description": "链接描述（支持 Markdown 格式）"
            },
            "message_url": {
                "type": "string",
                "description": "跳转链接地址",
                "default": ""
            },
            "btn_title": {
                "type": "string",
                "description": "按钮标题（最大12个字符，默认为'查看详情'）",
                "default": "查看详情"
            }
        },
        "required": ["webhook_name", "title", "text"]
    }
)
def send_woa_link_message(webhook_name: str, title: str, text: str, message_url: str = "", btn_title: str = "查看详情") -> str:
    """发送链接消息"""
    try:
        # 验证按钮标题长度
        if len(btn_title) > 12:
            return "[错误] 按钮标题长度不能超过12个字符"
        
        # 构建消息数据
        message_data = {
            "msgtype": "link",
            "title": title,
            "text": text
        }
        
        if message_url:
            message_data["messageUrl"] = message_url
        
        if btn_title != "查看详情":
            message_data["btnTitle"] = btn_title
        
        # 发送消息
        result = _woa_manager._send_message(webhook_name, message_data)
        
        if result['success']:
            return f"[成功] 链接消息发送完成\nWebhook: {webhook_name}\n标题: {title}\n链接: {message_url or '无'}"
        else:
            return f"[错误] 消息发送失败: {result['error']}"
            
    except Exception as e:
        return f"[错误] 发送链接消息失败: {str(e)}"

# ==================== 快捷消息模板 ====================

@register_tool(
    name="send_woa_alert_message",
    description="发送监控报警消息模板",
    requires_confirmation=True,
    confirmation_category="notification",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "webhook_name": {
                "type": "string",
                "description": "使用的 webhook 配置名称"
            },
            "alert_title": {
                "type": "string",
                "description": "报警标题"
            },
            "alert_content": {
                "type": "string",
                "description": "报警内容"
            },
            "severity": {
                "type": "string",
                "description": "严重程度",
                "enum": ["低", "中等", "高", "严重"],
                "default": "中等"
            },
            "at_all": {
                "type": "boolean",
                "description": "是否 @所有人",
                "default": False
            }
        },
        "required": ["webhook_name", "alert_title", "alert_content"]
    }
)
def send_woa_alert_message(webhook_name: str, alert_title: str, alert_content: str, severity: str = "中等", at_all: bool = False) -> str:
    """发送监控报警消息"""
    try:
        # 根据严重程度设置颜色
        color_map = {
            "低": "#00FF00",      # 绿色
            "中等": "#FFA500",    # 橙色  
            "高": "#FF6600",      # 深橙色
            "严重": "#FF0000"     # 红色
        }
        
        color = color_map.get(severity, "#FFA500")
        
        # 构建 Markdown 消息
        markdown_text = f"""## 🚨 监控报警通知

**报警内容：** {alert_title}

**详细信息：**
{alert_content}

> **严重程度：** <font color='{color}'>{severity}</font>
> **报警时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        if at_all:
            markdown_text += "\n\n<at user_id=\"-1\">所有人</at> 请注意处理！"
        
        # 发送消息
        message_data = {
            "msgtype": "markdown",
            "markdown": {
                "text": markdown_text
            }
        }
        
        result = _woa_manager._send_message(webhook_name, message_data)
        
        if result['success']:
            return f"[成功] 监控报警消息发送完成\nWebhook: {webhook_name}\n报警: {alert_title}\n严重程度: {severity}"
        else:
            return f"[错误] 报警消息发送失败: {result['error']}"
            
    except Exception as e:
        return f"[错误] 发送报警消息失败: {str(e)}" 