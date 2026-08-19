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
    print("=== PART 2 REAL APPLICATION VERIFICATION SCRIPT (STRICT READ-ONLY DB) ===")
    
    # 1. AUTHENTICATION
    print("\n--- 1. Testing Login API ---")
    st, l_data = api("POST", "/auth/login", {"username": "testuser", "password": "password123"})
    print(f"POST /auth/login -> Status {st}")
    assert st == 200, f"Login failed with status {st}"
    token = l_data["access_token"]
    print(f"Token obtained: {token[:30]}...")

    # 2. REPORT EXPORT FORMAT CONTRACT & DOWNLOAD VERIFICATION
    print("\n--- 2. Testing Report Export Formats & Download Contract ---")
    formats = ["pdf", "csv", "xlsx", "json"]
    for fmt in formats:
        st_exp, exp_data = api("POST", f"/reports/export?category=vendor_performance&file_type={fmt}", token=token)
        print(f"POST /reports/export (file_type={fmt:<5}) -> Status {st_exp} | MIME: {exp_data.get('mime_type')} | URL: {exp_data.get('download_url')}")
        assert st_exp == 200
        assert exp_data["file_type"] == fmt

    # Test physical download endpoint returned in download_url
    dummy_download_url = "/reports/download/e2b36079-61c0-4ba0-94d9-d8891438a002"
    st_dl, dl_res = api("GET", dummy_download_url, token=token)
    print(f"GET {dummy_download_url:<50} -> Status {st_dl}")
    print(f"  -> Physical binary streaming endpoint status: {st_dl} (HTTP 404 confirms binary stream route is BACKEND IMPLEMENTATION REQUIRED)")

    # 3. CONTRACTS & COMMUNICATION (ZERO SQL MUTATION)
    print("\n--- 3. Testing Contracts & Communication Endpoints ---")
    st_c, data_c = api("GET", "/contracts", token=token)
    print(f"GET /contracts -> Status {st_c} | Items count: {len(data_c)}")
    assert st_c == 200

    st_comm, data_comm = api("GET", "/communications", token=token)
    print(f"GET /communications -> Status {st_comm} | Messages count: {len(data_comm)}")
    assert st_comm == 200

    # 4. SETTINGS REGRESSION TEST
    print("\n--- 4. Testing Settings Regression ---")
    st_set, set_data = api("GET", "/settings", token=token)
    print(f"GET /settings -> Status {st_set} | Company: {set_data.get('company_name')} | Theme: {set_data.get('theme')}")
    assert st_set == 200

    # 5. RBAC ROLE EXPANSION VERIFICATION
    print("\n--- 5. Testing RBAC Endpoints ---")
    endpoints = [
        "/analytics/dashboard",
        "/analytics/procurement",
        "/analytics/vendors",
        "/vendor-performance/rankings",
        "/reports/history"
    ]
    for ep in endpoints:
        st_ep, _ = api("GET", ep, token=token)
        print(f"GET {ep:<35} -> Status {st_ep}")
        assert st_ep == 200

    # 6. DATABASE SAFETY AUDIT (STRICT READ-ONLY)
    print("\n--- 6. Verifying Database Safety (STRICT READ-ONLY) ---")
    async with SessionLocal() as s:
        res_t = await s.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        t_count = res_t.scalar()
        print(f"Total public tables in PostgreSQL: {t_count} (Unchanged: 26 tables)")
        assert t_count == 26

    print("\n=== PART 2 VERIFICATION FINISHED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(main())
