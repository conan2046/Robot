$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
. "$PSScriptRoot\windows-common.ps1"

Write-Host "========================================"
Write-Host "  Environment check"
Write-Host "========================================"

$pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
if ($pwsh) { Write-Host "PowerShell 7: $($pwsh.Source)" } else { Write-Host "PowerShell 7: NOT FOUND" }

try {
    $runner = Get-PythonRunner
    Write-Host "Python: $($runner.Exe) $($runner.Args -join ' ')"
    & $runner.Exe @($runner.Args) -c "import sys; print('Python version:', sys.version); import imageio_ffmpeg; print('Bundled FFmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"
    if ($LASTEXITCODE -ne 0) { Write-Host "imageio-ffmpeg: NOT READY" -ForegroundColor Yellow }
}
catch {
    Write-Host "Python: NOT FOUND" -ForegroundColor Red
}

$sysFfmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($sysFfmpeg) { Write-Host "System FFmpeg: $($sysFfmpeg.Source)" } else { Write-Host "System FFmpeg: not in PATH (optional)" }
$sysFfprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
if ($sysFfprobe) { Write-Host "System FFprobe: $($sysFfprobe.Source)" } else { Write-Host "System FFprobe: not in PATH (optional)" }
