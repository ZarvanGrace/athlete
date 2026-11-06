@echo off
REM Run this ON A WINDOWS PC with Python installed (python.org, tick "Add to PATH")
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconsole --onefile --name AthleteFiles app.py
echo.
echo Done. Your exe is in the "dist" folder: dist\AthleteFiles.exe
pause
