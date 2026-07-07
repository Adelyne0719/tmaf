@echo off
echo =========================================
echo Warhammer 40k Roster Checker (Public Share)
echo =========================================
echo.
echo Make sure you have already run 'start_app.bat' first!
echo.
echo Requesting a highly stable public URL (localhost.run)...
echo Please wait a moment...
echo.
echo NOTE: A URL looking like "https://[random].lhr.life" will appear.
echo Copy and paste that URL into your mobile browser!
echo To stop sharing, simply close this window.
echo =========================================

ssh -o StrictHostKeyChecking=accept-new -R 80:localhost:5173 nokey@localhost.run

pause
