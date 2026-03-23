import json
import math
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..llm import llm_client


def _default_store_path() -> str:
    return os.getenv("VECTOR_MEMORY_PATH", "minibot_vector_memory.jsonl")


def _enabled() -> bool:
    return os.getenv("VECTOR_MEMORY_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def _provider() -> str:
    return os.getenv("VECTOR_EMBEDDING_PROVIDER", "hash").strip().lower()


def _model() -> str:
    return os.getenv("VECTOR_EMBEDDING_MODEL", "text-embedding-3-small").strip()


def _tokenize(text: str) -> List[str]:
    lower = text.lower()
    return re.findall(r"[\u4e00-\u9fff]|[a-z0-9_]+", lower)


def _hash_embedding(text: str, dim: int = 256) -> List[float]:
    vec = [0.0] * dim
    for tok in _tokenize(text):
        idx = hash(tok) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


async def _openai_embedding(text: str) -> List[float]:
    resp = await llm_client.client.embeddings.create(model=_model(), input=text)
    data = resp.data[0].embedding
    norm = math.sqrt(sum(v * v for v in data))
    if norm > 0:
        data = [v / norm for v in data]
    return data


async def _embed(text: str) -> List[float]:
    text = text.strip()
    if not text:
        return []
    text = text[:2000]
    if _provider() == "openai":
        return await _openai_embedding(text)
    return _hash_embedding(text)


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return -1.0
    if len(a) != len(b):
        return -1.0
    return sum(x * y for x, y in zip(a, b))


@dataclass
class VectorRecord:
    ts: float
    role: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]


class VectorMemory:
    def __init__(self, path: Optional[str] = None):
        self.path = path or _default_store_path()
        self._cache: List[VectorRecord] = []
        self._cache_mtime: float = 0.0
        base_dir = os.path.dirname(self.path)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)

    def _load(self) -> None:
        if not os.path.exists(self.path):
            self._cache = []
            self._cache_mtime = 0.0
            return
        mtime = os.path.getmtime(self.path)
        if mtime == self._cache_mtime and self._cache:
            return
        records: List[VectorRecord] = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    records.append(
                        VectorRecord(
                            ts=float(obj.get("ts", 0.0)),
                            role=str(obj.get("role", "")),
                            content=str(obj.get("content", "")),
                            embedding=obj.get("embedding") or [],
                            metadata=obj.get("metadata") or {},
                        )
                    )
                except Exception:
                    continue
        self._cache = records
        self._cache_mtime = mtime

    async def add(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not _enabled():
            return
        embedding = await _embed(content)
        if not embedding:
            return
        record = {
            "ts": time.time(),
            "role": role,
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._cache_mtime = 0.0

    async def search(self, query: str, top_k: int = 5) -> List[VectorRecord]:
        if not _enabled():
            return []
        self._load()
        q = await _embed(query)
        if not q:
            return []
        scored = []
        for rec in self._cache:
            score = _cosine(q, rec.embedding)
            if score > 0:
                scored.append((score, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [rec for _, rec in scored[:top_k]]

    async def get_context(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        hits = await self.search(query, top_k=top_k)
        if not hits:
            return []
        lines = ["Vector Memory (Relevant):"]
        for rec in hits:
            snippet = rec.content.strip().replace("\n", " ")
            if len(snippet) > 240:
                snippet = snippet[:240] + "..."
            lines.append(f"- [{rec.role}] {snippet}")
        return [{"role": "system", "content": "\n".join(lines)}]


try:
    vector_memory = VectorMemory()
except Exception:
    vector_memory = None

