import os

env_path = 'backend/.env'
new_content = """POSTGRES_SERVER=127.0.0.1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=timetable_db
REDIS_URL=redis://127.0.0.1:6379/0
GEMINI_API_KEY=your_gemini_api_key_here
"""

with open(env_path, 'w') as f:
    f.write(new_content)
print("Updated .env template successfully.")
