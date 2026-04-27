# Standard Operating Procedure
## Next_Obs_Daily Batch Process — Daily Full Report Build

| Field | Detail |
|---|---|
| **SOP Title** | Next_Obs_Daily Batch Process |
| **Script** | GitHub: [`scripts/batch-processing-script/Next_Obs_Daily/src/main.py`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/scripts/batch-processing-script/Next_Obs_Daily/src/main.py) |
| **Batch Launcher** | GitHub: [`scripts/batch-processing-script/Next_Obs_Daily/next_observed_daily_reports.bat`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/scripts/batch-processing-script/Next_Obs_Daily/next_observed_daily_reports.bat) |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **Input** | Partner forecast CSVs in `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv` |
| **Output** | Daily consolidated CSV in `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv`; execution logs in `run_log.json` and `output.log` |
| **Current Schedule** | Executed daily at **8:15 AM** via Windows Task Scheduler on **F.R.E.D** |
| **Associated Batch Files** | `scripts/batch-processing-script/Next_Obs_Daily/next_observed_daily_reports.bat` |

---

## 1. Purpose

This SOP documents the automated **Next_Obs_Daily** batch process that consolidates partner-level NOI prediction outputs into a single daily file for downstream reporting and distribution. The process runs unattended via Task Scheduler and provides run-level logging for operations support.

---

## 2. Scope

This SOP applies to HTOC analysts and engineers responsible for operating, monitoring, and troubleshooting the `Next_Obs_Daily` scheduled task. It covers the batch launcher, Python processing logic, logging, validation, and failure handling.

---

## 3. Prerequisites

### 3.1 Runtime and Access

| Requirement | Notes |
|---|---|
| Python 3.13 via `py -3.13` | Required by batch guard clause in `.bat` |
| pandas, openpyxl | Installed on each run by the batch file (`pip install --user`) |
| Access to `Z:\HTOC\Data_Analytics\` | Required for input and output paths |
| Task Scheduler access on F.R.E.D | Required to verify task history and trigger reruns |

Example dependency install command:
```powershell
pip install pandas openpyxl
```

### 3.2 Input Data Availability

The process expects partner files to already exist for the execution date under:

`Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv`

If no files exist for the current date, the script exits cleanly with `No data to save.`

---

## 4. Process Components

| Component | Path | Role |
|---|---|---|
| Batch launcher | `scripts/batch-processing-script/Next_Obs_Daily/next_observed_daily_reports.bat` | Validates Python runtime, installs dependencies, runs script, writes logs |
| Main script | `scripts/batch-processing-script/Next_Obs_Daily/src/main.py` | Loads today’s partner CSVs, adds metadata columns, writes consolidated CSV |
| Structured log | `scripts/batch-processing-script/Next_Obs_Daily/run_log.json` | JSON history of timestamp + output line per run |
| Raw output log | `scripts/batch-processing-script/Next_Obs_Daily/output.log` | Full pip + script stdout/stderr stream |

---

## 5. Execution Flow

| Step | Action | Expected Result |
|---|---|---|
| 1 | Task Scheduler triggers `next_observed_daily_reports.bat` at 8:15 AM | Batch starts in script directory |
| 2 | Batch verifies `py -3.13` availability | Continues if present; exits with error if missing |
| 3 | Batch runs pip install for `pandas openpyxl` | Dependencies ensured for current user profile |
| 4 | Batch executes `src/main.py` | Script scans partner folders and builds `daily_search` dataframe |
| 5 | Script writes `full_daily_report_{YYYYMMDD}.csv` if not already present | Consolidated output file exists in `Full Daily Reports` |
| 6 | Batch appends run entry to `run_log.json` and full output to `output.log` | Run is auditable |

---

## 6. Python Script Logic (`src/main.py`)

### 6.1 Key constants

| Constant | Value |
|---|---|
| `DATA_PATH` | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions` |
| `SAVE_PATH` | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports` |
| `EXCLUDE_FOLDERS` | `automation scripts`, `Logs`, `LogsBackup`, `Full Daily Reports` |

### 6.2 Data processing behavior

- Scans all subfolders under `DATA_PATH`.
- Filters files to **today only** (`YYYYMMDD.csv` naming pattern).
- Skips excluded folders to prevent recursion into output/log paths.
- Adds columns:
  - `Partner` (folder name)
  - `FileDate` (date extracted from filename)
- Concatenates all matching files into one dataframe.
- Writes output only if file does not already exist for today.

### 6.3 Idempotency guard

If `full_daily_report_{YYYYMMDD}.csv` already exists, the script prints `File already exists: ...` and does not overwrite it.

---

## 7. Batch Launcher Behavior (`next_observed_daily_reports.bat`)

- Forces execution in script directory (`cd /d "%~dp0"`).
- Enforces Python 3.13 usage (`py -3.13`) to avoid older pip/runtime issues.
- Sets user-scoped package paths (`PYTHONUSERBASE`, `PYTHONPATH`).
- Installs dependencies with retries and trusted hosts.
- Runs Python script and captures output.
- Appends structured run output to `run_log.json` via PowerShell JSON append logic.

---

## 8. Run Success Criteria

A successful run should satisfy all of the following:

1. Task Scheduler result code is success (`0x0`).
2. `run_log.json` has a new entry with today’s timestamp.
3. Entry output is either:
   - `Saved to ...full_daily_report_{YYYYMMDD}.csv`, or
   - `File already exists: ...full_daily_report_{YYYYMMDD}.csv`.
4. Output file exists and is readable at:
   `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv`.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `[ERROR] Python 3.13 not found` in `output.log` | Runtime missing on host | Install Python 3.13 and confirm `py -3.13` works from a new shell |
| `No CSV files found for today.` then `No data to save.` | Upstream partner files not present yet | Verify upstream NOI process completed and date-stamped files exist |
| `Skipping <file>` errors | One or more CSV files unreadable/corrupt | Inspect and fix malformed CSV in the partner folder |
| `File already exists: ...` | Re-run for same date | Expected idempotent behavior; no action needed |
| Task failed but no clear message in scheduler | Output only in log files | Review `output.log` and latest object in `run_log.json` |

---

## 10. Operator Decision Points

- If no data exists by 8:15 AM, verify upstream forecast process before rerunning this batch.
- If run fails due to environment/runtime, fix Python or package issues first, then rerun task manually.
- If output exists but appears incomplete, validate partner source folders and rerun only after correcting source data.

---

## 11. Related Documents

- `SOP_Daily_Reports_Consolidation.md` — combined notebook + script process documentation
- `SOP_NextObservedIndicator_Forecasting.md` — upstream forecast generation process
- GitHub repository: [jaytlinaskew-OIS/HTOC](https://github.com/jaytlinaskew-OIS/HTOC)

