import os
import gzip
from datetime import datetime, timedelta

from .memory_manager import MemoryManager
from ..memory.vector_memory import vector_memory


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _now_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


class DailyJournal:
    def __init__(self, base_dir: str, archive_dir: str):
        self.base_dir = base_dir
        self.archive_dir = archive_dir
        _ensure_dir(self.base_dir)
        _ensure_dir(self.archive_dir)
        self._memory_manager = MemoryManager()

    def _daily_path(self, date_str: str) -> str:
        return os.path.join(self.base_dir, f"{date_str}.md")

    def _archive_path(self, date_str: str) -> str:
        return os.path.join(self.archive_dir, f"{date_str}.md.gz")

    def append_turn(self, role: str, content: str, date_str: str | None = None) -> None:
        date_str = date_str or _today_str()
        path = self._daily_path(date_str)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {date_str} 对话记录\n\n")

        with open(path, "a", encoding="utf-8") as f:
            f.write(f"## {_now_str()} {role}\n\n")
            f.write(content.strip() + "\n\n")

    async def finalize_date(self, date_str: str) -> str | None:
        path = self._daily_path(date_str)
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        extracted = await self._memory_manager.extract_from_daily_log(
            date_str=date_str,
            markdown=content,
        )

        summary = extracted.get("summary")
        memories = extracted.get("memories")

        if summary:
            self._memory_manager.ltm.add(f"daily_summary:{date_str}", summary)
            try:
                if vector_memory:
                    await vector_memory.add("daily_summary", summary, {"date": date_str})
            except Exception:
                pass

        if isinstance(memories, dict):
            for k, v in memories.items():
                if k and v is not None:
                    self._memory_manager.ltm.add(str(k), str(v))

        archive_path = self._archive_path(date_str)
        with gzip.open(archive_path, "wt", encoding="utf-8") as gz:
            gz.write(content)

        summary_md = summary or extracted.get("fallback_summary") or ""
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {date_str} 当日摘要\n\n")
            if summary_md:
                f.write(summary_md.strip() + "\n\n")
            f.write(f"- 归档文件：{archive_path}\n")

        return archive_path

    async def finalize_previous_day(self) -> str | None:
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return await self.finalize_date(date_str)

    async def finalize_overdue(self) -> list[str]:
        today = _today_str()
        archived = []
        for name in os.listdir(self.base_dir):
            if not name.endswith(".md"):
                continue
            date_str = name[:-3]
            if date_str < today:
                result = await self.finalize_date(date_str)
                if result:
                    archived.append(result)
        return archived


def _default_base_dir() -> str:
    return os.getenv("DAILY_LOG_DIR", "minibot_logs/daily")


def _default_archive_dir() -> str:
    return os.getenv("DAILY_ARCHIVE_DIR", "minibot_logs/archive")


try:
    daily_journal = DailyJournal(
        base_dir=_default_base_dir(),
        archive_dir=_default_archive_dir(),
    )
except Exception:
    daily_journal = None
