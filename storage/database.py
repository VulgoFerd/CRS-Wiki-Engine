from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path
import json
import os


class Database:
    """
    Lightweight persistence layer for CRS Wiki Engine.

    Current implementation:
    - JSON-based storage (fast + simple)
    - Designed to be replaceable by SQLite/Postgres later

    Responsibilities:
    - Store indexed dataset
    - Cache resolved entities
    - Persist wiki outputs
    """

    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, Any] = {}

    # -----------------------------
    # Generic IO
    # -----------------------------

    def save(self, key: str, data: Any) -> None:
        path = self._path(key)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._cache[key] = data

    def load(self, key: str) -> Optional[Any]:
        if key in self._cache:
            return self._cache[key]

        path = self._path(key)

        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._cache[key] = data
        return data

    def delete(self, key: str) -> None:
        path = self._path(key)

        if path.exists():
            path.unlink()

        self._cache.pop(key, None)

    # -----------------------------
    # Helpers
    # -----------------------------

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_path / f"{safe_key}.json"

    # -----------------------------
    # High-level helpers (CRS-specific)
    # -----------------------------

    def save_index(self, index: Dict[str, Any]) -> None:
        self.save("indexed_dataset", index)

    def load_index(self) -> Optional[Dict[str, Any]]:
        return self.load("indexed_dataset")

    def save_wiki_page(self, boss_id: str, page: Dict[str, Any]) -> None:
        self.save(f"wiki_{boss_id}", page)

    def load_wiki_page(self, boss_id: str) -> Optional[Dict[str, Any]]:
        return self.load(f"wiki_{boss_id}")