import json
import os
import time
from typing import Any, Dict, Optional


def _checkpoint_dir() -> str:
    return os.getenv("CHECKPOINT_DIR", "minibot_logs/checkpoints")


def _latest_file() -> str:
    return os.path.join(_checkpoint_dir(), "_latest.json")


def _task_file(task_id: str) -> str:
    return os.path.join(_checkpoint_dir(), f"{task_id}.json")


def save_checkpoint(task_id: str, payload: Dict[str, Any]) -> str:
    os.makedirs(_checkpoint_dir(), exist_ok=True)
    payload = dict(payload or {})
    payload["task_id"] = task_id
    payload["ts"] = time.time()
    path = _task_file(task_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(_latest_file(), "w", encoding="utf-8") as f:
        json.dump({"task_id": task_id, "ts": payload["ts"]}, f, ensure_ascii=False)
    return path


def load_checkpoint(task_id: str) -> Optional[Dict[str, Any]]:
    path = _task_file(task_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def latest_task_id() -> Optional[str]:
    path = _latest_file()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        v = obj.get("task_id")
        return str(v) if v else None
    except Exception:
        return None

