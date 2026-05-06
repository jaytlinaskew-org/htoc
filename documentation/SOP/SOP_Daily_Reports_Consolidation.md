# Standard Operating Procedure
## Daily Partner Prediction Report Consolidation

| Field | Detail |
|---|---|
| **SOP Title** | Daily Partner Prediction Report Consolidation |
| **Batch script** | SharePoint: [NextObserved/main.py](https://hhsgov.sharepoint.com/:u:/r/sites/HTOCDataAnalyticsASA/Shared%20Documents/HTOC%20Data%20Analytics/Python%20Scripts/NextObserved/main.py?csf=1&web=1&e=qebIUV) — **`Documents/HTOC Data Analytics/Python Scripts/NextObserved/main.py`** |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **SOP library** | **SharePoint** (site **`HTOCDataAnalyticsASA`**): **`Documents/HTOC Data Analytics/SOPs/`** *(published procedure `.md` files and **`Appendix Scripts/`** live here)* |
| **Input** | Partner prediction CSVs `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv` |
| **Output** | Consolidated CSV `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv` |
| **Execution** | Run **`next_observed_daily_reports.bat`** from **`Documents/HTOC Data Analytics/Python Scripts/Next_Obs_Daily/`** after sync, **or** run **`py`** on synced **`NextObserved/main.py`** with the same setup the batch file uses—see SharePoint **`Documents/HTOC Data Analytics/SOPs/SOP_Next_Obs_Daily_Batch.md`**. |
| **Associated batch / script** | SharePoint **`NextObserved/main.py`** and **`Next_Obs_Daily/next_observed_daily_reports.bat`** — confirm your local **`next_observed_daily_reports.bat`** still points at the **`main.py`** you intend to run. |

---

## 1. Purpose

This SOP describes the daily consolidation of per-partner NOI (Next Observed Indicator) prediction CSVs into a single full daily report. Each day, partner-specific prediction files are written to subfolders under the `OpDiv_Predictions` directory. This process discovers those files, merges them into one consolidated dataset, and writes a dated output CSV to the `Full Daily Reports` folder.

This process runs as **Python**: operators start **`main.py`** via the Next_Obs launcher **`.bat`** (or **`py`** on **`main.py`**), or use the appendix **`daily_reports_standalone.py`** for ad hoc runs.

---

## 2. Scope

This procedure applies to HTOC analysts and data engineers who run, monitor, or troubleshoot the daily prediction report consolidation. It covers running **`main.py`** (batch or direct **`py`**), ad hoc runs, and troubleshooting.

---

## 3. Prerequisites

### 3.1 Environment

| Requirement | Notes |
|---|---|
| Python 3.x | Must be available in the environment where `main.py` executes |
| pandas | CSV loading and concatenation |
| numpy | Indirect dependency |
| Access to `Z:\HTOC\Data_Analytics\` | All input and output paths are on this share |

Example dependency install command:
```powershell
pip install pandas
```

### 3.2 Input Data

Partner prediction CSVs must be present under the `OpDiv_Predictions` directory tree **before** this process runs. These files are produced by the NOI forecasting pipeline (see SharePoint **`Documents/HTOC Data Analytics/SOPs/SOP_NextObservedIndicator_Forecasting.md`**).

Expected input file naming convention:
```
Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv
```

---

## 4. Key Configuration

Production `main.py` and the appendix standalone script use the same path constants:

| Constant | Value |
|---|---|
| `DATA_PATH` | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions` |
| `SAVE_PATH` | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports` |
| `EXCLUDE_FOLDERS` | `automation scripts`, `Logs`, `LogsBackup`, `Full Daily Reports` |

The `EXCLUDE_FOLDERS` set prevents the loader from reading its own output or log directories during the folder walk.

---

## 5. How the Process Works

### 5.1 File Discovery

The loader uses `os.walk` to recursively traverse all subfolders under `DATA_PATH`. For each directory, it:

1. Skips any path containing a folder name in `EXCLUDE_FOLDERS`.
2. Treats the **immediate folder name** as the `Partner` value.
3. Matches files whose names end with `{YYYYMMDD}.csv` — in the default **`main.py`** path, only **today's** date is matched.

### 5.2 Consolidation

For each matched file:
- The CSV is read into a DataFrame.
- Two columns are added: `Partner` (from the folder name) and `FileDate` (from the filename date string).
- All per-partner DataFrames are concatenated into a single `daily_search` DataFrame.

If no files are found, the process prints `"No CSV files found for today."` and exits without writing an output file.

### 5.3 Output

The consolidated DataFrame is written to:
```
Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv
```

The output file is **never overwritten** — if it already exists for today's date, the process prints `"File already exists: …"` and skips the write. This prevents duplicate runs from corrupting the report.

---

## 6. Running `main.py` (today-only)

### 6.1 Operator entry points

Production **`main.py`** is maintained on **SharePoint**: [NextObserved/main.py](https://hhsgov.sharepoint.com/:u:/r/sites/HTOCDataAnalyticsASA/Shared%20Documents/HTOC%20Data%20Analytics/Python%20Scripts/NextObserved/main.py?csf=1&web=1&e=qebIUV). **Typical run:** start **`next_observed_daily_reports.bat`** from your synced **`Next_Obs_Daily/`** folder (installs deps, invokes **`main.py`**, writes logs — see SharePoint **`Documents/HTOC Data Analytics/SOPs/SOP_Next_Obs_Daily_Batch.md`**). **Alternative:** from a shell, run **`py -3.13 path\to\main.py`** using the same working directory and packages the batch file expects. The script executes the **today-only** consolidation flow: load today's partner CSVs → merge → save a single consolidated report.

Use **Section 7** when backfilling historical dates, spot-checking with a standalone copy, or validating a revised **`main.py`** before publishing it to SharePoint.

### 6.2 Script logic

```
main()
  ├── Compute today_str (YYYYMMDD)
  ├── load_all_csvs_from_folders(DATA_PATH, today_only=True)
  │     ├── Walk DATA_PATH, skip EXCLUDE_FOLDERS
  │     ├── Match files: {today_str}.csv only
  │     ├── Add Partner and FileDate columns
  │     └── Return concatenated DataFrame (or empty if none found)
  └── If DataFrame is non-empty:
        └── save_daily_report(df, SAVE_PATH, today_str)
              ├── Build output path: full_daily_report_{today_str}.csv
              ├── If file exists → print and skip
              └── Else → makedirs + to_csv + print path
```

### 6.3 Verifying a successful run

Confirm the run succeeded by checking that:
1. The file `full_daily_report_{YYYYMMDD}.csv` exists in `Full Daily Reports` for today's date.
2. The file is non-empty and contains the expected `Partner` and `FileDate` columns.

---

## 7. Ad hoc execution (Python)

Use a **local copy** of production **`main.py`** (SharePoint) or the appendix **`daily_reports_standalone.py`** when you need to run consolidation without the batch launcher—for example after a failed batch run, spot checks, or while testing a code change before publish.

### 7.1 Verify prerequisites

- [ ] `Z:\HTOC\Data_Analytics\` is accessible and mapped.
- [ ] Partner prediction CSVs for the target date exist under `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\`.
- [ ] Python 3.x with `pandas` (and any imports your deployed `main.py` requires).

### 7.2 Run today-only consolidation

From a shell, with the script on disk (path per your deployment):

```powershell
py "path\to\main.py"
```

Expected behavior matches **Section 6.2**: non-empty partner files for today produce `full_daily_report_{YYYYMMDD}.csv` under `Full Daily Reports` unless that file already exists.

### 7.3 Backfill or custom date ranges

The production **`main.py`** path is **today-only**. For historical rebuilds, either (a) temporarily adjust the date filter in a **non-production copy** of the script and run once per needed date with care, or (b) extend a private copy of the loader logic to iterate `FileDate` values—always validate outputs before replacing production archives.

---

## 8. Output File

| Detail | Value |
|---|---|
| Location | `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\` |
| Filename | `full_daily_report_{YYYYMMDD}.csv` |
| Overwrite behavior | Never overwritten — skipped if already exists |
| Key added columns | `Partner` (source folder name), `FileDate` (from filename) |

The output file contains all prediction columns from the upstream NOI forecasting output, with `Partner` and `FileDate` appended for traceability.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `"No CSV files found for today."` | Partner prediction CSVs not yet written for today | Verify the NOI forecasting pipeline ran successfully; check `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\` for today's files |
| `"File already exists: …"` | A successful run already wrote today’s file | No action needed; this is the expected idempotency guard |
| `"No data to save."` | `daily_search` is empty after loading | Same as above — check upstream prediction files |
| Output file is missing partners | One or more partner subfolders had no matching file | Check the partner's subfolder for a `{YYYYMMDD}.csv` file; the loader skips unreadable files but prints a skip message |
| `Skipping {path}: …` printed | A CSV file could not be read (encoding, permissions, corruption) | Inspect the file at the printed path; re-run after fixing or removing the corrupt file |
| Custom backfill needed | Built-in script is today-only | Use a controlled copy of the script with explicit date logic; see **Section 7.3** |
| `Z:\` path not found | Network drive not mapped | Map the `Z:\` drive to `\\cscso1fsappv01\...` and re-run |

---

## 10. Relationship to Other Processes

This process sits **downstream** of the NOI forecasting pipeline and **upstream** of any reporting or distribution that consumes the consolidated daily file.

| Step | Process | Output |
|---|---|---|
| 1 | NOI forecasting pipeline runs first | Partner-level daily files: `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\{PartnerName}\{YYYYMMDD}.csv` |
| 2 | Daily reports consolidation (`main.py`) runs second | Consolidated daily file: `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\full_daily_report_{YYYYMMDD}.csv` |
| 3 | Downstream reporting/distribution jobs consume the consolidated file | Partner distribution products and operational reports |

If the daily report is missing or incomplete, check the NOI forecasting step first before rerunning this process.

---

## 11. Appendix — standalone Python script

Published **SharePoint** path *(site **`HTOCDataAnalyticsASA`*)*: **`Documents/HTOC Data Analytics/SOPs/Appendix Scripts/daily_reports_standalone.py`**

After syncing **`Documents/HTOC Data Analytics/`** locally, **`cd`** to **`...\Documents\HTOC Data Analytics\SOPs\Appendix Scripts`**, then:

```powershell
py .\daily_reports_standalone.py
```

---

## 12. Related documents

Procedure Markdown files for this workflow live in **SharePoint** under **`Documents/HTOC Data Analytics/SOPs/`**.

- `SOP_NextObservedIndicator_Forecasting.md` — upstream process that generates the per-partner input CSVs
- `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\` (input data location)
- `Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\Full Daily Reports\` (output location)
- SharePoint ([NextObserved/main.py](https://hhsgov.sharepoint.com/:u:/r/sites/HTOCDataAnalyticsASA/Shared%20Documents/HTOC%20Data%20Analytics/Python%20Scripts/NextObserved/main.py?csf=1&web=1&e=qebIUV)) — production **`main.py`**
