@echo off
setlocal

cd /d "%~dp0"

echo [1/5] Checking Python...

where py >nul 2>&1
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>&1
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo Python was not found.
        pause
        exit /b 1
    )
)

echo [2/5] Installing PyInstaller...

%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo PyInstaller installation failed.
    pause
    exit /b 1
)

echo [3/5] Building DailyBoard.exe...

%PY% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name DailyBoard ^
    --add-data "src;src" ^
    daily_board_launcher.pyw

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo [4/5] Copying opinet_API.json...

if not exist "opinet_API.json" (
    echo opinet_API.json was not found.
    pause
    exit /b 1
)

copy /Y "opinet_API.json" "dist\opinet_API.json" >nul

if errorlevel 1 (
    echo Failed to copy opinet_API.json.
    pause
    exit /b 1
)

echo [5/5] Creating shortcut...

set "EXE=%~dp0dist\DailyBoard.exe"
set "LNK=%~dp0DailyBoard.lnk"

powershell -NoProfile -ExecutionPolicy Bypass ^
"$W=New-Object -ComObject WScript.Shell; ^
$S=$W.CreateShortcut('%LNK%'); ^
$S.TargetPath='%EXE%'; ^
$S.WorkingDirectory='%~dp0dist'; ^
$S.IconLocation='%EXE%,0'; ^
$S.Description='Daily Board'; ^
$S.Save();"

if errorlevel 1 (
    echo Failed to create shortcut.
    pause
    exit /b 1
)

echo.
echo Build completed.
echo.
echo EXE      : %EXE%
echo JSON     : %~dp0dist\opinet_API.json
echo Shortcut : %LNK%
echo.

pause