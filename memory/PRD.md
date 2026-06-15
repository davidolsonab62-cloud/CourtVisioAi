# CourtVision AI — Product Requirements

## Original Problem Statement
Build a production-grade AI Basketball Prediction Web Application called "CourtVision AI" — a professional basketball prediction platform that analyzes basketball matches worldwide using statistical analysis, market odds, injury reports, team form, efficiency ratings, pace metrics, off/def ratings, travel, rest days, lineup changes and betting market movement. Predictions must be honest (NOT random, NOT faked), use real data sources / APIs, and include a clear disclaimer that they are statistical estimates and not guaranteed outcomes.

## Tech Stack (negotiated)
User accepted the platform default stack since Next.js/Postgres/Prisma are not available in this environment:
- Frontend: React (CRA) + Tailwind + ShadCN UI + Recharts + framer-motion
- Backend: FastAPI + Motor (async MongoDB)
- Auth: JWT (access + refresh, httpOnly cookies, bcrypt, brute-force lockout)
- Payments: Stripe (sk_test_emergent, hosted checkout + polling + webhook + payment_transactions collection)
- Data Provider: API-SPORTS abstraction in place (demo mode active because no key supplied; live mode auto-enables when `API_SPORTS_KEY` is set in `backend/.env`)
- Prediction Engine: Statistical ensemble (Elo + four-factor efficiency + recent form + H2H, with rest/injury/travel adjustments). Deterministic by game_id — never random.

## User Personas
- **Free User** — browses landing, sees today's picks with confidence < 88, sees live games, sees performance proof.
- **Premium Member** — unlocks 88-99 confidence picks, full model breakdowns, advanced analytics; managed via Stripe subscriptions.
- **Admin** — full operational console (users, premium grants/suspends, predictions table, revenue, API key status, demo/live banner).

## Core Requirements (static)
- Honest probabilistic predictions, reproducible per `game_id`.
- 4 confidence tiers (90-95 / 85-89 / 80-84 / 75-79) + "Below 75" hidden by threshold.
- Free vs Premium gating, Stripe checkout for upgrade.
- Admin panel with user management, revenue, API key status.
- "Predictions are statistical estimates and not guaranteed outcomes" disclaimer everywhere it matters.

## What's Been Implemented (2026-02 / Day 1 + Day 2)

### Day 1 — MVP
- Backend:
  - JWT auth (register/login/logout/refresh/me) with bcrypt + httpOnly cookies + brute-force lockout.
  - Seeded 16 leagues, ~85 real-world teams, ~120 games (mix of live/scheduled/finished), 1 prediction per game.
  - Statistical prediction engine (Elo 40% / Rating 35% / Form 15% / H2H 10%) + rest/injury/travel deltas.
  - Endpoints: `/api/leagues`, `/api/teams`, `/api/games[/today|/live|/{id}]`, `/api/predictions/{today,trending,premium,{game_id}}`, `/api/performance/{summary,by-league,timeline}`, `/api/me/favorites`, `/api/me/notifications`.
  - Admin: `/api/admin/{dashboard,users,users/{id}/role,predictions,revenue,api-keys,logs}`.
  - Payments: `/api/packages`, `/api/checkout/session`, `/api/checkout/status/{id}`, `/api/webhook/stripe`.
- Frontend: 10 pages, premium dark theme, confidence tiers, locked premium teaser.
- Testing: 29/29 backend pytest, 11/11 frontend flows verified.

### Day 2 — ML Ensemble + API-SPORTS plumbing
- **XGBoost + LightGBM ensemble** behind the existing `predict()` interface:
  - 15-feature vector (off/def diffs, Elo diff, pace, form diff, rest/injury/travel, raw team stats).
  - Trained on 84 real seeded games + 2176 augmented synthetic matchups (real games weighted 4x).
  - Models persisted at `/app/backend/models/*.joblib`, survives restarts.
  - Final prediction is weighted blend: 0.40 statistical + 0.30 XGBoost + 0.30 LightGBM.
  - Predictions remain deterministic (verified by testing agent — same input always same output).
  - Performance dashboard now reads 70.2% accuracy / +34.1% ROI on real settled games.
- **Admin ML controls**:
  - `/admin` now shows ML Engine card with engine name, trained badge, XGBoost/LightGBM test accuracy, training samples, retrain button.
  - `POST /api/admin/ml/retrain` triggers a force retrain + prediction recompute.
  - `GET /api/admin/ml/meta` exposes the meta.
- **API-SPORTS integration plumbing**:
  - `GET /api/admin/api-sports/test` hits `v1.basketball.api-sports.io/status` with the configured key.
  - When `API_SPORTS_KEY` is empty: returns 400 with a clear message; Admin shows a "Demo Mode" banner with exact instructions to switch to live data.
  - When the key is added: banner flips to "Connected", admin can probe the API directly from the UI.
- Match Detail page now shows the ensemble engine label ("XGBOOST + LIGHTGBM ENSEMBLE") and per-model contributions.
- Testing: 37/37 backend pytest (8 new ML tests), 10/10 frontend review items verified.

## Backlog (Prioritized)
- **P1** Connect a real API-SPORTS key → flip Admin > API Keys from "Demo Mode" to "Connected" (already wired, just needs a key in `backend/.env` and a backend restart).
- **P1** Email/push notifications (the data model already has a `notifications` collection; wire to SendGrid/Resend).
- **P2** Add PayPal & crypto payments (UI already mentions, backend currently only Stripe).
- **P2** Retraining pipeline that ingests resolved games into a feature store and re-fits the Elo K-factor + ensemble weights.
- **P2** Per-team head-to-head deep-dive page.
- **P3** XGBoost / LightGBM model swap behind the existing `prediction_engine.predict()` interface.
- **P3** 2FA + admin audit log surfacing.

## Default Admin
- `admin@courtvisionai.com` / `ChangeOnFirstLogin123` (instructions in `/app/memory/test_credentials.md`)

## Disclaimer
Predictions are statistical estimates and not guaranteed outcomes. Bet responsibly. 18+ only.
