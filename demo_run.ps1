# demo_run.ps1
# One-command demo runner for AI honeypot project
# Usage: Open PowerShell, cd C:\project, .\demo_run.ps1

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Start-VagrantVM {
    Write-Host "==> Ensuring vagrant VM is up..." -ForegroundColor Cyan
    try {
        vagrant status --machine-readable > $null 2>&1
        vagrant up
    } catch {
        Write-Host "vagrant up failed or not available: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Start-HoneypotVM {
    Write-Host "==> Starting honeypot inside VM (background)..." -ForegroundColor Cyan
    try {
        vagrant ssh -c "cd /home/vagrant/project && source venv/bin/activate || true; nohup ./venv/bin/python run_honeypot.py > /home/vagrant/project/honeypot_vm.log 2>&1 & echo HONEYPOT_STARTED"
    } catch {
        Write-Host "Failed to start honeypot in VM: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Start-StreamlitHost {
    Write-Host "==> Starting streamlit on host (background)..." -ForegroundColor Cyan
    try {
        $streamlitExe = Join-Path $PWD "venv\Scripts\streamlit.exe"
        if (Test-Path $streamlitExe) {
            # Start hidden to avoid a new window popping up
            Start-Process -FilePath $streamlitExe -ArgumentList "run streamlit_app.py --server.port 8501" -WindowStyle Hidden
            Start-Sleep -Seconds 2
            Write-Host "Started streamlit (background)."
        } else {
            Write-Host "Streamlit executable not found in venv. To install run:`n  .\venv\Scripts\Activate.ps1; pip install -r requirements_streamlit.txt" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Error starting streamlit: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Invoke-TestClient {
    Write-Host "==> Running test client to create a session..." -ForegroundColor Cyan
    try {
        # Activate venv if present
        $act = Join-Path $PWD "venv\Scripts\Activate.ps1"
        if (Test-Path $act) { & $act }
        python test_client_interactive.py
    } catch {
        Write-Host "Test client failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Invoke-GenerateReport {
    Write-Host "==> Generating report..." -ForegroundColor Cyan
    try {
        python generate_report.py
        if (Get-Command code -ErrorAction SilentlyContinue) {
            code OUTPUT.md
        } else {
            Start-Process OUTPUT.md
        }
    } catch {
        Write-Host "Report generation failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Flow
Start-VagrantVM
Start-HoneypotVM
Start-StreamlitHost
Start-Sleep -Seconds 2
Invoke-TestClient
Start-Sleep -Seconds 1
Invoke-GenerateReport

Write-Host "`nDemo script finished. Open http://localhost:8501 or OUTPUT.md" -ForegroundColor Green
