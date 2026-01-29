# PowerShell script to download MaxMind GeoLite2-Country database
# Instructions:
# 1. Sign up for free at https://www.maxmind.com/en/geolite2/signup
# 2. Download GeoLite2-Country.mmdb from your account dashboard
# 3. Place the file at C:\project\data\GeoLite2-Country.mmdb
# 4. Or use this script if you have wget/curl available
#
# Alternative: Use curl (built into Windows 10+) if you have a download URL
# curl -o C:\project\data\GeoLite2-Country.mmdb "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-Country&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"

Write-Host "========================================="
Write-Host "MaxMind GeoLite2-Country Database Setup"
Write-Host "========================================="
Write-Host ""
Write-Host "STEP 1: Get Free MaxMind Account"
Write-Host "  - Go to: https://www.maxmind.com/en/geolite2/signup"
Write-Host "  - Create a free account"
Write-Host ""
Write-Host "STEP 2: Download Database"
Write-Host "  - Log in to MaxMind"
Write-Host "  - Navigate to 'Downloads' section"
Write-Host "  - Download 'GeoLite2-Country.mmdb' (binary format)"
Write-Host ""
Write-Host "STEP 3: Place File"
Write-Host "  - Save to: C:\project\data\GeoLite2-Country.mmdb"
Write-Host "  - File size should be ~76 MB"
Write-Host ""
Write-Host "STEP 4: Verify"
Write-Host ""

$dbPath = "C:\project\data\GeoLite2-Country.mmdb"

if (Test-Path $dbPath) {
    $fileSize = (Get-Item $dbPath).Length / 1MB
    Write-Host "✓ Database file found!"
    Write-Host "  Location: $dbPath"
    Write-Host "  Size: $([Math]::Round($fileSize, 2)) MB"
} else {
    Write-Host "✗ Database file not found at $dbPath"
    Write-Host "  Please download and place the file manually."
}
