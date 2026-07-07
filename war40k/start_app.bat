@echo off
echo =========================================
echo Warhammer 40k Roster Checker
echo Starting Local Server...
echo =========================================

cd /d "%~dp0"
call npm run dev -- --open

pause
