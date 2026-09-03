#!/usr/bin/env python3
"""
seed_users.py
Creates two demo users:
  employee1 / employee123  (role: employee — can write data)
  manager1  / manager123   (role: manager  — read-only view)

Run locally or against deployed app:
  python seed_users.py
  python seed_users.py https://carbon-calculation.onrender.com
"""

import os
import sys
import requests

DEFAULT_URL = "http://127.0.0.1:8000"
ENV_URL = os.environ.get("BASE_URL")
CLI_URL = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("http") else None
BASE_URL = (ENV_URL or CLI_URL or DEFAULT_URL).rstrip("/")

USERS = [
    {"username": "employee1", "password": "employee123", "role": "employee"},
    {"username": "manager1",  "password": "manager123",  "role": "manager"},
]

def seed_local_db():
    try:
        from database import SessionLocal, engine, Base
        import models
        import auth
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        for u in USERS:
            existing = db.query(models.User).filter(models.User.username == u["username"]).first()
            if not existing:
                db.add(models.User(
                    username=u["username"],
                    hashed_password=auth.hash_password(u["password"]),
                    role=u["role"]
                ))
                db.commit()
                print(f"  [Local DB] Created user '{u['username']}' ({u['role']})")
            else:
                print(f"  [Local DB] User '{u['username']}' already exists")
        db.close()
    except Exception as e:
        print(f"  [Local DB note]: {e}")

def main():
    print(f"--- Seeding Demo Users ---")
    
    # Always ensure local DB is updated if in local project directory
    if os.path.exists("database.py"):
        seed_local_db()

    # If targeting remote or running server, also call the API
    if CLI_URL or ENV_URL or BASE_URL.startswith("https://"):
        target = BASE_URL
    else:
        target = "http://127.0.0.1:8000"

    print(f"\nChecking API endpoint at {target}...")
    try:
        res = requests.get(f"{target}/emissions/summary", timeout=30)
        api_available = res.status_code == 200
    except Exception:
        api_available = False

    if api_available:
        for user in USERS:
            try:
                res = requests.post(f"{target}/auth/seed-user", json=user, timeout=15)
                if res.status_code == 201:
                    print(f"  [API Created] {user['username']} ({user['role']})")
                elif res.status_code == 409:
                    print(f"  [API Exists]  {user['username']} ({user['role']})")
                else:
                    print(f"  [API Error]   {user['username']}: HTTP {res.status_code}")
            except Exception as e:
                print(f"  [API Error]   {user['username']}: {e}")

        print("\nVerifying login via API...")
        for user in USERS:
            try:
                res = requests.post(
                    f"{target}/auth/login",
                    data={"username": user["username"], "password": user["password"]},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=15,
                )
                if res.status_code == 200:
                    data = res.json()
                    print(f"  [OK] {user['username']} -> role={data['role']}, token={data['access_token'][:20]}...")
                else:
                    print(f"  [FAIL] {user['username']}: HTTP {res.status_code}")
            except Exception as e:
                print(f"  [FAIL] {user['username']}: {e}")
    else:
        print(f"  (API at {target} not running or unreachable — local DB was updated)")

    print("\nUsers configured:")
    print("  Employee: employee1 / employee123 (Write + Read)")
    print("  Manager:  manager1  / manager123  (View-only)")

if __name__ == "__main__":
    main()
