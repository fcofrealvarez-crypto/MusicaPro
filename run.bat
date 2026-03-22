@echo off
title MusicPro Suite
color 0B
cls

:MENU
cls
echo ==================================================
echo               MUSICPRO SUITE
echo ==================================================
echo.
echo  1. Download Music (CLI)
echo  2. Download Music (GUI)
echo  3. Enhance Audio (Normalize/Trim)
echo  4. Open Downloads Folder
echo  5. Exit
echo.
echo ==================================================
set /p choice=Select an option (1-5): 

if "%choice%"=="1" goto CLI
if "%choice%"=="2" goto GUI
if "%choice%"=="3" goto ENHANCER
if "%choice%"=="4" goto FOLDER
if "%choice%"=="5" goto EXIT

echo Invalid option.
pause
goto MENU

:CLI
cls
"C:\Users\michi\AppData\Local\Programs\Python\Python312\python.exe" downloader.py
pause
goto MENU

:GUI
cls
start "" "C:\Users\michi\AppData\Local\Programs\Python\Python312\python.exe" gui.py
goto MENU

:ENHANCER
cls
"C:\Users\michi\AppData\Local\Programs\Python\Python312\python.exe" enhancer.py
pause
goto MENU

:FOLDER
if not exist "downloads" mkdir "downloads"
start "" "downloads"
goto MENU

:EXIT
exit
