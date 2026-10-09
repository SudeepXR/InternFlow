@echo off
cd /d "%~dp0"
echo Setting up InternFlow...
call npm run setup
if errorlevel 1 (
  echo Setup failed. See the message above.
  pause
  exit /b 1
)
call npm start
pause
