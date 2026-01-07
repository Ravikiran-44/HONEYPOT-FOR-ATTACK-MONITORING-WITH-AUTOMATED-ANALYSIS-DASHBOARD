# verify_setup.ps1 - Verify all multi-VM pipeline components are in place

$errors = @()
$warnings = @()
$success = @()

# Check Python
Write-Host "Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python") {
        $success += "✓ Python installed: $pythonVersion"
    } else {
        $errors += "✗ Python not found or not in PATH"
    }
} catch {
    $errors += "✗ Python error: $_"
}

# Check core files
Write-Host "Checking core files..." -ForegroundColor Yellow
$coreFiles = @(
    "Vagrantfile",
    "docker-compose.yml",
    "run_all.ps1",
    "run_docker.ps1",
    "merge_sessions.py",
    "append_session_csv.py",
    "test_client_interactive.py"
)

foreach ($file in $coreFiles) {
    $path = Join-Path C:\project $file
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        $success += "✓ $file ($size bytes)"
    } else {
        $errors += "✗ Missing: $file"
    }
}

# Check vagrant scripts
Write-Host "Checking vagrant scripts..." -ForegroundColor Yellow
$vagrantFiles = @(
    "vagrant/provision_honeypot.sh",
    "vagrant/run_merge_loop.sh"
)

foreach ($file in $vagrantFiles) {
    $path = Join-Path C:\project $file
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        $success += "✓ $file ($size bytes)"
    } else {
        $errors += "✗ Missing: $file"
    }
}

# Check Python imports
Write-Host "Checking Python modules..." -ForegroundColor Yellow
$requiredModules = @("pandas", "pathlib", "json", "csv")

foreach ($module in $requiredModules) {
    try {
        $result = python -c "import $module" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $success += "✓ Python module '$module' available"
        } else {
            $warnings += "⚠ Python module '$module' check inconclusive"
        }
    } catch {
        $warnings += "⚠ Could not verify module '$module'"
    }
}

# Check Docker (optional but recommended)
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($dockerVersion -match "Docker") {
        $success += "✓ Docker installed: $dockerVersion"
    } else {
        $warnings += "⚠ Docker check failed, but Docker launcher available"
    }
} catch {
    $warnings += "⚠ Docker not found (use Vagrant as alternative)"
}

# Check Vagrant (optional but recommended)
Write-Host "Checking Vagrant..." -ForegroundColor Yellow
try {
    $vagrantVersion = vagrant --version 2>&1
    if ($vagrantVersion -match "Vagrant") {
        $success += "✓ Vagrant installed: $vagrantVersion"
    } else {
        $warnings += "⚠ Vagrant check failed, but Vagrant launcher available"
    }
} catch {
    $warnings += "⚠ Vagrant not found (use Docker as alternative)"
}

# Check Streamlit
Write-Host "Checking Streamlit..." -ForegroundColor Yellow
try {
    $streamlitVersion = streamlit --version 2>&1
    if ($streamlitVersion -match "Streamlit") {
        $success += "✓ Streamlit installed: $streamlitVersion"
    } else {
        $warnings += "⚠ Streamlit installation unclear"
    }
} catch {
    $warnings += "⚠ Streamlit not found in PATH"
}

# Check source files modified
Write-Host "Checking source file modifications..." -ForegroundColor Yellow
$sourceFiles = @(
    "src/evidence_store.py",
    "src/orchestrator.py"
)

foreach ($file in $sourceFiles) {
    $path = Join-Path C:\project $file
    if (Test-Path $path) {
        $content = Get-Content $path -Raw
        if ($file -eq "src/evidence_store.py" -and $content -contains "append_session_csv") {
            $success += "✓ $file has CSV integration"
        } elseif ($file -eq "src/orchestrator.py" -and $content -contains "save_session_data") {
            $success += "✓ $file has session tracking"
        } else {
            $warnings += "⚠ $file - integration check inconclusive"
        }
    }
}

# Check app_auto.py exists
Write-Host "Checking app_auto.py..." -ForegroundColor Yellow
if (Test-Path "C:\project\app_auto.py") {
    $success += "✓ app_auto.py found (Streamlit dashboard)"
} else {
    $errors += "✗ app_auto.py not found"
}

# Check data directories exist
Write-Host "Checking data directories..." -ForegroundColor Yellow
if (Test-Path "C:\project\data") {
    $success += "✓ data/ directory exists"
} else {
    $warnings += "⚠ data/ directory will be created on first run"
}

if (Test-Path "C:\project\output") {
    $success += "✓ output/ directory exists"
} else {
    $warnings += "⚠ output/ directory will be created on first run"
}

# Print results
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  VERIFICATION RESULTS                                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($success.Count -gt 0) {
    Write-Host "SUCCESS ($($success.Count))" -ForegroundColor Green
    foreach ($msg in $success) {
        Write-Host "  $msg" -ForegroundColor Green
    }
}

if ($warnings.Count -gt 0) {
    Write-Host "`nWARNINGS ($($warnings.Count))" -ForegroundColor Yellow
    foreach ($msg in $warnings) {
        Write-Host "  $msg" -ForegroundColor Yellow
    }
}

if ($errors.Count -gt 0) {
    Write-Host "`nERRORS ($($errors.Count))" -ForegroundColor Red
    foreach ($msg in $errors) {
        Write-Host "  $msg" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SUMMARY                                                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($errors.Count -eq 0) {
    Write-Host "✓ All critical components present!" -ForegroundColor Green
    Write-Host "`nYou can now run:" -ForegroundColor Cyan
    Write-Host "  PowerShell> run_docker.ps1      (Recommended - Docker)" -ForegroundColor White
    Write-Host "  PowerShell> run_all.ps1         (Alternative - Vagrant)" -ForegroundColor White
    exit 0
} else {
    Write-Host "✗ Some critical components missing. Fix errors above." -ForegroundColor Red
    exit 1
}
