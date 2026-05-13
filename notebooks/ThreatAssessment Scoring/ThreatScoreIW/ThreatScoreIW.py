# Auto-generated from ThreatScoreIW.ipynb

# %% [code cell 0]
import sys
import os
import urllib3
import logging
import json
from configparser import ConfigParser

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ThreatScoreIW")

def _mask(s: object, keep_last: int = 4) -> str:
    v = "" if s is None else str(s)
    if len(v) <= keep_last:
        return "*" * len(v)
    return ("*" * (len(v) - keep_last)) + v[-keep_last:]

try:
    from IPython.display import display  # type: ignore
except Exception:  # pragma: no cover
    def display(*args, **kwargs):
        print(*args)

# Add your local ThreatConnect SDK to path
sys.path.append(r"Z:\HTOC\Data_Analytics\threatconnect")
from ThreatConnect import ThreatConnect
from RequestObject import RequestObject
from Owners import Owners

# Resolve a valid project root for shared utils imports.
def _resolve_project_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root_from_script = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    candidates = [
        os.environ.get("HTOC_PROJECT_ROOT"),
        repo_root_from_script,
        r"H:\HTOC",
        r"C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if os.path.exists(os.path.join(candidate, "utils", "config_loader.py")):
            return candidate
    raise FileNotFoundError("Could not locate project root containing utils/config_loader.py")

project_root = _resolve_project_root()
if project_root not in sys.path:
    # Insert first so local project modules win over site-packages names.
    sys.path.insert(0, project_root)

from utils.config_loader import load_config

# Resolve a usable config path (prefer real credentials over template placeholders).
def _resolve_config_path(root: str) -> str:
    candidates = [
        os.environ.get("HTOC_CONFIG_PATH"),
        os.path.join(root, "utils", "config.json"),
        r"H:\HTOC\scripts\Data Movement\ThrearConnect-api-pull\utils\config.json",
        r"H:\HTOC\notebooks\HTOCThreatConnect\HTOCThreatConnect\utils\config.json",
        r"H:\HTOC\notebooks\HTOCThreatConnect\build\lib\AlynThreatConnect\utils\config.json",
        r"H:\HTOC\utils\config.json",
    ]
    placeholder_values = {"YOUR_SECRET_KEY", "YOUR_ACCESS_ID", "Your Organization Name"}

    for path in candidates:
        if not path or not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            values = {
                cfg.get("api_secret_key"),
                cfg.get("api_access_id"),
                cfg.get("api_default_org"),
            }
            if not any(v in placeholder_values for v in values):
                return path
        except Exception:
            continue

    raise FileNotFoundError("No non-placeholder ThreatConnect config.json found.")

# Load API config
config_path = _resolve_config_path(project_root)
try:
    api_secret_key, api_access_id, api_base_url, api_default_org = load_config(config_path)
    logger.info("Loaded config from: %s", config_path)
    logger.info("Base URL: %s", api_base_url)
    logger.info("Access ID: %s", _mask(api_access_id))
    logger.info("Default Org: %s", api_default_org)
except Exception as e:
    logger.exception("Failed to load configuration from %s", config_path)
    sys.exit(1)

# Disable SSL verification warnings (use cautiously)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
verify_ssl = False
logger.info("SSL verification disabled: %s", not verify_ssl)

# Initialize ThreatConnect session
try:
    tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
    logger.info("ThreatConnect initialized.")
except Exception as e:
    logger.exception("Failed to initialize ThreatConnect.")
    sys.exit(1)

# Define the owner (organization scope)
owner = 'HTOC Org'

# Create a request object to fetch indicators (or other data)
try:
    ro = RequestObject()
    ro.set_http_method('GET')
    ro.set_owner(owner)
    ro.set_owner_allowed(True)
    # ro.set_resource_pagination(True)  # Uncomment if needed
    logger.info("RequestObject successfully created (owner=%s).", owner)
except Exception as e:
    logger.exception("Failed to initialize RequestObject.")
    sys.exit(1)

# %% [code cell 1]
import pandas as pd
import ast
from datetime import datetime, timedelta
import pytz
import urllib.parse

def _ensure_observed_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure downstream-required columns exist even when API returns no rows."""
    required_cols = ["indicator", "lastObserved", "associatedGroups.data", "tags.data"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype="object")
    return df

# Configuration for ThreatConnect indicator query (aligned with ThreatScoreIW.ipynb)
QUERY_LOOKBACK_HOURS = 48  # rolling wall-clock window in UTC (not calendar midnights)
INDICATOR_TYPE_NAMES = [
    "Address", "EmailAddress", "File", "Host", "URL", "ASN", "CIDR",
    "Email Subject", "Hashtag", "Mutex", "Registry Key", "User Agent",
]
OWNER_NAMES = [
    'HTOC Org',
    'CISA Federal Feed',
    'CMS_CTI',
    'Crowdstrike Falcon Intelligence',
    'DHS CISCP',
    'Intel471',
    'Mandiant Advantage Threat Intelligence',
    'VA_TIP Data',
]
RESULT_PAGE_SIZE = 500  # keep this smaller; same fields, just paged

# Single cutoff instant for TQL, observed_src filter, and workbook filter
_now_utc = datetime.now(pytz.UTC)
_last_observed_cutoff_dt = _now_utc - timedelta(hours=QUERY_LOOKBACK_HOURS)
start = _last_observed_cutoff_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
LAST_OBSERVED_CUTOFF_TS = pd.Timestamp(_last_observed_cutoff_dt)

type_names = INDICATOR_TYPE_NAMES
type_name_condition = ", ".join([f'"{t}"' for t in type_names])

list_of_owners = OWNER_NAMES

# Build owner IN (...) clause
owner_condition = ", ".join([f'"{o}"' for o in list_of_owners])

tql_raw = (
    f'ownerName IN ({owner_condition}) AND '
    f'typeName IN ({type_name_condition}) AND '
    f'lastObserved >= "{start}"'
)

tql_encoded = urllib.parse.quote(tql_raw)

final_results = []
logger.info(
    "Querying indicators (QUERY_LOOKBACK_HOURS=%s) cutoff=%s TQL lastObserved>=%s",
    QUERY_LOOKBACK_HOURS,
    LAST_OBSERVED_CUTOFF_TS,
    start,
)
logger.debug("TQL (raw): %s", tql_raw)

# Query indicators (paginate so you don't 502 with heavy fields)
# Create a NEW RequestObject WITHOUT owner restriction to query across all owners
ro_multi = RequestObject()
ro_multi.set_http_method('GET')

result_start = 0
result_limit = RESULT_PAGE_SIZE

while True:
    try:
        # NOTE: same fields list you requested (tags,observations,associatedGroups,falsePositives,threatAssess)
        # Only change here is removing the trailing comma after threatAssess which can break parsing.
        ro_multi.set_request_uri(
            f'/v3/indicators?tql={tql_encoded}'
            f'&fields=tags,observations,associatedGroups,falsePositives,threatAssess'
            f'&resultStart={result_start}&resultLimit={result_limit}'
        )

        response = tc.api_request(ro_multi)

        ct = response.headers.get('content-type', '')
        if not ct.startswith('application/json'):
            raise RuntimeError(f"Non-JSON response ({ct}): {response.content[:200]}")

        results = response.json()
        data_items = results.get('data', []) or []

        # stop when no more results
        if not data_items:
            logger.info("Indicator query complete (pages=%s).", max(1, result_start // result_limit) if result_start else 0)
            break

        final_results.append(results)
        logger.info("Fetched %s indicators (resultStart=%s).", len(data_items), result_start)
        result_start += result_limit

    except Exception as e:
        logger.exception("Failed to query indicators (resultStart=%s).", result_start)
        break

# Normalize results
normalized_data = []
for result in final_results:
    data_items = result.get('data', [])
    if not data_items:
        logger.warning("API page returned no data items.")
    for item in data_items:
        if isinstance(item, dict) and 'summary' in item:
            normalized_data.append(item)

if normalized_data:
    logger.info("Normalizing %s indicator records.", len(normalized_data))
    observed_src = pd.json_normalize(normalized_data)
    observed_src['indicator'] = observed_src['summary'].astype(str).str.split().str[0].str.strip()
    observed_src['lastObserved'] = pd.to_datetime(observed_src['lastObserved'], utc=True, errors='coerce')
    observed_src = observed_src[observed_src["lastObserved"] >= LAST_OBSERVED_CUTOFF_TS]
    
    # Create a 'sources' column by aggregating ownerName values per indicator
    sources_per_indicator = (
        observed_src.groupby('indicator')['ownerName']
        .apply(lambda x: ', '.join(sorted(set(x))))
        .reset_index()
        .rename(columns={'ownerName': 'sources'})
    )

    # Merge sources back into observed_src
    observed_src = observed_src.merge(sources_per_indicator, on='indicator', how='left')
    # Filter to keep only records where ownerName is 'HTOC Org'
    observed_src = observed_src[observed_src['ownerName'] == 'HTOC Org'].copy()
    # Keep rows where top-level rating >= 3 OR coalesced threatAssessRating >= 3, and confidence >= 50.
    # Coalesce flat vs nested threatAssess columns per row.
    _rating_cols = ("threatAssessRating", "threatAssess.threatAssessRating", "rating")
    _confidence_cols = ("threatAssessConfidence", "threatAssess.threatAssessConfidence", "confidence")

    def _first_non_null_numeric(df, ordered_cols):
        present = [c for c in ordered_cols if c in df.columns]
        if not present:
            return None
        out = pd.to_numeric(df[present[0]], errors="coerce")
        for c in present[1:]:
            s = pd.to_numeric(df[c], errors="coerce")
            out = out.mask(out.isna(), s)
        return out

    _tar = _first_non_null_numeric(observed_src, _rating_cols)
    _tc = _first_non_null_numeric(observed_src, _confidence_cols)
    if _tar is None or _tc is None:
        raise KeyError(
            f"Could not resolve Threat Assess columns. Tried rating={_rating_cols}, "
            f"confidence={_confidence_cols}. Columns: {list(observed_src.columns)}"
        )
    if "rating" in observed_src.columns:
        _r = pd.to_numeric(observed_src["rating"], errors="coerce")
    else:
        _r = pd.Series(float("nan"), index=observed_src.index, dtype=float)

    if "confidence" in observed_src.columns:
        _c = pd.to_numeric(observed_src["confidence"], errors="coerce")
    else:
        _c = pd.Series(float("nan"), index=observed_src.index, dtype=float)

    _pre_ta = len(observed_src)
    # Use >= 50 so a boundary value of 50.0 is included (strict > 50 dropped those rows).
    _pass_rating_band = (_tar >= 3) | (_r >= 3)
    _pass_confidence_band = (_tc >= 50) | (_c >= 50)
    observed_src = observed_src[_pass_rating_band & _pass_confidence_band].copy()
    logger.info(
        "Threat assess filter ((rating>=3 OR threatAssessRating>=3), confidence>=50) "
        "coalescing %s / %s: %s -> %s rows.",
        _rating_cols,
        _confidence_cols,
        _pre_ta,
        len(observed_src),
    )
    observed_src = _ensure_observed_schema(observed_src)
    logger.info("observed_src ready (rows=%s, cols=%s).", len(observed_src), len(observed_src.columns))
else:
    logger.warning("No valid indicator data found.")
    observed_src = _ensure_observed_schema(pd.DataFrame())

# %% [code cell 2]
import pandas as pd

# Load the Excel file
file_path = r"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\Threat_Assessment_Scores.xlsx"
logger.info("Reading Excel scores: %s", file_path)
df = pd.read_excel(file_path)
logger.info("Loaded df (rows=%s, cols=%s).", len(df), len(df.columns))

# Keep only indicators that are also in observed_src
_indicator_col = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in df.columns), None)
if _indicator_col is None:
    raise KeyError(f"Could not find indicator column in df. Columns: {list(df.columns)}")

_observed_indicators = set(observed_src["indicator"].dropna().astype(str))
_pre = len(df)
df = df[df[_indicator_col].astype(str).isin(_observed_indicators)].copy()
logger.info("Filtered df by observed_src indicators: %s -> %s rows.", _pre, len(df))

# Last Observed column: values come only from observed_src (ThreatConnect), not the workbook
_last_observed_col = next(
    (
        c
        for c in [
            "Last Observed",
            "lastObserved",
            "LastObserved",
            "last_observed",
            "LAST OBSERVED",
        ]
        if c in df.columns
    ),
    None,
)
if _last_observed_col is None:
    raise KeyError(f"Could not find 'Last Observed' column in df. Columns: {list(df.columns)}")

_assoc_groups_src_col = "associatedGroups.data"
_assoc_groups_target_col = "Associated Groups"
if _assoc_groups_src_col not in observed_src.columns:
    raise KeyError(
        f"Could not find '{_assoc_groups_src_col}' column in observed_src. Columns: {list(observed_src.columns)}"
    )

def _extract_group_ids(value):
    # Handle scalar nulls safely; avoid pd.isna on list-like values.
    if value is None:
        return pd.NA

    parsed = value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return pd.NA
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return text
    elif isinstance(value, float) and pd.isna(value):
        return pd.NA

    if isinstance(parsed, dict):
        gid = parsed.get("id")
        return f"Group Id: {gid}" if gid is not None else pd.NA

    if isinstance(parsed, list):
        ids = []
        for item in parsed:
            if isinstance(item, dict) and item.get("id") is not None:
                ids.append(f"Group Id: {item.get('id')}")
        return ", ".join(ids) if ids else pd.NA

    return pd.NA

_observed_latest = (
    observed_src.dropna(subset=["indicator"])
    .assign(
        indicator=lambda d: d["indicator"].astype(str),
        lastObserved=lambda d: pd.to_datetime(d["lastObserved"], utc=True, errors="coerce"),
    )
    .sort_values("lastObserved")
    .drop_duplicates(subset=["indicator"], keep="last")
)
_last_obs_by_indicator = _observed_latest.set_index("indicator")["lastObserved"]
_assoc_groups_by_indicator = _observed_latest.set_index("indicator")[_assoc_groups_src_col].map(_extract_group_ids)

# Last Observed: only from ThreatConnect (observed_src); do not fall back to Excel dates
_df_ind = df[_indicator_col].astype(str)
df[_last_observed_col] = pd.to_datetime(_df_ind.map(_last_obs_by_indicator), utc=True, errors="coerce")
_qh = QUERY_LOOKBACK_HOURS if "QUERY_LOOKBACK_HOURS" in globals() else 48
_last_obs_cutoff = (
    LAST_OBSERVED_CUTOFF_TS
    if "LAST_OBSERVED_CUTOFF_TS" in globals()
    else pd.Timestamp(datetime.now(pytz.UTC) - timedelta(hours=_qh), tz="UTC")
)
_pre_lo = len(df)
df = df[df[_last_observed_col].notna() & (df[_last_observed_col] >= _last_obs_cutoff)].copy()
logger.info(
    "Last Observed filter (ThreatConnect only, >= %s): %s -> %s rows.",
    _last_obs_cutoff,
    _pre_lo,
    len(df),
)

_df_ind = df[_indicator_col].astype(str)

# Add associatedGroups.data ids from observed_src by indicator, stored as 'Associated Groups'
if _assoc_groups_target_col in df.columns:
    df[_assoc_groups_target_col] = _df_ind.map(_assoc_groups_by_indicator).combine_first(df[_assoc_groups_target_col])
else:
    df[_assoc_groups_target_col] = _df_ind.map(_assoc_groups_by_indicator)
logger.info("Updated '%s' from observed_src.lastObserved (unique indicators=%s).", _last_observed_col, df[_indicator_col].nunique(dropna=True))

# %% [code cell 3]
import pandas as pd
from datetime import datetime, timedelta

# OpDiv observation files (same as ThreatScoreIW.ipynb)
base_path = r"Z:/HTOC/Data_Analytics/Data/OpDiv_Observations/htoc_opdiv_obs_d{date}.csv"
date_format = "%Y%m%d"


def get_file_paths(base_path, days=2):
    today = datetime.utcnow()
    dates_to_pull = [(today - timedelta(days=i)).strftime(date_format) for i in range(days)]
    file_paths = [base_path.format(date=dt) for dt in dates_to_pull]
    existing_files = [fp for fp in file_paths if os.path.exists(fp)]
    if not existing_files:
        logger.warning("No OpDiv observation files found for the date range.")
    else:
        logger.info("OpDiv files to load: %s", existing_files)
    return existing_files


def load_observed_data(file_paths):
    frames = []
    for fp in file_paths:
        try:
            frames.append(pd.read_csv(fp))
        except Exception:
            logger.exception("Error reading OpDiv file %s", fp)
    if frames:
        out = pd.concat(frames, ignore_index=True)
        logger.info("Loaded OpDiv observations from %s file(s), %s rows.", len(frames), len(out))
    else:
        out = pd.DataFrame()
    return out


file_paths = get_file_paths(base_path, days=2)
observed_data_df = load_observed_data(file_paths)

# %% [code cell 4]
_indicator_col_df = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in df.columns), None)
_indicator_col_obs = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in observed_data_df.columns), None)
_opdiv_col = next((c for c in ["OpDiv", "opdiv", "OPDIV"] if c in observed_data_df.columns), None)
if _indicator_col_df is None:
    raise KeyError(f"Could not find indicator column in df. Columns: {list(df.columns)}")
if _indicator_col_obs is None:
    raise KeyError(
        f"Could not find indicator column in observed_data_df. Columns: {list(observed_data_df.columns)}"
    )
if _opdiv_col is None:
    raise KeyError(f"Could not find OpDiv column in observed_data_df. Columns: {list(observed_data_df.columns)}")

obs = observed_data_df.dropna(subset=[_indicator_col_obs, _opdiv_col]).copy()
obs[_indicator_col_obs] = obs[_indicator_col_obs].astype(str).str.strip()
obs[_opdiv_col] = obs[_opdiv_col].astype(str).str.strip()

partners_by_indicator = obs.groupby(_indicator_col_obs)[_opdiv_col].apply(lambda s: sorted(set(x for x in s if x)))
eligible_partners = partners_by_indicator[partners_by_indicator.str.len() >= 2]
opdiv_map = eligible_partners.apply(lambda vals: ", ".join(vals))

last_24h_multiple_partners = df[df[_indicator_col_df].astype(str).str.strip().isin(eligible_partners.index)].copy()
last_24h_multiple_partners["OpDiv"] = last_24h_multiple_partners[_indicator_col_df].astype(str).str.strip().map(
    opdiv_map
)
last_24h_multiple_partners["Partners"] = last_24h_multiple_partners["OpDiv"]
logger.info("Multi-partner (2+ OpDiv) rows: %s", len(last_24h_multiple_partners))

# %% [code cell 5]
vt_scores = last_24h_multiple_partners["Explanation"].str.extract(r"VT score:\s*(\d+)", expand=False)
vt_scores = pd.to_numeric(vt_scores, errors="coerce")
last_24h_multi_partners_vt15 = last_24h_multiple_partners[vt_scores >= 2]
logger.info("VT>=14 filter: %s rows.", len(last_24h_multi_partners_vt15))

# %% [code cell 6]
final_indicators = last_24h_multi_partners_vt15[
    last_24h_multi_partners_vt15["Severity"].isin(["high", "critical"])
].copy()
logger.info("final_indicators (high/critical): %s rows.", len(final_indicators))

# %% [code cell 7]
tags_path = r"Z:\HTOC\Data_Analytics\Data\Observed_Tags\htoc_observed_indicator_tags.csv"
tags_df = pd.read_csv(tags_path)
tags_indicator_col = None
for col in tags_df.columns:
    if str(col).lower() == "indicator":
        tags_indicator_col = col
        break
if tags_indicator_col is None:
    raise ValueError("Could not find an 'Indicator' column in the tags CSV.")
tags_value_col = None
for col in tags_df.columns:
    if str(col).lower() in ("tags", "tag"):
        tags_value_col = col
        break
if tags_value_col is None:
    raise ValueError(
        f"Could not find a 'Tag' or 'Tags' column in the tags CSV. "
        f"Available columns: {list(tags_df.columns)}"
    )
indicator_to_tags = tags_df.set_index(tags_indicator_col)[tags_value_col].to_dict()
final_tags = final_indicators["Indicator"].map(indicator_to_tags)
final_cols = list(final_indicators.columns)
if "Tags" in final_cols:
    final_cols.remove("Tags")
new_cols = final_cols[:-1] + ["Tags"] + final_cols[-1:]
final_indicators["Tags"] = final_tags
final_indicators = final_indicators[new_cols]

# %% [code cell 8]


def has_iw(tags_value):
    if tags_value is None or (isinstance(tags_value, float) and pd.isna(tags_value)):
        return False
    if not isinstance(tags_value, (list, tuple)):
        return False
    for t in tags_value:
        try:
            if isinstance(t, dict):
                name = str(t.get("name", "")).strip()
            else:
                name = str(t).strip()
            if name.lower() in {"i&w", "i & w", "iw"}:
                return True
        except Exception:
            continue
    return False


if "tags.data" in observed_src.columns:
    observed_src["has_iw"] = observed_src["tags.data"].apply(has_iw)
else:
    observed_src["has_iw"] = False

if observed_src.empty:
    iw_per_indicator = pd.DataFrame(columns=["Indicator", "Reported I&W?_raw"])
else:
    iw_per_indicator = (
        observed_src.groupby("indicator", dropna=False)["has_iw"]
        .max()
        .reset_index()
        .rename(columns={"indicator": "Indicator", "has_iw": "Reported I&W?_raw"})
    )

cols_to_drop = [c for c in final_indicators.columns if c.startswith("Reported I&W?")]
final_indicators = final_indicators.drop(columns=cols_to_drop, errors="ignore")
final_indicators = final_indicators.merge(iw_per_indicator, on="Indicator", how="left")
final_indicators["Reported I&W?"] = (
    final_indicators["Reported I&W?_raw"].fillna(False).map({True: "Yes", False: "No"})
)
final_indicators = final_indicators.drop(columns=["Reported I&W?_raw"])
if "HTOC Threat Score" in final_indicators.columns:
    final_indicators = final_indicators.rename(columns={"HTOC Threat Score": "PRISM Score"})

# %% [code cell 9]
from datetime import datetime

# Build dated output path
today_str = datetime.today().strftime('%Y%m%d')  # e.g. 20260316
output_path = rf"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\ThreatAssessI_W_{today_str}.xlsx"

# Excel can't write timezone-aware datetimes; strip tz info before export
_dt_tz_cols = final_indicators.select_dtypes(include=["datetimetz"]).columns
for _c in _dt_tz_cols:
    final_indicators[_c] = final_indicators[_c].dt.tz_convert(None)

# Write to Excel with explicit column widths/wrapping for readability
logger.info("Writing Excel output: %s", output_path)
try:
    iw_col = "Reported I&W?"
    if iw_col not in final_indicators.columns:
        raise KeyError(f"Missing required column '{iw_col}' for sheet split.")

    final_iw_no = final_indicators[final_indicators[iw_col] == "No"].copy()
    final_iw_yes = final_indicators[final_indicators[iw_col] == "Yes"].copy()

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        final_iw_no.to_excel(writer, index=False, sheet_name="I&W_No")
        final_iw_yes.to_excel(writer, index=False, sheet_name="I&W_Yes")

        workbook = writer.book
        wrap_fmt = workbook.add_format({"text_wrap": True, "valign": "top"})

        for sheet_name, sheet_df in [("I&W_No", final_iw_no), ("I&W_Yes", final_iw_yes)]:
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column(0, len(final_indicators.columns) - 1, 18)

            if "Explanation" in final_indicators.columns:
                _exp_idx = final_indicators.columns.get_loc("Explanation")
                worksheet.set_column(_exp_idx, _exp_idx, 100, wrap_fmt)

            if "Associated Groups" in final_indicators.columns:
                _ag_idx = final_indicators.columns.get_loc("Associated Groups")
                worksheet.set_column(_ag_idx, _ag_idx, 45, wrap_fmt)

        logger.info(
            "Excel write succeeded (total=%s, I&W No=%s, I&W Yes=%s).",
            len(final_indicators),
            len(final_iw_no),
            len(final_iw_yes),
        )
except Exception:
    logger.exception("Excel write failed: %s", output_path)
    raise

output_path

