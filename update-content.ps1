$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\windows-common.ps1"

try {
    Write-Host "========================================"
    Write-Host "  Step 1/2: Generate video stills"
    Write-Host "========================================"
    $code = Invoke-Python -Arguments @("tools\extract_video_stills.py")
    if ($code -ne 0) {
        Write-Host "[WARNING] Video still generation returned exit code $code. Site data generation will continue." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "========================================"
    Write-Host "  Step 2/2: Build site data"
    Write-Host "========================================"
    $buildArgs = @("tools\build_content.py") + $args
    $code = Invoke-Python -Arguments $buildArgs
    if ($code -ne 0) { throw "site-data generation failed with exit code $code" }

    Write-Host ""
    Write-Host "Update completed successfully." -ForegroundColor Green
    exit 0
}
catch {
    Write-Host ""
    Write-Host "UPDATE FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
