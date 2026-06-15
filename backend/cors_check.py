#!/usr/bin/env python3
import httpx
from pprint import pprint

BASE = 'http://127.0.0.1:8000/api'

def preflight():
    url = f"{BASE}/checkout/session"
    headers = {
        'Origin': 'http://localhost:3001',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
    }
    with httpx.Client(timeout=10) as c:
        r = c.options(url, headers=headers)
        print('OPTIONS', r.status_code)
        pprint(dict(r.headers))

def post_check():
    url = f"{BASE}/checkout/session"
    headers = {'Origin': 'http://localhost:3001'}
    payload = {"package_id": "weekly", "origin_url": "http://localhost:3001"}
    login_url = f"{BASE}/auth/login"
    creds = {"email": "pro@courtvisionai.com", "password": "Pro123!"}
    with httpx.Client(timeout=20) as c:
        # login first to obtain cookies
        r_login = c.post(login_url, json=creds, headers={'Origin': 'http://localhost:3001'})
        print('\nLOGIN', r_login.status_code)
        try:
            print(r_login.json())
        except Exception:
            print(r_login.text[:400])
        print('Cookies after login:', c.cookies.jar)

        r = c.post(url, json=payload, headers=headers)
        print('\nPOST', r.status_code)
        print('POST headers:')
        from pprint import pprint
        pprint(dict(r.headers))
        try:
            j = r.json()
            print(j)
        except Exception:
            print(r.text[:400])
            j = {}

        # call checkout status to simulate polling/processing
        if j.get('session_id'):
            status_url = f"{BASE}/checkout/status/{j['session_id']}"
            rs = c.get(status_url, headers={'Origin': 'http://localhost:3001'})
            print('\nSTATUS', rs.status_code)
            try:
                print(rs.json())
            except Exception:
                print(rs.text[:400])

    # fetch trending and premium predictions as the logged-in user
    turl = f"{BASE}/predictions/trending"
    purl = f"{BASE}/predictions/premium"
    with httpx.Client(timeout=20) as c2:
        # reuse cookies by performing a request with same domain; we simulate by logging in again
        c2.post(f"{BASE}/auth/login", json={"email": "pro@courtvisionai.com", "password": "Pro123!"}, headers={'Origin': 'http://localhost:3001'})
        rt = c2.get(turl, headers={'Origin': 'http://localhost:3001'})
        print('\nTRENDING', rt.status_code)
        try:
            print(rt.json())
        except Exception:
            print(rt.text[:400])
        rp = c2.get(purl, headers={'Origin': 'http://localhost:3001'})
        print('\nPREMIUM', rp.status_code)
        try:
            print(rp.json())
        except Exception:
            print(rp.text[:400])
    post_check()
