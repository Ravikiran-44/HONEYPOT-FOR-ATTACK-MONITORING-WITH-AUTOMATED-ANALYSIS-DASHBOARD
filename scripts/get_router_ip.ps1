# Detect Router Gateway IP (PowerShell Helper)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ROUTER DETECTION HELPER" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get default gateway
$gateway = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Select-Object -First 1).NextHop
Write-Host "Your Default Gateway (Router): $gateway" -ForegroundColor Green

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open browser and go to: http://$gateway" -ForegroundColor White
Write-Host "2. Login with admin credentials (check router label)" -ForegroundColor White
Write-Host "3. Look for 'Port Forwarding' or 'NAT' section" -ForegroundColor White
Write-Host "4. Add rule: External 2222 → 192.168.56.50:2222" -ForegroundColor White
Write-Host "5. Save and REBOOT router" -ForegroundColor White

Write-Host ""
Write-Host "See INTERNET_EXPOSURE_GUIDE.md for your router model" -ForegroundColor Cyan
