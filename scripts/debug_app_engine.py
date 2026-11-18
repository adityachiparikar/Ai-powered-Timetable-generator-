
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import engine
from sqlalchemy import text

print(f"Connecting with URI: {engine.url}")

try:
    with engine.connect() as conn:
        print("✅ Connection Successful!")
        result = conn.execute(text("SELECT 1"))
        print(f"Result: {result.scalar()}")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
