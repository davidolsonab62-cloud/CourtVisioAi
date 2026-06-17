"""Basketball data provider abstraction.

Goal: make API replacement painless. We expose a thin interface used by the
rest of the app. When `API_SPORTS_KEY` is configured, calls hit the live
api-sports.io endpoints; otherwise we serve seeded data that lives in our
MongoDB (populated by `seed_runtime.py`).
"""
from __future__ import annotations
import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def is_live_mode() -> bool:
    return bool(os.environ.get("API_SPORTS_KEY"))


async def fetch_live_games(league_external_id: Optional[int] = None) -> list:
    """Optional live fetch from api-sports.io v1.basketball."""
    if not is_live_mode():
        return []
    host = os.environ.get("API_SPORTS_HOST", "v1.basketball.api-sports.io")
    api_key = os.environ["API_SPORTS_KEY"]
    # Support both direct api-sports.io key and RapidAPI key
    headers = {
        "x-apisports-key": api_key,
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": host,
    }
    params = {}
    if league_external_id:
        params["league"] = league_external_id
    url = f"https://{host}/games"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json().get("response", [])
    except Exception as e:
        logger.warning(f"api-sports fetch failed: {e}")
        return []
