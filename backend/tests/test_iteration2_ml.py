"""CourtVision AI iteration 2 tests — XGBoost+LightGBM ensemble + API-SPORTS endpoint."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

ADMIN = {"email": "admin@courtvisionai.com", "password": "ChangeOnFirstLogin123"}
FREE = {"email": "user@courtvisionai.com", "password": "User123!"}


def _login(s, creds):
    return s.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = _login(s, ADMIN)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def free_session():
    s = requests.Session()
    r = _login(s, FREE)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def anon():
    return requests.Session()


# ---------- ML meta ----------
class TestMLMeta:
    def test_ml_meta_trained_with_metrics(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/ml/meta", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["trained"] is True
        meta = body["meta"]
        assert meta is not None
        assert isinstance(meta.get("xgb_test_accuracy"), float)
        assert isinstance(meta.get("lgb_test_accuracy"), float)
        assert meta.get("total_samples", 0) >= 2000, f"total_samples={meta.get('total_samples')}"
        assert meta.get("real_samples", 0) >= 80, f"real_samples={meta.get('real_samples')}"
        assert isinstance(meta.get("feature_names"), list) and len(meta["feature_names"]) >= 10

    def test_ml_meta_non_admin_forbidden(self, free_session):
        r = free_session.get(f"{BASE_URL}/api/admin/ml/meta", timeout=15)
        assert r.status_code == 403

    def test_ml_retrain_non_admin_forbidden(self, free_session):
        r = free_session.post(f"{BASE_URL}/api/admin/ml/retrain", timeout=15)
        assert r.status_code == 403


# ---------- API-SPORTS test endpoint ----------
class TestAPISports:
    def test_api_sports_no_key_returns_400(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/api-sports/test", timeout=15)
        assert r.status_code == 400, r.text
        detail = r.json().get("detail", "")
        assert "API_SPORTS_KEY" in detail and "not configured" in detail

    def test_api_sports_non_admin_forbidden(self, free_session):
        r = free_session.get(f"{BASE_URL}/api/admin/api-sports/test", timeout=15)
        assert r.status_code == 403


# ---------- Prediction shape & determinism ----------
class TestPredictions:
    def test_engine_and_model_breakdown(self, anon):
        games = anon.get(f"{BASE_URL}/api/games/today", timeout=10).json()
        assert games, "expected at least one game from seed"
        gid = games[0]["id"]
        r = anon.get(f"{BASE_URL}/api/predictions/{gid}", timeout=15)
        assert r.status_code == 200, r.text
        pred = r.json()["prediction"]
        assert pred.get("engine") == "ensemble-ml", f"engine={pred.get('engine')}"
        mb = pred.get("model_breakdown", {})
        for key in ("statistical", "xgboost", "lightgbm", "elo", "rating"):
            assert key in mb, f"missing model_breakdown.{key}: {mb}"

    def test_deterministic_predictions(self, anon):
        games = anon.get(f"{BASE_URL}/api/games/today", timeout=10).json()
        assert games
        gid = games[0]["id"]
        r1 = anon.get(f"{BASE_URL}/api/predictions/{gid}", timeout=15).json()["prediction"]
        r2 = anon.get(f"{BASE_URL}/api/predictions/{gid}", timeout=15).json()["prediction"]
        assert r1["confidence"] == r2["confidence"]
        assert r1["home_win_prob"] == r2["home_win_prob"]
        assert r1["model_breakdown"] == r2["model_breakdown"]


# ---------- Performance still works ----------
class TestPerformance:
    def test_performance_summary_after_retrain(self, anon):
        r = anon.get(f"{BASE_URL}/api/performance/summary", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert 0 <= d["accuracy"] <= 100
        assert "roi" in d
        assert d["total_predictions"] > 0
