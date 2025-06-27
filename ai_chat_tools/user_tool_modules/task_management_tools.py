# MODULE_DESCRIPTION: 任务调度管理工具模块 - 允许AI创建和管理定时任务
# MODULE_CATEGORY: task_management  
# MODULE_AUTHOR: AI Assistant
# MODULE_VERSION: 1.0.0

from ..tool_manager import register_tool
from ..task_manager import task_manager
from ..task_scheduler import task_scheduler
import json
from datetime import datetime, timezone
from typing import Dict, Any, List


@register_tool(
    name="create_scheduled_task",
    description="创建新的定时任务。支持cron、interval、date、weekday、monthly等调度类型",
    requires_confirmation=True,
    confirmation_category="task_create",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "任务名称"
            },
            "description": {
                "type": "string", 
                "description": "任务描述"
            },
            "schedule_type": {
                "type": "string",
                "enum": ["cron", "interval", "date", "weekday", "monthly"],
                "description": "调度类型"
            },
            "schedule_config": {
                "type": "string",
                "description": "调度配置JSON字符串，如: cron调度用 '{\"cron\": \"0 9 * * 1-5\", \"timezone\": \"Asia/Shanghai\"}'"
            },
            "prompt": {
                "type": "string",
                "description": "要发送给AI的提示词"
            },
            "model_provider": {
                "type": "string",
                "description": "模型提供商 (ollama/qwen/openrouter)，为空则使用默认",
                "default": ""
            },
            "tools": {
                "type": "string",
                "description": "要使用的工具模块列表，JSON数组格式，如: '[\"web_scraper_tools\", \"file_manager_tools\"]'",
                "default": "[]"
            },
            "enabled": {
                "type": "boolean",
                "description": "是否启用任务",
                "default": True
            },
            "save_response": {
                "type": "boolean", 
                "description": "是否保存AI响应到文件",
                "default": False
            }
        },
        "required": ["name", "schedule_type", "schedule_config", "prompt"]
    }
)
def create_scheduled_task(
    name: str,
    description: str = "",
    schedule_type: str = "cron", 
    schedule_config: str = "",
    prompt: str = "",
    model_provider: str = "",
    tools: str = "[]",
    enabled: bool = True,
    save_response: bool = False
) -> str:
    """创建新的定时任务"""
    
    try:
        # 解析调度配置
        schedule_data = json.loads(schedule_config)
        schedule_data["type"] = schedule_type
        
        # 解析工具列表
        tools_list = json.loads(tools) if tools else []
        
        # 构建任务数据
        task_data = {
            "name": name,
            "description": description,
            "schedule": schedule_data,
            "execution": {
                "prompt": prompt,
                "tools": tools_list
            },
            "actions": {
                "save_response": save_response,
                "send_notification": False,
                "log_execution": True
            },
            "enabled": enabled
        }
        
        # 添加模型提供商（如果指定）
        if model_provider:
            task_data["execution"]["model_provider"] = model_provider
        
        # 创建任务
        task_id = task_manager.create_task(task_data)
        
        # 如果调度器正在运行，添加到调度器
        if task_scheduler.scheduler.running and enabled:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                asyncio.create_task(task_scheduler.add_task_to_scheduler(task_manager.get_task(task_id)))
            else:
                # 如果事件循环未运行，同步添加
                loop.run_until_complete(task_scheduler.add_task_to_scheduler(task_manager.get_task(task_id)))
        
        return f"✅ 任务创建成功！\n📋 任务ID: {task_id}\n📝 任务名称: {name}\n⏰ 调度类型: {schedule_type}\n🎯 状态: {'已启用' if enabled else '已禁用'}"
        
    except json.JSONDecodeError as e:
        return f"❌ 配置解析失败: {e}"
    except Exception as e:
        return f"❌ 任务创建失败: {e}"


@register_tool(
    name="list_scheduled_tasks",
    description="列出所有的定时任务",
    schema={
        "type": "object",
        "properties": {
            "enabled_only": {
                "type": "boolean",
                "description": "是否只显示已启用的任务",
                "default": False
            }
        }
    }
)
def list_scheduled_tasks(enabled_only: bool = False) -> str:
    """列出所有定时任务"""
    
    try:
        tasks = task_manager.list_tasks(enabled_only)
        
        if not tasks:
            return "📋 暂无任务" + ("（已启用）" if enabled_only else "")
        
        result = f"📋 **定时任务列表** {'（已启用）' if enabled_only else ''}\n"
        result += f"总共 {len(tasks)} 个任务\n\n"
        
        for i, task in enumerate(tasks, 1):
            status = "✅ 已启用" if task.get("enabled", True) else "❌ 已禁用"
            schedule_type = task.get("schedule", {}).get("type", "unknown")
            
            result += f"**{i}. {task['name']}**\n"
            result += f"   📋 ID: `{task['id']}`\n"
            result += f"   📝 描述: {task.get('description', '无')}\n"
            result += f"   ⏰ 调度: {schedule_type}\n"
            result += f"   🎯 状态: {status}\n"
            result += f"   📅 创建时间: {task.get('created_at', '未知')}\n"
            result += f"   🔄 最后运行: {task.get('last_run', '未运行')}\n"
            result += f"   ⏭️  下次运行: {task.get('next_run', '未设置')}\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ 获取任务列表失败: {e}"


@register_tool(
    name="get_task_details", 
    description="获取指定任务的详细信息",
    schema={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "任务ID"
            }
        },
        "required": ["task_id"]
    }
)
def get_task_details(task_id: str) -> str:
    """获取任务详细信息"""
    
    try:
        task = task_manager.get_task(task_id)
        if not task:
            return f"❌ 任务不存在: {task_id}"
        
        # 获取任务状态
        status = task_manager.get_task_status(task_id)
        
        result = f"📋 **任务详情**\n\n"
        result += f"**基本信息:**\n"
        result += f"   📋 ID: `{task['id']}`\n"
        result += f"   📝 名称: {task['name']}\n"
        result += f"   📄 描述: {task.get('description', '无')}\n"
        result += f"   🎯 状态: {'✅ 已启用' if task.get('enabled', True) else '❌ 已禁用'}\n\n"
        
        result += f"**调度配置:**\n"
        schedule = task.get('schedule', {})
        result += f"   ⏰ 类型: {schedule.get('type', 'unknown')}\n"
        if schedule.get('cron'):
            result += f"   📅 Cron表达式: `{schedule['cron']}`\n"
        if schedule.get('timezone'):
            result += f"   🌍 时区: {schedule['timezone']}\n"
        result += "\n"
        
        result += f"**执行配置:**\n"
        execution = task.get('execution', {})
        result += f"   🤖 模型: {execution.get('model_provider', '默认')}\n"
        result += f"   🛠️  工具: {', '.join(execution.get('tools', [])) or '无'}\n"
        result += f"   💬 提示词: {execution.get('prompt', '')[:100]}{'...' if len(execution.get('prompt', '')) > 100 else ''}\n\n"
        
        result += f"**运行状态:**\n"
        result += f"   📅 创建时间: {task.get('created_at', '未知')}\n"
        result += f"   🔄 最后运行: {task.get('last_run', '未运行')}\n"
        result += f"   ⏭️  下次运行: {task.get('next_run', '未设置')}\n"
        result += f"   📊 执行次数: {status.get('execution_count', 0)}\n"
        
        return result
        
    except Exception as e:
        return f"❌ 获取任务详情失败: {e}"


@register_tool(
    name="update_scheduled_task",
    description="更新现有的定时任务配置",
    requires_confirmation=True,
    confirmation_category="task_modify",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "要更新的任务ID"
            },
            "updates": {
                "type": "string",
                "description": "更新内容的JSON字符串，可包含name、description、schedule、execution、enabled等字段"
            }
        },
        "required": ["task_id", "updates"]
    }
)
def update_scheduled_task(task_id: str, updates: str) -> str:
    """更新定时任务"""
    
    try:
        # 检查任务是否存在
        if not task_manager.get_task(task_id):
            return f"❌ 任务不存在: {task_id}"
        
        # 解析更新数据
        update_data = json.loads(updates)
        
        # 执行更新
        success = task_manager.update_task(task_id, update_data)
        
        if success:
            # 如果调度器正在运行，更新调度器中的任务
            if task_scheduler.scheduler.running:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(task_scheduler.update_task(task_id, update_data))
                else:
                    loop.run_until_complete(task_scheduler.update_task(task_id, update_data))
            
            return f"✅ 任务更新成功: {task_id}"
        else:
            return f"❌ 任务更新失败: {task_id}"
            
    except json.JSONDecodeError as e:
        return f"❌ 更新数据解析失败: {e}"
    except Exception as e:
        return f"❌ 任务更新失败: {e}"


@register_tool(
    name="delete_scheduled_task",
    description="删除指定的定时任务",
    requires_confirmation=True,
    confirmation_category="task_delete", 
    risk_level="high",
    schema={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "要删除的任务ID"
            }
        },
        "required": ["task_id"]
    }
)
def delete_scheduled_task(task_id: str) -> str:
    """删除定时任务"""
    
    try:
        # 检查任务是否存在
        task = task_manager.get_task(task_id)
        if not task:
            return f"❌ 任务不存在: {task_id}"
        
        task_name = task.get('name', '未知任务')
        
        # 删除任务
        success = task_manager.delete_task(task_id)
        
        if success:
            # 从调度器中移除
            task_scheduler.remove_task_from_scheduler(task_id)
            return f"✅ 任务删除成功: {task_name} ({task_id})"
        else:
            return f"❌ 任务删除失败: {task_id}"
            
    except Exception as e:
        return f"❌ 任务删除失败: {e}"


@register_tool(
    name="enable_scheduled_task",
    description="启用或禁用指定的定时任务",
    requires_confirmation=True,
    confirmation_category="task_modify",
    risk_level="low",
    schema={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "任务ID"
            },
            "enabled": {
                "type": "boolean",
                "description": "是否启用任务"
            }
        },
        "required": ["task_id", "enabled"]
    }
)
def enable_scheduled_task(task_id: str, enabled: bool) -> str:
    """启用或禁用定时任务"""
    
    try:
        # 检查任务是否存在
        task = task_manager.get_task(task_id)
        if not task:
            return f"❌ 任务不存在: {task_id}"
        
        task_name = task.get('name', '未知任务')
        
        # 更新任务状态
        if enabled:
            success = task_manager.enable_task(task_id)
            action = "启用"
        else:
            success = task_manager.disable_task(task_id)
            action = "禁用"
        
        if success:
            # 更新调度器
            if task_scheduler.scheduler.running:
                if enabled:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(task_scheduler.add_task_to_scheduler(task_manager.get_task(task_id)))
                    else:
                        loop.run_until_complete(task_scheduler.add_task_to_scheduler(task_manager.get_task(task_id)))
                else:
                    task_scheduler.remove_task_from_scheduler(task_id)
            
            return f"✅ 任务{action}成功: {task_name} ({task_id})"
        else:
            return f"❌ 任务{action}失败: {task_id}"
            
    except Exception as e:
        return f"❌ 操作失败: {e}"


@register_tool(
    name="execute_task_now",
    description="立即执行指定的任务（不影响正常调度）",
    requires_confirmation=True,
    confirmation_category="task_execute",
    risk_level="medium",
    schema={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "要执行的任务ID"
            }
        },
        "required": ["task_id"]
    }
)
def execute_task_now(task_id: str) -> str:
    """立即执行任务"""
    
    try:
        # 检查任务是否存在
        task = task_manager.get_task(task_id)
        if not task:
            return f"❌ 任务不存在: {task_id}"
        
        task_name = task.get('name', '未知任务')
        
        # 立即执行任务
        import asyncio
        loop = asyncio.get_event_loop()
        
        if loop.is_running():
            # 如果事件循环正在运行，创建任务
            asyncio.create_task(task_scheduler.execute_task(task_id))
            return f"🚀 任务已开始执行: {task_name} ({task_id})\n💡 任务将在后台运行，可通过 get_task_history 查看执行结果"
        else:
            # 如果事件循环未运行，同步执行
            loop.run_until_complete(task_scheduler.execute_task(task_id))
            return f"✅ 任务执行完成: {task_name} ({task_id})"
            
    except Exception as e:
        return f"❌ 任务执行失败: {e}"


@register_tool(
    name="get_task_history",
    description="获取任务的执行历史记录",
    schema={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "任务ID"
            },
            "limit": {
                "type": "integer",
                "description": "返回记录数量限制",
                "default": 10
            }
        },
        "required": ["task_id"]
    }
)
def get_task_history(task_id: str, limit: int = 10) -> str:
    """获取任务执行历史"""
    
    try:
        # 检查任务是否存在
        task = task_manager.get_task(task_id)
        if not task:
            return f"❌ 任务不存在: {task_id}"
        
        task_name = task.get('name', '未知任务')
        
        # 获取执行历史
        history = task_manager.get_task_history(task_id, limit)
        
        if not history:
            return f"📋 任务 {task_name} 暂无执行记录"
        
        result = f"📋 **任务执行历史**: {task_name}\n"
        result += f"最近 {len(history)} 条记录:\n\n"
        
        for i, record in enumerate(reversed(history), 1):
            status_icon = {"success": "✅", "error": "❌", "missed": "⏸️"}.get(record.get("status"), "❓")
            
            result += f"**{i}. {status_icon} {record.get('status', 'unknown').upper()}**\n"
            result += f"   📅 时间: {record.get('timestamp', '未知')}\n"
            result += f"   ⏱️  耗时: {record.get('duration', 0):.2f}秒\n"
            
            if record.get("status") == "success":
                result += f"   📊 响应长度: {record.get('response_length', 0)} 字符\n"
                result += f"   🤖 模型: {record.get('model_provider', '未知')}\n"
                result += f"   🛠️  工具: {', '.join(record.get('tools_used', [])) or '无'}\n"
            elif record.get("status") == "error":
                result += f"   ❌ 错误: {record.get('error', '未知错误')}\n"
            elif record.get("status") == "missed":
                result += f"   ⏸️  原因: {record.get('reason', '未知原因')}\n"
                
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ 获取执行历史失败: {e}"


@register_tool(
    name="get_scheduler_status",
    description="获取任务调度器的整体状态信息",
    schema={
        "type": "object",
        "properties": {}
    }
)
def get_scheduler_status() -> str:
    """获取调度器状态"""
    
    try:
        # 获取调度器状态
        status = task_scheduler.get_scheduler_status()
        
        # 获取任务统计
        summary = task_manager.get_tasks_summary()
        
        result = f"🚀 **任务调度器状态**\n\n"
        result += f"**调度器信息:**\n"
        result += f"   🎯 状态: {'🟢 运行中' if status['running'] else '🔴 已停止'}\n"
        result += f"   📋 调度任务数: {status['total_jobs']}\n"
        result += f"   🏃 运行中任务: {status['running_tasks']}\n"
        
        if status['current_running']:
            result += f"   ⚡ 当前运行: {', '.join(status['current_running'])}\n"
        
        result += f"\n**任务统计:**\n"
        result += f"   📊 总任务数: {summary['total_tasks']}\n"
        result += f"   ✅ 已启用: {summary['enabled_tasks']}\n"
        result += f"   ❌ 已禁用: {summary['disabled_tasks']}\n"
        result += f"   🔢 总执行次数: {summary['total_executions']}\n"
        
        if summary.get('schedule_types'):
            result += f"\n**调度类型分布:**\n"
            for schedule_type, count in summary['schedule_types'].items():
                result += f"   📅 {schedule_type}: {count}\n"
        
        if status.get('jobs'):
            result += f"\n**即将执行的任务:**\n"
            for job in status['jobs'][:5]:  # 只显示前5个
                next_run = job.get('next_run_time', '未设置')
                if next_run != '未设置':
                    # 简化时间显示
                    try:
                        dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
                        next_run = dt.strftime('%m-%d %H:%M')
                    except:
                        pass
                result += f"   ⏰ {job.get('name', job.get('id'))}: {next_run}\n"
        
        return result
        
    except Exception as e:
        return f"❌ 获取调度器状态失败: {e}" 