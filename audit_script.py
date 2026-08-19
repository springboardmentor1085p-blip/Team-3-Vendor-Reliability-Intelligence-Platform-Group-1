"""
Comprehensive Reality Audit Runner for Vendor Reliability Intelligence Platform.
Tests all endpoints, authentications, permissions, settings persistence, and data flows.
"""
import asyncio
import json
import httpx
from sqlalchemy import text
from app.database import SessionLocal
from app.core.security import verify_password

BASE_URL = "http://127.0.0.1:8000"

async def test_auth_and_get_tokens():
    """Find valid users and login to obtain JWT tokens."""
    tokens = {}
    users_info = {}
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT u.user_id, u.username, u.email, u.password_hash, r.role_name, u.is_active FROM users u JOIN roles r ON u.role_id = r.role_id WHERE u.is_active = true")
        )
        users = result.fetchall()
        print(f"Found {len(users)} active users in PostgreSQL database.")
        
        # Test common passwords to see which user can login
        test_passwords = ["password", "admin123", "password123", "amar", "sai123", "admin", "testuser"]
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            for user in users:
                uid, username, email, pwd_hash, role_name, is_active = user
                matched_pwd = None
                for pwd in test_passwords:
                    if verify_password(pwd, pwd_hash):
                        matched_pwd = pwd
                        break
                
                if matched_pwd:
                    # Attempt actual API login endpoint call
                    login_resp = await client.post(
                        "/api/v1/auth/login",
                        json={"username": username, "password": matched_pwd}
                    )
                    if login_resp.status_code == 200:
                        data = login_resp.json()
                        token = data.get("access_token")
                        tokens[role_name] = token
                        users_info[role_name] = {
                            "username": username,
                            "email": email,
                            "user_id": str(uid),
                            "role_name": role_name,
                            "password": matched_pwd,
                            "token": token
                        }
                        print(f"  [SUCCESS LOGIN] Role: '{role_name}' | User: '{username}' | HTTP {login_resp.status_code}")
                    else:
                        print(f"  [FAILED LOGIN] Role: '{role_name}' | User: '{username}' | HTTP {login_resp.status_code}: {login_resp.text}")
                else:
                    print(f"  [NO KNOWN PWD] User: '{username}' | Role: '{role_name}' | Hash: {pwd_hash[:20]}...")
                    
    return users_info

async def test_all_endpoints(users_info):
    """Test all routes for each role and record results."""
    # Obtain openapi spec to discover all endpoints
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        swagger_resp = await client.get("/openapi.json")
        if swagger_resp.status_code != 200:
            print("Failed to fetch OpenAPI JSON!")
            return
        openapi = swagger_resp.json()
        paths = openapi.get("paths", {})
        
        results = []
        print(f"\nDiscovered {len(paths)} unique URL paths in OpenAPI specification.\n")
        
        # Select an admin token or test user token
        admin_info = users_info.get("Administrator") or users_info.get("Procurement Manager") or list(users_info.values())[0] if users_info else None
        
        for path, methods in paths.items():
            for method, details in methods.items():
                summary = details.get("summary", "")
                tags = details.get("tags", [])
                
                headers = {}
                auth_req = len(details.get("security", [])) > 0 or "auth" not in path
                if auth_req and admin_info:
                    headers["Authorization"] = f"Bearer {admin_info['token']}"
                    
                # Craft sample payload or params if POST/PUT/PATCH
                json_body = None
                if method in ["post", "put", "patch"]:
                    if "/settings" in path and method == "put":
                        json_body = {
                            "company_name": "AUDIT_TEST_CORP_123",
                            "theme": "dark",
                            "timezone": "Asia/Kolkata",
                            "email_notifications": True
                        }
                
                try:
                    req_kwargs = {"headers": headers}
                    if json_body:
                        req_kwargs["json"] = json_body
                        
                    res = await client.request(method.upper(), path, **req_kwargs)
                    results.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": summary,
                        "tags": tags,
                        "status_code": res.status_code,
                        "auth_sent": "Authorization" in headers,
                        "user_tested": admin_info["username"] if admin_info else None,
                        "user_role": admin_info["role_name"] if admin_info else None,
                        "response_preview": res.text[:200]
                    })
                    print(f"  {method.upper():<6} {path:<45} -> HTTP {res.status_code} | Role: {admin_info['role_name'] if admin_info else 'Anon'}")
                except Exception as e:
                    results.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": summary,
                        "status_code": 500,
                        "error": str(e)
                    })
                    print(f"  {method.upper():<6} {path:<45} -> ERROR: {e}")
                    
        with open("scratch/api_audit_results.json", "w") as f:
            json.dump(results, f, indent=2)

async def investigate_settings_save(users_info):
    """Specifically investigate Settings Save issue (Rule 10)."""
    admin_info = users_info.get("Administrator") or list(users_info.values())[0]
    headers = {"Authorization": f"Bearer {admin_info['token']}"}
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        print("\n=== RULE 10: SETTINGS SAVE INVESTIGATION ===")
        # 1. Initial GET
        get1 = await client.get("/api/v1/settings", headers=headers)
        print(f"1. Initial GET /api/v1/settings -> HTTP {get1.status_code}")
        print(f"   Payload: {get1.text}")
        
        # 2. PUT update
        put_payload = {
            "company_name": "UPDATED_COMPANY_TEST",
            "company_email": "updated@company.com",
            "company_phone": "+91 9999999999",
            "theme": "dark",
            "timezone": "UTC",
            "email_notifications": False
        }
        put_res = await client.put("/api/v1/settings", headers=headers, json=put_payload)
        print(f"2. PUT /api/v1/settings -> HTTP {put_res.status_code}")
        print(f"   Response Body: {put_res.text}")
        
        # 3. Subsequent GET
        get2 = await client.get("/api/v1/settings", headers=headers)
        print(f"3. Subsequent GET /api/v1/settings -> HTTP {get2.status_code}")
        print(f"   Response Body: {get2.text}")
        
        # 4. Check DB row directly
        async with SessionLocal() as session:
            db_res = await session.execute(
                text("SELECT user_id, company_name, company_email, company_phone, theme, timezone, email_notifications FROM user_settings WHERE user_id = :uid"),
                {"uid": admin_info["user_id"]}
            )
            row = db_res.fetchone()
            print(f"4. Direct Database query for user {admin_info['user_id']}:")
            print(f"   DB Row: {row}")

async def test_known_403_issues(users_info):
    """Specifically investigate Known 403 endpoints (Rule 11)."""
    endpoints = [
        "/api/v1/analytics/dashboard",
        "/api/v1/analytics/vendors",
        "/api/v1/analytics/procurement",
        "/api/v1/vendor-performance/rankings",
        "/api/v1/reports/history"
    ]
    print("\n=== RULE 11: KNOWN 403 ISSUES INVESTIGATION ===")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for role, user in users_info.items():
            headers = {"Authorization": f"Bearer {user['token']}"}
            print(f"\nTesting User: {user['username']} | Role: '{role}'")
            for ep in endpoints:
                res = await client.get(ep, headers=headers)
                print(f"  GET {ep:<40} -> HTTP {res.status_code} | Body: {res.text[:150]}")

async def main():
    users_info = await test_auth_and_get_tokens()
    await test_all_endpoints(users_info)
    if users_info:
        await investigate_settings_save(users_info)
        await test_known_403_issues(users_info)

if __name__ == "__main__":
    asyncio.run(main())
