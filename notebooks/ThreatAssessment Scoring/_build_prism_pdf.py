"""Build PRISM_Scoring_Rules.pdf from the structured rules."""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)

OUT = r"h:\HTOC\notebooks\ThreatAssessment Scoring\PRISM_Scoring_Rules.pdf"

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                    fontSize=20, textColor=colors.HexColor("#1F4E79"), spaceAfter=10, spaceBefore=4)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                    fontSize=14, textColor=colors.HexColor("#1F4E79"), spaceBefore=14, spaceAfter=6)
H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName="Helvetica-Bold",
                    fontSize=11.5, textColor=colors.HexColor("#2E75B6"), spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica",
                      fontSize=10, leading=14, spaceAfter=6)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=9, textColor=colors.HexColor("#555555"))
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=9.5, leading=12, spaceAfter=0)
CELL_HDR = ParagraphStyle("CellHdr", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)
NOTE = ParagraphStyle("Note", parent=BODY, fontSize=9.5, leading=13,
                       leftIndent=10, borderPadding=6, backColor=colors.HexColor("#FFF4CE"),
                       borderColor=colors.HexColor("#E0C068"), borderWidth=0.5, spaceBefore=6, spaceAfter=6)

HEADER_BG = colors.HexColor("#1F4E79")
ROW_ALT   = colors.HexColor("#F2F6FB")
GRID      = colors.HexColor("#BFBFBF")

def P(t, s=BODY): return Paragraph(t, s)

def styled_table(data, col_widths, header=True):
    rows = [[Paragraph(c, CELL_HDR) if header and i == 0 else Paragraph(c, CELL)
             for c in row] for i, row in enumerate(data)]
    t = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("GRID", (0,0), (-1,-1), 0.4, GRID),
    ]
    if header:
        cmds += [("BACKGROUND", (0,0), (-1,0), HEADER_BG)]
        for r in range(1, len(rows)):
            if r % 2 == 0:
                cmds.append(("BACKGROUND", (0,r), (-1,r), ROW_ALT))
    t.setStyle(TableStyle(cmds))
    return t

story = []

story.append(P("PRISM Scoring Rules", H1))
story.append(P("A plain-language reference for how PRISM indicator scores are built up, adjusted, and capped.", SMALL))
story.append(Spacer(1, 6))

# 1. How a Score is Built
story.append(P("1. How a Score Is Built", H2))

story.append(P("1.1 What Raises the Score", H3))
raise_data = [
    ["Category", "Contributing Signal"],
    ["Threat evidence", "Malware evidence on the indicator"],
    ["", "Presence of a named threat actor"],
    ["", "Linked incidents or events"],
    ["Indicator metadata", "Indicator type"],
    ["", "Recency &mdash; newer indicators add more than older ones"],
    ["Ratings", "ThreatConnect rating"],
    ["", "ThreatConnect confidence"],
    ["", "Threat scores from ThreatConnect, VirusTotal, and CAL"],
    ["Network behavior", "TOR activity"],
    ["", "TOR <b>combined with</b> strong malware evidence (extra impact)"],
    ["Breadth", "Number of sources reporting the indicator"],
    ["", "Number of partners reporting the indicator"],
    ["Stacked context", "Bonus when several strong signals appear together"],
]
story.append(styled_table(raise_data, [1.5*inch, 4.7*inch]))

story.append(P("1.2 What Lowers the Score", H3))
lower_data = [
    ["Adjustment", "Effect"],
    ["PB Scanning tags", "Strong reduction to the total score"],
    ["Observation volume", "Penalty grows as observation volume grows"],
    ["Botnet-related activity", "Reduction, unless overridden by a boost tag or file-type rule"],
    ["False-positive markers", "Reduction"],
    ["Scanner-related tags", "Reduction"],
    ["Mass-scanning behavior", "Additional tiered penalties on top of scanner reduction"],
]
story.append(styled_table(lower_data, [1.8*inch, 4.4*inch]))

story.append(P("1.3 Overrides (Score Set Directly)", H3))
override_data = [
    ["Condition", "Result"],
    ["Indicator is a <b>file hash</b>", "Score is set to <b>900 (Critical)</b> automatically"],
]
story.append(styled_table(override_data, [2.2*inch, 4.0*inch]))

# 2. Boost Tags
story.append(P("2. Boost Tags", H2))
story.append(P("Boost tags raise the score. They fall into three groups.", BODY))

story.append(P("2.1 Country + Threat-Group Pairs", H3))
story.append(P("A boost applies only when <b>both</b> the country tag and a matching group tag are present.", BODY))
country_data = [
    ["Country", "Paired Group Tags"],
    ["Iran", "MOIS, IRGC, IRGC QF, IRGC CEC, IRGC EWCD, *Sandstorm, *Kitten"],
    ["Russia", "SVR, FSB, GRU, *Blizzard, *Bear"],
    ["China", "MSS, PLA, PLA SSF, PLA CSF, PLAN, *Panda, *Typhoon, regional SSB groups"],
    ["North Korea", "RGB, *Chollima, *Sleet"],
    ["Palestine", "Hamas"],
    ["Lebanon", "Lebanese Hizballah"],
]
story.append(styled_table(country_data, [1.2*inch, 5.0*inch]))

story.append(P("2.2 Standalone Boost Tags", H3))
story.append(P("Any one of these tags on its own triggers a boost.", BODY))
standalone_data = [
    ["Group", "Tags"],
    ["Country / affiliation",
     "vietnam, belarus, palestine, pakistan, india, teampcp, cisco"],
    ["Activity / capability",
     "compromised, trivy, operational relay box, command and control (c2), "
     "data exfiltration, wiper, destructive wiper, data wiper, loader/dropper, "
     "backdoor/rat, ransomware, remote code execution (rce)"],
    ["Targeted technology / campaign",
     "Fortigate/fortinet, sap netweaver, apt &amp; targeted attack, spacehop, orb, superjumper"],
]
story.append(styled_table(standalone_data, [1.8*inch, 4.4*inch]))

story.append(P("2.3 CVE Tags", H3))
story.append(P("Any tag matching the pattern <b>CVE-####-#####</b> triggers a CVE boost.", BODY))

# 3. Penalty Tags
story.append(P("3. Penalty Tags", H2))
story.append(P("Penalty tags lower the score. They fall into two groups.", BODY))

story.append(P("3.1 PB Lowering Tags", H3))
pb_data = [
    ["Tags"],
    ["soar indicator pb, scanning cdn pb, known scanning pb, web scanner, "
     "active scanning, scan, scanner, scanning"],
]
story.append(styled_table(pb_data, [6.2*inch]))

story.append(P("3.2 Botnet Activity Tags", H3))
botnet_data = [
    ["Tags"],
    ["scanning, ddos, spam, phishing, cryptojacking, credential stuffing, "
     "ransomware, data theft, cross site scripting attacks, sql injections"],
]
story.append(styled_table(botnet_data, [6.2*inch]))

story.append(P(
    "<b>Note:</b> <i>ransomware</i> and <i>scanning</i> appear in both boost and "
    "penalty contexts. The botnet penalty applies when the tag indicates "
    "botnet-driven behavior; it can be overridden by a stronger boost signal or "
    "by the file-hash override in &sect;1.3.", NOTE))

# 4. Penalty summary
story.append(P("4. Penalty Summary", H2))
summary_data = [
    ["Penalty Source", "Severity"],
    ["PB scanning tags", "Significant reduction"],
    ["Botnet tags", "Reduction, unless overridden"],
    ["Scanner tags", "Reduction"],
    ["High-volume scanning behavior", "Additional tiered reduction"],
]
story.append(styled_table(summary_data, [2.6*inch, 3.6*inch]))

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(0.75*inch, 0.5*inch, "PRISM Scoring Rules")
    canvas.drawRightString(LETTER[0]-0.75*inch, 0.5*inch, f"Page {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=LETTER,
                        leftMargin=0.75*inch, rightMargin=0.75*inch,
                        topMargin=0.75*inch, bottomMargin=0.75*inch,
                        title="PRISM Scoring Rules")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("Wrote:", OUT)
