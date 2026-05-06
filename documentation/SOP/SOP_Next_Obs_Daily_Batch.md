# Standard Operating Procedure
## Next_Obs_Daily Batch Process — Daily Full Report Build

| Field | Detail |
|---|---|
| **SOP Title** | Next_Obs_Daily Batch Process |
| **Script** | SharePoint: [NextObserved/main.py](https://hhsgov.sharepoint.com/:u:/r/sites/HTOCDataAnalyticsASA/Shared%20Documents/HTOC%20Data%20Analytics/Python%20Scripts/NextObserved/main.py?csf=1&web=1&e=qebIUV) — path **`Documents/HTOC Data Analytics/Python Scripts/NextObserved/main.py`** |
| **Batch launcher** | **`Documents/HTOC Data Analytics/Python Scripts/Next_Obs_Daily/next_observed_daily_reports.bat`** (sync locally); must invoke the same **`main.py`** revision you intend to run |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **SOP library** | **SharePoint** (site **`HTOCDataAnalyticsASA`**): **`Documents/HTOC Data Analytics/SOPs/`** *(published procedure `.md` files and **`Appendix Scripts/`** live here)* |
| **Input** | Partner forecast CSVs in `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv` |
| **Output** | Daily consolidated CSV in `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv`; execution logs in `run_log.json` and `output.log` |
| **Execution** | Run **`next_observed_daily_reports.bat`** from your synced copy of **`Documents/HTOC Data Analytics/Python Scripts/Next_Obs_Daily/`**, **or** run **`py -3.13`** on a synced copy of SharePoint **`NextObserved/main.py`** using the same working directory and dependency steps the batch file performs. |
| **Associated batch file** | **`Next_Obs_Daily/next_observed_daily_reports.bat`** under the SharePoint script library (see **Batch launcher** row) |

---

## 1. Purpose

This SOP documents the **Next_Obs_Daily** process that consolidates partner-level NOI prediction outputs into a single daily file for downstream reporting and distribution. Production **`main.py`** lives at **`Documents/HTOC Data Analytics/Python Scripts/NextObserved/main.py`** on that site (linked in the header table). Operators invoke **`next_observed_daily_reports.bat`** or **`main.py`** directly; logs document each run for support.

---

## 2. Scope

This SOP applies to HTOC analysts and engineers responsible for operating, monitoring, and troubleshooting **`Next_Obs_Daily`** runs. It covers the batch launcher, Python processing logic, logging, validation, and failure handling.

---

## 3. Prerequisites

### 3.1 Runtime and Access

| Requirement | Notes |
|---|---|
| Python 3.13 via `py -3.13` | Required by batch guard clause in `.bat` |
| pandas, openpyxl | Installed on each run by the batch file (`pip install --user`) |
| Access to `Z:\HTOC\Data_Analytics\` | Required for input and output paths |
| Shell access on execution host | Run `.bat` or `py -3.13` interactively when troubleshooting failed runs |

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
| Batch launcher | **`Next_Obs_Daily/next_observed_daily_reports.bat`** (SharePoint library; sync locally) | Validates Python runtime, installs dependencies, runs script, writes logs |
| Main script | SharePoint: [NextObserved/main.py](https://hhsgov.sharepoint.com/:u:/r/sites/HTOCDataAnalyticsASA/Shared%20Documents/HTOC%20Data%20Analytics/Python%20Scripts/NextObserved/main.py?csf=1&web=1&e=qebIUV) | Loads today’s partner CSVs, adds metadata columns, writes consolidated CSV |
| Structured log | **`run_log.json`** next to **`next_observed_daily_reports.bat`** on the run host | JSON history of timestamp + output line per run |
| Raw output log | **`output.log`** next to **`next_observed_daily_reports.bat`** on the run host | Full pip + script stdout/stderr stream |

---

## 5. Execution Flow

| Step | Action | Expected Result |
|---|---|---|
| 1 | Operator runs **`next_observed_daily_reports.bat`** from its directory (double-click or `cmd`) | Batch sets working directory and starts the launcher flow |
| 2 | Batch verifies `py -3.13` availability | Continues if present; exits with error if missing |
| 3 | Batch runs pip install for `pandas openpyxl` | Dependencies ensured for current user profile |
| 4 | Batch executes production `main.py` (hosted on SharePoint; see header table) | Script scans partner folders and builds `daily_search` dataframe |
| 5 | Script writes `full_daily_report_{YYYYMMDD}.csv` if not already present | Consolidated output file exists in `Full Daily Reports` |
| 6 | Batch appends run entry to `run_log.json` and full output to `output.log` | Run is auditable |

---

## 6. Python Script Logic (`main.py`)

Runs should use the **SharePoint** copy of **`main.py`** referenced in the header table (synced locally as your team prefers). If you maintain an extra copy of **`main.py`** outside SharePoint, verify it matches the SharePoint revision before using it for operations.

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

## 7. Batch launcher behavior (`next_observed_daily_reports.bat`)

- Forces execution in script directory (`cd /d "%~dp0"`).
- Enforces Python 3.13 usage (`py -3.13`) to avoid older pip/runtime issues.
- Sets user-scoped package paths (`PYTHONUSERBASE`, `PYTHONPATH`).
- Installs dependencies with retries and trusted hosts.
- Runs Python script and captures output.
- Appends structured run output to `run_log.json` via PowerShell JSON append logic.

---

## 8. Run Success Criteria

A successful run should satisfy all of the following:

1. The batch exits with code **0** (or **`py`** returns **0** if you invoked **`main.py`** without the `.bat`).
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
| Run failed but no clear message in the console | Output only in log files | Review `output.log` and latest object in `run_log.json` |

---

## 10. Operator Decision Points

- If no partner CSVs exist for today yet, verify the upstream forecast process before rerunning this batch.
- If a run fails due to environment/runtime, fix Python or package issues first, then rerun **`next_observed_daily_reports.bat`** or **`main.py`** manually.
- If output exists but appears incomplete, validate partner source folders and rerun only after correcting source data.

---

## 11. Related documents

Procedure Markdown files live in **SharePoint** under **`Documents/HTOC Data Analytics/SOPs/`**.

- `SOP_Daily_Reports_Consolidation.md` — consolidation process (production `main.py` + appendix standalone)
- `SOP_NextObservedIndicator_Forecasting.md` — upstream forecast generation process

