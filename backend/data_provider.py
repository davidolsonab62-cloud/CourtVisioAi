"""Basketball data provider abstraction."""
from __future__ import annotations
import os
import logging
from typing import Optional
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)


def is_live_mode() -> bool:
    return bool(os.environ.get("API_SPORTS_KEY"))


async def _api_get(path: str, params: dict) -> list:
    """Make a GET request to api-sports.io."""
    host = os.environ.get("API_SPORTS_HOST", "v1.basketball.api-sports.io")
    api_key = os.environ["API_SPORTS_KEY"]
    headers = {
        "x-apisports-key": api_key,
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": host,
    }
    url = f"https://{host}/{path}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json().get("response", [])
    except Exception as e:
        logger.warning(f"api-sports fetch failed for {path}: {e}")
        return []


async def fetch_live_games(league_external_id: Optional[int] = None) -> list:
    """Fetch games from api-sports.io for today and next 3 days."""
    if not is_live_mode():
        return []

    all_games = []
    today = datetime.utcnow()

    # Fetch for today + next 3 days to get upcoming games
    for i in range(4):
        date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        params = {"date": date, "season": "2024-2025"}
        if league_external_id:
            params["league"] = str(league_external_id)
        games = await _api_get("games", params)
        all_games.extend(games)

    # Also fetch live games
    live_params = {"live": "all"}
    live_games = await _api_get("games", live_params)
    # Avoid duplicates
    existing_ids = {g.get("id") for g in all_games}
    for g in live_games:
        if g.get("id") not in existing_ids:
            all_games.append(g)

    logger.info(f"Fetched {len(all_games)} total games from api-sports.io")
    return all_games
