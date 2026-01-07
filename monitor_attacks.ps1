# Monitor real attacks in real-time
# Run this after exposing honeypot to internet

$SessionDir = "C:\project\data\sessions"
$LastCheck = 0
$AttackCount = 0

function Get-AttackSummary {
    param($SessionPath)
    
    $metaFile = Join-Path $SessionPath "meta.json"
    if (Test-Path $metaFile) {
        $meta = Get-Content $metaFile | ConvertFrom-Json
        return @{
            ID = $meta.session_id
            Source = $meta.src_ip
            Port = $meta.src_port
            Time = $meta.start_ts
            Events = $meta.events.Count
        }
    }
    return $null
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  🔥 REAL HONEYPOT ATTACK MONITOR 🔥" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Waiting for real attacker sessions..." -ForegroundColor Green
Write-Host "Checking: $SessionDir" -ForegroundColor Gray
Write-Host ""

# Initial count
if (Test-Path $SessionDir) {
    $LastCheck = (Get-ChildItem $SessionDir -Directory).Count
    Write-Host "Starting with $LastCheck existing attacks" -ForegroundColor Gray
}

$CheckInterval = 10

while ($true) {
    $Now = Get-Date
    $CurrentCount = 0
    
    if (Test-Path $SessionDir) {
        $CurrentCount = (Get-ChildItem $SessionDir -Directory).Count
        
        if ($CurrentCount -gt $LastCheck) {
            $NewAttacks = $CurrentCount - $LastCheck
            Write-Host ""
            Write-Host "[$($Now.ToString('HH:mm:ss'))] ⚠️  NEW ATTACK(S) DETECTED! ($NewAttacks new)" -ForegroundColor Red -BackgroundColor Black
            
            # Show latest attacks
            $Latest = Get-ChildItem $SessionDir -Directory | 
                      Sort-Object CreationTime -Descending | 
                      Select-Object -First $NewAttacks
            
            foreach ($session in $Latest) {
                $summary = Get-AttackSummary $session.FullName
                if ($summary) {
                    Write-Host "  ➤ $($summary.ID) from $($summary.Source):$($summary.Port) with $($summary.Events) events" -ForegroundColor Yellow
                }
            }
            
            Write-Host ""
            $LastCheck = $CurrentCount
        }
    }
    
    # Show running count
    Write-Host "[$($Now.ToString('HH:mm:ss'))] Total attacks collected: $CurrentCount" -ForegroundColor Cyan -NoNewline
    Write-Host " | Waiting..." -ForegroundColor Gray
    
    Start-Sleep -Seconds $CheckInterval
}
