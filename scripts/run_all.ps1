# C:\project\run_all.ps1
# Auto launcher for AI Honeypot (writes logs). Save as UTF-8.
param(
    [string]$ProjectDir = (Join-Path $PSScriptRoot ""),
    [string]$LogDir = (Join-Path $PSScriptRoot "logs")
)

# ensure paths
if (!(Test-Path $ProjectDir)) { Throw "Project dir not found: $ProjectDir" }
New-Item -Path $LogDir -ItemType Directory -Force | Out-Null

$log = Join-Path $LogDir ("run_all_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
function Log($m) { $t = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; "$t`t$m" | Out-File -FilePath $log -Append -Encoding utf8 }

Log "=== run_all.ps1 START ==="
Set-Location $ProjectDir

# venv python executable
$py = Join-Path $ProjectDir ".venv\Scripts\python.exe"

if (!(Test-Path $py)) {
    Log "venv not found. Creating .venv..."
    python -m venv .venv 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
}

Log "Using python: $py"

# Upgrade pip & install requirements (non-failing)
try {
    & $py -m pip install --upgrade pip 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
    & $py -m pip install -r (Join-Path $ProjectDir "requirements.txt") 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
} catch {
    Log "WARNING: pip/install step failed: $_"
}

# Kill previous processes that look like this project (safe attempt)
Get-Process -Name python -ErrorAction SilentlyContinue |
 ForEach-Object {
   try {
     if ($_.Path -and $_.Path -like "*\.venv*") { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue; Log "Stopped old python PID:$($_.Id)" }
   } catch {}
}

Start-Sleep -Milliseconds 500

# Start honeypot backend as a detached process and log output
$honeypotLog = Join-Path $LogDir "honeypot.log"
Log "Starting honeypot (backend/run_honeypot.py) -> $honeypotLog"
Start-Process -FilePath $py -ArgumentList "backend/run_honeypot.py" -WindowStyle Hidden -RedirectStandardOutput $honeypotLog

Start-Sleep -Seconds 1

# Start Streamlit (app_auto.py or streamlit_app.py) as detached process with its own log
$streamlitLog = Join-Path $LogDir "streamlit.log"
$streamlitCmd = "-m streamlit run app_auto.py --server.address=127.0.0.1 --server.port=8501"
Log "Starting Streamlit -> $streamlitLog"
Start-Process -FilePath $py -ArgumentList $streamlitCmd -WindowStyle Hidden -RedirectStandardOutput $streamlitLog

Start-Sleep -Seconds 2

# Open browser to Streamlit (only if interactive session; fails silently in system contexts)
try {
    Start-Process "http://127.0.0.1:8501" -ErrorAction SilentlyContinue
    Log "Attempted to open browser to http://127.0.0.1:8501"
} catch { Log "Could not open browser: $_" }

Log "=== run_all.ps1 END ==="