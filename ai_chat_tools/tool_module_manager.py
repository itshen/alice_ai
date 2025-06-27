"""
工具模块管理器 - 重新设计版本
所有工具模块都会被加载，用户选择的是在AI调用时哪些工具可见
"""
import os
import importlib.util
from typing import List, Dict, Any, Set
from .config import config

class ToolModuleManager:
    def __init__(self):
        self.available_modules: Dict[str, Dict[str, Any]] = {}
        self.active_modules: Set[str] = set()  # 用户激活的模块（AI可见）
        self.loaded_modules: Set[str] = set()  # 已加载的模块
        
    def scan_and_load_all_modules(self):
        """扫描并加载所有工具模块"""
        print("🔍 扫描工具模块...")
        
        # 扫描用户工具模块目录
        user_modules_dir = os.path.join(os.path.dirname(__file__), "user_tool_modules")
        if os.path.exists(user_modules_dir):
            self._scan_and_load_directory(user_modules_dir, "user")
        
        print(f"✅ 成功加载 {len(self.loaded_modules)} 个工具模块")
        
        # 设置默认激活的模块
        tool_modules_config = config.get("tool_modules", {}) or {}
        default_active = tool_modules_config.get("default_active", [])
        if default_active:
            self.active_modules.update(default_active)
        # 如果没有配置，默认不激活任何模块，让AI自己决定
    
    def _scan_and_load_directory(self, directory: str, source: str):
        """扫描并加载目录中的模块"""
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                module_path = os.path.join(directory, filename)
                
                # 解析模块信息
                module_info = self._parse_module_info(module_path)
                module_info['source'] = source
                module_info['name'] = module_name
                module_info['path'] = module_path
                
                self.available_modules[module_name] = module_info
                
                # 直接加载模块
                if self._load_module_file(module_name, module_path):
                    self.loaded_modules.add(module_name)
    
    def _load_module_file(self, module_name: str, module_path: str) -> bool:
        """加载模块文件"""
        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return True
        except Exception as e:
            print(f"❌ 加载模块 '{module_name}' 失败: {e}")
            return False
        return False
    
    def _parse_module_info(self, file_path: str) -> Dict[str, str]:
        """解析模块文件头部的信息注释"""
        info = {
            'description': '未知模块',
            'category': 'other',
            'author': '未知',
            'version': '1.0.0'
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# MODULE_DESCRIPTION:'):
                        info['description'] = line.split(':', 1)[1].strip()
                    elif line.startswith('# MODULE_CATEGORY:'):
                        info['category'] = line.split(':', 1)[1].strip()
                    elif line.startswith('# MODULE_AUTHOR:'):
                        info['author'] = line.split(':', 1)[1].strip()
                    elif line.startswith('# MODULE_VERSION:'):
                        info['version'] = line.split(':', 1)[1].strip()
                    elif not line.startswith('#'):
                        break
        except Exception:
            pass
        
        return info
    
    def interactive_module_selection(self) -> List[str]:
        """交互式选择要激活的模块"""
        if not self.available_modules:
            print("❌ 没有可用的工具模块")
            return []
        
        print("\n" + "="*60)
        print("🔧 选择要激活的工具模块")
        print("="*60)
        
        # 按类别分组显示
        categories = {}
        for name, info in self.available_modules.items():
            category = info['category'].upper()
            if category not in categories:
                categories[category] = []
            categories[category].append((name, info))
        
        module_list = []
        index = 1
        
        for category, modules in categories.items():
            print(f"\n📁 {category} 工具模块:")
            for name, info in modules:
                status = "✅ 已激活" if name in self.active_modules else "⭕ 未激活"
                print(f"  {index}. {name} - {info['description']} [{status}]")
                module_list.append(name)
                index += 1
        
        print(f"\n💡 请选择要激活的工具模块:")
        print(f"   • 输入序号 (如: 1,3,5)")
        print(f"   • 输入模块名 (如: web_scraper_tools,file_manager_tools)")
        print(f"   • 输入 'all' 激活所有模块")
        print(f"   • 输入 'none' 取消激活所有模块")
        print(f"   • 直接回车保持当前状态")
        
        try:
            choice = input("请选择: ").strip()
            
            if choice.lower() == 'all':
                self.active_modules = set(self.loaded_modules)
                return list(self.active_modules)
            elif choice.lower() == 'none':
                self.active_modules.clear()
                return []
            elif not choice:
                return list(self.active_modules)
            else:
                selected_modules = []
                
                # 尝试解析输入：可能是序号或模块名
                choices = [x.strip() for x in choice.split(',')]
                
                for item in choices:
                    # 检查是否为数字序号
                    if item.isdigit():
                        idx = int(item)
                        if 1 <= idx <= len(module_list):
                            module_name = module_list[idx - 1]
                            selected_modules.append(module_name)
                    # 检查是否为模块名
                    elif item in self.loaded_modules:
                        selected_modules.append(item)
                    else:
                        print(f"⚠️  无效选择: {item}")
                
                if selected_modules:
                    self.active_modules = set(selected_modules)
                    return selected_modules
                else:
                    print("❌ 没有有效的选择")
                    return list(self.active_modules)
                
        except (ValueError, KeyboardInterrupt):
            print("❌ 输入无效，保持当前状态")
            return list(self.active_modules)
    
    def get_active_tools(self) -> List[Dict[str, Any]]:
        """获取当前激活模块中的所有工具信息（用于传递给AI）"""
        from .tool_manager import tool_registry
        
        active_tools = []
        
        # 核心工具总是激活（只保留工具管理相关的工具）
        core_tools = ['list_available_tools', 'list_tool_modules', 
                     'activate_tool_modules', 'deactivate_tool_modules', 
                     'get_tool_schema', 'help']
        
        for tool_name, tool_info in tool_registry.tools.items():
            # 核心工具总是包含
            if tool_name in core_tools:
                active_tools.append({
                    'name': tool_name,
                    'description': tool_info['description'],
                    'schema': tool_info['schema']
                })
                continue
            
            # 检查工具是否属于激活的模块
            if self._is_tool_in_active_modules(tool_name):
                active_tools.append({
                    'name': tool_name,
                    'description': tool_info['description'],
                    'schema': tool_info['schema']
                })
        
        return active_tools
    
    def _is_tool_in_active_modules(self, tool_name: str) -> bool:
        """检查工具是否属于激活的模块"""
        # 如果没有激活任何模块，则不显示模块工具
        if not self.active_modules:
            return False
        
        # 通用的模块检测逻辑：直接从工具注册信息中获取模块名
        from .tool_manager import tool_registry
        
        tool_info = tool_registry.tools.get(tool_name)
        if not tool_info:
            return False
        
        # 获取工具所属的模块
        tool_module = tool_info.get('module')
        
        # 如果工具没有模块信息（核心工具），则不需要激活
        if not tool_module:
            return False
        
        # 检查工具的模块是否在激活列表中
        return tool_module in self.active_modules
    
    def list_available_modules(self) -> List[Dict[str, Any]]:
        """列出所有可用模块"""
        return [
            {
                'name': name,
                'description': info['description'],
                'category': info['category'],
                'author': info['author'],
                'version': info['version'],
                'loaded': name in self.loaded_modules,
                'active': name in self.active_modules
            }
            for name, info in self.available_modules.items()
        ]
    
    def activate_modules(self, module_names: List[str]) -> bool:
        """激活指定的模块"""
        
        # 检查所有模块是否都存在于已加载模块中
        invalid_modules = [name for name in module_names if name not in self.loaded_modules]
        if invalid_modules:
            return False
        
        # 激活模块（update会自动去重，已激活的模块不会重复添加）
        self.active_modules.update(module_names)
        
        # 只要所有请求的模块都存在于loaded_modules中，就返回成功
        # 不管它们之前是否已经激活
        return True
    
    def deactivate_modules(self, module_names: List[str]) -> bool:
        """取消激活指定的模块"""
        for name in module_names:
            self.active_modules.discard(name)
        return True
    
    def save_active_modules_to_config(self):
        """保存当前激活的模块到配置文件"""
        try:
            current_config = config.data
            if 'tool_modules' not in current_config:
                current_config['tool_modules'] = {}
            
            current_config['tool_modules']['default_active'] = list(self.active_modules)
            config.save()
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False

    def load_modules(self, module_names: List[str]) -> Dict[str, bool]:
        """加载指定的模块"""
        results = {}
        
        for module_name in module_names:
            if module_name in self.loaded_modules:
                # 模块已经加载，直接激活
                self.active_modules.add(module_name)
                results[module_name] = True
            elif module_name in self.available_modules:
                # 模块可用但未加载，尝试加载
                module_info = self.available_modules[module_name]
                if self._load_module_file(module_name, module_info['path']):
                    self.loaded_modules.add(module_name)
                    self.active_modules.add(module_name)
                    results[module_name] = True
                else:
                    results[module_name] = False
            else:
                # 模块不存在
                results[module_name] = False
        
        return results

    def unload_module(self, module_name: str) -> bool:
        """卸载指定的模块"""
        try:
            # 从激活列表中移除
            self.active_modules.discard(module_name)
            
            # 从已加载列表中移除
            self.loaded_modules.discard(module_name)
            
            # 注意：Python中无法真正卸载已导入的模块
            # 这里只是从我们的管理列表中移除
            # 实际的模块代码和注册的工具仍然存在
            
            return True
        except Exception as e:
            print(f"❌ 卸载模块失败: {e}")
            return False

# 全局实例
tool_module_manager = ToolModuleManager() 