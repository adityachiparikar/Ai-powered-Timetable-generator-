import requests
import sys

try:
    print("Testing API Connectivity...")
    r = requests.get("http://localhost:8000/")
    print(f"Root: {r.status_code} {r.text}")
    
    print("\nAttempting to create a course...")
    payload = {
        "code": "CLI_TEST_01",
        "name": "CLI Test Course",
        "weekly_sessions": 4,
        "course_type": "THEORY"
    }
    r = requests.post("http://localhost:8000/api/v1/courses/", json=payload)
    print(f"Create Course: {r.status_code} {r.text}")
    
except Exception as e:
    print(f"Error: {e}")
