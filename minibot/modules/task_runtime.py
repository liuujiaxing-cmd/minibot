import asyncio
from typing import Dict, Optional


_tasks: Dict[str, asyncio.Task] = {}


def register(task_id: str, task: asyncio.Task) -> None:
    _tasks[task_id] = task


def get(task_id: str) -> Optional[asyncio.Task]:
    return _tasks.get(task_id)


def is_running(task_id: str) -> bool:
    t = _tasks.get(task_id)
    return bool(t) and not t.done()


def cancel(task_id: str) -> bool:
    t = _tasks.get(task_id)
    if not t:
        return False
    if t.done():
        return True
    t.cancel()
    return True


def cleanup(task_id: str) -> None:
    t = _tasks.get(task_id)
    if not t:
        return
    if t.done():
        _tasks.pop(task_id, None)

