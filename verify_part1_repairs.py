import asyncio
import json
import urllib.request
import urllib.error
from sqlalchemy import text
from app.database import SessionLocal

BASE = "http://127.0.0.1:8000/api/v1"

def api(method, path, body=None, token=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        try:
            return e.code, json.loads(body_text)
        except Exception:
            return e.code, body_text

async def main():
    print("=== PART 1 REPAIR VERIFICATION SCRIPT ===")
    
    # 1. LOGIN
    print("\n--- 1. Testing Login API ---")
    st, l_data = api("POST", "/auth/login", {"username": "testuser", "password": "password123"})
    print(f"POST /auth/login for 'testuser' -> Status {st}")
    assert st == 200, f"Login failed with status {st}"
    token = l_data["access_token"]
    print(f"Token obtained successfully: {token[:30]}...")

    # 2. SETTINGS DYNAMIC FORM PERSISTENCE TEST
    print("\n--- 2. Testing Settings Update & Persistence ---")
    dynamic_payload = {
        "company_name": "Acme Global Procurement Inc",
        "company_email": "contact@acmeglobal.com",
        "company_phone": "+91 9123456789",
        "company_address": "Financial District, Hyderabad",
        "language": "English",
        "theme": "dark",
        "timezone": "Asia/Kolkata",
        "preferred_currency": "INR",
        "security_2fa": True
    }
    st_put, put_data = api("PUT", "/settings", body=dynamic_payload, token=token)
    print(f"PUT /settings -> Status {st_put}")
    print(f"PUT Response Payload:\n{json.dumps(put_data, indent=2)}")
    assert st_put == 200, f"PUT /settings failed with {st_put}"

    # Verification GET
    st_get, get_data = api("GET", "/settings", token=token)
    print(f"GET /settings -> Status {st_get}")
    assert st_get == 200
    assert get_data["company_name"] == "Acme Global Procurement Inc", f"Company name mismatch: {get_data.get('company_name')}"
    assert get_data["theme"] == "dark", f"Theme mismatch: {get_data.get('theme')}"
    assert get_data["security_2fa"] is True, f"2FA mismatch: {get_data.get('security_2fa')}"
    print("Settings GET verified successfully!")

    # PostgreSQL DB Direct Verification (READ-ONLY)
    async with SessionLocal() as s:
        res = await s.execute(text("SELECT user_id FROM users WHERE username = 'testuser'"))
        uid = res.scalar()
        res_set = await s.execute(
            text("SELECT company_name, theme, security_2fa FROM user_settings WHERE user_id = :uid"),
            {"uid": uid}
        )
        row = res_set.fetchone()
        print(f"Direct PostgreSQL DB Query Result for user {uid}:\n  company_name='{row[0]}', theme='{row[1]}', 2fa={row[2]}")
        assert row[0] == "Acme Global Procurement Inc"
        assert row[1] == "dark"

    # 3. RBAC ROLE EXPANSION VERIFICATION
    print("\n--- 3. Testing RBAC Role Expansion ---")
    async with SessionLocal() as s:
        # Check users with role 'Supply Chain Manager' or 'Finance Officer'
        res_u = await s.execute(
            text("SELECT u.username, r.role_name FROM users u JOIN roles r ON u.role_id = r.role_id WHERE r.role_id IN (2, 3, 5) AND u.is_active = true LIMIT 5")
        )
        role_users = res_u.fetchall()
        print(f"Found active management users: {role_users}")

    # Test protected analytics & report endpoints with token
    endpoints = [
        "/analytics/dashboard",
        "/analytics/procurement",
        "/analytics/vendors",
        "/vendor-performance/rankings",
        "/reports/history"
    ]
    for ep in endpoints:
        st_ep, data_ep = api("GET", ep, token=token)
        print(f"GET {ep:<35} -> Status {st_ep}")
        assert st_ep == 200, f"Endpoint {ep} failed with {st_ep}"

    # 4. REPORT EXPORT & DOWNLOAD TEST
    print("\n--- 4. Testing Report Export & Download Contract ---")
    st_exp, exp_data = api("POST", "/reports/export?category=vendor_performance&file_type=json", token=token)
    print(f"POST /reports/export -> Status {st_exp}")
    print(f"Export Response Payload:\n{json.dumps(exp_data, indent=2)}")
    assert st_exp == 200
    assert "download_url" in exp_data
    assert exp_data["file_type"] == "json"

    # 5. DATABASE SAFETY AUDIT
    print("\n--- 5. Verifying Database Safety (READ-ONLY) ---")
    async with SessionLocal() as s:
        res_t = await s.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        t_count = res_t.scalar()
        print(f"Total public tables in PostgreSQL: {t_count} (Unchanged: 26 tables)")
        assert t_count == 26

    print("\n=== ALL REPAIR VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(main())
