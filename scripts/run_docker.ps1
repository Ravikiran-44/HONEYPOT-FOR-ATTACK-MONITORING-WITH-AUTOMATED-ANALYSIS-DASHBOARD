# run_docker.ps1: Windows PowerShell script to bring up Docker containers and Streamlit
cd C:\project

Write-Host "================================" -ForegroundColor Cyan
Write-Host "HONEYPOT DOCKER MULTI-INSTANCE" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "[✓] Docker found" -ForegroundColor Green
} catch {
    Write-Host "[✗] Docker not found. Install Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Start Docker containers
Write-Host "`n[*] Starting 5 honeypot containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "[✓] Containers started. Waiting 30 seconds for initialization..." -ForegroundColor Green
Start-Sleep -Seconds 30

# Start periodic aggregator in background
Write-Host "[*] Starting aggregator (every 5 seconds)..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "while(`$true){ python .\merge_sessions.py ; Start-Sleep -Seconds 5 }" -WindowStyle Hidden

# Start Streamlit
Write-Host "[✓] Starting Streamlit dashboard..." -ForegroundColor Green
Write-Host "`n" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "SERVICES RUNNING:" -ForegroundColor Cyan
Write-Host "  Honeypot 1: localhost:2222" -ForegroundColor Green
Write-Host "  Honeypot 2: localhost:2223" -ForegroundColor Green
Write-Host "  Honeypot 3: localhost:2224" -ForegroundColor Green
Write-Host "  Honeypot 4: localhost:2225" -ForegroundColor Green
Write-Host "  Honeypot 5: localhost:2226" -ForegroundColor Green
Write-Host "  Dashboard:  http://localhost:8501" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host "`n"

streamlit run app_auto.py
