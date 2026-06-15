"""Runtime seeder: leagues, teams, sample games, and a handful of resolved
historical games used to power the performance dashboard.

Idempotent: safe to run on every startup."""
import logging
import hashlib
from datetime import datetime, timezone, timedelta

from db import get_db
from data_provider import is_live_mode
from seed_data import LEAGUES, TEAMS
from prediction_engine import TeamStats, confidence_tier
try:
    import ml_engine
except ImportError:
    ml_engine = None
from auth import hash_password, verify_password

logger = logging.getLogger(__name__)


def _game_id(home_id: str, away_id: str, dt: datetime) -> str:
    raw = f"{home_id}-{away_id}-{dt.date().isoformat()}"
    return "g_" + hashlib.sha1(raw.encode()).hexdigest()[:14]


async def seed_users():
    db = get_db()
    import os
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@courtvisionai.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "ChangeOnFirstLogin123")
    accounts = [
        (admin_email, admin_password, "CourtVision Admin", "admin"),
        ("user@courtvisionai.com", "User123!", "Free User", "user"),
        ("pro@courtvisionai.com", "Pro123!", "Premium User", "premium"),
    ]
    for email, password, name, role in accounts:
        existing = await db.users.find_one({"email": email})
        if existing is None:
            await db.users.insert_one({
                "email": email,
                "password_hash": hash_password(password),
                "name": name,
                "role": role,
                "favorites": [],
                "premium_until": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        elif not verify_password(password, existing.get("password_hash", "")):
            await db.users.update_one(
                {"email": email},
                {"$set": {"password_hash": hash_password(password), "role": role}},
            )


async def seed_leagues_and_teams():
    db = get_db()
    if await db.leagues.count_documents({}) == 0:
        await db.leagues.insert_many([{**lg} for lg in LEAGUES])
    if await db.teams.count_documents({}) == 0:
        docs = []
        for (tid, lid, name, short, city, off_r, def_r, pace, elo, form) in TEAMS:
            docs.append({
                "id": tid, "league_id": lid, "name": name, "short": short,
                "city": city, "off_rating": off_r, "def_rating": def_r,
                "pace": pace, "elo": elo, "form": form, "injuries": 0,
                "logo": None,
            })
        await db.teams.insert_many(docs)


async def _generate_games():
    """Generate upcoming and live games using actual team pairings.

    We're deterministic: same date + matchup => same game_id."""
    db = get_db()
    
    # Clear seeded games - they should come from live API instead
    await db.games.delete_many({})
    
    if is_live_mode():
        logger.info("Live mode: games will be fetched from API")
        return
    
    logger.info("No API_SPORTS_KEY: not seeding games")
    return

    games = []

    schedule_offsets_hours = {
        "live": [-1, -0.5],                    # currently live
        "today": [3, 6, 9],                    # later today
        "tomorrow": [24, 27, 30, 33],
        "day2": [48, 51, 54],
        "day3": [72, 75],
        "day4": [96],
        "day5": [120],
        "day6": [144],
    }

    def make_pair(league_teams, idx_a, idx_b):
        return league_teams[idx_a % len(league_teams)], league_teams[idx_b % len(league_teams)]

    pairings = [
        # (league, [(home_idx, away_idx), ...])
        ("nba", [(0,1),(2,3),(4,5),(15,16),(17,18),(19,20),(21,22),(23,24),(25,26),(27,28),(8,9),(11,12)]),
        ("wnba", [(0,1),(2,3),(4,5)]),
        ("euroleague", [(0,1),(2,3),(4,5),(6,7)]),
        ("acb", [(0,1),(2,3)]),
        ("lba", [(0,1)]),
        ("bbl", [(0,1)]),
        ("lnb", [(0,1),(1,2)]),
        ("bsl", [(0,1)]),
        ("gbl", [(0,1)]),
        ("nbl_aus", [(0,1),(1,2)]),
        ("jbl", [(0,1)]),
        ("cba", [(0,1)]),
        ("pba", [(0,1)]),
        ("ncaa", [(0,1),(2,3)]),
        ("eurocup", [(0,1)]),
        ("fiba", [(0,1),(2,3)]),
    ]

    # featured real matchup: Paris Basketball vs ASVEL in France Pro A
    lnb_teams = teams_by_league.get("lnb", [])
    par_team = next((t for t in lnb_teams if t["id"] == "par"), None)
    asv_team = next((t for t in lnb_teams if t["id"] == "asv"), None)
    if par_team and asv_team and not _feature_match_exists(games, "par", "asv"):
        start = now + timedelta(hours=4)
        games.append({
            "id": _game_id("par", "asv", start),
            "league_id": "lnb",
            "home_team_id": "par",
            "away_team_id": "asv",
            "start_time": start.isoformat(),
            "status": "scheduled",
            "venue": "Paris Arena",
            "home_score": None,
            "away_score": None,
            "current_period": None,
            "winner": None,
        })

    # distribute pairings across the schedule slots
    all_slots = []
    for bucket, offsets in schedule_offsets_hours.items():
        for off in offsets:
            all_slots.append((bucket, off))

    slot_i = 0
    for league_id, pairs in pairings:
        league_teams = teams_by_league.get(league_id, [])
        if not league_teams:
            continue
        for (a, b) in pairs:
            if slot_i >= len(all_slots):
                slot_i = 0
            bucket, off = all_slots[slot_i]
            slot_i += 1
            start = now + timedelta(hours=off)
            home, away = make_pair(league_teams, a, b)
            gid = _game_id(home["id"], away["id"], start)
            status = "live" if bucket == "live" else "scheduled"
            game = {
                "id": gid,
                "league_id": league_id,
                "home_team_id": home["id"],
                "away_team_id": away["id"],
                "start_time": start.isoformat(),
                "status": status,
                "venue": f"{home['city']} Arena",
                "home_score": None,
                "away_score": None,
                "current_period": None,
                "winner": None,
            }
            if status == "live":
                # synthesize a believable live state
                game["home_score"] = 54 + (hash(gid) % 12)
                game["away_score"] = 50 + (hash(gid + "a") % 14)
                game["current_period"] = "Q3"
            games.append(game)

    # historical resolved games for performance dashboard
    for day_back in range(1, 22):
        bucket_slot = (day_back * 3) % len(pairings)
        for league_id, pairs in pairings[bucket_slot:bucket_slot + 3]:
            league_teams = teams_by_league.get(league_id, [])
            if not league_teams:
                continue
            for (a, b) in pairs[:2]:
                start = now - timedelta(days=day_back, hours=(a + b))
                home, away = make_pair(league_teams, a, b)
                gid = _game_id(home["id"], away["id"], start)
                # base scores from ratings (deterministic), then add ±10 variance
                # using a hash so upsets happen ~30% of the time -> realistic accuracy
                base_h = int(round((home["off_rating"] + away["def_rating"]) / 2 * (home["pace"] / 100)))
                base_a = int(round((away["off_rating"] + home["def_rating"]) / 2 * (away["pace"] / 100)))
                seed = hash(gid)
                home_variance = (seed % 23) - 11
                away_variance = ((seed >> 8) % 23) - 11
                home_score = max(75, base_h + 2 + home_variance)
                away_score = max(73, base_a + away_variance)
                if home_score == away_score:
                    home_score += 2
                winner = home["id"] if home_score > away_score else away["id"]
                games.append({
                    "id": gid,
                    "league_id": league_id,
                    "home_team_id": home["id"],
                    "away_team_id": away["id"],
                    "start_time": start.isoformat(),
                    "status": "finished",
                    "venue": f"{home['city']} Arena",
                    "home_score": home_score,
                    "away_score": away_score,
                    "current_period": "Final",
                    "winner": winner,
                })

    if games:
        await db.games.insert_many(games)


async def _generate_predictions():
    db = get_db()
    
    # Clear seeded predictions - they should be generated from live games
    await db.predictions.delete_many({})
    
    if ml_engine is None:
        logger.warning("Skipping predictions because ml_engine is unavailable")
        return
    
    if is_live_mode():
        logger.info("Live mode: predictions will be generated from live API games")
        return
    
    logger.info("No API_SPORTS_KEY: not seeding predictions")
    return
    # build team lookup
    team_lookup = {t["id"]: t async for t in db.teams.find({})}
    preds = []
    query = {} if not existing_predictions else {"id": {"$nin": existing_predictions}}
    async for g in db.games.find(query):
        h = team_lookup.get(g["home_team_id"])
        a = team_lookup.get(g["away_team_id"])
        if not h or not a:
            continue
        home_ts = TeamStats(
            id=h["id"], name=h["name"], off_rating=h["off_rating"], def_rating=h["def_rating"],
            pace=h["pace"], elo=h["elo"], form=h.get("form", ""), rest_days=2, injuries=h.get("injuries", 0),
        )
        away_ts = TeamStats(
            id=a["id"], name=a["name"], off_rating=a["off_rating"], def_rating=a["def_rating"],
            pace=a["pace"], elo=a["elo"], form=a.get("form", ""), rest_days=1, injuries=a.get("injuries", 0),
            travel_km=1200,
        )
        result = ml_engine.predict(home_ts, away_ts)
        # market line synthesized off our spread, with a 1-pt offset to create value bets
        market_spread = round(result["predicted_spread"] + ((hash(g["id"]) % 3) - 1) * 0.5, 1)
        market_total = round(result["predicted_total"] + ((hash(g["id"]) % 5) - 2) * 0.5, 1)
        edge_spread = abs(result["predicted_spread"] - market_spread)
        is_value = edge_spread >= 1.2 or result["confidence"] >= 88
        tier = confidence_tier(result["confidence"])
        winner_pred = h["id"] if result["home_win_prob"] >= 0.5 else a["id"]
        was_correct = None
        if g.get("status") == "finished":
            was_correct = (winner_pred == g.get("winner"))
        preds.append({
            "game_id": g["id"],
            "league_id": g["league_id"],
            "home_team_id": h["id"],
            "away_team_id": a["id"],
            **result,
            "confidence_tier": tier,
            "predicted_winner_id": winner_pred,
            "market_spread": market_spread,
            "market_total": market_total,
            "is_value_bet": is_value,
            "is_safest_pick": result["confidence"] >= 88,
            "was_correct": was_correct,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    if preds:
        await db.predictions.insert_many(preds)


async def train_ml_models(force: bool = False) -> dict:
    """Train XGBoost + LightGBM models. Idempotent unless force=True."""
    if ml_engine is None:
        logger.warning("Skipping ML training because ml_engine is unavailable")
        return {}
    if ml_engine.is_trained() and not force:
        return ml_engine.load_meta() or {}
    db = get_db()
    teams = await db.teams.find({}, {"_id": 0}).to_list(2000)
    finished = await db.games.find({"status": "finished"}, {"_id": 0}).to_list(2000)
    meta = ml_engine.train(teams, finished)
    ml_engine.reset_models()
    return meta


async def regenerate_predictions():
    """Recompute predictions for ALL games — used after a retrain."""
    db = get_db()
    await db.predictions.delete_many({})
    await _generate_predictions()


async def run_seed():
    await seed_users()
    await seed_leagues_and_teams()
    await _generate_games()
    # Train ML models BEFORE generating predictions so the ensemble runs from day one
    try:
        meta = await train_ml_models()
        logger.info(f"ML models ready: total_samples={meta.get('total_samples')} xgb_acc={meta.get('xgb_test_accuracy')} lgb_acc={meta.get('lgb_test_accuracy')}")
    except Exception as e:
        logger.exception(f"ML training failed; falling back to statistical engine: {e}")
    await _generate_predictions()
    logger.info("Seed complete")
