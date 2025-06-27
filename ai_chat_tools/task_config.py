# -*- coding: utf-8 -*-
"""
任务配置管理模块
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid


class TaskConfig:
    """任务配置管理器"""
    
    def __init__(self, config_file: str = "tasks_config.json"):
        self.config_file = config_file
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载任务配置文件"""
        default_config = {
            "tasks": {},
            "global_settings": {
                "max_concurrent_tasks": 3,
                "task_timeout": 1800,  # 30分钟超时
                "retry_failed_tasks": True,
                "max_retries": 3,
                "log_level": "INFO",
                "default_max_turns": 20,  # 默认最大对话轮数
                "task_max_turns": 50      # 任务模式最大对话轮数
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 深度合并配置
                    self._deep_merge(default_config, user_config)
            except Exception as e:
                print(f"任务配置文件加载失败: {e}")
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
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """保存配置文件"""
        config = config or self.data
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"任务配置文件保存失败: {e}")
            return False
    
    def create_task(self, task_data: Dict[str, Any]) -> str:
        """创建新任务"""
        # 生成任务ID
        task_id = task_data.get('id') or str(uuid.uuid4())
        
        # 验证任务数据
        if not self._validate_task_data(task_data):
            raise ValueError("任务数据验证失败")
        
        # 添加时间戳
        now = datetime.now(timezone.utc).isoformat()
        task_data.update({
            'id': task_id,
            'created_at': now,
            'updated_at': now,
            'last_run': None,
            'next_run': None,
            'enabled': task_data.get('enabled', True)
        })
        
        # 保存任务
        self.data['tasks'][task_id] = task_data
        self.save_config()
        
        return task_id
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务"""
        if task_id not in self.data['tasks']:
            return False
        
        # 更新时间戳
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # 合并更新
        self.data['tasks'][task_id].update(updates)
        
        # 验证更新后的数据
        if not self._validate_task_data(self.data['tasks'][task_id]):
            return False
        
        return self.save_config()
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.data['tasks']:
            del self.data['tasks'][task_id]
            return self.save_config()
        return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        return self.data['tasks'].get(task_id)
    
    def list_tasks(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = list(self.data['tasks'].values())
        if enabled_only:
            tasks = [task for task in tasks if task.get('enabled', True)]
        return tasks
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        return self.update_task(task_id, {'enabled': True})
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        return self.update_task(task_id, {'enabled': False})
    
    def get_global_setting(self, key: str, default=None):
        """获取全局设置"""
        return self.data['global_settings'].get(key, default)
    
    def set_global_setting(self, key: str, value: Any):
        """设置全局设置"""
        self.data['global_settings'][key] = value
        self.save_config()
    
    def _validate_task_data(self, task_data: Dict[str, Any]) -> bool:
        """验证任务数据"""
        required_fields = ['name', 'schedule', 'execution']
        
        # 检查必需字段
        for field in required_fields:
            if field not in task_data:
                print(f"缺少必需字段: {field}")
                return False
        
        # 验证调度配置
        schedule = task_data['schedule']
        if not isinstance(schedule, dict):
            print("调度配置必须是字典")
            return False
        
        schedule_type = schedule.get('type')
        if schedule_type not in ['cron', 'interval', 'date', 'weekday', 'monthly']:
            print(f"不支持的调度类型: {schedule_type}")
            return False
        
        # 验证执行配置
        execution = task_data['execution']
        if not isinstance(execution, dict):
            print("执行配置必须是字典")
            return False
        
        if 'prompt' not in execution:
            print("执行配置缺少prompt字段")
            return False
        
        return True


# 全局任务配置实例
task_config = TaskConfig() 