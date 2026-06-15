#!/usr/bin/env python3
"""End-to-end test: auth → games → predictions → payments."""
import asyncio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BASE_URL = "http://127.0.0.1:8000/api"
TEST_EMAIL = "test.user.123@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Test User"

async def test():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        print("=" * 60)
        print("COURTVISION AI - END-TO-END TEST")
        print("=" * 60)
        
        # 1. Test register
        print("\n[1] REGISTER NEW USER")
        try:
            resp = await client.post("/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": TEST_NAME})
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                user = resp.json()
                print(f"  ✓ Registered: {user.get('email')} | ID: {user.get('id')}")
                test_uid = user.get("id")
            elif resp.status_code == 409:
                print(f"  ℹ User already exists (expected)")
                test_uid = None
            else:
                print(f"  ✗ Error: {resp.text[:200]}")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        # 2. Test login
        print("\n[2] LOGIN")
        try:
            resp = await client.post("/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                user = resp.json()
                print(f"  ✓ Logged in: {user.get('email')} | Role: {user.get('role')}")
                test_uid = user.get("id")
            else:
                print(f"  ✗ Error: {resp.text[:200]}")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        # 3. Test /auth/me
        print("\n[3] GET CURRENT USER (/auth/me)")
        try:
            resp = await client.get("/auth/me", cookies=client.cookies)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                user = resp.json()
                print(f"  ✓ Current user: {user.get('email')}")
            else:
                print(f"  ℹ Status {resp.status_code} (may need to be logged in)")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        # 4. List games
        print("\n[4] LIST GAMES")
        try:
            resp = await client.get("/games")
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                games = resp.json()
                print(f"  ✓ Found {len(games)} games")
                if games:
                    g = games[0]
                    print(f"    Sample: {g.get('id')} | {g.get('home_team_id')} vs {g.get('away_team_id')} | Status: {g.get('status')}")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        # 5. List live games
        print("\n[5] LIST LIVE GAMES")
        try:
            resp = await client.get("/games/live")
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                games = resp.json()
                print(f"  ✓ Found {len(games)} live games")
                if games:
                    g = games[0]
                    print(f"    Sample: {g.get('id')} | {g.get('home_team', {}).get('name')} vs {g.get('away_team', {}).get('name')}")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        # 6. Today's predictions
        print("\n[6] TODAY'S PREDICTIONS")
        try:
            resp = await client.get("/predictions/today")
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                preds = resp.json()
                print(f"  ✓ Found {len(preds)} predictions (threshold-filtered)")
                if preds:
                    p = preds[0]
                    pred = p.get("prediction", {})
                    game = p.get("game", {})
                    print(f"    Sample: {game.get('id')} | Home: {pred.get('home_win_prob', '?'):.2%} | Confidence: {pred.get('confidence')}%")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        # 7. Trending picks
        print("\n[7] TRENDING PICKS")
        try:
            resp = await client.get("/predictions/trending")
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                preds = resp.json()
                print(f"  ✓ Found {len(preds)} trending predictions")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        # 8. Test /admin/api-sports/test
        print("\n[8] API-SPORTS INTEGRATION CHECK")
        try:
            resp = await client.get("/admin/api-sports/test")
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✓ API-Sports: {data.get('status')}")
            else:
                print(f"  ℹ Status {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  ✗ Exception: {e}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

asyncio.run(test())
