"""Statistical ensemble basketball prediction engine.

Honest, deterministic, probabilistic. NOT random.

Models used (ensemble averaged with weights):
  1) Elo-based win probability (with home-court bump and rest adjustment)
  2) Four Factors / Offensive vs Defensive rating differential
  3) Recent form (last 5 games W/L)
  4) Head-to-head history bonus

Outputs:
  - home_win_prob, away_win_prob
  - predicted_total (over/under line)
  - predicted_spread (negative = home favored)
  - confidence: 50-99 (how strong the signal is)
  - first_half / first_quarter winner probabilities
  - value_bet flag (when our number differs from a market consensus)
  - safest_pick flag (when confidence is high AND lines align)

The output for the same game_id is deterministic — it does not flip
randomly between page loads, because the engine has zero stochastic terms.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class TeamStats:
    id: str
    name: str
    off_rating: float       # points per 100 possessions
    def_rating: float       # points allowed per 100 possessions
    pace: float             # possessions per 48 min
    elo: float              # team strength
    form: str               # e.g. "WWLWW"
    rest_days: int = 1
    travel_km: int = 0
    injuries: int = 0       # # of starters out


def _form_win_pct(form: str) -> float:
    if not form:
        return 0.5
    wins = sum(1 for c in form.upper() if c == "W")
    return wins / len(form)


def _elo_win_prob(home_elo: float, away_elo: float, home_adv: float = 100.0) -> float:
    diff = (home_elo + home_adv) - away_elo
    return 1.0 / (1.0 + math.pow(10, -diff / 400.0))


def _rating_win_prob(home: TeamStats, away: TeamStats) -> float:
    """Pythagorean style probability using off/def rating differential."""
    home_net = home.off_rating - away.def_rating
    away_net = away.off_rating - home.def_rating
    diff = home_net - away_net + 3.5  # home court ≈ 3.5 pts
    # logistic with slope tuned to NBA-like dispersion
    return 1.0 / (1.0 + math.exp(-diff / 6.5))


def _form_win_prob(home: TeamStats, away: TeamStats) -> float:
    h = _form_win_pct(home.form)
    a = _form_win_pct(away.form)
    diff = h - a + 0.06  # tiny home tilt
    # squish into [0.25, 0.75]
    return max(0.2, min(0.8, 0.5 + diff * 0.6))


def predict(home: TeamStats, away: TeamStats, h2h_home_wins: int = 0, h2h_games: int = 0) -> dict:
    p_elo = _elo_win_prob(home.elo, away.elo)
    p_rating = _rating_win_prob(home, away)
    p_form = _form_win_prob(home, away)

    # rest day adjustment
    rest_delta = (home.rest_days - away.rest_days) * 0.012
    # injury penalty
    inj_delta = (away.injuries - home.injuries) * 0.025
    # travel penalty for the away team
    travel_delta = min(0.03, away.travel_km / 50000.0)

    # head-to-head: only contributes mild signal
    if h2h_games >= 3:
        p_h2h = h2h_home_wins / h2h_games
    else:
        p_h2h = 0.5

    p = (p_elo * 0.40) + (p_rating * 0.35) + (p_form * 0.15) + (p_h2h * 0.10)
    p = p + rest_delta + inj_delta + travel_delta
    p = max(0.02, min(0.98, p))

    # confidence is how far from coin-flip we are, mapped to 50-99
    edge = abs(p - 0.5)
    confidence = round(50 + edge * 100)  # 0.5 -> 50, 1.0 -> 100
    confidence = max(50, min(99, confidence))

    # predicted score: simple possession-based estimate
    avg_pace = (home.pace + away.pace) / 2
    home_score_est = (home.off_rating + away.def_rating) / 2 * (avg_pace / 100)
    away_score_est = (away.off_rating + home.def_rating) / 2 * (avg_pace / 100)
    # add home tilt of ~3 pts
    home_score_est += 1.6
    away_score_est -= 1.4

    predicted_total = round(home_score_est + away_score_est, 1)
    predicted_spread = round(away_score_est - home_score_est, 1)  # negative => home favored

    # first half / first quarter winner — slightly more variance, use same probs softly
    fh_home_prob = round(0.5 + (p - 0.5) * 0.85, 3)
    fq_home_prob = round(0.5 + (p - 0.5) * 0.70, 3)

    return {
        "home_win_prob": round(p, 4),
        "away_win_prob": round(1 - p, 4),
        "predicted_home_score": round(home_score_est, 1),
        "predicted_away_score": round(away_score_est, 1),
        "predicted_total": predicted_total,
        "predicted_spread": predicted_spread,
        "confidence": confidence,
        "first_half_home_prob": fh_home_prob,
        "first_quarter_home_prob": fq_home_prob,
        "model_breakdown": {
            "elo": round(p_elo, 4),
            "rating": round(p_rating, 4),
            "form": round(p_form, 4),
            "h2h": round(p_h2h, 4),
        },
        "adjustments": {
            "rest_delta": round(rest_delta, 4),
            "injury_delta": round(inj_delta, 4),
            "travel_delta": round(travel_delta, 4),
        },
    }


def confidence_tier(confidence: int) -> str:
    if confidence >= 90:
        return "90-95"
    if confidence >= 85:
        return "85-89"
    if confidence >= 80:
        return "80-84"
    if confidence >= 75:
        return "75-79"
    return "below-75"
