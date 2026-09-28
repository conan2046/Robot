$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\windows-common.ps1"

try {
    $code = Invoke-Python -Arguments (@("tools\extract_video_stills.py") + $args)
    if ($code -ne 0) { exit $code }
    exit 0
}
catch {
    Write-Host "STILL GENERATION FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Run setup-video-tools.bat once, then retry."
    exit 1
}
