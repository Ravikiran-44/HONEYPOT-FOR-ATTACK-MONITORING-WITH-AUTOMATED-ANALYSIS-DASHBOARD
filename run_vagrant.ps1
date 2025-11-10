# run_vagrant.ps1
# Usage: Open PowerShell in project root and run: .\run_vagrant.ps1
# This script will:
#  1) run `vagrant up`
#  2) print `vagrant ssh-config`
#  3) print suggested ~/.ssh/config lines to add for VS Code Remote-SSH

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Running: vagrant up (this may take several minutes on first run) ===" -ForegroundColor Cyan
vagrant up

Write-Host "`n=== vagrant ssh-config output ===" -ForegroundColor Cyan
$vagrantSshConfig = vagrant ssh-config 2>&1
Write-Output $vagrantSshConfig

# Parse useful fields from ssh-config (HostName, User, IdentityFile, Port)
function Get-SshConfigValue($text, $key) {
    if ($null -eq $text) { return $null }
    $m = Select-String -InputObject $text -Pattern "^\s*$key\s+(.*)$" -AllMatches
    if ($m -and $m.Matches.Count -gt 0) { return $m.Matches[0].Groups[1].Value.Trim() }
    return $null
}

$hostName = Get-SshConfigValue $vagrantSshConfig "HostName"
$user = Get-SshConfigValue $vagrantSshConfig "User"
$identityFile = Get-SshConfigValue $vagrantSshConfig "IdentityFile"
$port = Get-SshConfigValue $vagrantSshConfig "Port"

Write-Host "`n=== Suggested SSH config lines to add to your ~/.ssh/config or to paste into VS Code Remote-SSH ===" -ForegroundColor Green
Write-Host "`n# --- Add this block to your ~/.ssh/config (or add as a new host in VS Code Remote-SSH) ---`n"

$configBlock = @"
Host vagrant-honeypot
    HostName $hostName
    User $user
    Port $port
    IdentityFile $identityFile
    IdentitiesOnly yes
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
"@

Write-Host $configBlock

Write-Host "=== Next steps ===" -ForegroundColor Yellow
Write-Host "1) Open VS Code → Remote-SSH → Add New SSH Host... and paste the block above (or manually add to ~/.ssh/config)."
Write-Host "2) In VS Code Command Palette: Remote-SSH: Connect to Host... → choose 'vagrant-honeypot'."
Write-Host "3) If VS Code asks to install the server on the remote VM, allow it. Then open the remote folder: /home/vagrant/project"
Write-Host "4) Inside the remote VS Code window run in terminal:"
Write-Host "     source venv/bin/activate"
Write-Host "     pip install -r requirements.txt" -ForegroundColor DarkYellow
Write-Host "     python run_honeypot.py" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "Optional: To create a second attacker VM, copy your Vagrantfile and change the private_network IP (e.g., 192.168.56.11), then run `vagrant up` for that second VM in a different folder." -ForegroundColor Magenta
Write-Host "`nScript finished." -ForegroundColor Cyan
