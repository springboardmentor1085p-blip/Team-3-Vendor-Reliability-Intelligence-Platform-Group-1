import asyncio
from sqlalchemy import text
from app.database import SessionLocal
from app.core.security import verify_password

async def main():
    async with SessionLocal() as s:
        res = await s.execute(text("SELECT username, email, password_hash, role_id FROM users WHERE is_active = true"))
        users = res.fetchall()
        print(f"Total active users: {len(users)}")
        
        passwords_to_try = [
            "password", "admin123", "password123", "amar", "sai123", "sai", "admin", "testuser",
            "Pass@123", "Admin@123", "123456", "secret", "user123", "manager123"
        ]
        
        matched_users = []
        for u, email, h, r in users:
            for p in passwords_to_try:
                try:
                    if verify_password(p, h):
                        print(f"MATCH: username='{u}' | email='{email}' | pwd='{p}' | role_id={r}")
                        matched_users.append((u, p, r))
                        break
                except Exception as e:
                    pass
        print(f"\nTotal matched users: {len(matched_users)}")

if __name__ == "__main__":
    asyncio.run(main())
