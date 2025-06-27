"""
简化的配置管理
"""
import os
import json
from typing import Dict, Any, List

class Config:
    """简化的配置类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "default_model": {
                "provider": "ollama",  # 默认模型提供商
                "fallback_providers": ["qwen", "openrouter"]  # 备用提供商列表
            },
            "models": {
                "ollama": {
                    "enabled": True,
                    "host": "http://localhost:11434",
                    "model": "qwen3:8b"
                },
                "qwen": {
                    "enabled": False,
                    "api_key": "",
                    "model": "qwen-plus-latest"
                },
                "openrouter": {
                    "enabled": False,
                    "api_key": "",
                    "model": "anthropic/claude-sonnet-4"
                }
            },
            "database": {
                "path": "chat_history.db"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000
            },
            "tool_modules": {
                "auto_load": True,  # 是否在启动时自动加载工具模块
                "interactive_selection": True,  # 是否启用交互式选择
                "default_active": ["web_scraping_tools"],  # 默认激活的模块列表 - 包含search_bing和fetch_webpage_content
                "module_directories": [
                    "ai_chat_tools/tool_modules",  # 内置工具模块目录
                    "ai_chat_tools/user_tool_modules"  # 用户工具模块目录
                ],
                "enabled_categories": ["builtin", "user"],  # 启用的工具类别
                "module_configs": {
                    # 特定模块的配置
                    # "file_manager": {
                    #     "max_file_size": 1048576,  # 1MB
                    #     "allowed_extensions": [".txt", ".md", ".py"]
                    # },
                    # "time_manager": {
                    #     "timezone": "Asia/Shanghai",
                    #     "date_format": "%Y-%m-%d %H:%M:%S"
                    # }
                }
            },
            "user_confirmation": {
                "default_policy": "ask",  # 默认策略: ask(每次询问), allow(自动同意), deny(自动拒绝)
                "tool_policies": {},  # 特定工具的策略设置
                "category_policies": {  # 按类别设置策略
                    "file_write": "ask",
                    "file_delete": "ask", 
                    "file_modify": "ask",
                    "system_command": "ask",
                    "network_request": "allow"
                },
                "remember_choices": True,  # 是否记住用户的选择
                "session_memory": {}  # 当前会话的临时记忆
            },
            "token_optimization": {
                "enabled": True,  # 是否启用 Token 优化
                "filter_old_tool_results": True,  # 是否过滤旧的工具结果
                "keep_recent_messages": 5,  # 保留最近几条消息不过滤
                "filter_tools": [  # 需要过滤的工具列表
                    "list_tool_modules",
                    "list_available_tools"
                ],
                "filter_threshold": 1000  # 工具结果超过多少字符时进行过滤
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 深度合并配置
                    self._deep_merge(default_config, user_config)
            except Exception as e:
                print(f"配置文件加载失败: {e}")
        else:
            # 创建默认配置文件
            self.save_config(default_config)
        
        return default_config
    
    def _deep_merge(self, default: Dict[str, Any], user: Dict[str, Any]):
        """深度合并配置字典"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._deep_merge(default[key], value)
            else:
                default[key] = value
    
    def save_config(self, config: Dict[str, Any] = None):
        """保存配置文件"""
        config = config or self.data
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"配置文件保存失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值，支持点号分隔的键"""
        keys = key.split('.')
        value = self.data
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值，支持点号分隔的键"""
        keys = key.split('.')
        config = self.data
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_tool_module_config(self, module_name: str) -> Dict[str, Any]:
        """获取特定工具模块的配置"""
        return self.get(f"tool_modules.module_configs.{module_name}", {})
    
    def set_tool_module_config(self, module_name: str, config: Dict[str, Any]):
        """设置特定工具模块的配置"""
        self.set(f"tool_modules.module_configs.{module_name}", config)
    
    def get_default_modules(self) -> List[str]:
        """获取默认加载的工具模块列表"""
        return self.get("tool_modules.default_modules", [])
    
    def set_default_modules(self, modules: List[str]):
        """设置默认加载的工具模块列表"""
        self.set("tool_modules.default_modules", modules)
    
    def is_auto_load_enabled(self) -> bool:
        """检查是否启用自动加载工具模块"""
        return self.get("tool_modules.auto_load", True)
    
    def is_interactive_selection_enabled(self) -> bool:
        """检查是否启用交互式模块选择"""
        return self.get("tool_modules.interactive_selection", True)
    
    # 新增：默认模型配置相关方法
    def get_default_provider(self) -> str:
        """获取默认模型提供商"""
        return self.get("default_model.provider", "ollama")
    
    def set_default_provider(self, provider: str):
        """设置默认模型提供商"""
        self.set("default_model.provider", provider)
    
    def get_fallback_providers(self) -> List[str]:
        """获取备用模型提供商列表"""
        return self.get("default_model.fallback_providers", [])
    
    def set_fallback_providers(self, providers: List[str]):
        """设置备用模型提供商列表"""
        self.set("default_model.fallback_providers", providers)
    
    def get_available_providers(self) -> List[str]:
        """获取所有已启用的模型提供商"""
        providers = []
        models_config = self.get("models", {})
        
        for provider, config in models_config.items():
            if config.get("enabled", False):
                providers.append(provider)
        
        return providers

    def enable_provider(self, provider: str):
        """启用模型提供商"""
        self.set(f"models.{provider}.enabled", True)
    
    def disable_provider(self, provider: str):
        """禁用模型提供商"""
        self.set(f"models.{provider}.enabled", False)
    
    def update_provider_config(self, provider: str, **kwargs):
        """更新模型提供商配置"""
        for key, value in kwargs.items():
            if value is not None:
                self.set(f"models.{provider}.{key}", value)
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取特定提供商的配置"""
        return self.get(f"models.{provider}", {})
    
    def is_provider_enabled(self, provider: str) -> bool:
        """检查提供商是否已启用"""
        return self.get(f"models.{provider}.enabled", False)
    
    def get_all_providers_config(self) -> Dict[str, Any]:
        """获取所有提供商的配置"""
        return self.get("models", {})
    
    # 用户确认偏好管理方法
    def get_confirmation_policy(self, tool_name: str = None, category: str = None) -> str:
        """获取确认策略"""
        # 优先级：工具级别 > 类别级别 > 默认策略
        if tool_name:
            tool_policy = self.get(f"user_confirmation.tool_policies.{tool_name}")
            if tool_policy:
                return tool_policy
        
        if category:
            category_policy = self.get(f"user_confirmation.category_policies.{category}")
            if category_policy:
                return category_policy
        
        return self.get("user_confirmation.default_policy", "ask")
    
    def set_confirmation_policy(self, policy: str, tool_name: str = None, category: str = None):
        """设置确认策略"""
        if tool_name:
            self.set(f"user_confirmation.tool_policies.{tool_name}", policy)
        elif category:
            self.set(f"user_confirmation.category_policies.{category}", policy)
        else:
            self.set("user_confirmation.default_policy", policy)
    
    def get_session_memory(self, key: str) -> str:
        """获取会话记忆"""
        return self.get(f"user_confirmation.session_memory.{key}")
    
    def set_session_memory(self, key: str, value: str):
        """设置会话记忆"""
        self.set(f"user_confirmation.session_memory.{key}", value)
    
    def clear_session_memory(self):
        """清除会话记忆"""
        self.set("user_confirmation.session_memory", {})
    
    def is_remember_choices_enabled(self) -> bool:
        """检查是否启用记住选择"""
        return self.get("user_confirmation.remember_choices", True)
    
    def save(self):
        """保存配置到文件"""
        self.save_config()
        return self.get("models", {})

# 全局配置实例
config = Config() 