from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
import xml.sax.saxutils as saxutils
from datetime import datetime

# ── Branding & Professional Palette ───────────────────────────────────────────
PRIMARY_BLUE = colors.HexColor("#0D47A1")  # Deep Navy
SECONDARY_BLUE = colors.HexColor("#1976D2") # Corporate Blue
ACCENT_GREY = colors.HexColor("#F5F5F5")   # Light Background
STATUS_PASS = colors.HexColor("#2E7D32")   # Success Green
STATUS_FAIL = colors.HexColor("#D32F2F")   # Danger Red
STATUS_UNCLEAR = colors.HexColor("#EF6C00") # Warning Amber
STATUS_NA = colors.HexColor("#607D8B")     # Neutral Blue-Grey

VERDICT_COLORS = {
    "PASS":           STATUS_PASS,
    "FAIL":           STATUS_FAIL,
    "UNCLEAR":        STATUS_UNCLEAR,
    "NOT_APPLICABLE": STATUS_NA,
}

def _format_finding(result: dict) -> str:
    """Refined finding formatter for maximum clarity."""
    verdict   = result.get("verdict", "UNCLEAR")
    mismatch  = saxutils.escape(str(result.get("mismatch") or ""))
    evidence  = saxutils.escape(str(result.get("evidence", "") or ""))
    guidance  = saxutils.escape(str(result.get("fail_criteria") or result.get("client_guidance") or ""))
    
    parts = []
    
    if verdict == "PASS":
        if evidence and evidence.lower() not in ("null", "none", "pass", ""):
            parts.append(f"<b>Observation:</b> {evidence.strip()}")
        else:
            parts.append("Compliance verified with drawing standards.")
        return "<br/>".join(parts)
        
    if verdict == "NOT_APPLICABLE":
        return "Not applicable for this site type or work scope."

    # For Failures/Unclear
    if guidance:
        parts.append(f"<b>Engineering Requirement:</b> {guidance}")
    else:
        parts.append("<b>Action:</b> Manual audit required to confirm compliance.")

    if mismatch and mismatch.lower() not in ("null", "none", ""):
        parts.append(f"<b>Discrepancy:</b> {mismatch.strip()}")
        
    if evidence:
        parts.append(f"<b>Audit Evidence:</b> {evidence.strip()}")

    return "<br/>".join(parts)

def generate_report(results: dict, output_path: str, pdf_filename: str):
    """Generate a premium, enterprise-grade compliance report."""
    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                            leftMargin=0.5*inch, rightMargin=0.5*inch, 
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(
        name='MainHeader',
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=colors.white,
        alignment=TA_LEFT,
        leftIndent=12,
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='SubHeader',
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.white,
        alignment=TA_LEFT,
        leftIndent=12
    ))

    body_style = ParagraphStyle("Body", fontSize=8, leading=10, fontName="Helvetica")
    body_bold = ParagraphStyle("BodyBold", fontSize=8, leading=10, fontName="Helvetica-Bold")
    
    story = []

    # 1. ── Premium Header Section ─────────────────────────────────────────────
    header_data = [
        [
            Paragraph("AUDIT COMPLIANCE REPORT", styles['MainHeader']),
            Paragraph(f"Date: {datetime.now().strftime('%d %b %Y | %H:%M')}<br/>File: {pdf_filename}", styles['SubHeader'])
        ]
    ]
    header_table = Table(header_data, colWidths=[5.5*inch, 2.0*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY_BLUE),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))

    # 2. ── Executive Summary ──────────────────────────────────────────────────
    all_results = results.get("results", [])
    total = len(all_results)
    passed = sum(1 for r in all_results if r.get("verdict") == "PASS")
    failed = sum(1 for r in all_results if r.get("verdict") == "FAIL")
    na     = sum(1 for r in all_results if r.get("verdict") == "NOT_APPLICABLE")
    unclear = total - (passed + failed + na)
    
    # Calculate Score
    score = (passed / (total - na) * 100) if (total - na) > 0 else 0
    score_color = STATUS_PASS if score > 90 else (STATUS_UNCLEAR if score > 70 else STATUS_FAIL)

    summary_data = [
        ["Total Rules Audited", "Compliance Score", "Status Breakdown"],
        [
            str(total),
            Paragraph(f"<b><font size=16 color='{score_color.hexval()}'>{score:.1f}%</font></b>", styles['Normal']),
            Paragraph(f"<font color='{STATUS_PASS.hexval()}'>● PASS: {passed}</font> | "
                      f"<font color='{STATUS_FAIL.hexval()}'>● FAIL: {failed}</font> | "
                      f"<font color='{STATUS_UNCLEAR.hexval()}'>● UNCLR: {unclear}</font> | "
                      f"<font color='{STATUS_NA.hexval()}'>● N/A: {na}</font>", body_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.0*inch, 3.0*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.white),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4*inch))

    # 3. ── Findings Table ─────────────────────────────────────────────────────
    story.append(Paragraph("DETAILED AUDIT FINDINGS", ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=12, textColor=PRIMARY_BLUE, spaceAfter=8)))
    
    table_header = [["ID", "Compliance Requirement", "Verdict", "Observation & Required Action"]]
    sorted_results = sorted(all_results, key=lambda x: str(x.get("rule_id", "R999")).upper())
    
    table_data = table_header
    for r in sorted_results:
        verdict = r.get("verdict", "UNCLEAR")
        v_color = VERDICT_COLORS.get(verdict, colors.black).hexval()
        
        rid = Paragraph(f"<b>{saxutils.escape(str(r.get('rule_id', '')))}</b>", body_style)
        text = Paragraph(saxutils.escape(str(r.get("rule_text", ""))), body_style)
        stat = Paragraph(f'<b><font color="{v_color}">{verdict}</font></b>', body_style)
        finding = Paragraph(_format_finding(r), body_style)
        
        table_data.append([rid, text, stat, finding])

    findings_table = Table(table_data, colWidths=[0.6*inch, 2.2*inch, 0.9*inch, 3.8*inch], repeatRows=1)
    findings_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.1, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, ACCENT_GREY])  # Zebra Striping
    ]))
    story.append(findings_table)

    # 4. ── Footer ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*inch))
    footer_text = f"Telecos Engineering Audit Engine V3.0 | Proprietary & Confidential | Generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(f"<font color='grey' size=8>{footer_text}</font>", ParagraphStyle("Footer", alignment=TA_CENTER)))

    try:
        doc.build(story)
    except Exception as e:
        print(f"FAILED TO GENERATE PREMIUM REPORT: {e}")
        raise e
