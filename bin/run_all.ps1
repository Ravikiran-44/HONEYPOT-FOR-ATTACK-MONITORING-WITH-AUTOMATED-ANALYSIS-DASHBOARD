# Copied run_all.ps1 to bin/
# Use original at repository root for primary launcher.
# This copy is provided for convenience.

param(
    [string]$ProjectDir = (Join-Path $PSScriptRoot ".."),
    [string]$LogDir = (Join-Path $PSScriptRoot "..\logs")
)

# Invoke root launcher
& (Join-Path $ProjectDir "run_all.ps1") -ProjectDir $ProjectDir -LogDir $LogDir
