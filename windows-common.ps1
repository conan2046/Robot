$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Get-PythonRunner {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @{ Exe = $py.Source; Args = @('-3') }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{ Exe = $python.Source; Args = @() }
    }
    throw "Python 3 was not found. Install Python 3 first."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )
    $runner = Get-PythonRunner

    # IMPORTANT:
    # Native stdout must be sent to the host, otherwise PowerShell captures
    # every output line together with the numeric exit code when the caller
    # does: $code = Invoke-Python ...
    & $runner.Exe @($runner.Args) @Arguments 2>&1 | ForEach-Object { Write-Host $_ }
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }
    return [int]$exitCode
}
