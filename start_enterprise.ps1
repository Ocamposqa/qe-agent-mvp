# Quantum QE Enterprise Runner

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " STARTING QUANTUM QE ENTERPRISE SUITE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend Telemetry/Agents (Port 8000)
Write-Host "[1/2] Initializing Backend Orchestrator (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\Activate.ps1; uvicorn src.quantum_qe_core.api_server:app --reload --port 8000" -WindowStyle Normal

# 2. Wait a moment
Start-Sleep -Seconds 3

# 3. Start Next.js Frontend (Port 3001 to avoid conflicts with tests)
Write-Host "[2/2] Booting Mission Control Interface (Port 3001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd qe-agent-ui; npm run dev -- -p 3001" -WindowStyle Normal

Write-Host "All systems GO. Access Mission Control Pilot UI at http://localhost:3001" -ForegroundColor Green
