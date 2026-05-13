# PRISM Scoring Rules

A plain-language reference for how PRISM indicator scores are built up, adjusted, and capped.

---

## 1. How a Score Is Built

### 1.1 What Raises the Score

| Category | Contributing Signal |
|---|---|
| **Threat evidence** | Malware evidence on the indicator |
| | Presence of a named threat actor |
| | Linked incidents or events |
| **Indicator metadata** | Indicator type |
| | Recency — newer indicators add more than older ones |
| **Ratings** | ThreatConnect rating |
| | ThreatConnect confidence |
| | Threat scores from ThreatConnect, VirusTotal, and CAL |
| **Network behavior** | TOR activity |
| | TOR **combined with** strong malware evidence (extra impact) |
| **Breadth** | Number of sources reporting the indicator |
| | Number of partners reporting the indicator |
| **Stacked context** | Bonus when several strong signals appear together |

### 1.2 What Lowers the Score

| Adjustment | Effect |
|---|---|
| PB Scanning tags | Strong reduction to the total score |
| Observation volume | Penalty grows as observation volume grows |
| Botnet-related activity | Reduction, unless overridden by a boost tag or file-type rule |
| False-positive markers | Reduction |
| Scanner-related tags | Reduction |
| Mass-scanning behavior | Additional tiered penalties on top of scanner reduction |

### 1.3 Overrides (Score Set Directly)

| Condition | Result |
|---|---|
| Indicator is a **File hash** | Score is set to **900 (Critical)** automatically |

## 2. Boost Tags

Boost tags raise the score. They fall into three groups.

### 2.1 Country + Threat-Group Pairs

A boost applies only when **both** the country tag and a matching group tag are present.

| Country | Paired Group Tags |
|---|---|
| Iran | MOIS, IRGC, IRGC QF, IRGC CEC, IRGC EWCD, *Sandstorm, *Kitten |
| Russia | SVR, FSB, GRU, *Blizzard, *Bear |
| China | MSS, PLA, PLA SSF, PLA CSF, PLAN, *Panda, *Typhoon, regional SSB groups |
| North Korea | RGB, *Chollima, *Sleet |
| Palestine | Hamas |
| Lebanon | Lebanese Hizballah |

### 2.2 Standalone Boost Tags

Any one of these tags on its own triggers a boost.

| Group | Tags |
|---|---|
| Country / affiliation | vietnam, belarus, palestine, pakistan, india, teampcp, cisco |
| Activity / capability | compromised, trivy, operational relay box, command and control (c2), data exfiltration, wiper, destructive wiper, data wiper, loader/dropper, backdoor/rat, ransomware, remote code execution (rce) |
| Targeted technology / campaign | Fortigate/fortinet, sap netweaver, apt & targeted attack, spacehop, orb, superjumper |

### 2.3 CVE Tags

Any tag matching the pattern `CVE-####-#####` triggers a CVE boost.

---

## 3. Penalty Tags

Penalty tags lower the score. They fall into two groups.

### 3.1 PB Lowering Tags

| Tags |
|---|
| soar indicator pb, scanning cdn pb, known scanning pb, web scanner, active scanning, scan, scanner, scanning |

### 3.2 Botnet Activity Tags

| Tags |
|---|
| scanning, ddos, spam, phishing, cryptojacking, credential stuffing, ransomware, data theft, cross site scripting attacks, sql injections |

> Note: `ransomware` and `scanning` appear in both boost and penalty contexts. The botnet penalty applies when the tag indicates botnet-driven behavior; it can be overridden by a stronger boost signal or by the file-hash override in §1.3.

---

## 4. Penalty Summary

| Penalty Source | Severity |
|---|---|
| PB scanning tags | Significant reduction |
| Botnet tags | Reduction, unless overridden |
| Scanner tags | Reduction |
| High-volume scanning behavior | Additional tiered reduction |
