# Standard Operating Procedure
## ThreatConnect Playbook — SET SOAR Tagger

| Field | Detail |
|---|---|
| **SOP Title** | SET SOAR Tagger |
| **Playbook Name** | SET SOAR Tagger |
| **Playbook File** | `Z:\HTOC\JA\Documents\TC Playbooks\SET SOAR Tagger.pbxz` |
| **Playbook Version** | 1.16 |
| **Last Auto-Saved** | April 6, 2026 |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **Input** | ThreatConnect indicators in `HTOC Org` matching TQL: Address indicators added in last 1 day and not tagged `SOAR Indicator PB` |
| **Output** | Adds `SOAR Indicator PB` tag to qualifying SOAR-created indicators; writes indicator payloads to Local DataStore; emits logs and failure alert emails |
| **Current Schedule** | Executed every 12 hours at **6:00 AM** and **6:00 PM** via Timer trigger (`0 0 6,18 * * ?`) |
| **Associated Batch Files** | None (ThreatConnect-native playbook process) |

---

## 1. Purpose

This playbook identifies newly added Address indicators in `HTOC Org`, verifies whether they are SOAR-generated, and applies a persistent marker tag (`SOAR Indicator PB`) to those indicators. It also records processed indicator data in ThreatConnect Local DataStore and sends operational alert emails when key processing steps fail.

The tag is used as a control to prevent reprocessing. Indicators already tagged `SOAR Indicator PB` are excluded by TQL on future runs.

---

## 2. Scope

This SOP applies to HTOC analysts and ThreatConnect administrators who monitor, modify, or troubleshoot the **SET SOAR Tagger** playbook.

---

## 3. Trigger Configuration

The playbook has two triggers. The timer trigger is the production trigger.

| Trigger Name | Type | Schedule | Status |
|---|---|---|---|
| **Set SOAR Tag Timer 12 hours** | Timer | `0 0 6,18 * * ?` (6:00 AM and 6:00 PM) | **Active — Production** |
| SOAR Trigger | HttpLink (Webhook) | On demand | Inactive (manual/testing only) |

---

## 4. Selection Logic (TQL)

The **ThreatConnect Get Indicators** step uses the following TQL:

```
typeName in ("Address") and dateAdded >= "NOW() - 1 DAY" and NOT hasTag(summary in ("SOAR Indicator PB")) and ownerName in ("HTOC Org")
```

| Filter | Purpose |
|---|---|
| `typeName in ("Address")` | Processes IP address indicators only |
| `dateAdded >= NOW() - 1 DAY` | Restricts scope to newly added indicators |
| `NOT hasTag(..."SOAR Indicator PB")` | Prevents reprocessing of previously handled indicators |
| `ownerName in ("HTOC Org")` | Restricts to HTOC-owned indicators |
| `max_results = 2000` | Batch upper bound per execution |

---

## 5. Playbook Flow

### 5.1 Primary Processing Path

| Step | App | Action |
|---|---|---|
| 1 | ThreatConnect Get Indicators | Pull candidate indicators by TQL |
| 2 | If / Else | Continue only if indicator count > 0 |
| 3 | Iterator | Process each indicator entity individually |
| 4 | ThreatConnect Attributes Data Pull | Get attributes for current indicator |
| 5 | Pull Indicator's LastName Value (JMESPath) | Extract creator last name from attributes |
| 6 | If 'SOAR' Tag, Else, Skip Tagging | Continue only when extracted last name equals `SOAR` |
| 7 | Indicator's Current Tags | Retrieve pre-action tag state |
| 8 | Assign new Tag to SOAR Indicators | Add tag `SOAR Indicator PB` |
| 9 | Tag JMESPath | Extract indicator summary/data from tag response |
| 10 | DataStore | Write indicator data to Local DataStore |
| 11 | Indicator's Post Action Tags | Retrieve post-action tag state |
| 12 | Compare Pre/Post Process Tagging (Logger) | Log before/after tagging state |
| 13 | Successful Process / None SOAR Indicator Summary | Log completion outcome |

### 5.2 Decision Conditions

- **Count gate:** `tc.indicators.count > 0` (numeric compare)
- **SOAR gate:** extracted `lastName == "SOAR"`
  - `true` -> tag is applied
  - `false` -> no tagging; logs non-SOAR summary

---

## 6. Error Handling and Notifications

Failure paths emit Send Email alerts to `jaytlin.askew@hhs.gov`.

| Failure Point | Email Step | Subject |
|---|---|---|
| Get Indicators step fails | `SET SOAR Tag Failed: GET Indicators Failed` | `SET SOAR Tagger GET Indicator Process Failed` |
| Iterator failure | `SET SOAR Tag Failed: Iterator Failed` | `SET SOAR Tagger Iterator Failed` |
| Tag assignment failure | `Failed SOAR Tagging` | `SET SOAR Tagger Failed` |

Additional logging steps include:
- `Failed Process` (ERROR logger)
- `Get Indicators Debug Summary`
- `Compare Pre/Post Process Tagging`
- `Successful Process`
- `None SOAR Indicator Summary`

---

## 7. Key Configuration Values

| Parameter | Value |
|---|---|
| Tag applied | `SOAR Indicator PB` |
| TC owner scope | `HTOC Org` |
| Indicator type | `Address` |
| TQL time window | `NOW() - 1 DAY` |
| Max results | `2000` |
| Active schedule | Every 12 hours (`6:00 AM`, `6:00 PM`) |

---

## 8. Run Success Criteria

A healthy run should show:

1. Trigger execution at the scheduled time.
2. No failure email sent.
3. For SOAR-created indicators in scope, tag `SOAR Indicator PB` appears after processing.
4. Local DataStore receives entries keyed by indicator summary.
5. Success/compare loggers execute for processed indicators.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| No indicators processed | No new indicators in last day or all already tagged | Validate TQL in ThreatConnect and check indicator ingest timing |
| Indicators skipped unexpectedly | Creator last name is not `SOAR` | Review `ThreatConnect Attributes Data Pull` output and JMESPath extraction |
| Tag not applied but no clear UI error | Tag step failure path triggered | Check failure email body and `Failed Process` logger content |
| Reprocessing occurs | Tag removed/renamed or TQL exclusion mismatch | Confirm tag name is exactly `SOAR Indicator PB` in both TQL and add-tag step |
| Schedule not running | Trigger inactive or playbook disabled | Verify timer trigger active and playbook enabled in ThreatConnect |

---

## 10. Operator Decision Points

- If the process sends repeated failure emails, pause trigger and validate app permissions on Tags/Attributes/DataStore apps.
- If expected SOAR indicators are not tagged, check attribute extraction path before adjusting TQL.
- If throughput exceeds 2000 per run, increase `max_results` or run manually between scheduled intervals.

---

## 11. Related Documents

- `SOP_TC_Playbook_GetCDNScanningIndicatorsByASN.md`
- `SOP_TC_Playbook_GetKnownScanningIndicatorsByASN_NonCDN.md`
- ThreatConnect Playbook documentation: [ThreatConnect Playbooks](https://docs.threatconnect.com)
