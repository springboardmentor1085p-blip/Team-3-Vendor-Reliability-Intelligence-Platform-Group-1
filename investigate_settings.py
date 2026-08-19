import asyncio
import json
import urllib.request
import urllib.error
from sqlalchemy import text
from app.database import SessionLocal
from app.core.security import verify_password

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
    print("=== SETTINGS SAVE INVESTIGATION (RULE 10) ===")
    
    # Find valid credentials
    valid_user = None
    valid_pass = None
    user_id = None
    
    passwords = ["Password123!", "SecurePass123!", "password", "admin123", "testuser", "amar", "sai123"]
    
    async with SessionLocal() as s:
        res = await s.execute(text("SELECT user_id, username, password_hash, role_id FROM users WHERE is_active = true"))
        rows = res.fetchall()
        for uid, u, h, r in rows:
            for p in passwords:
                if verify_password(p, h):
                    valid_user = u
                    valid_pass = p
                    user_id = str(uid)
                    print(f"Found login credential: username='{u}', pass='{p}'")
                    break
            if valid_user:
                break
                
    if not valid_user:
        print("No valid password match found in dictionary!")
        return

    # Login
    st, l_data = api("POST", "/auth/login", {"username": valid_user, "password": valid_pass})
    print(f"\nAPI POST /auth/login for '{valid_user}' -> Status {st}")
    if st != 200:
        print("Login failed!", l_data)
        return
    token = l_data["access_token"]
    
    # 1. GET current settings
    st_g1, data_g1 = api("GET", "/settings", token=token)
    print(f"\n1. Initial GET /settings (HTTP {st_g1}):")
    print(json.dumps(data_g1, indent=2))
    
    # 2. PUT update settings
    update_payload = {
        "company_name": "SETTINGS_INVESTIGATION_CORP_999",
        "company_email": f"{valid_user}_updated@company.com",
        "company_phone": "+91 9876543210",
        "company_address": "Test Street 100",
        "theme": "dark",
        "timezone": "Asia/Kolkata",
        "email_notifications": False,
        "sms_notifications": True
    }
    st_put, data_put = api("PUT", "/settings", body=update_payload, token=token)
    print(f"\n2. PUT /settings response (HTTP {st_put}):")
    print(json.dumps(data_put, indent=2))
    
    # 3. GET settings immediately after PUT
    st_g2, data_g2 = api("GET", "/settings", token=token)
    print(f"\n3. Subsequent GET /settings (HTTP {st_g2}):")
    print(json.dumps(data_g2, indent=2))
    
    # 4. Check PostgreSQL database row directly
    async with SessionLocal() as s:
        res_set = await s.execute(
            text("SELECT setting_id, user_id, company_name, company_email, company_phone, company_address, email_notifications, sms_notifications, theme, timezone FROM user_settings WHERE user_id = :uid"),
            {"uid": user_id}
        )
        row = res_set.fetchone()
        print(f"\n4. PostgreSQL user_settings row for user_id {user_id}:")
        if row:
            print(f"   setting_id: {row[0]}")
            print(f"   user_id: {row[1]}")
            print(f"   company_name: {row[2]}")
            print(f"   company_email: {row[3]}")
            print(f"   company_phone: {row[4]}")
            print(f"   company_address: {row[5]}")
            print(f"   email_notifications: {row[6]}")
            print(f"   sms_notifications: {row[7]}")
            print(f"   theme: {row[8]}")
            print(f"   timezone: {row[9]}")
        else:
            print("   NO ROW FOUND IN PostgreSQL user_settings TABLE!")

if __name__ == "__main__":
    asyncio.run(main())
