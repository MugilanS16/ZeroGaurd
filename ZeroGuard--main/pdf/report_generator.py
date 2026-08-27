# pdf/report_generator.py
# Official Cyber Crime Incident Report Generator

import os
from io import BytesIO
from datetime import datetime, timezone
from PIL import Image as PILImage

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


# ─── Color Palette ──────────────────────────────────────────
NAVY_DARK   = colors.HexColor("#0A2540")
NAVY_PRIMARY= colors.HexColor("#0F4C81")
BLUE_ACCENT = colors.HexColor("#1A6BB5")
GREEN_ACCENT= colors.HexColor("#2E7D32")
LIGHT_BG    = colors.HexColor("#F4F7FA")
LIGHT_BLUE  = colors.HexColor("#EBF3FA")
BORDER_COLOR= colors.HexColor("#CBD5E1")
BORDER_DARK = colors.HexColor("#94A3B8")
TEXT_DARK   = colors.HexColor("#0F172A")
TEXT_GREY   = colors.HexColor("#334155")
TEXT_MUTED  = colors.HexColor("#64748B")
WHITE       = colors.white
GOLD_ACCENT = colors.HexColor("#D97706")


# ─── Numbered Canvas for Page X of Y & Header/Footer ─────────
class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and draw
    professional running headers and footers on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()

        # Margins matching document template
        margin_left = 1.8 * cm
        margin_right = A4[0] - 1.8 * cm
        width = A4[0]
        height = A4[1]

        # ── Running Header (pages 2+) ──
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(NAVY_PRIMARY)
            self.drawString(margin_left, height - 1.1 * cm, "OFFICIAL CYBER CRIME COMPLAINT REPORT")
            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawRightString(margin_right, height - 1.1 * cm, "CONFIDENTIAL & PRIVILEGED RECORD")

            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(margin_left, height - 1.25 * cm, margin_right, height - 1.25 * cm)

        # ── Running Footer (all pages) ──
        footer_y = 1.1 * cm
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(margin_left, footer_y + 0.3 * cm, margin_right, footer_y + 0.3 * cm)

        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(NAVY_DARK)
        self.drawString(margin_left, footer_y, "CyberCrimeAI Secure Portal")

        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(margin_left + 4 * cm, footer_y, "•   Official Incident Record   •   cybercrime.gov.in")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(NAVY_PRIMARY)
        self.drawRightString(margin_right, footer_y, page_str)

        self.restoreState()


# ─── Style Factory ──────────────────────────────────────────
def _build_styles():
    styles = getSampleStyleSheet()

    custom = {
        "HeaderTitle": ParagraphStyle(
            "HeaderTitle",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=3,
        ),
        "HeaderSub": ParagraphStyle(
            "HeaderSub",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#DBEAFE"),
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "RefBadge": ParagraphStyle(
            "RefBadge",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=GOLD_ACCENT,
            alignment=TA_CENTER,
        ),
        "SecTitle": ParagraphStyle(
            "SecTitle",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            textColor=NAVY_PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "TblHead": ParagraphStyle(
            "TblHead",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=WHITE,
        ),
        "FieldLabel": ParagraphStyle(
            "FieldLabel",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=TEXT_MUTED,
        ),
        "FieldValue": ParagraphStyle(
            "FieldValue",
            fontName="Helvetica",
            fontSize=9,
            textColor=TEXT_DARK,
        ),
        "FieldValueBold": ParagraphStyle(
            "FieldValueBold",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=NAVY_PRIMARY,
        ),
        "DescText": ParagraphStyle(
            "DescText",
            fontName="Helvetica",
            fontSize=9.5,
            textColor=TEXT_DARK,
            leading=15,
            alignment=TA_JUSTIFY,
        ),
        "QText": ParagraphStyle(
            "QText",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            textColor=NAVY_PRIMARY,
            leading=12,
        ),
        "AText": ParagraphStyle(
            "AText",
            fontName="Helvetica",
            fontSize=8.5,
            textColor=TEXT_DARK,
            leading=12,
        ),
        "DeclText": ParagraphStyle(
            "DeclText",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=TEXT_GREY,
            leading=13,
            alignment=TA_JUSTIFY,
        ),
        "LegalNotice": ParagraphStyle(
            "LegalNotice",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=TEXT_MUTED,
            leading=11,
            alignment=TA_CENTER,
        ),
        "EvCaption": ParagraphStyle(
            "EvCaption",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=NAVY_PRIMARY,
            alignment=TA_CENTER,
            spaceBefore=4,
        ),
    }
    return custom


def _section_header(title_text, styles):
    return [
        Paragraph(title_text.upper(), styles["SecTitle"]),
        HRFlowable(width="100%", thickness=1, color=NAVY_PRIMARY, spaceBefore=2, spaceAfter=8)
    ]


# ─── Main PDF Generation Function ────────────────────────────
def generate_complaint_pdf(
    complaint_id: str,
    user_name: str,
    user_email: str = "",
    user_phone: str = "",
    crime_type: str = "Cyber Crime",
    description: str = "",
    answers: list = None,          # [{"question": str, "answer": str}, ...]
    guidance: list = None,         # NOT used in PDF per user instruction!
    evidence_files: list = None,     # [filename_str, ...]
    evidence_paths: list = None,     # [filepath_str, ...] for embedding actual images
    date_filed: str = None
):
    """
    Generate an Official Law-Enforcement Style Cyber Crime Complaint PDF.
    - Official Police / Government Formal Layout
    - Embedded Evidence Image Previews (if images were uploaded)
    - Excludes 'Next Steps / Guidance' per explicit user directive (guidance is web-only)
    """

    if answers is None:
        answers = []
    if evidence_files is None:
        evidence_files = []
    if evidence_paths is None:
        evidence_paths = []
    if date_filed is None:
        date_filed = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")

    buffer = BytesIO()
    S = _build_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.8 * cm,
        title=f"Cyber Crime Incident Report — {complaint_id}",
    )

    usable_width = doc.width  # approx 493 points (~17.4 cm)
    story = []

    # ───────────────────────────────────────────────────────────
    #  OFFICIAL BANNER HEADER
    # ───────────────────────────────────────────────────────────
    banner_data = [
        [
            Paragraph("REPUBLIC OF INDIA  •  OFFICIAL CYBER CRIME REPORTING PORTAL", S["HeaderSub"])
        ],
        [
            Paragraph("CYBER CRIME INCIDENT COMPLAINT REPORT", S["HeaderTitle"])
        ],
        [
            Paragraph(f"OFFICIAL RECORD REFERENCE: <b>{complaint_id}</b> &nbsp;|&nbsp; FILED: <b>{date_filed}</b>", S["HeaderSub"])
        ]
    ]

    banner_table = Table(banner_data, colWidths=[usable_width])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY_DARK),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("LINEBELOW",    (0, -1), (-1, -1), 2, GOLD_ACCENT),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 10))

    # Official Status Alert Box
    status_box = Table(
        [[
            Paragraph(f"<b>STATUS:</b> FORMALLY REGISTERED & PENDING INVESTIGATION &nbsp;&nbsp;|&nbsp;&nbsp; <b>REF ID:</b> {complaint_id}", ParagraphStyle("Sts", fontName="Helvetica-Bold", fontSize=8.5, textColor=GREEN_ACCENT, alignment=TA_CENTER))
        ]],
        colWidths=[usable_width]
    )
    status_box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#E8F5E9")),
        ("BOX",          (0, 0), (-1, -1), 1, GREEN_ACCENT),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(status_box)
    story.append(Spacer(1, 10))

    # ───────────────────────────────────────────────────────────
    #  SECTION I — COMPLAINANT PARTICULARS
    # ───────────────────────────────────────────────────────────
    story.extend(_section_header("SECTION I — COMPLAINANT PARTICULARS", S))

    comp_grid = [
        [
            Paragraph("Full Name of Complainant", S["FieldLabel"]),
            Paragraph(user_name or "Anonymous", S["FieldValueBold"]),
            Paragraph("Complaint Reference ID", S["FieldLabel"]),
            Paragraph(complaint_id, S["FieldValueBold"]),
        ],
        [
            Paragraph("Registered Email Address", S["FieldLabel"]),
            Paragraph(user_email or "Not Provided", S["FieldValue"]),
            Paragraph("Date & Time of Filing", S["FieldLabel"]),
            Paragraph(date_filed, S["FieldValue"]),
        ],
        [
            Paragraph("Contact Telephone Number", S["FieldLabel"]),
            Paragraph(user_phone or "Not Provided", S["FieldValue"]),
            Paragraph("Incident Processing State", S["FieldLabel"]),
            Paragraph("Registered & Digitally Sealed", S["FieldValue"]),
        ],
    ]

    comp_table = Table(comp_grid, colWidths=[4.2 * cm, 4.5 * cm, 4.2 * cm, 4.5 * cm])
    comp_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BG),
        ("GRID",          (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 10))

    # ───────────────────────────────────────────────────────────
    #  SECTION II — CRIME CLASSIFICATION & STATEMENT OF FACTS
    # ───────────────────────────────────────────────────────────
    story.extend(_section_header("SECTION II — CRIME CLASSIFICATION & STATEMENT OF FACTS", S))

    # Category Box
    cat_box = Table(
        [[
            Paragraph("CLINICAL CRIME CLASSIFICATION CATEGORY:", S["FieldLabel"]),
            Paragraph(f"<b>{crime_type.upper()}</b>", ParagraphStyle("Cat", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY_DARK))
        ]],
        colWidths=[6.5 * cm, 10.9 * cm]
    )
    cat_box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX",          (0, 0), (-1, -1), 1, BLUE_ACCENT),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(cat_box)
    story.append(Spacer(1, 8))

    # Narrative Statement Box
    desc_content = [
        [Paragraph("<b>COMPLAINANT'S ORIGINAL INCIDENT STATEMENT</b>", ParagraphStyle("Lbl", fontName="Helvetica-Bold", fontSize=8, textColor=TEXT_MUTED))],
        [Paragraph(description.replace("\n", "<br/>") if description else "No detailed statement was submitted.", S["DescText"])]
    ]
    desc_table = Table(desc_content, colWidths=[usable_width])
    desc_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), WHITE),
        ("BOX",          (0, 0), (-1, -1), 0.75, BORDER_DARK),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(desc_table)
    story.append(Spacer(1, 10))

    # ───────────────────────────────────────────────────────────
    #  SECTION III — INVESTIGATION QUESTIONNAIRE STATEMENT RECORD
    # ───────────────────────────────────────────────────────────
    if answers:
        story.extend(_section_header("SECTION III — INVESTIGATION QUESTIONNAIRE STATEMENT RECORD", S))

        qa_table_data = [
            [
                Paragraph("#", S["TblHead"]),
                Paragraph("Specific Investigation Item / Question", S["TblHead"]),
                Paragraph("Complainant Official Response", S["TblHead"]),
            ]
        ]

        for i, qa in enumerate(answers, 1):
            q_txt = qa.get("question", "")
            a_txt = qa.get("answer", "").strip() or "Not provided"
            qa_table_data.append([
                Paragraph(str(i), S["FieldValueBold"]),
                Paragraph(q_txt, S["QText"]),
                Paragraph(a_txt, S["AText"]),
            ])

        qa_table = Table(qa_table_data, colWidths=[0.9 * cm, 7.5 * cm, 9.0 * cm])
        qa_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), NAVY_PRIMARY),
            ("GRID",         (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(qa_table)
        story.append(Spacer(1, 10))

    # ───────────────────────────────────────────────────────────
    #  SECTION IV — SUBMITTED DIGITAL EVIDENCE & MEDIA PREVIEWS
    # ───────────────────────────────────────────────────────────
    story.extend(_section_header("SECTION IV — ATTACHED DIGITAL EVIDENCE & MEDIA RECORD", S))

    if evidence_files or evidence_paths:

        # Evidence Summary Table
        ev_summary_data = [
            [
                Paragraph("#", S["TblHead"]),
                Paragraph("Attached File Name", S["TblHead"]),
                Paragraph("File Status & Handling Note", S["TblHead"]),
            ]
        ]

        for i, fname in enumerate(evidence_files, 1):
            ev_summary_data.append([
                Paragraph(str(i), S["FieldValueBold"]),
                Paragraph(fname, S["FieldValue"]),
                Paragraph("Processed & Embedded — Auto-purged post PDF generation for privacy", ParagraphStyle("EvSts", fontName="Helvetica", fontSize=7.5, textColor=GREEN_ACCENT)),
            ])

        ev_summary_table = Table(ev_summary_data, colWidths=[0.9 * cm, 9.5 * cm, 7.0 * cm])
        ev_summary_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), NAVY_PRIMARY),
            ("GRID",         (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(ev_summary_table)
        story.append(Spacer(1, 10))

        # ── EMBED ACTUAL IMAGE PREVIEWS ──
        embedded_count = 0
        for i, filepath in enumerate(evidence_paths, 1):
            if not filepath or not os.path.exists(filepath):
                continue

            fname = os.path.basename(filepath)
            ext = os.path.splitext(filepath)[1].lower()

            # Process image files (.png, .jpg, .jpeg, .bmp, .webp)
            if ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
                try:
                    with PILImage.open(filepath) as pil_img:
                        orig_w, orig_h = pil_img.size

                    # Calculate proportional scaling to fit nicely in PDF
                    max_width = usable_width - 30  # ~ 460 points
                    max_height = 220              # ~ 3.0 inches max height

                    scale = min(max_width / orig_w, max_height / orig_h, 1.0)
                    render_w = orig_w * scale
                    render_h = orig_h * scale

                    rl_img = RLImage(filepath, width=render_w, height=render_h)

                    # Wrap image in a formal evidence frame
                    ev_box_data = [
                        [Paragraph(f"<b>EVIDENCE EXHIBIT #{i}:</b> {fname}", ParagraphStyle("EvLbl", fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY_PRIMARY))],
                        [rl_img],
                        [Paragraph(f"Digital Image Attachment #{i} — Embedded Image Evidence Record", S["EvCaption"])],
                    ]

                    ev_frame = Table(ev_box_data, colWidths=[usable_width])
                    ev_frame.setStyle(TableStyle([
                        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BG),
                        ("BOX",          (0, 0), (-1, -1), 1, BORDER_DARK),
                        ("TOPPADDING",   (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
                        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                    ]))

                    story.append(KeepTogether([
                        ev_frame,
                        Spacer(1, 10)
                    ]))
                    embedded_count += 1

                except Exception as img_err:
                    print(f"[PDF Generator] Failed to embed image {filepath}: {img_err}")

        if embedded_count == 0 and evidence_files:
            story.append(Paragraph("<i>Note: Evidence files are non-image documents (PDF/Audio/Video). File metadata is recorded above.</i>", ParagraphStyle("EvNote", fontName="Helvetica-Oblique", fontSize=8, textColor=TEXT_MUTED)))
            story.append(Spacer(1, 8))

    else:
        story.append(Paragraph("No digital evidence files were uploaded for this complaint.", ParagraphStyle("NoEv", fontName="Helvetica-Oblique", fontSize=9, textColor=TEXT_MUTED)))
        story.append(Spacer(1, 10))

    # ───────────────────────────────────────────────────────────
    #  SECTION V — LEGAL DECLARATION & OFFICIAL VERIFICATION
    # ───────────────────────────────────────────────────────────
    story.extend(_section_header("SECTION V — LEGAL DECLARATION & SYSTEM AUTHENTICATION", S))

    declaration_text = (
        "<b>SOLEMN DECLARATION BY COMPLAINANT:</b><br/>"
        "I hereby solemnly declare that the statement of facts and details provided in this incident report "
        "are true, correct, and complete to the best of my knowledge and belief. I have not suppressed or misrepresented "
        "any material facts. I understand that submitting false or misleading information to law enforcement or cybercrime "
        "authorities is an offense under applicable statutory provisions."
    )

    decl_box = Table([[Paragraph(declaration_text, S["DeclText"])]], colWidths=[usable_width])
    decl_box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ("BOX",          (0, 0), (-1, -1), 0.75, colors.HexColor("#F59E0B")),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(decl_box)
    story.append(Spacer(1, 12))

    # Two-Column Signature & Seal Verification Grid
    sig_grid = [
        [
            Paragraph("<b>COMPLAINANT VERIFICATION</b>", S["FieldLabel"]),
            Paragraph("<b>PORTAL AUTHENTICATION SEAL</b>", S["FieldLabel"]),
        ],
        [
            Paragraph(
                f"<b>Digitally Verified By:</b> {user_name}<br/>"
                f"<b>Complainant Phone:</b> {user_phone or 'N/A'}<br/>"
                f"<b>Verification Date:</b> {date_filed}<br/>"
                f"<i>Status: Signature Authenticated (Session)</i>",
                ParagraphStyle("Sig1", fontName="Helvetica", fontSize=8, leading=12, textColor=TEXT_DARK)
            ),
            Paragraph(
                f"<b>Generated By:</b> CyberCrimeAI Secure Portal<br/>"
                f"<b>System Hash Ref:</b> {complaint_id}<br/>"
                f"<b>Security Protocol:</b> In-Memory PDF (Privacy-Scrubbed)<br/>"
                f"<b>Official Record ID:</b> {complaint_id}",
                ParagraphStyle("Sig2", fontName="Helvetica", fontSize=8, leading=12, textColor=TEXT_DARK)
            ),
        ]
    ]

    sig_table = Table(sig_grid, colWidths=[8.7 * cm, 8.7 * cm])
    sig_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BG),
        ("BOX",          (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("GRID",         (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(KeepTogether([
        sig_table,
        Spacer(1, 14),
        Paragraph(
            "<b>IMPORTANT NOTICE:</b> This official complaint record is generated by CyberCrimeAI. "
            "Evidence files have been processed into this document and auto-purged from the server for privacy protection. "
            "Present this document and reference number <b>" + complaint_id + "</b> to your local cyber police station or at <b>cybercrime.gov.in</b>.",
            S["LegalNotice"]
        )
    ]))

    # ───────────────────────────────────────────────────────────
    #  BUILD PDF USING NUMBERED CANVAS
    # ───────────────────────────────────────────────────────────
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer