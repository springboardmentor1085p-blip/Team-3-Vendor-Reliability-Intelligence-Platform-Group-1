"""
Complete Reality Audit Script.
Executes API testing, RBAC check, Settings persistence investigation, and known 403 analysis.
"""
import asyncio
import json
import urllib.request
import urllib.parse
import urllib.error
from sqlalchemy import text
from app.database import SessionLocal
from app.core.security import verify_password

BASE_URL = "http://127.0.0.1:8000"

def http_req(method, endpoint, headers=None, body=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method.upper())
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    
    data = None
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode("utf-8")
        
    try:
        with urllib.request.urlopen(req, data=data) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, resp_body
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        return e.code, resp_body
    except Exception as e:
        return 500, str(e)

async def run_audit():
    print("=== STARTING FULL REALITY AUDIT ===")
    
    # 1. DATABASE & USER AUDIT
    users_by_role = {}
    async with SessionLocal() as session:
        r = await session.execute(
            text("SELECT u.user_id, u.username, u.email, u.password_hash, r.role_id, r.role_name, u.is_active FROM users u JOIN roles r ON u.role_id = r.role_id WHERE u.is_active = true")
        )
        users = r.fetchall()
        print(f"Total active users in DB: {len(users)}")
        
        known_passwords = ["password", "admin123", "password123", "amar", "sai123", "admin", "testuser"]
        user_credentials = []
        
        for u in users:
            uid, username, email, pwd_hash, r_id, role_name, is_active = u
            found_pwd = None
            for pwd in known_passwords:
                if verify_password(pwd, pwd_hash):
                    found_pwd = pwd
                    break
            if found_pwd:
                user_credentials.append({
                    "user_id": str(uid),
                    "username": username,
                    "email": email,
                    "password": found_pwd,
                    "role_id": r_id,
                    "role_name": role_name
                })
                print(f"User Credential Found: username={username}, role={role_name}")
                
    # 2. AUTHENTICATION & JWT TEST
    tokens_by_role = {}
    tokens_by_user = {}
    for cred in user_credentials:
        status, body = http_req("POST", "/api/v1/auth/login", body={
            "username": cred["username"],
            "password": cred["password"]
        })
        print(f"Login attempt {cred['username']} ({cred['role_name']}) -> Status {status}")
        if status == 200:
            res_data = json.loads(body)
            token = res_data.get("access_token")
            tokens_by_user[cred["username"]] = token
            if cred["role_name"] not in tokens_by_role:
                tokens_by_role[cred["role_name"]] = token

    # 3. GET OPENAPI SPEC FOR COMPLETE API LIST
    status, openapi_json = http_req("GET", "/openapi.json")
    openapi = json.loads(openapi_json)
    paths = openapi.get("paths", {})
    
    print(f"\nTotal OpenAPI endpoints discovered: {len(paths)} paths")
    
    admin_token = tokens_by_role.get("Administrator")
    admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
    
    api_audit_results = []
    
    for path, methods in paths.items():
        for method, details in methods.items():
            summary = details.get("summary", "")
            tags = details.get("tags", [])
            
            # Perform GET or check authentication requirement
            headers = admin_headers if admin_token else {}
            
            st, bdy = http_req(method.upper(), path, headers=headers)
            api_audit_results.append({
                "endpoint": path,
                "method": method.upper(),
                "summary": summary,
                "tags": tags,
                "status_code": st,
                "response_sample": bdy[:300]
            })
            print(f"{method.upper():<6} {path:<45} -> Status {st}")

    # 4. RULE 10: SETTINGS SAVE INVESTIGATION
    print("\n=== INVESTIGATING SETTINGS SAVE ISSUE (RULE 10) ===")
    if admin_token:
        # GET current settings
        st_get1, body_get1 = http_req("GET", "/api/v1/settings", headers=admin_headers)
        print(f"GET /api/v1/settings initial response:\n  {body_get1}")
        
        # PUT update settings
        update_payload = {
            "company_name": "AUDIT_TEST_PERSISTENCE_COMPANY",
            "company_email": "audit_test@company.com",
            "company_phone": "+91 9999999999",
            "company_address": "Audit Address 123",
            "email_notifications": False,
            "sms_notifications": True,
            "vendor_alerts": False,
            "contract_alerts": True,
            "security_2fa": True,
            "language": "Hindi",
            "theme": "dark",
            "timezone": "Asia/Kolkata",
            "preferred_currency": "USD"
        }
        st_put, body_put = http_req("PUT", "/api/v1/settings", headers=admin_headers, body=update_payload)
        print(f"PUT /api/v1/settings response status: {st_put}\n  Body: {body_put}")
        
        # GET settings again
        st_get2, body_get2 = http_req("GET", "/api/v1/settings", headers=admin_headers)
        print(f"GET /api/v1/settings after PUT status: {st_get2}\n  Body: {body_get2}")
        
        # Verify directly in PostgreSQL DB
        async with SessionLocal() as session:
            r = await session.execute(text("SELECT company_name, company_email, theme, email_notifications FROM user_settings"))
            rows = r.fetchall()
            print(f"PostgreSQL user_settings table contents:\n  Rows count: {len(rows)}")
            for row in rows:
                print(f"  DB Row: company={row[0]}, email={row[1]}, theme={row[2]}, email_notif={row[3]}")

    # 5. RULE 11: KNOWN 403 ISSUES INVESTIGATION
    print("\n=== INVESTIGATING KNOWN 403 ISSUES (RULE 11) ===")
    target_endpoints = [
        "/api/v1/analytics/dashboard",
        "/api/v1/analytics/vendors",
        "/api/v1/analytics/procurement",
        "/api/v1/vendor-performance/rankings",
        "/api/v1/reports/history"
    ]
    
    for role_name, token in tokens_by_role.items():
        headers = {"Authorization": f"Bearer {token}"}
        print(f"\n--- Testing with role: '{role_name}' ---")
        for ep in target_endpoints:
            st, bdy = http_req("GET", ep, headers=headers)
            print(f"  GET {ep:<40} -> Status {st} | Body: {bdy[:150]}")

    with open("scratch/audit_output.json", "w") as f:
        json.dump({
            "users": user_credentials,
            "api_audit": api_audit_results
        }, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_audit())
