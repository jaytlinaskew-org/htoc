@echo off
REM ─── Work in this script’s folder ────────────────────────────────────────────
cd /d "%~dp0"

REM ─── Configuration (same pattern as NextObserved.bat) ─────────────────────
set "LOG_FILE=%~dp0TipperRunLogs.json"
set "OUTPUT_FILE=%~dp0TipperRunOutput.log"

REM ─── 0) Initialize JSON array ────────────────────────────────────────────────
> "%LOG_FILE%" echo [
 
REM ─── 1) Log “Start” (first element, with comma) ──────────────────────────────
for /f "delims=" %%T in (
  'powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"'
) do set "TSTAMP=%%T"
>> "%LOG_FILE%" echo     {"timestamp":"%TSTAMP%","event":"Start","exitCode":null},

REM ─── 2) Pip install check (if failure, second element, with comma) ───────────
"C:\Program Files\Python313\python.exe" -m pip install --upgrade --quiet --user ^
    pandas pytz numpy requests xlsxwriter openpyxl >> "%OUTPUT_FILE%" 2>&1
if %ERRORLEVEL% neq 0 (
    for /f "delims=" %%T in (
      'powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"'
    ) do set "TSTAMP=%%T"
    >> "%LOG_FILE%" echo     {"timestamp":"%TSTAMP%","event":"PipInstallFailed","exitCode":%ERRORLEVEL%},
    exit /b %ERRORLEVEL%
)

REM ─── 3) Run main.py and capture all output (same pattern as NextObserved.bat) ─
"C:\Program Files\Python313\python.exe" "%~dp0main.py" >> "%OUTPUT_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
for /f "delims=" %%T in (
  'powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"'
) do set "TSTAMP=%%T"
>> "%LOG_FILE%" echo     {"timestamp":"%TSTAMP%","event":"End","exitCode":%EXIT_CODE%}

REM ─── 4) Close JSON array ─────────────────────────────────────────────────────
>> "%LOG_FILE%" echo ]

exit /b %EXIT_CODE%
