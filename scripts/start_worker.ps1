$env:PYTHONPATH = "$PWD;$PWD\backend"
& ".\backend\venv\Scripts\celery.exe" -A worker.celery_app worker --loglevel=info --pool=solo
