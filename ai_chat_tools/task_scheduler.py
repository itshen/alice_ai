# -*- coding: utf-8 -*-
"""
任务调度器核心引擎
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from .task_manager import task_manager
from .core import ChatBot


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.task_manager = task_manager
        self.running_tasks: Set[str] = set()  # 当前正在运行的任务
        self.setup_logging()
        self.setup_event_listeners()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("TaskScheduler")
    
    def setup_event_listeners(self):
        """设置调度事件监听器"""
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
    
    def _job_executed(self, event):
        """任务执行成功事件"""
        job_id = event.job_id
        self.logger.info(f"任务执行成功: {job_id}")
        if job_id in self.running_tasks:
            self.running_tasks.remove(job_id)
    
    def _job_error(self, event):
        """任务执行错误事件"""
        job_id = event.job_id
        self.logger.error(f"任务执行错误: {job_id}, 异常: {event.exception}")
        if job_id in self.running_tasks:
            self.running_tasks.remove(job_id)
        
        # 记录错误到执行历史
        self.task_manager.add_execution_record(job_id, {
            "status": "error",
            "error": str(event.exception),
            "duration": 0
        })
    
    def _job_missed(self, event):
        """任务错过执行事件"""
        job_id = event.job_id
        self.logger.warning(f"任务错过执行: {job_id}")
        
        # 记录错过执行到历史
        self.task_manager.add_execution_record(job_id, {
            "status": "missed",
            "reason": "调度时间冲突或系统负载过高",
            "duration": 0
        })
    
    async def start(self):
        """启动调度器"""
        try:
            self.scheduler.start()
            self.logger.info("任务调度器已启动")
            
            # 加载现有任务
            await self.load_all_tasks()
            
        except Exception as e:
            self.logger.error(f"调度器启动失败: {e}")
            raise
    
    async def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown(wait=True)
            self.logger.info("任务调度器已停止")
        except Exception as e:
            self.logger.error(f"调度器停止失败: {e}")
    
    async def load_all_tasks(self):
        """加载所有启用的任务到调度器"""
        tasks = self.task_manager.list_tasks(enabled_only=True)
        
        for task in tasks:
            task_id = task["id"]
            try:
                await self.add_task_to_scheduler(task)
                self.logger.info(f"任务已加载: {task_id}")
            except Exception as e:
                self.logger.error(f"加载任务失败 {task_id}: {e}")
    
    async def add_task_to_scheduler(self, task: Dict[str, Any]):
        """添加任务到调度器"""
        task_id = task["id"]
        schedule = task["schedule"]
        
        # 创建触发器
        trigger = self._create_trigger(schedule)
        if not trigger:
            raise ValueError(f"无法创建触发器: {schedule}")
        
        # 添加任务到调度器
        self.scheduler.add_job(
            func=self._execute_task_wrapper,
            args=[task_id],
            trigger=trigger,
            id=task_id,
            name=task["name"],
            replace_existing=True,
            misfire_grace_time=60,  # 错过执行的容忍时间（秒）
            max_instances=1         # 最大同时执行实例数
        )
        
        self.logger.info(f"任务已添加到调度器: {task_id}")
    
    def _create_trigger(self, schedule: Dict[str, Any]):
        """根据调度配置创建触发器"""
        schedule_type = schedule.get("type")
        timezone_str = schedule.get("timezone", "Asia/Shanghai")
        
        if schedule_type == "cron":
            cron_expr = schedule.get("cron")
            if not cron_expr:
                raise ValueError("cron调度缺少cron表达式")
            
            # 解析cron表达式
            parts = cron_expr.split()
            if len(parts) != 5:
                raise ValueError("cron表达式格式错误，应为：分 时 日 月 周")
            
            minute, hour, day, month, day_of_week = parts
            
            return CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=timezone_str
            )
        
        elif schedule_type == "interval":
            kwargs = {}
            for key in ["seconds", "minutes", "hours", "days"]:
                if key in schedule:
                    kwargs[key] = schedule[key]
            
            if not kwargs:
                raise ValueError("interval调度缺少时间间隔配置")
            
            return IntervalTrigger(timezone=timezone_str, **kwargs)
        
        elif schedule_type == "date":
            run_date = schedule.get("date")
            if not run_date:
                raise ValueError("date调度缺少日期配置")
            
            return DateTrigger(run_date=run_date, timezone=timezone_str)
        
        elif schedule_type == "weekday":
            day = schedule.get("day")
            hour = schedule.get("hour", 9)
            minute = schedule.get("minute", 0)
            
            if not day:
                raise ValueError("weekday调度缺少day配置")
            
            # 转换星期名称为数字
            weekday_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            
            day_of_week = weekday_map.get(day.lower())
            if day_of_week is None:
                raise ValueError(f"无效的星期名称: {day}")
            
            return CronTrigger(
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                timezone=timezone_str
            )
        
        elif schedule_type == "monthly":
            day = schedule.get("day", 1)
            hour = schedule.get("hour", 9)
            minute = schedule.get("minute", 0)
            
            return CronTrigger(
                day=day,
                hour=hour,
                minute=minute,
                timezone=timezone_str
            )
        
        else:
            raise ValueError(f"不支持的调度类型: {schedule_type}")
    
    async def _execute_task_wrapper(self, task_id: str):
        """任务执行包装器"""
        # 检查是否已在运行
        if task_id in self.running_tasks:
            self.logger.warning(f"任务 {task_id} 正在运行，跳过此次执行")
            return
        
        self.running_tasks.add(task_id)
        
        try:
            await self.execute_task(task_id)
        except Exception as e:
            self.logger.error(f"任务执行异常 {task_id}: {e}")
        finally:
            # 确保从运行列表中移除
            if task_id in self.running_tasks:
                self.running_tasks.remove(task_id)
    
    async def execute_task(self, task_id: str):
        """执行单个任务"""
        task = self.task_manager.get_task(task_id)
        if not task:
            self.logger.error(f"任务不存在: {task_id}")
            return
        
        if not task.get("enabled", True):
            self.logger.info(f"任务已禁用，跳过执行: {task_id}")
            return
        
        execution_config = task["execution"]
        start_time = datetime.now(timezone.utc)
        
        self.logger.info(f"开始执行任务: {task_id} - {task['name']}")
        
        try:
            # 创建聊天机器人实例
            model_provider = execution_config.get("model_provider")
            chatbot = ChatBot(
                provider=model_provider,
                debug=True
            )
            
            # 创建新会话
            chatbot.create_session(f"Task: {task['name']}")
            
            # 准备工具模块列表
            tools = execution_config.get("tools", [])
            
            # 执行对话 - 使用流式方法收集完整响应
            prompt = execution_config["prompt"]
            response_parts = []
            
            async for chunk in chatbot.chat_stream(
                message=prompt,
                tools=tools
            ):
                response_parts.append(chunk)
            
            # 合并响应
            response = "".join(response_parts)
            
            # 记录执行结果
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            execution_record = {
                "status": "success",
                "response_length": len(response) if response else 0,
                "duration": duration,
                "model_provider": model_provider,
                "tools_used": tools
            }
            
            self.task_manager.add_execution_record(task_id, execution_record)
            
            # 更新任务运行时间
            self.task_manager.update_task_run_time(
                task_id,
                start_time.isoformat(),
                self._get_next_run_time(task_id)
            )
            
            self.logger.info(f"任务执行成功: {task_id}, 耗时: {duration:.2f}秒")
            
            # 处理执行后动作
            actions = task.get("actions", {})
            if actions.get("save_response", False) and response:
                self._save_task_response(task_id, response, start_time)
            
        except Exception as e:
            # 记录执行错误
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            execution_record = {
                "status": "error",
                "error": str(e),
                "duration": duration,
                "model_provider": execution_config.get("model_provider")
            }
            
            self.task_manager.add_execution_record(task_id, execution_record)
            
            self.logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            raise
    
    def _get_next_run_time(self, task_id: str) -> Optional[str]:
        """获取下次运行时间"""
        try:
            job = self.scheduler.get_job(task_id)
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
        except Exception:
            pass
        return None
    
    def _save_task_response(self, task_id: str, response: str, timestamp: datetime):
        """保存任务响应到文件"""
        try:
            import os
            
            # 创建任务响应目录
            responses_dir = "task_responses"
            if not os.path.exists(responses_dir):
                os.makedirs(responses_dir)
            
            # 生成文件名
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{task_id}_{timestamp_str}.txt"
            filepath = os.path.join(responses_dir, filename)
            
            # 保存响应
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"任务ID: {task_id}\n")
                f.write(f"执行时间: {timestamp.isoformat()}\n")
                f.write(f"{'='*50}\n\n")
                f.write(response)
            
            self.logger.info(f"任务响应已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存任务响应失败: {e}")
    
    async def add_task(self, task_data: Dict[str, Any]) -> str:
        """添加新任务"""
        task_id = self.task_manager.create_task(task_data)
        
        # 如果任务启用且调度器运行中，立即添加到调度器
        if task_data.get("enabled", True) and self.scheduler.running:
            task = self.task_manager.get_task(task_id)
            if task:
                await self.add_task_to_scheduler(task)
        
        return task_id
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务"""
        success = self.task_manager.update_task(task_id, updates)
        
        if success and self.scheduler.running:
            # 重新加载任务到调度器
            task = self.task_manager.get_task(task_id)
            if task and task.get("enabled", True):
                await self.add_task_to_scheduler(task)
            else:
                # 如果任务被禁用，从调度器移除
                self.remove_task_from_scheduler(task_id)
        
        return success
    
    def remove_task_from_scheduler(self, task_id: str):
        """从调度器移除任务"""
        try:
            self.scheduler.remove_job(task_id)
            self.logger.info(f"任务已从调度器移除: {task_id}")
        except Exception as e:
            self.logger.warning(f"移除任务失败: {task_id}, {e}")
    
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        # 先从调度器移除
        self.remove_task_from_scheduler(task_id)
        
        # 再从配置删除
        return self.task_manager.delete_task(task_id)
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        jobs = self.scheduler.get_jobs()
        
        return {
            "running": self.scheduler.running,
            "total_jobs": len(jobs),
            "running_tasks": len(self.running_tasks),
            "current_running": list(self.running_tasks),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        }


# 全局任务调度器实例
task_scheduler = TaskScheduler() 