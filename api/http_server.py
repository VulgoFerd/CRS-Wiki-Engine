from __future__ import annotations

from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:
    raise ImportError("FastAPI is required for this module")


from core.engine import CRSWikiEngine
from services.boss_resolver import BossResolver
from services.loot_resolver import LootResolver
from services.entity_linker import EntityLinker


# -----------------------------
# Setup Engine
# -----------------------------

boss_resolver = BossResolver()
loot_resolver = LootResolver()
entity_linker = EntityLinker()

engine = CRSWikiEngine(
    boss_resolver=boss_resolver,
    loot_resolver=loot_resolver,
    entity_linker=entity_linker
)

app = FastAPI(title="CRS Wiki Engine API")


# -----------------------------
# Request Models
# -----------------------------

class WikiRequest(BaseModel):
    query: str
    format: Optional[str] = "json"  # json | markdown


# -----------------------------
# Routes
# -----------------------------

@app.post("/wiki/boss")
def generate_boss_wiki(req: WikiRequest) -> Dict[str, Any]:
    page = engine.generate_boss_wiki(req.query)

    if not page:
        return {
            "success": False,
            "error": "Boss not found"
        }

    if req.format == "markdown":
        return {
            "success": True,
            "format": "markdown",
            "content": engine.generate_markdown(req.query)
        }

    return {
        "success": True,
        "format": "json",
        "data": page
    }


@app.get("/graph/{entity_id}")
def get_graph(entity_id: str) -> Dict[str, Any]:
    return engine.get_entity_graph(entity_id)