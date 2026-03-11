from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Dict, Any, List
import asyncio
import uuid

class TaskScheduler:
    """Manages scheduled tasks using APScheduler."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        # Do not start here, start explicitly in an async context
        self.tasks: Dict[str, Any] = {} # Metadata about tasks
    
    def start(self):
        """Start the scheduler if an event loop is running."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
        except RuntimeError:
            # Still no loop? Just ignore for now, user must call start() inside async def
            pass
    
    def add_cron_task(self, name: str, cron_expression: str, command: str) -> str:
        """
        Schedule a shell command using cron syntax.
        cron_expression format: "minute hour day month day_of_week"
        e.g., "0 8 * * *" for every day at 8:00 AM.
        """
        # Ensure scheduler is started
        self.start()
        
        import subprocess
        
        task_id = str(uuid.uuid4())[:8]
        
        async def job_function():
            print(f"⏰ [Scheduler] Executing task '{name}': {command}")
            # Execute command in background
            try:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                output = stdout.decode().strip() or stderr.decode().strip()
                print(f"✅ [Scheduler] Task '{name}' finished. Output: {output[:100]}...")
            except Exception as e:
                print(f"❌ [Scheduler] Task '{name}' failed: {e}")

        try:
            # Parse cron string "min hour day month dow"
            parts = cron_expression.split()
            if len(parts) != 5:
                return "Error: Cron expression must have 5 parts (min hour day month dow)."
                
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            )
            
            self.scheduler.add_job(job_function, trigger, id=task_id, name=name)
            
            self.tasks[task_id] = {
                "name": name,
                "cron": cron_expression,
                "command": command
            }
            
            return f"Task '{name}' scheduled with ID {task_id}. Next run at: {trigger.get_next_fire_time(None, None)}"
            
        except Exception as e:
            return f"Error scheduling task: {str(e)}"

    def list_tasks(self) -> str:
        if not self.tasks:
            return "No scheduled tasks."
        
        result = "Scheduled Tasks:\n"
        for tid, data in self.tasks.items():
            result += f"- [{tid}] {data['name']} ({data['cron']}): {data['command']}\n"
        return result

    def remove_task(self, task_id: str) -> str:
        if task_id in self.tasks:
            try:
                self.scheduler.remove_job(task_id)
                del self.tasks[task_id]
                return f"Task {task_id} removed."
            except Exception as e:
                return f"Error removing task: {str(e)}"
        return "Task ID not found."

# Global instance
scheduler = TaskScheduler()
