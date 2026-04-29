# Standard Operating Procedure
## I&W Batch Reporting Pipeline (Core + Expanded)

| Field | Detail |
|---|---|
| **SOP Title** | I&W Batch Reporting Pipeline (Core + Expanded) |
| **Primary Scripts** | GitHub: [`notebooks/I&W Reporting/Batch/I&W Spreadsheet/I&W_Spreadsheet.py`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Spreadsheet/I%26W_Spreadsheet.py)<br>GitHub: [`notebooks/I&W Reporting/Batch/I&W Generator/I&W_Generator.py`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Generator/I%26W_Generator.py)<br>GitHub: [`notebooks/I&W Reporting/Batch/I&W Expanded/I&W_Document_expanded_spreadsheet.py`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Expanded/I%26W_Document_expanded_spreadsheet.py)<br>GitHub: [`notebooks/I&W Reporting/Batch/I&W Expanded/I&W_Document_expanded_generator.py`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Expanded/I%26W_Document_expanded_generator.py) |
| **Batch Launchers** | GitHub: [`notebooks/I&W Reporting/Batch/I&W Spreadsheet/run_iw_spreadsheet.bat`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Spreadsheet/run_iw_spreadsheet.bat)<br>GitHub: [`notebooks/I&W Reporting/Batch/I&W Generator/run_iw_generator.bat`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Generator/run_iw_generator.bat)<br>GitHub: [`notebooks/I&W Reporting/Batch/I&W Expanded/run_iw_expanded_spreadsheet.bat`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Expanded/run_iw_expanded_spreadsheet.bat)<br>GitHub: [`notebooks/I&W Reporting/Batch/I&W Expanded/run_iw_expanded_generator.bat`](https://github.com/jaytlinaskew-OIS/HTOC/blob/main/notebooks/I%26W%20Reporting/Batch/I%26W%20Expanded/run_iw_expanded_generator.bat) |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **Input** | ThreatConnect indicator data (`HTOC Org`), OpDiv observation CSVs in `Z:\HTOC\Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{YYYYMMDD}.csv`, and historical reported-indicator list in `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Reported Indicators\indicators.csv` |
| **Output** | Core spreadsheet in `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet\I&W_indicators_full_{YYYYMMDD}.xlsx`; core reports in `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Generated Reports\{YYYY-MM-DD}\`; expanded spreadsheet in `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet\Expanded\expanded_indicators_{YYYYMMDD}.xlsx`; expanded reports in `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Expanded Reports\{YYYY-MM-DD}\`; run logs in `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\logs\` |
| **Current Schedule** | Run via Windows Task Scheduler on F.R.E.D (confirm exact trigger times in Task Scheduler before production updates) |
| **Associated Batch Files** | `run_iw_spreadsheet.bat`, `run_iw_generator.bat`, `run_iw_expanded_spreadsheet.bat`, `run_iw_expanded_generator.bat` |

---

## 1. Purpose

This SOP documents how to operate the full I&W batch workflow that identifies qualifying indicators, builds spreadsheet queues, enriches indicators with VirusTotal and OTX context, and generates Word-ready I&W reporting artifacts for analyst review and distribution.

---

## 2. Scope

This procedure is for operators maintaining daily I&W data production. It covers the core path and expanded path, including dependency checks, execution order, expected outputs, and actions to take when a run fails or returns no indicators.

---

## 3. Prerequisites

### 3.1 Runtime and Access

| Requirement | Notes |
|---|---|
| Python runtime on execution host | Batch files point to either `Z:\HTOC\JA\Python313\python.exe` or `\\10.1.4.22\data\HTOC\Data_Analytics\Py\python.exe` |
| ThreatConnect SDK path | `Z:\HTOC\Data_Analytics\threatconnect` must be accessible |
| ThreatConnect config file | `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\utils\config.json` |
| Access to I&W staging paths on `Z:` | Required for spreadsheet/report/log read-write operations |
| Task Scheduler access on F.R.E.D | Needed to verify and rerun scheduled tasks |

Example dependency install command:
```powershell
pip install pandas openpyxl requests python-docx urllib3 pytz
```

### 3.2 Data dependencies

- OpDiv observation source files must exist for the last 2-3 days.
- ThreatConnect API credentials must be valid and active.
- For expanded runs, `indicators.csv` must exist (or be creatable) at:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Reported Indicators\indicators.csv`

---

## 4. Process Components

| Component | Path | Role |
|---|---|---|
| Core spreadsheet builder | `notebooks/I&W Reporting/Batch/I&W Spreadsheet/I&W_Spreadsheet.py` | Pulls candidate indicators and writes full spreadsheet for report generation |
| Core report generator | `notebooks/I&W Reporting/Batch/I&W Generator/I&W_Generator.py` | Reads latest core spreadsheet, enriches indicators, creates Word reports |
| Expanded spreadsheet builder | `notebooks/I&W Reporting/Batch/I&W Expanded/I&W_Document_expanded_spreadsheet.py` | Builds expanded indicator spreadsheet and filters already-reported items |
| Expanded report generator | `notebooks/I&W Reporting/Batch/I&W Expanded/I&W_Document_expanded_generator.py` | Reads latest expanded spreadsheet, enriches, creates expanded report set, updates indicators list |
| Batch launchers | `run_iw_*.bat` files listed in header table | Install dependencies, run scripts, and write log output |

---

## 5. Required Execution Order

Run in this order for complete daily processing:

1. `run_iw_spreadsheet.bat`
2. `run_iw_generator.bat`
3. `run_iw_expanded_spreadsheet.bat`
4. `run_iw_expanded_generator.bat`

If step 1 or step 3 produces no spreadsheet output, do not run its corresponding generator step until source-data conditions are corrected.

---

## 6. Core Path Behavior

### 6.1 `I&W_Spreadsheet.py`

- Queries ThreatConnect `/v3/indicators` for `HTOC Org` and selected type list.
- Loads recent OpDiv observations from:
  `Z:\HTOC\Data_Analytics\Data\OpDiv_Observations\htoc_opdiv_obs_d{YYYYMMDD}.csv`.
- Keeps indicators observed by multiple partners and filters out undesired tags (for example `htoc_wl`).
- Fetches indicator attributes and excludes SOAR-authored attributes when present.
- Writes output spreadsheet to:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet\I&W_indicators_full_{YYYYMMDD}.xlsx`.

### 6.2 `I&W_Generator.py`

- Loads the latest core spreadsheet (`I&W_indicators_full_*.xlsx`).
- Enriches each indicator using ThreatConnect enrich (`Shodan`, `VirusTotalV3`) and OTX API.
- Groups indicators by `group_id` when available.
- Fills `I&W Report Template.docx` placeholders and table rows.
- Writes reports to:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Generated Reports\{YYYY-MM-DD}\`.

---

## 7. Expanded Path Behavior

### 7.1 `I&W_Document_expanded_spreadsheet.py`

- Repeats indicator collection and partner-filter pipeline for expanded processing.
- Loads prior reported indicators from:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Reported Indicators\indicators.csv`.
- Removes already-reported indicators from current batch.
- Writes expanded spreadsheet to:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet\Expanded\expanded_indicators_{YYYYMMDD}.xlsx`.

### 7.2 `I&W_Document_expanded_generator.py`

- Loads most recent file from:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet\Expanded\`.
- Enriches indicators with ThreatConnect and OTX.
- Generates report documents in:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Expanded Reports\{YYYY-MM-DD}\`.
- Appends processed indicators to:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Reported Indicators\indicators.csv`.

---

## 8. Batch Launcher Behavior

All four batch files perform operator-safe guardrails:

- Verify Python executable path exists.
- Verify target script path exists before execution.
- Install required packages (`pip install ...`) before run.
- Capture script output and write timestamped log files under:
  `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\logs\`.
- Return non-zero exit code on failure.

The hardened launchers (`run_iw_spreadsheet.bat` and `run_iw_expanded_spreadsheet.bat`) also support:

- Local temp directory (`C:\Temp`) for pip reliability.
- Optional wheelhouse fallback at `Z:\HTOC\JA\wheelhouse`.
- Additional success/failure summaries printed at end of run.

---

## 9. Run Success Criteria

A successful full-cycle run should satisfy all checks:

1. Each batch launcher exits cleanly (Task Scheduler result `0x0` when scheduled).
2. Core spreadsheet exists for current date in `Spreadsheet\`.
3. Core report folder for current date exists in `Generated Reports\`.
4. Expanded spreadsheet exists for current date in `Spreadsheet\Expanded\`.
5. Expanded report folder for current date exists in `Expanded Reports\`.
6. Latest log files in `logs\` show success state and no unhandled tracebacks.

---

## 10. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `Python executable not found` in batch output | Runtime path changed or inaccessible | Update launcher `PYTHON_EXE` to valid host path and retest interactively |
| `Failed to load configuration` | Missing/invalid `config.json` or no read access | Validate config file path and permissions; confirm keys (`access_id`, `secret_key`, `base_url`, `default_org`) |
| `No indicators retrieved` or `No data to export` | No qualifying indicators in date window | Confirm source observation files and ThreatConnect data freshness; rerun after upstream update |
| OTX/VirusTotal errors per indicator | External API throttling/network issue | Retry run; if persistent, keep core spreadsheet output and proceed with partial context note |
| No reports generated but spreadsheet exists | Template path issue or placeholder mismatch | Verify `I&W Report Template.docx` path and template integrity |
| Expanded run returns empty after filtering | All candidates already in `indicators.csv` | Expected behavior; validate with analyst before manual override |

---

## 11. Operator Decision Points

- If core spreadsheet is empty, confirm whether this is an expected low-activity day before escalation.
- If enrichment partially fails but critical outputs exist, decide whether to publish with reduced context or rerun.
- If expanded filtering removes all indicators, confirm no urgent operational need exists before bypassing reported-indicator controls.
- If any batch step fails, fix root cause and rerun that step before continuing to downstream steps.

---

## 12. How to Run Manually

From Task Scheduler host (or equivalent execution host), run each launcher in order:

```powershell
cmd /c "Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Spreadsheet_scripts\run_iw_spreadsheet.bat"
cmd /c "Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Spreadsheet_scripts\run_iw_generator.bat"
cmd /c "Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Expanded Scripts\run_iw_expanded_spreadsheet.bat"
cmd /c "Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Expanded Scripts\run_iw_expanded_generator.bat"
```

After each step, confirm:

- Exit code is `0`.
- Expected output file/folder for that step exists.
- Corresponding log file is written to the `logs` directory.

---

## 13. Related Documents

- `SOP_Next_Obs_Daily_Batch.md`
- `SOP_Daily_Reports_Consolidation.md`
- GitHub repository: [jaytlinaskew-OIS/HTOC](https://github.com/jaytlinaskew-OIS/HTOC)
