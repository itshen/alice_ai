# -*- coding: utf-8 -*-
"""
任务管理器模块
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .task_config import task_config


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.task_config = task_config
        self.execution_history = {}  # 内存中的执行历史
    
    def create_task(self, task_data: Dict[str, Any]) -> str:
        """创建新任务"""
        try:
            task_id = self.task_config.create_task(task_data)
            print(f"✅ 任务创建成功: {task_id}")
            return task_id
        except Exception as e:
            print(f"❌ 任务创建失败: {e}")
            raise
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务配置"""
        try:
            success = self.task_config.update_task(task_id, updates)
            if success:
                print(f"✅ 任务更新成功: {task_id}")
            else:
                print(f"❌ 任务更新失败: {task_id}")
            return success
        except Exception as e:
            print(f"❌ 任务更新异常: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            success = self.task_config.delete_task(task_id)
            if success:
                print(f"✅ 任务删除成功: {task_id}")
                # 清理执行历史
                if task_id in self.execution_history:
                    del self.execution_history[task_id]
            else:
                print(f"❌ 任务删除失败: {task_id}")
            return success
        except Exception as e:
            print(f"❌ 任务删除异常: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        return self.task_config.get_task(task_id)
    
    def list_tasks(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """列出所有任务"""
        return self.task_config.list_tasks(enabled_only)
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        success = self.task_config.enable_task(task_id)
        if success:
            print(f"✅ 任务已启用: {task_id}")
        else:
            print(f"❌ 任务启用失败: {task_id}")
        return success
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        success = self.task_config.disable_task(task_id)
        if success:
            print(f"✅ 任务已禁用: {task_id}")
        else:
            print(f"❌ 任务禁用失败: {task_id}")
        return success
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        task = self.get_task(task_id)
        if not task:
            return {"error": "任务不存在"}
        
        status = {
            "id": task_id,
            "name": task.get("name"),
            "enabled": task.get("enabled", False),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
            "last_run": task.get("last_run"),
            "next_run": task.get("next_run"),
            "execution_count": len(self.execution_history.get(task_id, [])),
            "last_execution": None
        }
        
        # 获取最后一次执行信息
        history = self.execution_history.get(task_id, [])
        if history:
            status["last_execution"] = history[-1]
        
        return status
    
    def get_task_history(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务执行历史"""
        history = self.execution_history.get(task_id, [])
        return history[-limit:] if limit > 0 else history
    
    def add_execution_record(self, task_id: str, record: Dict[str, Any]):
        """添加执行记录"""
        if task_id not in self.execution_history:
            self.execution_history[task_id] = []
        
        # 添加时间戳
        record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        
        self.execution_history[task_id].append(record)
        
        # 限制历史记录数量（最多保留100条）
        if len(self.execution_history[task_id]) > 100:
            self.execution_history[task_id] = self.execution_history[task_id][-100:]
    
    def update_task_run_time(self, task_id: str, last_run: str, next_run: Optional[str] = None):
        """更新任务运行时间"""
        updates = {"last_run": last_run}
        if next_run:
            updates["next_run"] = next_run
        
        return self.update_task(task_id, updates)
    
    def get_tasks_summary(self) -> Dict[str, Any]:
        """获取任务统计摘要"""
        all_tasks = self.list_tasks()
        enabled_tasks = self.list_tasks(enabled_only=True)
        
        # 统计执行次数
        total_executions = sum(len(history) for history in self.execution_history.values())
        
        # 统计各类调度类型
        schedule_types = {}
        for task in all_tasks:
            schedule_type = task.get("schedule", {}).get("type", "unknown")
            schedule_types[schedule_type] = schedule_types.get(schedule_type, 0) + 1
        
        return {
            "total_tasks": len(all_tasks),
            "enabled_tasks": len(enabled_tasks),
            "disabled_tasks": len(all_tasks) - len(enabled_tasks),
            "total_executions": total_executions,
            "schedule_types": schedule_types,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def validate_task_config(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证任务配置并返回详细信息"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 基础字段检查
        required_fields = ["name", "schedule", "execution"]
        for field in required_fields:
            if field not in task_data:
                result["errors"].append(f"缺少必需字段: {field}")
                result["valid"] = False
        
        if not result["valid"]:
            return result
        
        # 调度配置检查
        schedule = task_data.get("schedule", {})
        schedule_type = schedule.get("type")
        
        if schedule_type == "cron":
            if "cron" not in schedule:
                result["errors"].append("cron调度类型缺少cron表达式")
                result["valid"] = False
        elif schedule_type == "interval":
            if not any(key in schedule for key in ["seconds", "minutes", "hours", "days"]):
                result["errors"].append("interval调度类型缺少时间间隔配置")
                result["valid"] = False
        elif schedule_type == "date":
            if "date" not in schedule:
                result["errors"].append("date调度类型缺少日期配置")
                result["valid"] = False
        
        # 执行配置检查
        execution = task_data.get("execution", {})
        if "prompt" not in execution:
            result["errors"].append("执行配置缺少prompt字段")
            result["valid"] = False
        
        # 模型配置检查
        model_provider = execution.get("model_provider")
        if model_provider:
            from .config import config
            models_config = config.get("models", {}) or {}
            if model_provider not in models_config:
                result["warnings"].append(f"指定的模型提供商 '{model_provider}' 未在配置中找到")
            elif not models_config.get(model_provider, {}).get("enabled", False):
                result["warnings"].append(f"指定的模型提供商 '{model_provider}' 未启用")
        
        return result


# 全局任务管理器实例
task_manager = TaskManager() 