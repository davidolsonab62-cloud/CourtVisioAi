"""ML prediction engine — XGBoost + LightGBM ensemble.

This module sits BEHIND the existing prediction_engine.predict() interface so
the rest of the app does not change. When trained models exist on disk, the
ensemble blends:
   - statistical engine (Elo / four-factor / form / H2H)  — weight 0.40
   - XGBoost classifier (winner)                          — weight 0.30
   - LightGBM classifier (winner)                         — weight 0.30

Plus XGBoost regressors for predicted home/away score.

Training data:
   1. All finished games in the `games` collection (real labels).
   2. Augmented historicals — for every pair of teams we generate plausible
      past matchups by sampling combinations of rest days / travel / injuries
      and deriving the score using the statistical generator's deterministic
      formula plus calibrated noise. Yields ~2000 labelled samples even on a
      fresh database, so XGBoost/LightGBM have something useful to fit.

Models live at /app/backend/models/*.joblib and are reloaded by predict().
"""
from __future__ import annotations
import os
import logging
import hashlib
import math
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

import xgboost as xgb
import lightgbm as lgb

from prediction_engine import TeamStats, predict as statistical_predict, confidence_tier

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)
WIN_MODEL_XGB = MODELS_DIR / "winner_xgb.joblib"
WIN_MODEL_LGB = MODELS_DIR / "winner_lgb.joblib"
HOME_SCORE_MODEL = MODELS_DIR / "home_score_xgb.joblib"
AWAY_SCORE_MODEL = MODELS_DIR / "away_score_xgb.joblib"
META_FILE = MODELS_DIR / "meta.joblib"

FEATURE_NAMES = [
    "off_diff", "def_diff", "net_diff",
    "elo_diff", "pace_avg",
    "form_diff", "rest_diff", "injury_diff", "travel_km_away",
    "home_off", "home_def", "away_off", "away_def",
    "home_elo", "away_elo",
]


# ----------------- Features -----------------

def _form_pct(form: str) -> float:
    if not form:
        return 0.5
    return sum(1 for c in form.upper() if c == "W") / len(form)


def make_features(home: TeamStats, away: TeamStats) -> np.ndarray:
    home_net = home.off_rating - home.def_rating
    away_net = away.off_rating - away.def_rating
    return np.array([
        home.off_rating - away.off_rating,
        away.def_rating - home.def_rating,  # def_diff: lower opp D is good for home
        home_net - away_net,
        home.elo - away.elo,
        (home.pace + away.pace) / 2,
        _form_pct(home.form) - _form_pct(away.form),
        home.rest_days - away.rest_days,
        away.injuries - home.injuries,
        float(away.travel_km),
        home.off_rating, home.def_rating,
        away.off_rating, away.def_rating,
        float(home.elo), float(away.elo),
    ], dtype=np.float32)


# ----------------- Augmented training data -----------------

def _augment_samples(team_dicts: list[dict], n_per_pair: int = 2) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic past matchups for every league's team pairs.

    Outcomes are deterministic from the matchup hash so the training set
    is reproducible; noise comes from a deterministic Linear Congruential
    Generator seeded by a (home,away,k) hash.
    """
    by_league: dict[str, list[dict]] = {}
    for t in team_dicts:
        by_league.setdefault(t["league_id"], []).append(t)

    X = []
    y_winner = []
    y_home_score = []
    y_away_score = []

    for league_id, teams in by_league.items():
        if len(teams) < 2:
            continue
        for i, home in enumerate(teams):
            for j, away in enumerate(teams):
                if i == j:
                    continue
                for k in range(n_per_pair):
                    seed = int(hashlib.sha1(f"{home['id']}-{away['id']}-{k}".encode()).hexdigest()[:8], 16)
                    # Deterministic per-sample noise
                    rest_h = (seed % 4)
                    rest_a = ((seed >> 4) % 4)
                    inj_h = ((seed >> 8) % 3)
                    inj_a = ((seed >> 12) % 3)
                    travel = ((seed >> 16) % 4000) + 200
                    home_ts = TeamStats(
                        id=home["id"], name=home["name"],
                        off_rating=home["off_rating"], def_rating=home["def_rating"],
                        pace=home["pace"], elo=home["elo"], form=home.get("form", ""),
                        rest_days=rest_h, injuries=inj_h,
                    )
                    away_ts = TeamStats(
                        id=away["id"], name=away["name"],
                        off_rating=away["off_rating"], def_rating=away["def_rating"],
                        pace=away["pace"], elo=away["elo"], form=away.get("form", ""),
                        rest_days=rest_a, injuries=inj_a, travel_km=travel,
                    )

                    # Ground-truth score using statistical estimate + bounded noise
                    base = statistical_predict(home_ts, away_ts)
                    noise_h = ((seed >> 20) % 23) - 11
                    noise_a = ((seed >> 8) % 23) - 11
                    h_score = max(70, int(round(base["predicted_home_score"] + noise_h)))
                    a_score = max(68, int(round(base["predicted_away_score"] + noise_a)))
                    if h_score == a_score:
                        h_score += 2
                    winner_is_home = 1 if h_score > a_score else 0

                    X.append(make_features(home_ts, away_ts))
                    y_winner.append(winner_is_home)
                    y_home_score.append(h_score)
                    y_away_score.append(a_score)

    return (
        np.vstack(X),
        np.array(y_winner, dtype=np.int32),
        np.array(y_home_score, dtype=np.float32),
        np.array(y_away_score, dtype=np.float32),
    )


def _real_samples(games: list[dict], team_lookup: dict) -> tuple[list, list, list, list]:
    X, yw, yh, ya = [], [], [], []
    for g in games:
        if g.get("status") != "finished":
            continue
        h = team_lookup.get(g["home_team_id"])
        a = team_lookup.get(g["away_team_id"])
        if not h or not a:
            continue
        home_ts = TeamStats(
            id=h["id"], name=h["name"], off_rating=h["off_rating"], def_rating=h["def_rating"],
            pace=h["pace"], elo=h["elo"], form=h.get("form", ""),
            rest_days=2, injuries=h.get("injuries", 0),
        )
        away_ts = TeamStats(
            id=a["id"], name=a["name"], off_rating=a["off_rating"], def_rating=a["def_rating"],
            pace=a["pace"], elo=a["elo"], form=a.get("form", ""),
            rest_days=1, injuries=a.get("injuries", 0), travel_km=1200,
        )
        X.append(make_features(home_ts, away_ts))
        yw.append(1 if g.get("winner") == h["id"] else 0)
        yh.append(g.get("home_score") or 0)
        ya.append(g.get("away_score") or 0)
    return X, yw, yh, ya


# ----------------- Train / Persist -----------------

def train(team_dicts: list[dict], finished_games: list[dict]) -> dict:
    """Train models and persist to disk. Returns training metrics."""
    team_lookup = {t["id"]: t for t in team_dicts}

    Xr, ywr, yhr, yar = _real_samples(finished_games, team_lookup)
    Xa, ywa, yha, yaa = _augment_samples(team_dicts, n_per_pair=2)

    if Xr:
        X = np.vstack([np.array(Xr, dtype=np.float32), Xa])
        yw = np.concatenate([np.array(ywr, dtype=np.int32), ywa])
        yh = np.concatenate([np.array(yhr, dtype=np.float32), yha])
        ya = np.concatenate([np.array(yar, dtype=np.float32), yaa])
        real_weight = np.concatenate([
            np.full(len(Xr), 4.0, dtype=np.float32),     # real games count 4x
            np.full(len(Xa), 1.0, dtype=np.float32),
        ])
    else:
        X, yw, yh, ya = Xa, ywa, yha, yaa
        real_weight = np.ones(len(X), dtype=np.float32)

    # Simple 90/10 split for honest metric reporting
    rng = np.random.RandomState(42)
    idx = np.arange(len(X))
    rng.shuffle(idx)
    cut = int(len(X) * 0.9)
    tr, te = idx[:cut], idx[cut:]

    # XGBoost classifier
    xgb_clf = xgb.XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
        tree_method="hist", verbosity=0, n_jobs=2,
    )
    xgb_clf.fit(X[tr], yw[tr], sample_weight=real_weight[tr])
    xgb_acc = float((xgb_clf.predict(X[te]) == yw[te]).mean()) if len(te) else None

    # LightGBM classifier
    lgb_clf = lgb.LGBMClassifier(
        n_estimators=400, max_depth=-1, num_leaves=31,
        learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        n_jobs=2, verbosity=-1,
    )
    lgb_clf.fit(X[tr], yw[tr], sample_weight=real_weight[tr])
    lgb_acc = float((lgb_clf.predict(X[te]) == yw[te]).mean()) if len(te) else None

    # Score regressors (XGBoost)
    home_reg = xgb.XGBRegressor(n_estimators=250, max_depth=4, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                                verbosity=0, n_jobs=2)
    home_reg.fit(X[tr], yh[tr], sample_weight=real_weight[tr])
    away_reg = xgb.XGBRegressor(n_estimators=250, max_depth=4, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                                verbosity=0, n_jobs=2)
    away_reg.fit(X[tr], ya[tr], sample_weight=real_weight[tr])

    home_mae = float(np.abs(home_reg.predict(X[te]) - yh[te]).mean()) if len(te) else None
    away_mae = float(np.abs(away_reg.predict(X[te]) - ya[te]).mean()) if len(te) else None

    joblib.dump(xgb_clf, WIN_MODEL_XGB)
    joblib.dump(lgb_clf, WIN_MODEL_LGB)
    joblib.dump(home_reg, HOME_SCORE_MODEL)
    joblib.dump(away_reg, AWAY_SCORE_MODEL)

    from datetime import datetime, timezone
    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "real_samples": len(Xr),
        "augmented_samples": len(Xa),
        "total_samples": len(X),
        "xgb_test_accuracy": xgb_acc,
        "lgb_test_accuracy": lgb_acc,
        "home_score_mae": home_mae,
        "away_score_mae": away_mae,
        "feature_names": FEATURE_NAMES,
        "version": "1.0",
    }
    joblib.dump(meta, META_FILE)
    logger.info(f"ML training complete: {meta}")
    return meta


def is_trained() -> bool:
    return all(p.exists() for p in [WIN_MODEL_XGB, WIN_MODEL_LGB, HOME_SCORE_MODEL, AWAY_SCORE_MODEL])


def load_meta() -> Optional[dict]:
    if META_FILE.exists():
        try:
            return joblib.load(META_FILE)
        except Exception:
            return None
    return None


# ----------------- Predict (ensemble) -----------------

_models: dict = {}


def _ensure_models_loaded():
    if _models:
        return
    if not is_trained():
        return
    _models["xgb"] = joblib.load(WIN_MODEL_XGB)
    _models["lgb"] = joblib.load(WIN_MODEL_LGB)
    _models["home"] = joblib.load(HOME_SCORE_MODEL)
    _models["away"] = joblib.load(AWAY_SCORE_MODEL)
    _models["meta"] = load_meta()


def reset_models():
    _models.clear()


def predict(home: TeamStats, away: TeamStats, h2h_home_wins: int = 0, h2h_games: int = 0) -> dict:
    """Drop-in replacement for prediction_engine.predict().

    Returns the same shape but with an 'engine' field telling the UI which
    pipeline produced the result. Always falls back to the statistical
    engine when ML models are missing.
    """
    stat = statistical_predict(home, away, h2h_home_wins, h2h_games)
    _ensure_models_loaded()
    if not _models:
        stat["engine"] = "statistical-only"
        return stat

    feats = make_features(home, away).reshape(1, -1)
    p_xgb = float(_models["xgb"].predict_proba(feats)[0][1])
    p_lgb = float(_models["lgb"].predict_proba(feats)[0][1])
    p_stat = stat["home_win_prob"]
    p = 0.40 * p_stat + 0.30 * p_xgb + 0.30 * p_lgb
    p = max(0.02, min(0.98, p))

    home_score = float(_models["home"].predict(feats)[0])
    away_score = float(_models["away"].predict(feats)[0])
    # Blend with statistical scores (50/50) — keeps things stable for unseen pairings
    home_score = (home_score + stat["predicted_home_score"]) / 2
    away_score = (away_score + stat["predicted_away_score"]) / 2

    predicted_total = round(home_score + away_score, 1)
    predicted_spread = round(away_score - home_score, 1)

    edge = abs(p - 0.5)
    confidence = max(50, min(99, round(50 + edge * 100)))

    return {
        "home_win_prob": round(p, 4),
        "away_win_prob": round(1 - p, 4),
        "predicted_home_score": round(home_score, 1),
        "predicted_away_score": round(away_score, 1),
        "predicted_total": predicted_total,
        "predicted_spread": predicted_spread,
        "confidence": confidence,
        "first_half_home_prob": round(0.5 + (p - 0.5) * 0.85, 3),
        "first_quarter_home_prob": round(0.5 + (p - 0.5) * 0.70, 3),
        "model_breakdown": {
            "statistical": round(p_stat, 4),
            "xgboost": round(p_xgb, 4),
            "lightgbm": round(p_lgb, 4),
            "elo": stat["model_breakdown"]["elo"],
            "rating": stat["model_breakdown"]["rating"],
        },
        "adjustments": stat["adjustments"],
        "engine": "ensemble-ml",
    }
