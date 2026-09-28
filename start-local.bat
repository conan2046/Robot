@echo off
setlocal
cd /d "%~dp0"
where pwsh >nul 2>nul
if %errorlevel%==0 goto USE_PWSH
where powershell >nul 2>nul
if %errorlevel%==0 goto USE_WINPS
echo PowerShell was not found.
pause
exit /b 1
:USE_PWSH
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local.ps1" %*
set RC=%errorlevel%
goto END
:USE_WINPS
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-local.ps1" %*
set RC=%errorlevel%
:END
echo.
if not "%RC%"=="0" echo FAILED. Exit code: %RC%
pause
exit /b %RC%
