# Standard Operating Procedure
## ThreatConnect Playbook — Get CDN Scanning Indicators by ASN

| Field | Detail |
|---|---|
| **SOP Title** | Get CDN Scanning Indicators by ASN |
| **Playbook Name** | Get CDN Scanning indicators by ASN Tagger |
| **Playbook File** | `Get CDN Scanning indicators by ASN Tagger.pbxz` |
| **Playbook Version** | 1.8 |
| **Last Auto-Saved** | April 6, 2026 |
| **Owner** | HTOC Data Analytics |
| **Last Reviewed** | April 2026 |
| **Input** | ThreatConnect Playbook on `hvs.threatconnect.com` querying `HTOC Org` Address indicators for ASN `63949` |
| **Output** | `CDN PB` tag assignments, Local DataStore records, playbook logs, and failure notification emails |
| **Current Schedule** | Executed every 12 hours at **6:00 AM** and **6:00 PM** via Timer trigger (`0 0 6,18 * * ?`) |
| **Associated Batch Files** | None (ThreatConnect-native playbook process) |
| **SOP location** | **SharePoint** (site **`HTOCDataAnalyticsASA`**): **`Documents/HTOC Data Analytics/SOPs/`** *(published ThreatConnect playbook SOP Markdown files (`SOP_TC_Playbook_*.md`) live here alongside other procedures)* |

---

## 1. Purpose

This ThreatConnect playbook automatically identifies and labels **CDN-hosted scanning indicators** within HTOC's own indicator set. It queries for Address indicators belonging to the Linode/Akamai ASN (63949) that have not yet been labeled, applies the `CDN PB` (**CDN Playbook**) tag to mark them as CDN-sourced scanning activity, and stores the indicator data in the ThreatConnect DataStore. Email alerts are sent on any failures.

The `CDN PB` tag is the primary identifier that an indicator has been reviewed and classified by this playbook as originating from CDN infrastructure. The TQL exclusion filter (`NOT hasTag("CDN PB")`) ensures each indicator is only processed once. The playbook runs twice daily to keep labeling current as new indicators are added to ThreatConnect.

---

## 2. Scope

This procedure applies to HTOC analysts and ThreatConnect administrators who monitor, trigger, modify, or troubleshoot this playbook. It covers the playbook's trigger configuration, step-by-step logic, error handling, and maintenance guidance.

---

## 3. Prerequisites

| Requirement | Notes |
|---|---|
| ThreatConnect access | Must have playbook view/execute permissions |
| HTOC Org indicators | Address indicators with ASN 63949 must be present under the `HTOC Org` owner in ThreatConnect |
| ThreatConnect DataStore | Local DataStore must be available for POST operations |
| Email server configured | SMTPS (Implicit TLS) connection required for failure alert emails |
| Notification recipient | `jaytlin.askew@hhs.gov` — update if ownership changes |

---

## 4. Trigger Configuration

The playbook has three defined triggers. The **Every 12 Hours Trigger** is the current active production trigger. The WebHook Trigger is used for testing and manual execution only.

| Trigger Name | Type | Schedule | Status |
|---|---|---|---|
| **Every 12 Hours Trigger (6AM-6PM)** | Timer | 6:00 AM and 6:00 PM (`0 0 6,18 * * ?`) | **Active — Production** |
| WebHook Trigger | HttpLink (Webhook) | On demand | Testing / manual use only |
| Every 1 Minute Trigger (Testing Trigger) | Timer | Every 1 minute (`0 * * * * ?`) | Inactive |

### Every 12 Hours Trigger (Production)

- **Type:** Timer
- **Schedule:** Cron `0 0 6,18 * * ?` — fires at **6:00 AM and 6:00 PM** daily
- **Purpose:** Ensures new CDN scanning indicators are tagged and stored twice daily without manual intervention

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
AND addressASN IN (63949)
AND NOT hasTag(summary IN ("CDN PB"))
```

| Filter | Value | Purpose |
|---|---|---|
| Owner | `HTOC Org` | Limits to HTOC's own indicator set |
| Type | `Address` | IP addresses only |
| ASN | 63949 | Targets Linode / Akamai CDN hosting range |
| Tag exclusion | `NOT hasTag("CDN PB")` | Skips indicators already processed by this playbook |
| Max results | 1 | Processes one indicator per execution |

> **Important:** The `NOT hasTag("CDN PB")` filter is what prevents reprocessing. If this tag is removed from an indicator, the playbook will process it again on the next scheduled run.

### Monitored ASN

| ASN | Known Provider |
|---|---|
| 63949 | Linode / Akamai |

To add additional ASNs, update the `addressASN IN (...)` clause in the TQL field of the **ThreatConnect Get Indicators** step and add a comma-separated list of ASN numbers.

---

## 6. Playbook Flow

### 6.1 Error Paths

| Failure Point | Behavior |
|---|---|
| **Get Indicators fails** | → Logger: "Get Indicators FAILED. Please check the TQL and summary for output result errors." → Email: subject "GET Indicator Process Failed", body = logger content, to `jaytlin.askew@hhs.gov` |
| **Iterator fails** (no results returned) | → Email: subject "Get CDN Scanning Indicators by ASN Failed.", body = static message, to `jaytlin.askew@hhs.gov` |
| **Set HTOC Scanner Identifier (tag add) fails** | → Logger: "Process Failed with an error." (ERROR) → Email: subject "Set HTOC Scanner Identifier Failed", body = TC error message, to `jaytlin.askew@hhs.gov` → Loop continues (does not halt the remaining indicators) |

---

## 7. Step Details

### Step 1 — ThreatConnect Get Indicators
- **App:** TCPB - Threatconnect Get Indicators v1 (v1.0.9)
- **Action:** TQL
- **Output:** `tc.indicators.entity` (TCEntityArray) and `tc.indicators.summary` (StringArray)
- **Fail on no results:** Yes — triggers the error path if no new indicators are found
- **Also connects to:** Indicator List Summary Logger (logs the full summary list for each run)

### Step 2 — Iterator
- **App:** Iterator (v1.0.0)
- **Input:** `tc.indicators.entity` array from Step 1
- **Output:** `currentIndicator` (TCEntity) — one indicator per loop iteration
- **Loop behavior:** Iterates until all entities are processed; on loop completion (Pass) advances to the Success step; on failure sends the "playbook failed" email

### Step 3 — ThreatConnect Tags (Get)
- **App:** TCPB - Threatconnect Tags TI v2 (v2.0.7)
- **Action:** Get
- **Entity:** `currentIndicator` from the Iterator
- **Fail on no results:** No — indicators without existing tags proceed normally

### Step 4 — ThreatConnect Set HTOC Scanner Identifier
- **App:** TCPB - Threatconnect Tags TI v2 (v2.0.7)
- **Action:** Add
- **Tag applied:** `CDN PB`
- **Apply to all:** Yes
- **Entity:** `currentIndicator`
- **Fail on error:** Yes — failed tag additions route to the tag-failure email path
- **Purpose:** Marks the indicator as processed so the TQL query excludes it in future runs

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

### Step 1a — Indicator List Summary Logger
- **App:** Logger (v1.0.0)
- **Level:** INFO
- **Message:** Contents of `tc.indicators.summary` (StringArray) — logs all indicator summaries returned by the query
- **Purpose:** Provides a per-run audit log of which indicators were discovered before the loop begins

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
| Iterator / no results | `Get CDN Scanning Indicators by ASN Failed.` | Static: "Get CDN Scanning Indicators by ASN Failed." | Iterator step fails |
| Tag add failed | `Set HTOC Scanner Identifier Failed` | ThreatConnect error message from tag step | Tag Add step fails |

- **Connection type:** SMTPS (Implicit TLS)
- **Timeout:** 30 seconds
- **Send one:** Yes (single email per event, not one per indicator)
- **Fail on error:** No (email failures do not halt the playbook)

---

## 9. Modifying the Playbook

### Adding or Removing Monitored ASNs

1. Open the playbook in the ThreatConnect editor.
2. Click on the **ThreatConnect Get Indicators** step.
3. Update the `addressASN IN (...)` clause in the TQL field.
4. Save and re-activate the playbook.

### Changing the Max Results per Run

The `max_results` parameter in **ThreatConnect Get Indicators** is currently set to **5**. Increase this value to process more indicators per execution. Be aware that higher values increase execution time and the risk of hitting the 5-minute WebHook timeout.

### Changing the Scanner Tag Name

The tag `CDN PB` is the marker used to prevent reprocessing. To rename it:

1. Update the `name` parameter in **ThreatConnect Set HTOC Scanner Identifier**.
2. Update the `NOT hasTag(summary IN ("CDN PB"))` clause in the TQL.
3. Bulk-update existing tagged indicators in ThreatConnect before reactivating to avoid reprocessing.

> **Warning:** If the tag name in the TQL exclusion filter is not updated to match the new tag being applied, indicators will be reprocessed on every execution.

### Updating the Notification Email

Update the `recipient` field in all three **Send Email** steps to the new owner's address.

### Managing Triggers

- **Every 12 Hours (6AM-6PM):** This is the production trigger. It should always be active during normal operations.
- **WebHook Trigger:** For testing and manual one-off runs only. Activate when needed and confirm the 12-hour timer remains the primary trigger.
- **Every 1 Minute (Testing Trigger):** For development/debugging only. Disable immediately after use.

To toggle a trigger, open the playbook editor, click the trigger, and toggle the Active switch.

---

## 10. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Email: "GET Indicator Process Failed" | TQL syntax error, Mandiant feed unavailable, or no matching indicators with fail_on_no_results=true | Review the TQL in Get Indicators; verify the Mandiant feed is active and syncing |
| Email: "Get CDN Scanning Indicators by ASN Failed." | Iterator received an empty or failed entity array | Confirms no new untagged CDN indicators were found for the monitored ASNs — may be normal on low-activity days |
| Email: "Set HTOC Scanner Identifier Failed" | Tag add API error — possible permissions issue or indicator locked | Check ThreatConnect permissions for the playbook service account; review the TC error message in the email body |
| Indicators being reprocessed repeatedly | `CDN PB` tag is not persisting on indicators | Verify the tag add step is not failing silently; confirm the tag name in the TQL matches exactly (case-sensitive) |
| Playbook not triggering | WebHook trigger inactive or webhook URL changed | Verify WebHook Trigger is active in the playbook editor; confirm the calling system has the correct webhook URL |
| DataStore POST errors | Local DataStore unavailable or data format issue | Check ThreatConnect DataStore status; verify JMESPath is producing valid `indicatorData` JSON |
| Playbook times out | Processing via WebHook exceeds 5-minute timeout | The 12-hour timer trigger has no HTTP timeout constraint and is the preferred production trigger; use it instead of the webhook for normal operations |

---

## 11. Maintenance Notes

- **Tag name (`CDN PB`):** This is the production tag name used to mark processed indicators. Do not rename without simultaneously updating the TQL exclusion filter.
- **Max results = 1:** The playbook processes one new indicator per execution. With the 12-hour schedule this means up to 2 new indicators tagged per day. Increase `max_results` if faster catch-up is needed, keeping the 5-minute WebHook timeout in mind if using the webhook trigger.
- **Active trigger is Every 12 Hours:** The production schedule runs at 6:00 AM and 6:00 PM. The WebHook trigger is for testing only and should not be relied upon as the primary execution method.
- **DataStore use:** The Local DataStore is being used to persist indicator data. Ensure periodic review or cleanup of DataStore records to prevent unbounded growth.
- **Version history:** This is version 1.8. Export a new `.pbxz` backup from ThreatConnect after any significant changes.

---

## 12. Related documents

Playbook companion SOPs live in **SharePoint** under **`Documents/HTOC Data Analytics/SOPs/`**.

- ThreatConnect Playbook documentation: [ThreatConnect Playbook Apps](https://docs.threatconnect.com)
- Mandiant Advantage Threat Intelligence feed documentation
