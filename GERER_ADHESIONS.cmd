@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Installer d'abord l'environnement Python comme indique dans docs\PRISE_EN_MAIN.md.
  pause
  exit /b 1
)
set LNH_DATABASE_URL=
set LNH_STORAGE_BACKEND=local
set LNH_REQUIRE_REMOTE_STORAGE=0
set LNH_MODULE_ORIGIN=http://127.0.0.1:8787
set LNH_TRUSTED_PROXY=
set LNH_BOOTSTRAP_ADMIN_EMAIL=
set LNH_BOOTSTRAP_ADMIN_PASSWORD=
".venv\Scripts\python.exe" -m membership manage-local
pause
