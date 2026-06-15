"""CourtVision AI backend tests covering auth, core APIs, admin, and payments."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hoops-predict-1.preview.emergentagent.com").rstrip("/")

ADMIN = {"email": "admin@courtvisionai.com", "password": "ChangeOnFirstLogin123"}
PRO = {"email": "pro@courtvisionai.com", "password": "Pro123!"}
FREE = {"email": "user@courtvisionai.com", "password": "User123!"}


def _login(session: requests.Session, creds: dict) -> requests.Response:
    return session.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)


@pytest.fixture(scope="module")
def anon():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = _login(s, ADMIN)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def pro_session():
    s = requests.Session()
    r = _login(s, PRO)
    assert r.status_code == 200, f"pro login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def free_session():
    s = requests.Session()
    r = _login(s, FREE)
    assert r.status_code == 200, f"free login failed: {r.status_code} {r.text}"
    return s


# ---------- Health ----------
def test_health(anon):
    r = anon.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- Auth ----------
class TestAuth:
    def test_admin_login_sets_cookies(self):
        s = requests.Session()
        r = _login(s, ADMIN)
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == ADMIN["email"]
        assert body["role"] == "admin"
        # cookies should be set
        cookies = {c.name: c for c in s.cookies}
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    def test_pro_login(self):
        s = requests.Session()
        r = _login(s, PRO)
        assert r.status_code == 200
        body = r.json()
        assert body["role"] == "premium"
        assert body["is_premium"] is True

    def test_invalid_login(self):
        s = requests.Session()
        r = _login(s, {"email": "admin@courtvisionai.com", "password": "wrong"})
        assert r.status_code == 401

    def test_me_endpoint(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 200
        assert r.json()["email"] == ADMIN["email"]

    def test_me_unauth(self, anon):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert r.status_code == 401

    def test_register_and_login(self):
        import uuid
        email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/auth/register", json={
            "email": email, "password": "Testpass123!", "name": "Test User",
        }, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["email"] == email.lower()
        assert body["role"] == "user"
        # Should be logged in via cookie
        me = s.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert me.status_code == 200


# ---------- Core ----------
class TestCore:
    def test_leagues(self, anon):
        r = anon.get(f"{BASE_URL}/api/leagues", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0

    def test_teams(self, anon):
        r = anon.get(f"{BASE_URL}/api/teams", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 10
        # ensure no leaked mongodb _id
        assert all("_id" not in t for t in data)

    def test_games_today(self, anon):
        r = anon.get(f"{BASE_URL}/api/games/today", timeout=10)
        assert r.status_code == 200
        games = r.json()
        assert isinstance(games, list)
        # there should be at least some live or scheduled games due to seed
        if games:
            g = games[0]
            assert "home_team" in g and g["home_team"] is not None
            assert "away_team" in g and g["away_team"] is not None
            assert "league" in g

    def test_predictions_today_threshold(self, anon):
        r = anon.get(f"{BASE_URL}/api/predictions/today", timeout=15)
        assert r.status_code == 200
        preds = r.json()
        for item in preds:
            assert item["prediction"]["confidence"] >= 75

    def test_predictions_today_locks_for_anon(self, anon):
        """Anon (non-premium) users must see locked=true for confidence>=88."""
        r = anon.get(f"{BASE_URL}/api/predictions/today", timeout=15)
        assert r.status_code == 200
        for item in r.json():
            conf = item["prediction"]["confidence"]
            if conf >= 88:
                assert item["prediction"]["locked"] is True
                assert item["prediction"]["home_win_prob"] is None

    def test_predictions_today_full_for_premium(self, pro_session):
        r = pro_session.get(f"{BASE_URL}/api/predictions/today", timeout=15)
        assert r.status_code == 200
        for item in r.json():
            # premium user should never see locked=True
            assert item["prediction"]["locked"] is False
            assert item["prediction"]["home_win_prob"] is not None

    def test_premium_picks_locked_for_anon(self, anon):
        r = anon.get(f"{BASE_URL}/api/predictions/premium", timeout=10)
        assert r.status_code == 200
        data = r.json()
        for item in data:
            assert item.get("locked") is True

    def test_premium_picks_full_for_pro(self, pro_session):
        r = pro_session.get(f"{BASE_URL}/api/predictions/premium", timeout=10)
        assert r.status_code == 200
        data = r.json()
        # should not be locked teaser shape
        for item in data:
            assert "game" in item
            assert "prediction" in item

    def test_prediction_determinism(self, anon):
        """Same game_id must return identical prediction across calls."""
        games = anon.get(f"{BASE_URL}/api/games/today", timeout=10).json()
        if not games:
            pytest.skip("no scheduled games to test determinism")
        gid = games[0]["id"]
        r1 = anon.get(f"{BASE_URL}/api/predictions/{gid}", timeout=10)
        r2 = anon.get(f"{BASE_URL}/api/predictions/{gid}", timeout=10)
        assert r1.status_code == 200 and r2.status_code == 200
        p1 = r1.json()["prediction"]
        p2 = r2.json()["prediction"]
        assert p1["confidence"] == p2["confidence"]
        assert p1.get("predicted_winner_id") == p2.get("predicted_winner_id")

    def test_performance_summary(self, anon):
        r = anon.get(f"{BASE_URL}/api/performance/summary", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "accuracy" in d and "roi" in d
        # seed expects ~60-70% accuracy
        assert 0 <= d["accuracy"] <= 100
        assert d["total_predictions"] > 0

    def test_performance_by_league(self, anon):
        r = anon.get(f"{BASE_URL}/api/performance/by-league", timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_performance_timeline(self, anon):
        r = anon.get(f"{BASE_URL}/api/performance/timeline", timeout=10)
        assert r.status_code == 200
        rows = r.json()
        if rows:
            assert "cumulative_profit" in rows[0]
            assert "accuracy" in rows[0]


# ---------- Admin ----------
class TestAdmin:
    def test_admin_dashboard(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/dashboard", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["total_users"] >= 3

    def test_admin_users_list(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/users", timeout=10)
        assert r.status_code == 200
        users = r.json()
        emails = [u["email"] for u in users]
        assert ADMIN["email"] in emails
        # no _id should leak (we map to id)
        assert all("_id" not in u for u in users)

    def test_admin_api_keys_demo_mode(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/api-keys", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["api_sports"]["configured"] is False  # demo mode
        assert d["stripe"]["configured"] is True

    def test_non_admin_forbidden(self, free_session):
        r = free_session.get(f"{BASE_URL}/api/admin/dashboard", timeout=10)
        assert r.status_code == 403

    def test_anon_forbidden(self):
        r = requests.get(f"{BASE_URL}/api/admin/dashboard", timeout=10)
        assert r.status_code == 401

    def test_grant_premium_role(self, admin_session):
        # find the free user
        users = admin_session.get(f"{BASE_URL}/api/admin/users", timeout=10).json()
        free = next(u for u in users if u["email"] == FREE["email"])
        original_role = free["role"]
        r = admin_session.patch(
            f"{BASE_URL}/api/admin/users/{free['id']}/role",
            json={"role": "premium"}, timeout=10
        )
        assert r.status_code == 200
        # verify persisted
        users2 = admin_session.get(f"{BASE_URL}/api/admin/users", timeout=10).json()
        free2 = next(u for u in users2 if u["email"] == FREE["email"])
        assert free2["role"] == "premium"
        # revert so other tests stay sane
        admin_session.patch(
            f"{BASE_URL}/api/admin/users/{free['id']}/role",
            json={"role": original_role}, timeout=10
        )


# ---------- Payments ----------
class TestPayments:
    def test_packages_list(self, anon):
        r = anon.get(f"{BASE_URL}/api/packages", timeout=10)
        assert r.status_code == 200
        pkgs = r.json()
        ids = [p["id"] for p in pkgs]
        assert set(["weekly", "monthly", "quarterly", "yearly"]).issubset(set(ids))

    def test_checkout_unauth(self):
        r = requests.post(f"{BASE_URL}/api/checkout/session", json={
            "package_id": "weekly", "origin_url": BASE_URL,
        }, timeout=10)
        assert r.status_code == 401

    def test_checkout_invalid_package(self, pro_session):
        r = pro_session.post(f"{BASE_URL}/api/checkout/session", json={
            "package_id": "bogus", "origin_url": BASE_URL,
        }, timeout=15)
        assert r.status_code == 400

    def test_checkout_creates_session_and_pending_txn(self, pro_session):
        r = pro_session.post(f"{BASE_URL}/api/checkout/session", json={
            "package_id": "weekly", "origin_url": BASE_URL,
        }, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "url" in data and data["url"].startswith("http")
        assert "session_id" in data and data["session_id"]
