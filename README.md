# Athlete Files (پرونده ورزشکاران)

## Get the .exe (no Windows needed)
1. Create a new GitHub repo, upload EVERYTHING in this folder (keep the `.github` folder!).
2. Go to the repo's **Actions** tab -> "Build Windows EXE" -> wait ~5 min.
3. Open the finished run -> **Artifacts** -> download `AthleteFiles-exe` -> unzip -> AthleteFiles.exe

## Or build on a Windows PC
Double-click `build_windows.bat`. Exe appears in `dist\`.

## Run from source (Debian, for testing)
    python3 -m venv venv && . venv/bin/activate
    pip install -r requirements.txt
    python app.py              # if Wayland acts up: QT_QPA_PLATFORM=xcb python app.py

## Where is the data?
- Live data:  %APPDATA%\AthleteFiles\athletes.db
- Auto backups (start, exit, before any delete/restore, last 40 kept): Documents\AthleteBackups
- Manual backup/restore: buttons in the app. To move PCs: Backup -> copy file -> Restore.
