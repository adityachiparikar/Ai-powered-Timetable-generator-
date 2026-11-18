$env:PYTHONPATH = "$PWD;$PWD\backend"

Set-Location backend

Write-Host "Running Database Migrations..." -ForegroundColor Green
& ".\venv\Scripts\python.exe" -m alembic upgrade head

Write-Host "Starting Uvicorn Server..." -ForegroundColor Green
& ".\venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --reload
