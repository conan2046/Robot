$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\windows-common.ps1"

try {
    $code = Invoke-Python -Arguments @("tools\serve_local.py")
    exit $code
}
catch {
    Write-Host "LOCAL SERVER FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
