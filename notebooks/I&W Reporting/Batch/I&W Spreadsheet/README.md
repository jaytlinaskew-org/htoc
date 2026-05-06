# I&W Spreadsheet batch processing

This folder automates execution of **`I&W_Spreadsheet.py`** (scheduled runs use the enterprise launcher **`run_iw_spreadsheet.bat`**).

## Primary files

| File | Role |
|---|---|
| [`I&W_Spreadsheet.py`](./I&W_Spreadsheet.py) | Core pipeline: ThreatConnect queries, spreadsheet build |
| [`run_iw_spreadsheet.bat`](./run_iw_spreadsheet.bat) | Task Scheduler-friendly launcher (Python path, deps, logging) |

**Usage:**

```cmd
run_iw_spreadsheet.bat
```

## Prerequisites

1. **Python** executable configured in `run_iw_spreadsheet.bat` (see `PYTHON_EXE` in that file).
2. **Packages** installed as required by the script (launcher runs `pip install` before the script).
3. **Network access** to ThreatConnect and data shares.
4. **Permissions** on `Z:\HTOC\` staging paths used by `I&W_Spreadsheet.py`.

## Paths

- **Script (staging, typical):** `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\I&W Report Processing Scripts\Spreadsheet_scripts\I&W_Spreadsheet.py`
- **Output (typical):** `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet\`
- **Logs (typical):** `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\logs\`

Repo-relative copy for development: this directory’s `I&W_Spreadsheet.py`.

## Task Scheduler

Point the scheduled action at **`run_iw_spreadsheet.bat`** on the execution host, or run the same `python.exe` + `I&W_Spreadsheet.py` invocation the batch file uses after matching `PYTHON_EXE` and working directory.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Python or script path errors in log | `PYTHON_EXE` and `SCRIPT_PATH` inside `run_iw_spreadsheet.bat` |
| `pip` / package failures | Network, proxy, and writable user package location |
| ThreatConnect / file errors | `config.json`, VPN, and `Z:\HTOC\` ACLs |

Review timestamped logs under the staging **`logs`** directory named by the launcher.
