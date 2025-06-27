"""
用户确认管理器
处理需要用户确认的工具操作
"""

import time
from typing import Dict, Any, Optional, Callable
from enum import Enum

from .config import config

class ConfirmationResult(Enum):
    """确认结果枚举"""
    ALLOW = "allow"
    DENY = "deny"
    ALLOW_ALWAYS = "allow_always"
    DENY_ALWAYS = "deny_always"

class UserConfirmationManager:
    """用户确认管理器"""
    
    def __init__(self):
        self.session_start_time = time.time()
    
    def requires_confirmation(self, tool_name: str, tool_info: Dict[str, Any]) -> bool:
        """检查工具是否需要用户确认"""
        # 检查工具是否标记为需要确认
        requires_confirm = tool_info.get('requires_confirmation', False)
        if not requires_confirm:
            return False
        
        # 检查确认类别
        confirm_category = tool_info.get('confirmation_category', 'general')
        
        # 获取策略
        policy = config.get_confirmation_policy(tool_name=tool_name, category=confirm_category)
        
        # 如果策略是自动允许或拒绝，则不需要确认
        if policy in ['allow', 'deny']:
            return False
        
        # 检查会话记忆
        if config.is_remember_choices_enabled():
            session_key = f"{tool_name}_{confirm_category}"
            session_policy = config.get_session_memory(session_key)
            if session_policy in ['allow_always', 'deny_always']:
                return False
        
        return True
    
    def get_auto_decision(self, tool_name: str, tool_info: Dict[str, Any]) -> Optional[bool]:
        """获取自动决策结果"""
        confirm_category = tool_info.get('confirmation_category', 'general')
        
        # 检查工具级别策略
        policy = config.get_confirmation_policy(tool_name=tool_name, category=confirm_category)
        
        if policy == 'allow':
            return True
        elif policy == 'deny':
            return False
        
        # 检查会话记忆
        if config.is_remember_choices_enabled():
            session_key = f"{tool_name}_{confirm_category}"
            session_policy = config.get_session_memory(session_key)
            if session_policy == 'allow_always':
                return True
            elif session_policy == 'deny_always':
                return False
        
        return None
    
    def request_confirmation(self, tool_name: str, tool_info: Dict[str, Any], 
                           parameters: Dict[str, Any]) -> bool:
        """请求用户确认"""
        # 检查是否需要确认
        if not self.requires_confirmation(tool_name, tool_info):
            # 检查自动决策
            auto_decision = self.get_auto_decision(tool_name, tool_info)
            if auto_decision is not None:
                return auto_decision
            return True  # 默认允许
        
        # 显示确认信息
        self._show_confirmation_prompt(tool_name, tool_info, parameters)
        
        # 获取用户输入
        while True:
            try:
                choice = input("\n请选择 (y/n/a/d): ").strip().lower()
                
                if choice in ['y', 'yes', '是', '同意']:
                    return True
                elif choice in ['n', 'no', '否', '拒绝']:
                    return False
                elif choice in ['a', 'always', '总是同意']:
                    self._save_user_choice(tool_name, tool_info, ConfirmationResult.ALLOW_ALWAYS)
                    return True
                elif choice in ['d', 'deny_always', '总是拒绝']:
                    self._save_user_choice(tool_name, tool_info, ConfirmationResult.DENY_ALWAYS)
                    return False
                else:
                    print("❌ 无效选择，请输入 y(同意)/n(拒绝)/a(总是同意)/d(总是拒绝)")
                    
            except KeyboardInterrupt:
                print("\n❌ 用户取消操作")
                return False
            except EOFError:
                print("\n❌ 输入结束，默认拒绝")
                return False
    
    def _show_confirmation_prompt(self, tool_name: str, tool_info: Dict[str, Any], 
                                parameters: Dict[str, Any]):
        """显示确认提示"""
        print("\n" + "="*60)
        print("🔒 用户确认请求")
        print("="*60)
        
        # 工具信息
        print(f"🔧 工具名称: {tool_name}")
        print(f"📝 工具描述: {tool_info.get('description', '无描述')}")
        
        # 确认类别和风险等级
        category = tool_info.get('confirmation_category', 'general')
        risk_level = tool_info.get('risk_level', 'medium')
        print(f"📂 操作类别: {category}")
        print(f"⚠️  风险等级: {risk_level}")
        
        # 参数信息
        if parameters:
            print(f"\n📋 操作参数:")
            for key, value in parameters.items():
                # 对敏感信息进行脱敏
                if 'password' in key.lower() or 'token' in key.lower():
                    value = "***"
                elif isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"  • {key}: {value}")
        
        # 风险提示
        risk_messages = {
            'low': "💚 低风险操作",
            'medium': "💛 中等风险操作，请仔细确认",
            'high': "🔴 高风险操作，可能影响系统或数据安全！"
        }
        print(f"\n{risk_messages.get(risk_level, '💛 请确认操作')}")
        
        print("\n选项:")
        print("  y/yes/是/同意    - 同意本次操作")
        print("  n/no/否/拒绝     - 拒绝本次操作")
        print("  a/always/总是同意 - 同意并记住选择（以后自动同意此类操作）")
        print("  d/deny_always/总是拒绝 - 拒绝并记住选择（以后自动拒绝此类操作）")
    
    def _save_user_choice(self, tool_name: str, tool_info: Dict[str, Any], 
                         result: ConfirmationResult):
        """保存用户选择"""
        if not config.is_remember_choices_enabled():
            return
        
        confirm_category = tool_info.get('confirmation_category', 'general')
        
        if result in [ConfirmationResult.ALLOW_ALWAYS, ConfirmationResult.DENY_ALWAYS]:
            # 保存到会话记忆
            session_key = f"{tool_name}_{confirm_category}"
            config.set_session_memory(session_key, result.value)
            
            # 询问是否永久保存
            print(f"\n💾 是否将此选择永久保存到配置文件？")
            print(f"   这将影响所有未来的 '{tool_name}' 工具调用")
            
            try:
                save_choice = input("保存到配置文件? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes', '是']:
                    if result == ConfirmationResult.ALLOW_ALWAYS:
                        config.set_confirmation_policy('allow', tool_name=tool_name)
                    else:
                        config.set_confirmation_policy('deny', tool_name=tool_name)
                    config.save()
                    print("✅ 已保存到配置文件")
                else:
                    print("💡 仅在当前会话中生效")
            except (KeyboardInterrupt, EOFError):
                print("\n💡 仅在当前会话中生效")

# 全局确认管理器实例
user_confirmation_manager = UserConfirmationManager() 