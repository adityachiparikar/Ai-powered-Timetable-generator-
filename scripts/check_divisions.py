import requests

try:
    r = requests.get('http://localhost:8000/api/v1/student-groups/')
    groups = r.json()
    print(f'Total divisions: {len(groups)}')
    for g in groups:
        print(f"  - {g['name']} (Year {g['year_level']})")
except Exception as e:
    print(f'Error: {e}')
