# Standard Operating Procedure
## ThreatConnect Playbook — Get Known Scanning Indicators by ASN (Non-CDN) Tagger

| Field | Detail |
|---|---|
| **SOP Title** | Get Known Scanning Indicators by ASN (Non-CDN) Tagger |
| **Playbook Name** | Get Known Scanning indicators by ASN (none CDN) Tagger |
| **Playbook File** | `Get Known Scanning indicators by ASN (none CDN) Tagger.pbxz` |
| **Playbook Version** | 1.13 |
| **Last Auto-Saved** | April 6, 2026 |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **Input** | ThreatConnect Playbook on `hvs.threatconnect.com` querying `HTOC Org` Address indicators for ASN `396982` |
| **Output** | `Known Scanner PB` tag assignments, Local DataStore records, playbook logs, and failure notification emails |
| **Current Schedule** | Executed every 12 hours at **6:00 AM** and **6:00 PM** via Timer trigger (`0 0 6,18 * * ?`) |
| **Associated Batch Files** | None (ThreatConnect-native playbook process) |
| **SOP location** | **SharePoint** (site **`HTOCDataAnalyticsASA`**): **`Documents/HTOC Data Analytics/SOPs/`** *(published ThreatConnect playbook SOP Markdown files (`SOP_TC_Playbook_*.md`) live here alongside other procedures)* |

---

## 1. Purpose

This ThreatConnect playbook automatically identifies and labels **non-CDN known scanning indicators** within HTOC's own indicator set. It queries for Address indicators belonging to the Google Cloud ASN (396982) that have not yet been labeled, applies the `Known Scanner PB` (**Known Scanner Playbook**) tag to classify them as known non-CDN scanning activity, and stores the indicator data in the ThreatConnect DataStore. Email alerts are sent on any failures.

The `Known Scanner PB` tag is the primary identifier that an indicator has been reviewed and classified by this playbook as originating from a known non-CDN scanning source. The TQL exclusion filter (`NOT hasTag("Known Scanner PB")`) ensures each indicator is only processed once. The playbook runs twice daily to keep labeling current as new indicators are added to ThreatConnect.

This playbook is the **non-CDN counterpart** to the CDN Tagger playbook (`Get CDN Scanning indicators by ASN Tagger.pbxz`), which handles ASN 63949 (Linode/Akamai). Together they cover both CDN and non-CDN scanning infrastructure.

---

## 2. Scope

This procedure applies to HTOC analysts and ThreatConnect administrators who monitor, trigger, modify, or troubleshoot this playbook. It covers the playbook's trigger configuration, step-by-step logic, error handling, and maintenance guidance.

---

## 3. Prerequisites

| Requirement | Notes |
|---|---|
| ThreatConnect access | Must have playbook view/execute permissions |
| HTOC Org indicators | Address indicators with ASN 396982 must be present under the `HTOC Org` owner in ThreatConnect |
| ThreatConnect DataStore | Local DataStore must be available for POST operations |
| Email server configured | SMTPS (Implicit TLS) connection required for failure alert emails |
| Notification recipient | `jaytlin.askew@hhs.gov` — update if ownership changes |

---

## 4. Trigger Configuration

The playbook has three defined triggers. The **12 Hour Trigger** is the current active production trigger. The WebHook Trigger is used for testing and manual execution only.

| Trigger Name | Type | Schedule | Status |
|---|---|---|---|
| **12 Hour Trigger (6AM - 6PM)** | Timer | 6:00 AM and 6:00 PM (`0 0 6,18 * * ?`) | **Active — Production** |
| WebHook Trigger | HttpLink (Webhook) | On demand | Testing / manual use only |
| Every 2 Minutes Trigger (Test Trigger) | Timer | Every 2 minutes (`0 */2 * * * ?`) | Inactive |

### 12 Hour Trigger (Production)

- **Type:** Timer
- **Schedule:** Cron `0 0 6,18 * * ?` — fires at **6:00 AM and 6:00 PM** daily
- **Purpose:** Ensures new non-CDN scanning indicators are tagged and stored twice daily without manual intervention

### WebHook Trigger (Testing / Manual)

- **Type:** HTTP Link (external webhook)
- **Timeout:** 5 minutes
- **Cache:** 120 minutes (prevents duplicate executions within the cache window)
- **HTTP Response Body:** Returns the success log message (`logger.content`) from the final success step
- **Purpose:** Used for testing changes to the playbook or triggering a manual run outside the normal schedule. Send an HTTP request to the webhook URL found in the ThreatConnect playbook editor to invoke it.

> **Note:** Do not leave the WebHook Trigger as the primary active trigger in production. The 12-hour timer is the correct production trigger.

---

## 5. TQL Query

The playbook queries ThreatConnect using the following TQL expression in the **ThreatConnect Get Indicators** step:

```
(ownerName in ("HTOC Org"))
AND typeName in ("Address")
AND addressASN IN (396982)
AND NOT hasTag(summary IN ("Known Scanner PB"))
```

| Filter | Value | Purpose |
|---|---|---|
| Owner | `HTOC Org` | Limits to HTOC's own indicator set |
| Type | `Address` | IP addresses only |
| ASN | 396982 | Targets Google Cloud infrastructure (non-CDN known scanner range) |
| Tag exclusion | `NOT hasTag("Known Scanner PB")` | Skips indicators already processed by this playbook |
| Max results | 5 | Processes up to 5 indicators per execution |
| Fail on no results | No | Gracefully exits with no action if no new indicators are found |

> **Important:** The `NOT hasTag("Known Scanner PB")` filter is what prevents reprocessing. If this tag is removed from an indicator, the playbook will process it again on the next scheduled run.

### Monitored ASN

| ASN | Known Provider |
|---|---|
| 396982 | Google Cloud |

To add additional ASNs, update the `addressASN IN (...)` clause in the TQL field of the **ThreatConnect Get Indicators** step with a comma-separated list.

---

## 6. Playbook Flow

### 6.1 Error Paths

| Failure Point | Behavior |
|---|---|
| **Get Indicators fails** | → Logger: "Get Indicators FAILED. Please check the TQL and summary for output result errors." → Email: subject "GET Indicator Process Failed", body = logger content, to `jaytlin.askew@hhs.gov` |
| **No results found** | Playbook exits cleanly — no email, no error (fail_on_no_results = false) |
| **Iterator fails** | → Email: subject "Get CDN Scanning Indicators by ASN Failed.", to `jaytlin.askew@hhs.gov` |
| **Set HTOC Scanner Identifier (tag add) fails** | → Logger: "Process Failed with an error." (ERROR) → Email: subject "Set HTOC Scanner Identifier Failed", body = TC error message, to `jaytlin.askew@hhs.gov` → Loop continues (does not halt remaining indicators) |

---

## 7. Step Details

### Step 1 — ThreatConnect Get Indicators
- **App:** TCPB - Threatconnect Get Indicators v1 (v1.0.9)
- **Action:** TQL
- **Output:** `tc.indicators.entity` (TCEntityArray) and `tc.indicators.summary` (StringArray)
- **Fail on no results:** No — playbook exits cleanly if no untagged indicators are found
- **Also connects to:** List of Indicators Summary Logger (logs the full summary list for each run)

### Step 1a — List of Indicators Summary Logger
- **App:** Logger (v1.0.0)
- **Level:** INFO
- **Message:** Contents of `tc.indicators.summary` (StringArray) — logs all indicator summaries returned by the query
- **Purpose:** Provides a per-run audit log of which indicators were discovered before the loop begins

### Step 2 — Iterator
- **App:** Iterator (v1.0.0)
- **Input:** `tc.indicators.entity` array from Step 1
- **Output:** `currentIndicator` (TCEntity) — one indicator per loop iteration
- **Loop behavior:** Iterates until all entities are processed; on loop completion (Pass) advances to the Success step; on failure sends an alert email

### Step 3 — ThreatConnect Tags (Get)
- **App:** TCPB - Threatconnect Tags TI v2 (v2.0.7)
- **Action:** Get
- **Entity:** `currentIndicator` from the Iterator
- **Fail on no results:** No — indicators without existing tags proceed normally

### Step 4 — ThreatConnect Set HTOC Scanner Identifier
- **App:** TCPB - Threatconnect Tags TI v2 (v2.0.7)
- **Action:** Add
- **Tag applied:** `Known Scanner PB`
- **Apply to all:** Yes
- **Entity:** `currentIndicator`
- **Fail on error:** Yes — failed tag additions route to the tag-failure email path
- **Purpose:** Marks the indicator as a known non-CDN scanner and prevents reprocessing on future runs

### Step 5 — JMESPath
- **App:** TCPB - JMESPath v3.0 (v3.0.12)
- **Input:** `tc.response.json.raw` from Step 4 (tag response JSON)
- **Expressions:**
  - `[0].summary` → output variable `indicator` (String)
  - `[0]` → output variable `indicatorData` (String)
- **Fail on expression error:** Yes

### Step 6 — DataStore (POST)
- **App:** TCPB - DataStore v4 (v4.0.5)
- **Action:** POST
- **Domain:** Local
- **Data type:** JSON
- **Key (rid):** `indicator` (the indicator summary from JMESPath)
- **Data:** `{"indicatorData": <indicatorData from JMESPath>}`
- **Purpose:** Persists indicator metadata to the ThreatConnect Local DataStore for downstream reference

### Step 7 — Complete Success Logger
- **App:** Logger (v1.0.0)
- **Level:** INFO
- **Message:** "Process completed with no issues"

### Step 8 — Logger (Loop End)
- **App:** Logger (v1.0.0)
- **Level:** INFO
- **Message:** "Tagging process completed."
- **Behavior:** Triggers the EndLoop connection back to the Iterator

### Step 9 — Success Logger
- **App:** Logger (v1.0.0)
- **Level:** INFO
- **Message:** "Get CDN Scanning Indicators by ASN Completed Successfully!"
- **Output:** `logger.content` — returned as the WebHook HTTP response body when triggered via webhook

---

## 8. Email Alerts

All failure notifications are sent to **`jaytlin.askew@hhs.gov`**. Update this address in all three Send Email steps if the playbook owner changes.

| Alert | Subject | Body | Trigger |
|---|---|---|---|
| Get Indicators failed | `GET Indicator Process Failed` | Logger error content | Get Indicators step fails |
| Iterator / no results | `Get CDN Scanning Indicators by ASN Failed.` | Static message | Iterator step fails |
| Tag add failed | `Set HTOC Scanner Identifier Failed` | ThreatConnect error message from tag step | Tag Add step fails |

- **Connection type:** SMTPS (Implicit TLS)
- **Timeout:** 30 seconds
- **Send one:** Yes (single email per event)
- **Fail on error:** No (email failures do not halt the playbook)

> **Known issue:** The Iterator failure email subject reads "Get CDN Scanning Indicators by ASN Failed." — this is a copy-paste artefact from the CDN Tagger and does not affect functionality. Update the subject in the **Send Email** step connected to the Iterator's Fail path if clarity is needed.

---

## 9. Modifying the Playbook

### Adding or Removing Monitored ASNs

1. Open the playbook in the ThreatConnect editor.
2. Click on the **ThreatConnect Get Indicators** step.
3. Update the `addressASN IN (...)` clause in the TQL field.
4. Save and confirm the 12-hour trigger remains active.

### Changing the Max Results per Run

`max_results` is currently **5**. Increase this to process more indicators per execution. With the 12-hour schedule this allows up to 10 indicators tagged per day at the default setting.

### Changing the Scanner Tag Name

The tag `Known Scanner PB` is the marker used to prevent reprocessing. To rename it:

1. Update the `name` parameter in **ThreatConnect Set HTOC Scanner Identifier**.
2. Update the `NOT hasTag(summary IN ("Known Scanner PB"))` clause in the TQL.
3. Bulk-update existing tagged indicators in ThreatConnect before reactivating.

> **Warning:** If the tag name in the TQL exclusion filter is not updated to match the new tag being applied, indicators will be reprocessed on every execution.

### Updating the Notification Email

Update the `recipient` field in all three **Send Email** steps to the new owner's address.

### Managing Triggers

- **12 Hour Trigger (6AM - 6PM):** This is the production trigger. It should always be active during normal operations.
- **WebHook Trigger:** For testing and manual one-off runs only. Confirm the 12-hour timer remains the primary trigger.
- **Every 2 Minutes (Test Trigger):** For development/debugging only. Disable immediately after use.

To toggle a trigger, open the playbook editor, click the trigger, and toggle the Active switch.

---

## 10. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Email: "GET Indicator Process Failed" | TQL syntax error or API connectivity issue | Review the TQL in Get Indicators; verify ThreatConnect connectivity |
| No output, no email, no action | No untagged indicators found for ASN 396982 | Expected behavior — `fail_on_no_results` is false; check ThreatConnect for new Address indicators under ASN 396982 |
| Email: "Set HTOC Scanner Identifier Failed" | Tag add API error — possible permissions issue or indicator locked | Check ThreatConnect permissions for the playbook service account; review the TC error message in the email body |
| Indicators being reprocessed repeatedly | `Known Scanner PB` tag is not persisting | Verify the tag add step is not failing silently; confirm the tag name in the TQL matches exactly (case-sensitive) |
| Iterator failure email says "CDN" in subject | Known copy-paste artefact from the CDN Tagger | Cosmetic only; update the Send Email step subject if needed |
| Playbook not triggering | 12-hour timer inactive or misconfigured | Verify the 12 Hour Trigger is active in the playbook editor |
| DataStore POST errors | Local DataStore unavailable or data format issue | Check ThreatConnect DataStore status; verify JMESPath is producing valid `indicatorData` JSON |

---

## 11. Relationship to Other Playbooks

This playbook is one of a pair covering different scanning infrastructure categories:

| Playbook | Tag Applied | ASN | Provider |
|---|---|---|---|
| **Get Known Scanning indicators by ASN (none CDN) Tagger** *(this playbook)* | `Known Scanner PB` | 396982 | Google Cloud |
| Get CDN Scanning indicators by ASN Tagger | `CDN PB` | 63949 | Linode / Akamai |

Both playbooks share the same structure, run on the same 12-hour schedule, and write to the same Local DataStore. They differ only in the ASN they monitor and the tag they apply.

---

## 12. Maintenance Notes

- **Tag name (`Known Scanner PB`):** This is the production tag name used to classify non-CDN known scanners. Do not rename without simultaneously updating the TQL exclusion filter.
- **Max results = 5:** Processes up to 5 new indicators per execution (10 per day with the 12-hour schedule). Increase if faster catch-up is needed.
- **fail_on_no_results = false:** This playbook is designed to run silently when there are no new indicators to process, unlike the CDN Tagger which alerts on no results. This is intentional.
- **Active trigger is 12 Hour Timer:** The production schedule runs at 6:00 AM and 6:00 PM. The WebHook trigger is for testing only.
- **Version history:** This is version 1.13. Export a new `.pbxz` backup from ThreatConnect after any significant changes.

---

## 13. Related documents

Playbook companion SOPs live in **SharePoint** under **`Documents/HTOC Data Analytics/SOPs/`**.

- `SOP_TC_Playbook_GetCDNScanningIndicatorsByASN.md` — CDN counterpart playbook SOP
- ThreatConnect Playbook documentation: [ThreatConnect Playbook Apps](https://docs.threatconnect.com)
