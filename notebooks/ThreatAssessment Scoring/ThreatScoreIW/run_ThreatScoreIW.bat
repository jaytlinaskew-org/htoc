@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM ThreatScoreIW - Batch Script (hardened, logging, wheelhouse-first)
REM - Robust timestamp (no spaces/colons)
REM - Logs everything (pip + script)
REM - Uses local TEMP for pip (C:\Temp) to avoid network-drive flakiness
REM - pip: timeout/retries/no-cache + trusted-host
REM - Optional offline wheelhouse fallback
REM ============================================================================
echo [%date% %time%] Starting ThreatScoreIW...

REM ── HTOC on the file server (UNC) — Task Scheduler often has no mapped Z: ──
REM Same share as scripts\batch-processing-script\I&W_Automation\Generate_Report.bat
REM Override: set HTOC_SHARE_ROOT=\\server\share\HTOC before calling this .bat.
if not defined HTOC_SHARE_ROOT set "HTOC_SHARE_ROOT=\\10.1.4.22\data\HTOC"

REM ── Set the Python executable path ──────────────────────────────────────────
REM You can override by setting PYTHON_EXE before calling this .bat.
if not defined PYTHON_EXE set "PYTHON_EXE=%HTOC_SHARE_ROOT%\JA\Python313\python.exe"

REM ── Set script + working directory ─────────────────────────────────────────
set "WORK_DIR=%~dp0"
set "SCRIPT_PATH=%WORK_DIR%ThreatScoreIW.py"

REM ── Set log directory ──────────────────────────────────────────────────────
set "LOG_DIR=%WORK_DIR%logs"

REM ── Optional offline wheelhouse folder (create once) ───────────────────────
if not defined WHEELHOUSE set "WHEELHOUSE=%HTOC_SHARE_ROOT%\JA\wheelhouse"

REM ── Expected Excel output directory (from script) ──────────────────────────
set "OUTPUT_DIR=%HTOC_SHARE_ROOT%\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W"

REM ── Create log directory if it doesn't exist ───────────────────────────────
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create log directory. Error level: %ERRORLEVEL%
        pause
        exit /b 1
    )
)

REM ── Purge logs older than 14 days ──────────────────────────────────────────
REM Note: forfiles uses local filesystem timestamps; errors are ignored.
forfiles /p "%LOG_DIR%" /m "*.log" /d -14 /c "cmd /c del /q @path" >nul 2>&1
forfiles /p "%LOG_DIR%" /m "*.txt" /d -14 /c "cmd /c del /q @path" >nul 2>&1

REM ── Safe timestamp (avoids spaces/colons) ───────────────────────────────────
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set "TODAY_STR=%%i"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format HHmmss"') do set "NOW_STR=%%i"
set "TS=%TODAY_STR%_%NOW_STR%"

REM ── Log files ──────────────────────────────────────────────────────────────
set "LOG_FILE=%LOG_DIR%\threatscoreiw_%TS%.log"
set "TEMP_OUT=%LOG_DIR%\temp_output_%TS%.log"

echo [%date% %time%] Log file: "%LOG_FILE%"
echo [%date% %time%] Starting ThreatScoreIW...> "%LOG_FILE%" 2>nul
echo [%date% %time%] Log file: "%LOG_FILE%">> "%LOG_FILE%" 2>nul

REM ── Change to working directory (quoted handles spaces) ─────────────────────
pushd "%WORK_DIR%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to change to working directory. Error level: %ERRORLEVEL%
    echo [%date% %time%] ERROR: Failed to change to working directory >> "%LOG_FILE%" 2>nul
    pause
    exit /b 1
)

REM ── Check if Python executable exists ───────────────────────────────────────
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at "%PYTHON_EXE%"
    echo [%date% %time%] ERROR: Python executable not found >> "%LOG_FILE%" 2>nul
    popd >nul
    pause
    exit /b 1
)

REM ── Check if script exists ──────────────────────────────────────────────────
if not exist "%SCRIPT_PATH%" (
    echo [ERROR] Script not found at "%SCRIPT_PATH%"
    echo [%date% %time%] ERROR: Script not found >> "%LOG_FILE%" 2>nul
    popd >nul
    pause
    exit /b 1
)

REM ── Force local TEMP for pip (reduces network instability) ─────────────────
set "TMP=C:\Temp"
set "TEMP=C:\Temp"
if not exist "%TMP%" mkdir "%TMP%" >nul 2>&1

REM ── pip install settings ───────────────────────────────────────────────────
set "PIP_FLAGS=--user --disable-pip-version-check --no-warn-script-location --no-cache-dir --timeout 120 --retries 20"
set "PIP_TRUST=--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org"
set "PKGS=pandas openpyxl requests urllib3 pytz"

REM ── Install required packages (show output like reference) ─────────────────
echo [%date% %time%] Installing required packages...
echo [%date% %time%] Installing required packages...>> "%LOG_FILE%" 2>nul

REM Try wheelhouse first if it exists (offline, faster, more reliable)
if exist "%WHEELHOUSE%" (
    echo [%date% %time%] Attempting install from wheelhouse ^(offline^)
    echo [%date% %time%] Attempting install from wheelhouse>> "%LOG_FILE%" 2>nul
    
    "%PYTHON_EXE%" -m pip install --user --no-index --find-links="%WHEELHOUSE%" %PKGS% > "%TEMP_OUT%" 2>&1
    set "PIP_EXIT=!ERRORLEVEL!"
    
    type "%TEMP_OUT%"
    type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul
    
    if "!PIP_EXIT!"=="0" (
        echo.
        echo ========================================================================================================
        echo [SUCCESS] Packages installed from WHEELHOUSE ^(offline^)
        echo ========================================================================================================
        echo.
        echo [%date% %time%] SUCCESS: Packages installed from wheelhouse>> "%LOG_FILE%" 2>nul
        goto :pip_done
    )
    
    REM Check if packages were already satisfied from wheelhouse attempt
    findstr /C:"Requirement already satisfied" "%TEMP_OUT%" >nul
    set "FINDSTR_EXIT=!ERRORLEVEL!"
    
    if "!FINDSTR_EXIT!"=="0" (
        echo.
        echo ========================================================================================================
        echo [SUCCESS] Packages already installed ^(satisfied^)
        echo ========================================================================================================
        echo.
        echo [%date% %time%] SUCCESS: Packages already satisfied>> "%LOG_FILE%" 2>nul
        goto :pip_done
    )
    
    echo [WARNING] Wheelhouse install failed. Error level: !PIP_EXIT!
    echo [WARNING] Falling back to online PyPI installation...
    echo [%date% %time%] WARNING: Wheelhouse failed, trying PyPI>> "%LOG_FILE%" 2>nul
    echo.
)

REM Attempt online install from PyPI (either wheelhouse doesn't exist or failed)
echo [%date% %time%] Attempting install from PyPI ^(online^)...
echo [%date% %time%] Attempting install from PyPI>> "%LOG_FILE%" 2>nul

"%PYTHON_EXE%" -m pip install %PIP_FLAGS% %PIP_TRUST% %PKGS% > "%TEMP_OUT%" 2>&1
set "PIP_EXIT=!ERRORLEVEL!"

type "%TEMP_OUT%"
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul

if "!PIP_EXIT!"=="0" (
    echo.
    echo ========================================================================================================
    echo [SUCCESS] Packages installed from PyPI ^(online^)
    echo ========================================================================================================
    echo.
    echo [%date% %time%] SUCCESS: Packages installed from PyPI>> "%LOG_FILE%" 2>nul
    goto :pip_done
)

REM If we get here, PyPI also failed - check if packages were already satisfied
findstr /C:"Requirement already satisfied" "%TEMP_OUT%" >nul
set "FINDSTR_EXIT=!ERRORLEVEL!"

if "!FINDSTR_EXIT!"=="0" (
    echo.
    echo ========================================================================================================
    echo [SUCCESS] Packages already installed ^(satisfied^)
    echo ========================================================================================================
    echo.
    echo [%date% %time%] SUCCESS: Packages already satisfied>> "%LOG_FILE%" 2>nul
    goto :pip_done
)

REM Both wheelhouse and PyPI failed
echo.
echo ========================================================================================================
echo [ERROR] Package installation failed from all sources
echo ========================================================================================================
echo [ERROR] Both wheelhouse and PyPI installation failed. Error level: !PIP_EXIT!
echo [%date% %time%] ERROR: All package installation attempts failed. Error level: !PIP_EXIT!>> "%LOG_FILE%" 2>nul
del "%TEMP_OUT%" >nul 2>&1
popd >nul
pause
exit /b 1

:pip_done
del "%TEMP_OUT%" >nul 2>&1

REM ── Execute the Python script and capture output ────────────────────────────
echo.
echo ========================================================================================================
echo EXECUTING THREATSCOREIW SCRIPT
echo ========================================================================================================
echo [%date% %time%] Executing ThreatScoreIW script...
echo [%date% %time%] Executing ThreatScoreIW script...>> "%LOG_FILE%" 2>nul

REM Set log level for script output (optional)
REM set "LOG_LEVEL=INFO"

"%PYTHON_EXE%" "%SCRIPT_PATH%" > "%TEMP_OUT%" 2>&1
set "SCRIPT_EXIT_CODE=!ERRORLEVEL!"

REM ── Display and log script output ───────────────────────────────────────────
type "%TEMP_OUT%"
echo ========================================================================================================
type "%TEMP_OUT%" >> "%LOG_FILE%" 2>nul

REM ── Detailed success/failure handling ───────────────────────────────────────
echo.
if "!SCRIPT_EXIT_CODE!"=="0" (
    echo ========================================================================================================
    echo [SUCCESS] ThreatScoreIW completed successfully
    echo ========================================================================================================
    echo.
    echo [%date% %time%] SUCCESS: ThreatScoreIW completed successfully>> "%LOG_FILE%" 2>nul

    REM Check for today's expected Excel file (same naming as script)
    set "EXPECTED_FILE=%OUTPUT_DIR%\ThreatAssessI_W_%TODAY_STR%.xlsx"

    if exist "!EXPECTED_FILE!" (
        echo --------------------------------------------------------------------------------------------------------
        echo RESULT: Excel spreadsheet created successfully
        echo --------------------------------------------------------------------------------------------------------
        echo File: "!EXPECTED_FILE!"
        for %%a in ("!EXPECTED_FILE!") do set "FILE_SIZE=%%~za"
        set /a SIZE_KB=!FILE_SIZE! / 1024
        echo Size: !SIZE_KB! KB ^(!FILE_SIZE! bytes^)
        echo --------------------------------------------------------------------------------------------------------
        echo [%date% %time%] SUCCESS: Excel file found: !EXPECTED_FILE!>> "%LOG_FILE%" 2>nul
    ) else (
        echo --------------------------------------------------------------------------------------------------------
        echo WARNING: Script succeeded but expected Excel file not found
        echo --------------------------------------------------------------------------------------------------------
        echo Expected: "!EXPECTED_FILE!"
        echo OutputDir: "%OUTPUT_DIR%"
        echo --------------------------------------------------------------------------------------------------------
        echo [%date% %time%] WARNING: Expected Excel file not found: !EXPECTED_FILE!>> "%LOG_FILE%" 2>nul
    )
) else (
    echo ========================================================================================================
    echo [ERROR] ThreatScoreIW failed
    echo ========================================================================================================
    echo Error Code: !SCRIPT_EXIT_CODE!
    echo ========================================================================================================
    echo.
    echo [%date% %time%] ERROR: ThreatScoreIW failed with error code !SCRIPT_EXIT_CODE!>> "%LOG_FILE%" 2>nul

    set "ERROR_LOG=%LOG_DIR%\error_threatscoreiw_%TS%.log"
    (
        echo [%date% %time%] FAILURE DETAILS - Error Code: !SCRIPT_EXIT_CODE!
        echo Script Path: "%SCRIPT_PATH%"
        echo Working Directory: "%WORK_DIR%"
        echo Python Executable: "%PYTHON_EXE%"
        echo Wheelhouse: "%WHEELHOUSE%"
        echo Output Dir: "%OUTPUT_DIR%"
        echo ======== ERROR OUTPUT ========
        type "%TEMP_OUT%"
        echo ==============================
    ) > "%ERROR_LOG%" 2>nul

    echo [%date% %time%] Error details written to: "%ERROR_LOG%"
    echo [%date% %time%] Error log created: "%ERROR_LOG%">> "%LOG_FILE%" 2>nul
)

REM ── Clean up ───────────────────────────────────────────────────────────────
if exist "%TEMP_OUT%" del "%TEMP_OUT%" >nul 2>&1

REM ── Final status ───────────────────────────────────────────────────────────
if "!SCRIPT_EXIT_CODE!"=="0" (
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed successfully
    echo Log file: "%LOG_FILE%"
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed successfully>> "%LOG_FILE%" 2>nul
) else (
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed with errors
    echo Log file: "%LOG_FILE%"
    echo ========================================================================================================
    echo [%date% %time%] Batch script completed with errors>> "%LOG_FILE%" 2>nul
)

popd >nul
if "!SCRIPT_EXIT_CODE!"=="0" (
    REM Success: exit without pause so the console window can close (e.g. double-click runs).
    exit 0
) else (
    pause
    exit /b !SCRIPT_EXIT_CODE!
)

