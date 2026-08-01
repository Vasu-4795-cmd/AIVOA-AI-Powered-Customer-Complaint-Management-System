"""Run this after `pip install -r requirements.txt` and configuring .env to
sanity-check your MySQL connection and Groq API key before starting the
server. Usage: python scripts/check_setup.py (run from the backend/ folder)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings  # noqa: E402


def check_database():
    from sqlalchemy import create_engine, text
    print(f"-> Connecting to DATABASE_URL={settings.database_url}")
    try:
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        engine = create_engine(settings.database_url, connect_args=connect_args)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   OK: database connection succeeded.")
        return True
    except Exception as e:
        print(f"   FAILED: {e}")
        if "mysql" in settings.database_url:
            print("   Hint: did you run `mysql -u root -p < scripts/create_db.sql`?")
            print("   Hint: check host/port/user/password in .env match your MySQL setup.")
        return False


def check_groq_key():
    print("-> Checking GROQ_API_KEY")
    if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key_here":
        print("   FAILED: GROQ_API_KEY is not set in backend/.env")
        print("   Get one at https://console.groq.com/keys")
        return False
    print("   OK: a Groq API key is set (not validated against the live API here).")
    return True


if __name__ == "__main__":
    db_ok = check_database()
    groq_ok = check_groq_key()
    print()
    if db_ok and groq_ok:
        print("All checks passed. Start the server with: uvicorn app.main:app --reload --port 8000")
    else:
        print("Fix the issues above before starting the server.")
        sys.exit(1)
