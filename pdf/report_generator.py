import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from flask import current_app

def generate_complaint_pdf(complaint_data: dict, output_filepath: str) -> str:
    """
    Compiles a formal, police-ready Cybercrime Complaint PDF using ReportLab.
    """
    Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
    
    # Defense-in-depth safety check: refuse PDF generation for unverified amount mismatch
    verif_status = complaint_data.get('amount_verification_status', 'N/A')
    if verif_status == 'Mismatch':
        raise ValueError("CRITICAL DEFENSE-IN-DEPTH SECURITY BLOCK: Cannot generate official complaint PDF for an unverified evidence amount mismatch.")

    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F4C81'),
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1E3A5F'),
        alignment=TA_CENTER
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F4C81'),
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        alignment=TA_JUSTIFY
    )
    
    bold_body = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1E293B')
    )

    small_legal = ParagraphStyle(
        'SmallLegal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_CENTER
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("ZEROGUARD AI — CYBERCRIME INCIDENT DOSSIER", title_style))
    story.append(Paragraph("FORMAL COMPLAINT SUBMISSION UNDER INFORMATION TECHNOLOGY ACT, 2000", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0F4C81'), spaceAfter=12))

    # 2. Metadata Table
    ref_no = complaint_data.get('reference_number', 'CC-2026-XXXXX')
    crime_type = complaint_data.get('crime_type', 'Unclassified Cyber Offense')
    risk_level = complaint_data.get('risk_level', 'Medium')
    date_str = complaint_data.get('created_at_str', datetime.now().strftime('%d %B %Y, %I:%M %p'))

    # Format Evidence Status for PDF Stamp
    if verif_status == 'Verified':
        verif_stamp = "<font color='#16A34A'><b>✅ Amount Verified Against Evidence</b></font>"
    elif verif_status == 'Manual Review Needed':
        verif_stamp = "<font color='#D97706'><b>⚠️ Unverified — Pending Manual Review</b></font>"
    elif verif_status == 'Mismatch':
        verif_stamp = "<font color='#DC2626'><b>❌ Amount Mismatched Evidence</b></font>"
    else:
        verif_stamp = "<font color='#64748B'><b>➖ No Financial Amount Claimed</b></font>"

    # Format Evidence Content Relevance Status for PDF Stamp
    rel_status = complaint_data.get('evidence_relevance_status', 'Inconclusive')
    if rel_status in ('Verified', 'Relevant'):
        relevance_stamp = "<font color='#16A34A'><b>✅ Evidence Content Verified — Relevant to Complaint</b></font>"
    elif rel_status == 'Manual Review Needed':
        relevance_stamp = "<font color='#D97706'><b>⚠️ Unverified Evidence — Flagged for Manual Review</b></font>"
    elif rel_status in ('Unverified', 'No Relevant Signal Found'):
        relevance_stamp = "<font color='#DC2626'><b>❌ Unverified Evidence — Content Does Not Match Description</b></font>"
    else:
        relevance_stamp = "<font color='#64748B'><b>➖ Evidence Relevance Not Applicable (No Text Detected)</b></font>"

    meta_data = [
        [Paragraph("<b>Complaint Reference:</b>", bold_body), Paragraph(f"<b>{ref_no}</b>", bold_body),
         Paragraph("<b>Date Reported:</b>", bold_body), Paragraph(date_str, body_style)],
        [Paragraph("<b>Offense Category:</b>", bold_body), Paragraph(crime_type, body_style),
         Paragraph("<b>Evaluated Risk Level:</b>", bold_body), Paragraph(f"<b>{risk_level}</b>", bold_body)],
        [Paragraph("<b>Complainant Name:</b>", bold_body), Paragraph(complaint_data.get('user_name', 'Anonymous Citizen'), body_style),
         Paragraph("<b>Complainant Email:</b>", bold_body), Paragraph(complaint_data.get('user_email', 'Not Provided'), body_style)],
        [Paragraph("<b>Financial Amount Check:</b>", bold_body), Paragraph(verif_stamp, body_style),
         Paragraph("<b>Content Relevance Check:</b>", bold_body), Paragraph(relevance_stamp, body_style)]
    ]

    t_meta = Table(meta_data, colWidths=[125, 140, 125, 140])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    # 3. Formal Narrative Statement
    story.append(Paragraph("1. FORMAL INCIDENT NARRATIVE STATEMENT", section_heading))
    desc = complaint_data.get('description', 'No narrative provided.')
    story.append(Paragraph(desc, body_style))
    story.append(Spacer(1, 14))

    # 4. Question & Answer Evidentiary Table
    answers = complaint_data.get('answers', {})
    if answers:
        story.append(Paragraph("2. EVIDENTIARY QUESTIONNAIRE DETAILS", section_heading))
        qa_rows = [[Paragraph("<b>Field / Attribute</b>", bold_body), Paragraph("<b>Recorded Value</b>", bold_body)]]
        for k, v in answers.items():
            field_name = k.replace('_', ' ').title()
            qa_rows.append([Paragraph(field_name, body_style), Paragraph(str(v), body_style)])

        t_qa = Table(qa_rows, colWidths=[180, 350])
        t_qa.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_qa)
        story.append(Spacer(1, 14))

    # 5. Immediate Containment Checklist
    guidance = complaint_data.get('guidance', [])
    if guidance:
        story.append(Paragraph("3. IMMEDIATE CONTAINMENT ACTIONS & HELPLINE STATUS", section_heading))
        guide_rows = []
        for item in guidance:
            if isinstance(item, dict):
                title = item.get('title', '')
                action = item.get('action', '')
                guide_rows.append([Paragraph(f"• <b>{title}:</b> {action}", body_style)])
            else:
                guide_rows.append([Paragraph(f"• {str(item)}", body_style)])

        t_guide = Table(guide_rows, colWidths=[530])
        t_guide.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_guide)
        story.append(Spacer(1, 14))

    # 6. Uploaded Evidence Meta & OCR Status Stamp
    evidence_meta = complaint_data.get('evidence_meta', [])
    if evidence_meta:
        story.append(Paragraph("4. ATTACHED DIGITAL EVIDENCE METADATA & OCR VERIFICATION", section_heading))
        story.append(Paragraph(f"<b>Content Semantic Verification:</b> {relevance_stamp}", body_style))
        story.append(Spacer(1, 6))

        ev_rows = [[
            Paragraph("<b>Category</b>", bold_body),
            Paragraph("<b>Original File Name</b>", bold_body),
            Paragraph("<b>File Size</b>", bold_body),
            Paragraph("<b>Verification Status</b>", bold_body)
        ]]
        for ev in evidence_meta:
            ev_rows.append([
                Paragraph(ev.get('category', 'Document'), body_style),
                Paragraph(ev.get('original_name', ev.get('name', 'evidence_file')), body_style),
                Paragraph(ev.get('size', 'N/A'), body_style),
                Paragraph(relevance_stamp, body_style)
            ])

        t_ev = Table(ev_rows, colWidths=[100, 160, 60, 210])
        t_ev.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_ev)
        story.append(Spacer(1, 14))

    # 8. Declaration & Signature Block
    story.append(KeepTogether([
        Spacer(1, 10),
        Paragraph("6. COMPLAINANT DECLARATION & AFFIDAVIT", section_heading),
        Paragraph(
            "I hereby declare that the particulars furnished in this complaint dossier are true, correct, and complete to the best of my knowledge and belief. I understand that filing false or fabricated complaints is punishable under relevant provisions of the law.",
            body_style
        ),
        Spacer(1, 24),
        Table([
            [
                Paragraph("<b>Digitally Verified via ZeroGuard AI</b><br/><font color='#64748B'>Timestamp: " + date_str + "</font>", body_style),
                Paragraph("<b>Signature of Complainant / Authorized Signatory</b><br/><br/>________________________________________", ParagraphStyle('RightSig', parent=body_style, alignment=TA_RIGHT))
            ]
        ], colWidths=[260, 270]),
        Spacer(1, 16),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=8),
        Paragraph("ZeroGuard AI Incident Assistance &bull; In collaboration with Cyber Crime Cells across India &bull; Helpline: 1930", small_legal)
    ]))

    doc.build(story)
    return output_filepath
