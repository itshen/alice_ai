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

class UserConfirmationRequired(Exception):
    """需要用户确认的异常"""
    def __init__(self, tool_name: str, tool_info: Dict[str, Any], parameters: Dict[str, Any]):
        self.tool_name = tool_name
        self.tool_info = tool_info
        self.parameters = parameters
        self.confirmation_id = f"{tool_name}_{int(time.time() * 1000)}"
        super().__init__(f"工具 {tool_name} 需要用户确认")

class UserConfirmationManager:
    """用户确认管理器"""
    
    def __init__(self, web_mode: bool = False):
        self.session_start_time = time.time()
        self.web_mode = web_mode  # 是否为Web模式
        self.pending_confirmations = {}  # 存储待确认的请求
    
    def set_web_mode(self, web_mode: bool):
        """设置Web模式"""
        self.web_mode = web_mode
    
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
        
        # 如果是Web模式，抛出异常让上层处理
        if self.web_mode:
            confirmation_request = UserConfirmationRequired(tool_name, tool_info, parameters)
            self.pending_confirmations[confirmation_request.confirmation_id] = confirmation_request
            raise confirmation_request
        
        # 命令行模式：显示确认信息
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
    
    def handle_confirmation_response(self, confirmation_id: str, choice: str, 
                                   remember_choice: bool = False) -> bool:
        """处理Web模式下的确认响应"""
        if confirmation_id not in self.pending_confirmations:
            raise ValueError(f"未找到确认请求: {confirmation_id}")
        
        confirmation_request = self.pending_confirmations[confirmation_id]
        tool_name = confirmation_request.tool_name
        tool_info = confirmation_request.tool_info
        
        # 解析用户选择
        if choice in ['allow', 'y', 'yes', '是', '同意']:
            result = True
            if remember_choice:
                self._save_user_choice(tool_name, tool_info, ConfirmationResult.ALLOW_ALWAYS)
        elif choice in ['deny', 'n', 'no', '否', '拒绝']:
            result = False
            if remember_choice:
                self._save_user_choice(tool_name, tool_info, ConfirmationResult.DENY_ALWAYS)
            # 如果拒绝，立即清理确认请求
            del self.pending_confirmations[confirmation_id]
        else:
            result = False
            # 无效选择也清理确认请求
            del self.pending_confirmations[confirmation_id]
        
        # 注意：如果同意，不在这里删除确认请求，留给execute_confirmed_tool处理
        
        return result
    
    async def execute_confirmed_tool(self, confirmation_id: str):
        """执行已确认的工具"""
        if confirmation_id not in self.pending_confirmations:
            raise ValueError(f"未找到确认请求: {confirmation_id}")
        
        confirmation_request = self.pending_confirmations[confirmation_id]
        
        # 导入工具注册表
        from .tool_manager import tool_registry, ToolResult, ErrorCodes
        import time
        import inspect
        
        # 直接执行工具，完全跳过确认检查
        tool_name = confirmation_request.tool_name
        parameters = confirmation_request.parameters
        
        start_time = time.time()
        
        try:
            # 确保参数是字典类型
            if parameters is None:
                parameters = {}
            
            if tool_name not in tool_registry.tools:
                return ToolResult(
                    tool_name=tool_name,
                    parameters=parameters,
                    success=False,
                    data="",
                    error_code=ErrorCodes.TOOL_NOT_FOUND,
                    error_message=f"工具 {tool_name} 不存在",
                    execution_time=time.time() - start_time
                )
            
            tool = tool_registry.tools[tool_name]
            func = tool["function"]
            
            # 参数名映射（为了向后兼容性）
            mapped_parameters = tool_registry._map_parameters(tool_name, parameters)
            
            # 过滤参数
            sig = inspect.signature(func)
            valid_params = {}
            for param_name in sig.parameters.keys():
                if param_name in mapped_parameters:
                    valid_params[param_name] = mapped_parameters[param_name]
            
            # 直接调用工具函数，跳过所有确认检查
            if tool["is_async"]:
                result = await func(**valid_params)
            else:
                result = func(**valid_params)
            
            execution_time = time.time() - start_time
            
            # 验证并格式化返回结果
            formatted_result = tool_registry._validate_and_format_result(result, tool_name, parameters, execution_time)
            
            # 检查结果内容是否包含错误信息，如果包含则标记为失败
            if formatted_result.success and formatted_result.data and formatted_result.data.startswith('❌'):
                formatted_result.success = False
                formatted_result.error_code = "TOOL_EXECUTION_ERROR"
                formatted_result.error_message = formatted_result.data
                formatted_result.data = ""
            
            return formatted_result
            
        except TypeError as e:
            # 当参数错误时，返回工具的schema信息帮助用户理解正确的参数格式
            schema_info = tool_registry._format_tool_schema_for_error(tool_name)
            error_message = f"参数错误: {str(e)}\n\n{schema_info}"
            
            return ToolResult(
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                data="",
                error_code=ErrorCodes.PARAMETER_ERROR,
                error_message=error_message,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                data="",
                error_code=ErrorCodes.EXECUTION_ERROR,
                error_message=f"执行工具 {tool_name} 失败: {str(e)}",
                execution_time=time.time() - start_time
            )
        finally:
            # 执行完成后清理确认请求
            if confirmation_id in self.pending_confirmations:
                del self.pending_confirmations[confirmation_id]
    
    def get_confirmation_info(self, confirmation_id: str) -> Dict[str, Any]:
        """获取确认请求的详细信息，用于前端显示"""
        if confirmation_id not in self.pending_confirmations:
            raise ValueError(f"未找到确认请求: {confirmation_id}")
        
        confirmation_request = self.pending_confirmations[confirmation_id]
        
        # 格式化参数信息，对敏感信息进行脱敏
        formatted_params = {}
        for key, value in confirmation_request.parameters.items():
            if 'password' in key.lower() or 'token' in key.lower():
                formatted_params[key] = "***"
            elif isinstance(value, str) and len(value) > 100:
                formatted_params[key] = value[:100] + "..."
            else:
                formatted_params[key] = value
        
        return {
            'confirmation_id': confirmation_id,
            'tool_name': confirmation_request.tool_name,
            'description': confirmation_request.tool_info.get('description', '无描述'),
            'category': confirmation_request.tool_info.get('confirmation_category', 'general'),
            'risk_level': confirmation_request.tool_info.get('risk_level', 'medium'),
            'parameters': formatted_params,
            'risk_message': self._get_risk_message(confirmation_request.tool_info.get('risk_level', 'medium'))
        }
    
    def _get_risk_message(self, risk_level: str) -> str:
        """获取风险提示信息"""
        risk_messages = {
            'low': "💚 低风险操作",
            'medium': "💛 中等风险操作，请仔细确认",
            'high': "🔴 高风险操作，可能影响系统或数据安全！"
        }
        return risk_messages.get(risk_level, '💛 请确认操作')
    
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
            
            # 在Web模式下，直接保存到配置文件，不询问用户
            if self.web_mode:
                if result == ConfirmationResult.ALLOW_ALWAYS:
                    config.set_confirmation_policy('allow', tool_name=tool_name)
                else:
                    config.set_confirmation_policy('deny', tool_name=tool_name)
                config.save()
                return
            
            # 命令行模式：询问是否永久保存
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