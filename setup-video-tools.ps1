$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\windows-common.ps1"

Write-Host "========================================"
Write-Host "  Video tools setup"
Write-Host "========================================"

try {
    $runner = Get-PythonRunner
    Write-Host "Python: $($runner.Exe)"
    & $runner.Exe @($runner.Args) -m pip install --upgrade -r "$PSScriptRoot\tools\requirements.txt"
    if ($LASTEXITCODE -ne 0) { throw "pip install failed with exit code $LASTEXITCODE" }

    Write-Host ""
    Write-Host "Checking bundled FFmpeg..."
    & $runner.Exe @($runner.Args) -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
    if ($LASTEXITCODE -ne 0) { throw "imageio-ffmpeg check failed" }

    Write-Host ""
    Write-Host "Setup completed. You can now run update-content.bat."
    exit 0
}
catch {
    Write-Host ""
    Write-Host "SETUP FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check Python, pip, and network access."
    exit 1
}
