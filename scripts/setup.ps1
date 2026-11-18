$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Project Setup..." -ForegroundColor Cyan

# 1. Backend Setup
Write-Host "📦 Setting up Backend..." -ForegroundColor Green
if (!(Test-Path "backend\venv")) {
    Write-Host "Creating Python VENV..."
    python -m venv backend\venv
}

Write-Host "Installing Python Dependencies..."
& ".\backend\venv\Scripts\pip" install -r backend/requirements.txt

# 2. Frontend Setup
Write-Host "🎨 Setting up Frontend..." -ForegroundColor Green
cd frontend
if (!(Test-Path "node_modules")) {
    Write-Host "Installing NPM Packages..."
    npm install
}
cd ..

Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "To run the project:"
Write-Host "1. Start Backend: .\scripts\start_backend.ps1"
Write-Host "2. Start Frontend: .\scripts\start_frontend.ps1"
