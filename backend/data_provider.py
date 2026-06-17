"""Basketball data provider abstraction."""
from __future__ import annotations
import os
import logging
from typing import Optional
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)

def is_live_mode():
    return bool(os.environ.get("API_SPORTS_KEY"))

async def _api_get(path, params):
    host = os.environ.get("API_SPORTS_HOST", "v1.basketball.api-sports.io")
    api_key = os.environ["API_SPORTS_KEY"]
    headers = {"x-apisports-key": api_key, "x-rapidapi-key": api_key, "x-rapidapi-host": host}
    url = f"https://{host}/{path}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json().get("response", [])
    except Exception as e:
        logger.warning(f"api-sports fetch failed for {path}: {e}")
        return []

async def fetch_live_games(league_external_id=None):
    if not is_live_mode():
        return []
    all_games = []
    today = datetime.utcnow()
    for i in range(4):
        date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        params = {"date": date, "season": "2024-2025"}
        if league_external_id:
            params["league"] = str(league_external_id)
        all_games.extend(await _api_get("games", params))
    live_games = await _api_get("games", {"live": "all"})
    existing_ids = {g.get("id") for g in all_games}
    for g in live_games:
        if g.get("id") not in existing_ids:
            all_games.append(g)
    return all_games