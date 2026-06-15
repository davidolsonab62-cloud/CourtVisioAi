"""Leagues / Teams / Games / Predictions / Performance routes."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from data_provider import fetch_live_games, is_live_mode
from db import get_db
from prediction_engine import TeamStats, predict as statistical_predict, confidence_tier
from auth import get_optional_user, get_current_user, is_premium

try:
    import ml_engine
except ImportError:
    ml_engine = None

router = APIRouter(prefix="/api", tags=["core"])


def _clean(doc: dict) -> dict:
    if not doc:
        return doc
    doc.pop("_id", None)
    return doc


def _normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return "".join(ch.lower() if ch.isalnum() else " " for ch in text).strip()


async def _build_local_team_lookup(db):
    teams = await db.teams.find({}, {"_id": 0}).to_list(2000)
    lookup = {}
    for t in teams:
        keys = {
            _normalize_text(t.get("name")),
            _normalize_text(t.get("short")),
            _normalize_text(t.get("city")),
        }
        for key in keys:
            if key and key not in lookup:
                lookup[key] = t
    return lookup


def _live_status(raw_status: dict) -> str:
    short = (raw_status or {}).get("short", "").upper()
    if short in {"1H", "2H", "ET", "OT", "P"}:
        return "live"
    if short == "FT":
        return "finished"
    return "scheduled"


def _parse_iso(dt_str: str) -> datetime:
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)


def _map_live_game(raw: dict, team_lookup: dict) -> dict:
    fixture = raw.get("fixture", {})
    league = raw.get("league", {})
    teams = raw.get("teams", {})
    scores = raw.get("scores", {})

    home_raw = teams.get("home", {})
    away_raw = teams.get("away", {})
    home_key = _normalize_text(home_raw.get("name"))
    away_key = _normalize_text(away_raw.get("name"))
    home_local = team_lookup.get(home_key)
    away_local = team_lookup.get(away_key)

    home_team_id = home_local["id"] if home_local else f"api_home_{home_raw.get('id')}"
    away_team_id = away_local["id"] if away_local else f"api_away_{away_raw.get('id')}"

    home_score = scores.get("home", {}).get("points")
    away_score = scores.get("away", {}).get("points")
    winner = None
    if isinstance(home_score, int) and isinstance(away_score, int):
        if home_score > away_score:
            winner = home_team_id
        elif away_score > home_score:
            winner = away_team_id

    home_team = home_local or {
        "id": home_team_id,
        "name": home_raw.get("name"),
        "short": home_raw.get("name"),
        "city": home_raw.get("city"),
        "logo": home_raw.get("logo"),
    }
    away_team = away_local or {
        "id": away_team_id,
        "name": away_raw.get("name"),
        "short": away_raw.get("name"),
        "city": away_raw.get("city"),
        "logo": away_raw.get("logo"),
    }

    league_id = f"api_{league.get('id')}" if league.get('id') is not None else _normalize_text(league.get('name'))
    return {
        "id": f"api_{fixture.get('id')}",
        "league_id": league_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "start_time": fixture.get("date"),
        "status": _live_status(raw.get("status", {})),
        "venue": (fixture.get("venue", {}) or {}).get("name") or (fixture.get("venue", {}) or {}).get("city"),
        "home_score": home_score,
        "away_score": away_score,
        "current_period": raw.get("status", {}).get("long"),
        "winner": winner,
        "home_team": home_team,
        "away_team": away_team,
        "league": {
            "id": league_id,
            "name": league.get("name"),
            "country": league.get("country"),
        },
    }


async def _fetch_live_games(db):
    raw_games = await fetch_live_games()
    if not raw_games:
        return []
    team_lookup = await _build_local_team_lookup(db)
    return [_map_live_game(raw, team_lookup) for raw in raw_games]


def _filter_games(games: list[dict], status: Optional[str] = None, league_id: Optional[str] = None, within_hours: Optional[int] = None):
    now = datetime.now(timezone.utc)
    filtered = []
    for g in games:
        if status and g.get("status") != status:
            continue
        if league_id and g.get("league_id") != league_id:
            continue
        if within_hours is not None:
            try:
                start = _parse_iso(g.get("start_time"))
            except Exception:
                continue
            if start < now or start > (now + timedelta(hours=within_hours)):
                continue
        filtered.append(g)
    return filtered


async def _find_game(db, game_id: str) -> Optional[dict]:
    if is_live_mode():
        games = await _fetch_live_games(db)
        for g in games:
            if g["id"] == game_id:
                return g
    g = await db.games.find_one({"id": game_id}, {"_id": 0})
    return g


async def _predict_live_game(db, game: dict) -> Optional[dict]:
    home = game.get("home_team") or {}
    away = game.get("away_team") or {}
    if not home.get("id") or not away.get("id"):
        return None

    if home["id"].startswith("api_home_") or away["id"].startswith("api_away_"):
        return None

    home_ts = TeamStats(
        id=home["id"],
        name=home.get("name", ""),
        off_rating=home.get("off_rating", 100.0),
        def_rating=home.get("def_rating", 100.0),
        pace=home.get("pace", 75.0),
        elo=home.get("elo", 1500.0),
        form=home.get("form", ""),
        rest_days=2,
        injuries=home.get("injuries", 0),
    )
    away_ts = TeamStats(
        id=away["id"],
        name=away.get("name", ""),
        off_rating=away.get("off_rating", 100.0),
        def_rating=away.get("def_rating", 100.0),
        pace=away.get("pace", 75.0),
        elo=away.get("elo", 1500.0),
        form=away.get("form", ""),
        rest_days=1,
        injuries=away.get("injuries", 0),
        travel_km=1200,
    )
    try:
        result = ml_engine.predict(home_ts, away_ts) if ml_engine else statistical_predict(home_ts, away_ts)
    except Exception:
        result = statistical_predict(home_ts, away_ts)

    market_spread = round(result["predicted_spread"] + 1.0, 1)
    market_total = round(result["predicted_total"] + 1.0, 1)
    edge_spread = abs(result["predicted_spread"] - market_spread)
    is_value = edge_spread >= 1.0 or result["confidence"] >= 85

    return {
        **result,
        "confidence_tier": confidence_tier(result["confidence"]),
        "market_spread": market_spread,
        "market_total": market_total,
        "is_value_bet": is_value,
        "is_safest_pick": result["confidence"] >= 88,
    }


@router.get("/leagues")
async def list_leagues():
    db = get_db()
    leagues = await db.leagues.find({}, {"_id": 0}).to_list(200)
    return leagues


@router.get("/teams")
async def list_teams(league_id: Optional[str] = None):
    db = get_db()
    q = {}
    if league_id:
        q["league_id"] = league_id
    teams = await db.teams.find(q, {"_id": 0}).to_list(2000)
    return teams


@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    db = get_db()
    t = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not t:
        raise HTTPException(404, "Team not found")
    return t


async def _attach_teams(db, games: list) -> list:
    team_ids = set()
    for g in games:
        team_ids.add(g["home_team_id"])
        team_ids.add(g["away_team_id"])
    teams = await db.teams.find({"id": {"$in": list(team_ids)}}, {"_id": 0}).to_list(2000)
    by_id = {t["id"]: t for t in teams}
    leagues = await db.leagues.find({}, {"_id": 0}).to_list(200)
    leagues_by_id = {lg["id"]: lg for lg in leagues}
    for g in games:
        g["home_team"] = by_id.get(g["home_team_id"])
        g["away_team"] = by_id.get(g["away_team_id"])
        g["league"] = leagues_by_id.get(g["league_id"])
    return games


@router.get("/games")
async def list_games(
    status: Optional[str] = None,
    league_id: Optional[str] = None,
    within_hours: Optional[int] = None,
    limit: int = 100,
):
    db = get_db()
    if is_live_mode():
        games = await _fetch_live_games(db)
        results = _filter_games(games, status=status, league_id=league_id, within_hours=within_hours)
        return results[:limit]

    q = {}
    if status:
        q["status"] = status
    if league_id:
        q["league_id"] = league_id
    if within_hours:
        now = datetime.now(timezone.utc)
        until = (now + timedelta(hours=within_hours)).isoformat()
        q["start_time"] = {"$gte": now.isoformat(), "$lte": until}
    games = await db.games.find(q, {"_id": 0}).sort("start_time", 1).to_list(limit)
    games = await _attach_teams(db, games)
    return games


@router.get("/games/live")
async def list_live_games():
    db = get_db()
    if is_live_mode():
        games = await _fetch_live_games(db)
        return _filter_games(games, status="live")
    games = await db.games.find({"status": "live"}, {"_id": 0}).to_list(50)
    games = await _attach_teams(db, games)
    return games


@router.get("/games/today")
async def list_today_games():
    db = get_db()
    if is_live_mode():
        games = await _fetch_live_games(db)
        return _filter_games(games, status=None, within_hours=24)
    now = datetime.now(timezone.utc)
    end = (now + timedelta(hours=24)).isoformat()
    games = await db.games.find(
        {"status": {"$in": ["scheduled", "live"]}, "start_time": {"$gte": now.isoformat(), "$lte": end}},
        {"_id": 0},
    ).sort("start_time", 1).to_list(200)
    games = await _attach_teams(db, games)
    return games


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    db = get_db()
    g = await _find_game(db, game_id)
    if not g:
        raise HTTPException(404, "Game not found")
    if is_live_mode():
        return g
    g = (await _attach_teams(db, [g]))[0]
    return g


@router.get("/predictions/today")
async def todays_predictions(user=Depends(get_optional_user)):
    db = get_db()
    import os
    threshold = int(os.environ.get("CONFIDENCE_THRESHOLD", "75"))
    premium = is_premium(user) if user else False

    if is_live_mode():
        games = await _fetch_live_games(db)
        games = _filter_games(games, within_hours=36)
        out = []
        for g in games:
            p = await _predict_live_game(db, g)
            if not p or p["confidence"] < threshold:
                continue
            if not premium and p["confidence"] >= 88:
                p = {**p, "locked": True, "home_win_prob": None, "away_win_prob": None, "predicted_spread": None}
            else:
                p = {**p, "locked": False}
            out.append({"game": g, "prediction": p})
        return out

    now = datetime.now(timezone.utc)
    end = (now + timedelta(hours=36)).isoformat()
    games = await db.games.find(
        {"status": {"$in": ["scheduled", "live"]}, "start_time": {"$gte": (now - timedelta(hours=4)).isoformat(), "$lte": end}},
        {"_id": 0},
    ).sort("start_time", 1).to_list(200)
    if not games:
        return []
    game_ids = [g["id"] for g in games]
    preds = await db.predictions.find({"game_id": {"$in": game_ids}}, {"_id": 0}).to_list(500)
    by_id = {p["game_id"]: p for p in preds}
    games = await _attach_teams(db, games)
    out = []
    for g in games:
        p = by_id.get(g["id"])
        if not p or p["confidence"] < threshold:
            continue
        # free users only see <=84 confidence; premium sees everything
        if not premium and p["confidence"] >= 88:
            p = {**p, "locked": True, "home_win_prob": None, "away_win_prob": None, "predicted_spread": None}
        else:
            p = {**p, "locked": False}
        out.append({"game": g, "prediction": p})
    return out


@router.get("/predictions/trending")
async def trending_picks(user=Depends(get_optional_user)):
    db = get_db()
    premium = is_premium(user) if user else False

    if is_live_mode():
        games = await _fetch_live_games(db)
        out = []
        for g in _filter_games(games, within_hours=48):
            p = await _predict_live_game(db, g)
            if not p or not p.get("is_value_bet"):
                continue
            if not premium and p["confidence"] >= 88:
                p = {**p, "locked": True, "home_win_prob": None, "away_win_prob": None}
            else:
                p = {**p, "locked": False}
            out.append({"game": g, "prediction": p})
        out.sort(key=lambda item: item["prediction"]["confidence"], reverse=True)
        return out[:8]

    now = datetime.now(timezone.utc)
    end = (now + timedelta(hours=48)).isoformat()
    games = await db.games.find(
        {"status": {"$in": ["scheduled", "live"]}, "start_time": {"$gte": now.isoformat(), "$lte": end}},
        {"_id": 0},
    ).to_list(200)
    if not games:
        return []
    game_ids = [g["id"] for g in games]
    preds = await db.predictions.find({"game_id": {"$in": game_ids}, "is_value_bet": True}, {"_id": 0}).sort("confidence", -1).to_list(8)
    games_by_id = {g["id"]: g for g in games}
    needed = list({p["game_id"] for p in preds})
    enriched = await _attach_teams(db, [games_by_id[i] for i in needed if i in games_by_id])
    by_id = {g["id"]: g for g in enriched}
    out = []
    for p in preds:
        g = by_id.get(p["game_id"])
        if not g:
            continue
        if not premium and p["confidence"] >= 88:
            p = {**p, "locked": True, "home_win_prob": None, "away_win_prob": None}
        else:
            p = {**p, "locked": False}
        out.append({"game": g, "prediction": p})
    return out


@router.get("/predictions/premium")
async def premium_picks(user=Depends(get_optional_user)):
    db = get_db()
    if not is_premium(user):
        # show locked teasers
        if is_live_mode():
            games = await _fetch_live_games(db)
            preds = []
            for g in _filter_games(games, within_hours=72):
                p = await _predict_live_game(db, g)
                if p and p["confidence"] >= 88:
                    preds.append(p)
            preds.sort(key=lambda x: x["confidence"], reverse=True)
            return [{"locked": True, "confidence": p["confidence"], "confidence_tier": p["confidence_tier"]} for p in preds[:6]]
        preds = await db.predictions.find({"confidence": {"$gte": 88}}, {"_id": 0}).sort("confidence", -1).limit(6).to_list(6)
        return [{"locked": True, "confidence": p["confidence"], "confidence_tier": p["confidence_tier"]} for p in preds]

    if is_live_mode():
        games = await _fetch_live_games(db)
        out = []
        for g in _filter_games(games, within_hours=72):
            p = await _predict_live_game(db, g)
            if p and p["confidence"] >= 85:
                out.append({"game": g, "prediction": p})
        out.sort(key=lambda item: item["prediction"]["confidence"], reverse=True)
        return out[:20]

    now = datetime.now(timezone.utc)
    end = (now + timedelta(hours=72)).isoformat()
    games = await db.games.find(
        {"status": {"$in": ["scheduled", "live"]}, "start_time": {"$gte": now.isoformat(), "$lte": end}},
        {"_id": 0},
    ).to_list(300)
    game_ids = [g["id"] for g in games]
    preds = await db.predictions.find({"game_id": {"$in": game_ids}, "confidence": {"$gte": 85}}, {"_id": 0}).sort("confidence", -1).to_list(20)
    games = await _attach_teams(db, games)
    by_gid = {g["id"]: g for g in games}
    return [{"game": by_gid.get(p["game_id"]), "prediction": p} for p in preds if by_gid.get(p["game_id"])]


@router.get("/predictions/{game_id}")
async def get_prediction(game_id: str, user=Depends(get_optional_user)):
    db = get_db()
    if is_live_mode():
        g = await _find_game(db, game_id)
        if not g:
            raise HTTPException(404, "Prediction not found")
        p = await _predict_live_game(db, g)
        if not p:
            raise HTTPException(404, "Prediction not found")
        if not is_premium(user) and p["confidence"] >= 88:
            p = {**p, "locked": True, "model_breakdown": None, "adjustments": None, "predicted_spread": None, "predicted_total": None}
        else:
            p = {**p, "locked": False}
        return {"game": g, "prediction": p}

    p = await db.predictions.find_one({"game_id": game_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Prediction not found")
    g = await db.games.find_one({"id": game_id}, {"_id": 0})
    g = (await _attach_teams(db, [g]))[0] if g else None
    if not is_premium(user) and p["confidence"] >= 88:
        p["locked"] = True
        # still show the winner & confidence but hide odds detail
        p["model_breakdown"] = None
        p["adjustments"] = None
        p["predicted_spread"] = None
        p["predicted_total"] = None
    return {"game": g, "prediction": p}


@router.get("/performance/summary")
async def performance_summary(league_id: Optional[str] = None):
    db = get_db()
    q = {"was_correct": {"$ne": None}}
    if league_id:
        q["league_id"] = league_id
    preds = await db.predictions.find(q, {"_id": 0}).to_list(2000)
    total = len(preds)
    wins = sum(1 for p in preds if p.get("was_correct"))
    losses = total - wins
    accuracy = round(wins / total * 100, 1) if total else 0
    # ROI assuming flat $100 bet at -110 odds when prediction made
    profit = wins * 90.91 - losses * 100.0
    roi = round(profit / (total * 100.0) * 100, 2) if total else 0
    return {
        "total_predictions": total,
        "wins": wins,
        "losses": losses,
        "accuracy": accuracy,
        "roi": roi,
    }


@router.get("/performance/by-league")
async def performance_by_league():
    db = get_db()
    pipeline = [
        {"$match": {"was_correct": {"$ne": None}}},
        {"$group": {
            "_id": "$league_id",
            "total": {"$sum": 1},
            "wins": {"$sum": {"$cond": ["$was_correct", 1, 0]}},
        }},
    ]
    rows = await db.predictions.aggregate(pipeline).to_list(100)
    leagues = await db.leagues.find({}, {"_id": 0}).to_list(200)
    by_id = {lg["id"]: lg for lg in leagues}
    out = []
    for r in rows:
        lg = by_id.get(r["_id"], {"id": r["_id"], "name": r["_id"]})
        acc = round(r["wins"] / r["total"] * 100, 1) if r["total"] else 0
        out.append({"league_id": r["_id"], "league_name": lg.get("name", r["_id"]), "total": r["total"], "wins": r["wins"], "accuracy": acc})
    out.sort(key=lambda x: x["accuracy"], reverse=True)
    return out


@router.get("/performance/timeline")
async def performance_timeline(days: int = 21):
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    games = await db.games.find({"status": "finished", "start_time": {"$gte": cutoff}}, {"_id": 0}).to_list(500)
    game_ids = [g["id"] for g in games]
    preds = await db.predictions.find({"game_id": {"$in": game_ids}, "was_correct": {"$ne": None}}, {"_id": 0}).to_list(2000)
    games_by_id = {g["id"]: g for g in games}
    by_day = {}
    for p in preds:
        g = games_by_id.get(p["game_id"])
        if not g:
            continue
        day = g["start_time"][:10]
        slot = by_day.setdefault(day, {"date": day, "total": 0, "wins": 0, "profit": 0.0})
        slot["total"] += 1
        if p["was_correct"]:
            slot["wins"] += 1
            slot["profit"] += 90.91
        else:
            slot["profit"] -= 100.0
    rows = sorted(by_day.values(), key=lambda r: r["date"])
    cum_profit = 0
    for r in rows:
        cum_profit += r["profit"]
        r["accuracy"] = round(r["wins"] / r["total"] * 100, 1) if r["total"] else 0
        r["cumulative_profit"] = round(cum_profit, 2)
        r["profit"] = round(r["profit"], 2)
    return rows


class FavoritePayload(BaseModel):
    team_id: str


@router.post("/me/favorites")
async def add_favorite(payload: FavoritePayload, user=Depends(get_current_user)):
    db = get_db()
    await db.users.update_one(
        {"email": user["email"]},
        {"$addToSet": {"favorites": payload.team_id}},
    )
    return {"ok": True}


@router.delete("/me/favorites/{team_id}")
async def remove_favorite(team_id: str, user=Depends(get_current_user)):
    db = get_db()
    await db.users.update_one(
        {"email": user["email"]},
        {"$pull": {"favorites": team_id}},
    )
    return {"ok": True}


@router.get("/me/notifications")
async def list_notifications(user=Depends(get_current_user)):
    db = get_db()
    notes = await db.notifications.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    if not notes:
        notes = [
            {"id": "welcome", "title": "Welcome to CourtVision AI", "body": "Your statistical edge across global basketball.", "read": False, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
    return notes
