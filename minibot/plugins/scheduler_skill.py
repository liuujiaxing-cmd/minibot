from ..tools import tool
from ..modules.scheduler import scheduler as task_scheduler

# --- SKILL METADATA ---
# Description: Schedule cron-like tasks.
# Input: name, cron, command

@tool(name="schedule_task", description="Schedule a command to run periodically. Usage: schedule_task(name='morning_news', cron='0 8 * * *', command='echo hello')")
def schedule_task(name: str, cron: str, command: str):
    """Schedule a cron-like task."""
    return task_scheduler.add_cron_task(name, cron, command)

@tool(name="list_scheduled_tasks", description="List all scheduled tasks.")
def list_scheduled_tasks():
    """List scheduled tasks."""
    return task_scheduler.list_tasks()
