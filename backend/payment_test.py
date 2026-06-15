#!/usr/bin/env python3
"""Quick payment flow tester: login -> create checkout -> status."""
import requests
from pathlib import Path
import os

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000/api")
TEST_EMAIL = os.environ.get("TEST_PAYMENT_EMAIL", "test.user.123@example.com")
TEST_PASSWORD = os.environ.get("TEST_PAYMENT_PASSWORD", "TestPass123!")

def main():
    s = requests.Session()
    print('Logging in...')
    r = s.post(f"{BASE}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=20)
    print('Login status:', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text[:400])
    if r.status_code != 200:
        return

    print('\nListing packages...')
    r = s.get(f"{BASE}/packages", timeout=20)
    print('Packages status:', r.status_code)
    pkgs = r.json() if r.status_code == 200 else []
    if not pkgs:
        print('No packages available')
        return
    pkg = pkgs[0]
    print('Using package:', pkg)

    payload = {"package_id": pkg.get('id'), "origin_url": "http://localhost:3001"}
    print('\nCreating checkout session...')
    r = s.post(f"{BASE}/checkout/session", json=payload, timeout=30)
    print('Create session status:', r.status_code)
    try:
        data = r.json()
        print(data)
    except Exception:
        print(r.text[:400])
        return

    session_id = data.get('session_id')
    if not session_id:
        print('No session_id returned; cannot check status')
        return

    print('\nChecking checkout status...')
    r = s.get(f"{BASE}/checkout/status/{session_id}", timeout=20)
    print('Status check:', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text[:400])

if __name__ == '__main__':
    main()
