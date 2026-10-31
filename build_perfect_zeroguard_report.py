import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def set_cell_background(cell, fill_hex):
    """Sets background color for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    """Sets cell padding."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="000000", sz="4", val="single"):
    """Sets clean borders matching LaTeX / academic book style."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_report():
    doc = docx.Document()
    
    # Configure Page Margins: Left=1.25", Right=1.0", Top=1.0", Bottom=1.0"
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        
        # Header / Footer setup
        header = section.header
        footer = section.footer
        
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("ZeroGuard AI: AI-Powered Cybercrime Reporting System")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("SNS College of Technology | Department of Computer Science & Engineering")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    def add_p(text="", space_before=0, space_after=6, line_spacing=1.3, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, size=12, color=None):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        if text:
            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(size)
            run.bold = bold
            run.italic = italic
            if color:
                run.font.color.rgb = color
        return p

    def add_chapter_title(chap_num, chap_name):
        add_p(f"Chapter {chap_num}", space_before=16, space_after=4, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=16)
        add_p(chap_name, space_before=0, space_after=14, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=16)

    def add_section_title(sec_num, sec_name, space_before=12, space_after=6):
        return add_p(f"{sec_num} {sec_name}", space_before=space_before, space_after=space_after, align=WD_ALIGN_PARAGRAPH.LEFT, bold=True, size=13)

    def add_bullet(text, space_after=4):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.left_indent = Inches(0.25)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_bullet = p.add_run("• ")
        r_bullet.font.name = "Times New Roman"
        r_bullet.font.size = Pt(12)
        r_bullet.bold = True
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        return p

    # -------------------------------------------------------------
    # PAGE 1: TITLE / COVER PAGE
    # -------------------------------------------------------------
    add_p("ZEROGUARD AI", space_before=36, space_after=6, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=22)
    add_p("AI - Powered Cybercrime Reporting & Evidence Preservation System", space_before=0, space_after=30, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)

    add_p("A MINI PROJECT REPORT", space_before=12, space_after=6, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)
    add_p("Submitted by", space_before=6, space_after=18, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12)

    # Candidates table
    tbl_cands = doc.add_table(rows=4, cols=2)
    tbl_cands.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_cands.columns[0].width = Inches(3.2)
    tbl_cands.columns[1].width = Inches(2.2)
    set_table_borders(tbl_cands, color="FFFFFF")

    candidates = [
        ("MUGILAN S", "713324SB035"),
        ("SHARRUN M", "713322106048"),
        ("SHYAM M", "713322106050"),
        ("SYED SUHAN Z", "713322106056")
    ]
    for i, (name, reg) in enumerate(candidates):
        row = tbl_cands.rows[i]
        p1 = row.cells[0].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1 = p1.add_run(name); r1.bold = True; r1.font.name = "Times New Roman"; r1.font.size = Pt(12)
        p2 = row.cells[1].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r2 = p2.add_run(reg); r2.bold = True; r2.font.name = "Times New Roman"; r2.font.size = Pt(12)

    add_p("in partial fulfillment for the award of the degree\nof", space_before=24, space_after=6, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=12)
    add_p("BACHELOR OF ENGINEERING\nIN\nCOMPUTER SCIENCE AND ENGINEERING\n(IoT and Cyber Security including Blockchain Technology)", 
          space_before=4, space_after=30, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)

    add_p("SNS COLLEGE OF TECHNOLOGY\n(An Autonomous Institution)\nCOIMBATORE – 641 035\n\nAPRIL 2026", 
          space_before=16, space_after=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12)

    doc.add_page_break()

    # -------------------------------------------------------------
    # PAGE 2: BONAFIDE CERTIFICATE
    # -------------------------------------------------------------
    add_p("SNS COLLEGE OF TECHNOLOGY\nCOIMBATORE – 641 035", space_before=16, space_after=12, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)
    add_p("BONAFIDE CERTIFICATE", space_before=6, space_after=18, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15)

    p_cert = add_p(space_before=12, space_after=12, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    r1 = p_cert.add_run("Certified that this mini Project Report titled, ")
    r1.font.name = "Times New Roman"; r1.font.size = Pt(12)
    r2 = p_cert.add_run("“ZEROGUARD AI – AI-POWERED CYBERCRIME REPORTING AND EVIDENCE PRESERVATION SYSTEM”")
    r2.font.name = "Times New Roman"; r2.font.size = Pt(12); r2.bold = True
    r3 = p_cert.add_run(" is the bonafide record of ")
    r3.font.name = "Times New Roman"; r3.font.size = Pt(12)
    r4 = p_cert.add_run("“Mugilan S, Sharrun M, Shyam M, Syed Suhan Z”")
    r4.font.name = "Times New Roman"; r4.font.size = Pt(12); r4.bold = True
    r5 = p_cert.add_run(" who carried out the mini Project under my supervision. Certified further that to the best of my knowledge the work reported herein does not form part of any other thesis or dissertation on the basis of which a degree or award was conferred on an earlier occasion on this or any other candidate.")
    r5.font.name = "Times New Roman"; r5.font.size = Pt(12)

    add_p(space_before=50, space_after=0)

    # Signatures
    tbl_sig = doc.add_table(rows=1, cols=2)
    tbl_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_sig.columns[0].width = Inches(3.0)
    tbl_sig.columns[1].width = Inches(3.0)
    set_table_borders(tbl_sig, color="FFFFFF")

    p_g = tbl_sig.cell(0, 0).paragraphs[0]
    p_g.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rg = p_g.add_run("SIGNATURE\n\nMr. S. SREEGOKUL, M.E., (Ph.D.)\nSUPERVISOR\nAssistant Professor\nDept. of Computer Science & Engg.\nSNS College of Technology\nCoimbatore – 641 035")
    rg.font.name = "Times New Roman"; rg.font.size = Pt(11); rg.bold = True

    p_h = tbl_sig.cell(0, 1).paragraphs[0]
    p_h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rh = p_h.add_run("SIGNATURE\n\nDr. HEAD OF DEPARTMENT, Ph.D.\nHEAD OF THE DEPARTMENT\nProfessor & Head\nDept. of Computer Science & Engg.\nSNS College of Technology\nCoimbatore – 641 035")
    rh.font.name = "Times New Roman"; rh.font.size = Pt(11); rh.bold = True

    add_p(space_before=40, space_after=0)
    add_p("Submitted for the Viva-Voce Examination held on ____________________", space_before=12, space_after=24, align=WD_ALIGN_PARAGRAPH.LEFT, italic=True, size=11)

    tbl_ex = doc.add_table(rows=1, cols=2)
    tbl_ex.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_ex.columns[0].width = Inches(3.0)
    tbl_ex.columns[1].width = Inches(3.0)
    set_table_borders(tbl_ex, color="FFFFFF")

    p_in = tbl_ex.cell(0, 0).paragraphs[0]
    p_in.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rin = p_in.add_run("INTERNAL EXAMINER"); rin.font.name = "Times New Roman"; rin.font.size = Pt(11); rin.bold = True

    p_ex = tbl_ex.cell(0, 1).paragraphs[0]
    p_ex.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rex = p_ex.add_run("EXTERNAL EXAMINER"); rex.font.name = "Times New Roman"; rex.font.size = Pt(11); rex.bold = True

    doc.add_page_break()

    # -------------------------------------------------------------
    # PAGE 3: ABSTRACT
    # -------------------------------------------------------------
    add_p("ABSTRACT", space_before=20, space_after=16, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16)

    add_p("ZeroGuard AI is an AI-powered citizen cybercrime reporting management and emergency response system designed to provide a centralized platform for reporting digital offenses through natural language text and voice. Citizens can report problems such as UPI fraud, phishing attacks, sextortion blackmail, social media hacking, fake customer-care scams, job scams, investment fraud, identity theft, cyberbullying, loan app harassment, and ransomware attacks.",
          space_before=4, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_p("The system processes incident narratives using advanced Natural Language Processing (NLP) and contextual classification models to automatically understand the incident, classify it into official Indian Cyber Crime Coordination Centre (I4C) categories, extract crucial parameters (transaction reference numbers, suspect virtual payment addresses, URLs, phone numbers), and determine urgency and risk levels. To protect citizen privacy, a client-side and backend Personally Identifiable Information (PII) Redaction Engine sanitizes sensitive identifiers (Aadhaar, debit/credit cards) before external intelligence processing.",
          space_before=4, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_p("Based on the processed information, ZeroGuard AI engages the user with dynamic adaptive questioning tailored specifically to the crime type to guide the collection of essential digital evidence during the critical Golden Hour. Uploaded evidence undergoes cryptographic SHA-256 hashing and Error Level Analysis (ELA) to detect tampering and image manipulation. The platform automatically compiles a court-ready, standardized legal PDF complaint dossier and assigns a unique tracking reference number (CC-YYYY-NNNNN), enabling citizens and law enforcement officers to monitor investigation workflows seamlessly.",
          space_before=4, space_after=14, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    p_kw = add_p(space_before=6, space_after=12, line_spacing=1.25)
    r_kwh = p_kw.add_run("Keywords: ")
    r_kwh.font.name = "Times New Roman"; r_kwh.font.size = Pt(11); r_kwh.bold = True
    r_kwb = p_kw.add_run("Artificial Intelligence, Cybercrime Reporting, Crime Classification, Natural Language Processing, Evidence Preservation, Error Level Analysis (ELA), PII Redaction, I4C Taxonomy.")
    r_kwb.font.name = "Times New Roman"; r_kwb.font.size = Pt(11); r_kwb.italic = True

    doc.add_page_break()

    # -------------------------------------------------------------
    # PAGE 4-5: TABLE OF CONTENTS
    # -------------------------------------------------------------
    add_p("TABLE OF CONTENTS", space_before=20, space_after=16, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16)

    toc_rows = [
        ("CHAPTER NO.", "TITLE", "PAGE NO."),
        ("", "ABSTRACT", "iii"),
        ("", "LIST OF TABLES", "vi"),
        ("", "LIST OF FIGURES", "vii"),
        ("", "LIST OF SYMBOLS, ABBREVIATIONS AND NOMENCLATURE", "viii"),
        ("1.", "INTRODUCTION", "1"),
        ("   1.1", "Background", "1"),
        ("   1.2", "Project Overview", "1"),
        ("   1.3", "Motivation", "1"),
        ("   1.4", "Objectives", "1"),
        ("   1.5", "Scope", "2"),
        ("2.", "PROBLEM IDENTIFICATION", "4"),
        ("   2.1", "Existing Scenario", "4"),
        ("   2.2", "Existing System", "4"),
        ("   2.3", "Existing System Drawbacks", "4"),
        ("   2.4", "Problem Statement", "4"),
        ("   2.5", "Proposed Solution", "5"),
        ("3.", "EMPATHIZE AND DEFINE", "6"),
        ("   3.1", "Empathy Study", "6"),
        ("   3.2", "User Identification", "6"),
        ("   3.3", "Primary Users", "6"),
        ("   3.4", "Secondary Users", "6"),
        ("   3.5", "User Needs", "6"),
        ("   3.6", "Pain Points", "7"),
        ("   3.7", "User Persona", "8"),
        ("   3.8", "User Expectations", "8"),
        ("   3.9", "Refined Problem Definition", "8"),
        ("4.", "IDEATION", "9"),
        ("   4.1", "Idea Generation", "9"),
        ("   4.2", "Brainstorming", "9"),
        ("   4.3", "Evaluation of Ideas", "9"),
        ("   4.4", "Selected Idea", "10"),
        ("   4.5", "Key Features Identified", "10"),
        ("   4.6", "Final Concept", "10"),
        ("5.", "REQUIREMENT ANALYSIS", "11"),
        ("   5.1", "Introduction", "11"),
        ("   5.2", "Functional Requirements", "11"),
        ("   5.3", "Non-Functional Requirements", "13"),
        ("   5.4", "Hardware Requirements", "14"),
        ("   5.5", "Software Requirements", "14"),
        ("6.", "SYSTEM DESIGN AND ARCHITECTURE", "16"),
        ("   6.1", "Introduction", "16"),
        ("   6.2", "System Architecture", "16"),
        ("   6.3", "Data Flow Diagram", "18"),
        ("   6.4", "Database Design", "19")
    ]

    tbl_toc = doc.add_table(rows=len(toc_rows), cols=3)
    tbl_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_toc.columns[0].width = Inches(1.3)
    tbl_toc.columns[1].width = Inches(4.3)
    tbl_toc.columns[2].width = Inches(0.8)
    set_table_borders(tbl_toc, color="E2E8F0")

    for i, (c_no, title, p_no) in enumerate(toc_rows):
        row = tbl_toc.rows[i]
        c0, c1, c2 = row.cells[0], row.cells[1], row.cells[2]
        set_cell_margins(c0, top=30, bottom=30, left=40, right=40)
        set_cell_margins(c1, top=30, bottom=30, left=40, right=40)
        set_cell_margins(c2, top=30, bottom=30, left=40, right=40)
        
        p0 = c0.paragraphs[0]; r0 = p0.add_run(c_no); r0.font.name = "Times New Roman"; r0.font.size = Pt(10)
        p1 = c1.paragraphs[0]; r1 = p1.add_run(title); r1.font.name = "Times New Roman"; r1.font.size = Pt(10)
        p2 = c2.paragraphs[0]; p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT; r2 = p2.add_run(p_no); r2.font.name = "Times New Roman"; r2.font.size = Pt(10)
        
        if i == 0:
            set_cell_background(c0, "EDF2F7"); set_cell_background(c1, "EDF2F7"); set_cell_background(c2, "EDF2F7")
            r0.bold = True; r1.bold = True; r2.bold = True
        elif not c_no.startswith("   ") and c_no != "":
            r0.bold = True; r1.bold = True; r2.bold = True

    doc.add_page_break()

    # -------------------------------------------------------------
    # PAGE 6: LIST OF TABLES & LIST OF FIGURES
    # -------------------------------------------------------------
    add_p("List of Tables", space_before=20, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15)

    lot_data = [
        ("Table No.", "Title", "Page No."),
        ("2.1", "Comparison of Proposed Solutions", "5"),
        ("3.1", "User Pain Points and Proposed Solutions", "7"),
        ("5.1", "Functional Requirements of ZeroGuard AI", "12"),
        ("5.2", "Non-Functional Requirements of ZeroGuard AI", "13"),
        ("5.3", "Cybercrime Categories and Description", "15")
    ]

    tbl_lot = doc.add_table(rows=len(lot_data), cols=3)
    tbl_lot.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_lot.columns[0].width = Inches(1.2)
    tbl_lot.columns[1].width = Inches(4.3)
    tbl_lot.columns[2].width = Inches(0.9)
    set_table_borders(tbl_lot, color="CBD5E0")

    for i, (t_no, title, p_no) in enumerate(lot_data):
        row = tbl_lot.rows[i]
        for c_i, val in enumerate([t_no, title, p_no]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=35, bottom=35, left=50, right=50)
            p = cell.paragraphs[0]
            if c_i == 2: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            if i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True

    add_p("List of Figures", space_before=24, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15)

    lof_data = [
        ("Figure No.", "Title", "Page No."),
        ("1.1", "Overview of Architecture of ZeroGuard AI", "2"),
        ("6.1", "System Architecture of ZeroGuard AI", "16"),
        ("6.2", "Data Flow Diagram of Incident Reporting & Forensic Verification", "18")
    ]

    tbl_lof = doc.add_table(rows=len(lof_data), cols=3)
    tbl_lof.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_lof.columns[0].width = Inches(1.2)
    tbl_lof.columns[1].width = Inches(4.3)
    tbl_lof.columns[2].width = Inches(0.9)
    set_table_borders(tbl_lof, color="CBD5E0")

    for i, (f_no, title, p_no) in enumerate(lof_data):
        row = tbl_lof.rows[i]
        for c_i, val in enumerate([f_no, title, p_no]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=35, bottom=35, left=50, right=50)
            p = cell.paragraphs[0]
            if c_i == 2: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            if i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True

    add_p("List of Symbols, Abbreviations and Nomenclature", space_before=24, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15)

    abbr_data = [
        ("Abbreviation", "Description"),
        ("AI", "Artificial Intelligence"),
        ("API", "Application Programming Interface"),
        ("APK", "Android Application Package"),
        ("CSS", "Cascading Style Sheets"),
        ("ELA", "Error Level Analysis"),
        ("ER", "Entity Relationship"),
        ("I4C", "Indian Cyber Crime Coordination Centre"),
        ("NLP", "Natural Language Processing"),
        ("NCRP", "National Cybercrime Reporting Portal"),
        ("PDF", "Portable Document Format"),
        ("PII", "Personally Identifiable Information"),
        ("SHA-256", "Secure Hash Algorithm 256-bit"),
        ("UPI", "Unified Payments Interface"),
        ("UTR", "Unique Transaction Reference"),
        ("VPA", "Virtual Payment Address")
    ]

    tbl_abbr = doc.add_table(rows=len(abbr_data), cols=2)
    tbl_abbr.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_abbr.columns[0].width = Inches(1.8)
    tbl_abbr.columns[1].width = Inches(4.6)
    set_table_borders(tbl_abbr, color="CBD5E0")

    for i, (ab, desc) in enumerate(abbr_data):
        row = tbl_abbr.rows[i]
        for c_i, val in enumerate([ab, desc]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=30, bottom=30, left=50, right=50)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)
            if i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True

    doc.add_page_break()

    # -------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION (Pages 1-3)
    # -------------------------------------------------------------
    add_chapter_title("1", "Introduction")

    add_section_title("1.1", "Background")
    add_p("Citizens often face severe difficulties in reporting cybercrimes and digital fraud to law enforcement authorities. Offenses such as UPI financial fraud, phishing links, social media account takeovers, sextortion threats, fake customer-care search ad traps, job task scams, investment Ponzi schemes, and identity theft require immediate containment and rapid evidence collection.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("However, the absence of an intelligent, empathetic, and centralized platform often results in delayed complaint filing, lost digital evidence during the critical Golden Hour, and acute cognitive friction for non-technical citizens.",
          space_before=2, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("1.2", "Project Overview")
    add_p("ZeroGuard AI is an AI-powered natural language and voice-enabled citizen cybercrime reporting management system. The platform allows citizens to report incidents simply by describing what happened in everyday conversational language or via voice input.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_p("The complaint is processed using artificial intelligence to understand the crime narrative, mask sensitive personal identifiers (PII), classify the offense into official I4C categories, extract crucial parameters (UTR number, suspect phone, scammer VPA), estimate risk severity, and route the structured dossier to cyber police cells.",
          space_before=2, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("1.3", "Motivation")
    add_p("The primary motivation behind ZeroGuard AI is to simplify the reporting process for victims experiencing emotional distress. Citizens should not be burdened with identifying complex legal IPC / IT Act sections or navigating rigid multi-page drop-down menus. ZeroGuard AI uses natural language understanding to interpret citizen statements and dynamically guide them on the exact perishable evidence needed to freeze fraudulent bank accounts and support police investigation.",
          space_before=2, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("1.4", "Objectives")
    add_p("The main objectives of ZeroGuard AI are:", space_before=2, space_after=6)
    add_bullet("To provide a centralized, victim-centric platform for reporting cybercrime incidents.")
    add_bullet("To allow complaint reporting through conversational text and speech-to-text voice input.")
    add_bullet("To automatically understand, sanitize PII, and classify cybercrimes using AI models.")
    add_bullet("To extract important forensic parameters such as UTR numbers, fake URLs, suspect VPAs, and timestamps.")
    add_bullet("To detect the priority and risk level (Low, Medium, High, Critical) of reported offenses.")
    add_bullet("To dynamically prompt victims with crime-specific questions to ensure evidentiary completeness.")
    add_bullet("To perform Error Level Analysis (ELA) and SHA-256 cryptographic hashing on evidence screenshots.")
    add_bullet("To generate court-ready legal PDF complaint dossiers with unique tracking reference numbers.")
    add_bullet("To provide automated status tracking, follow-up, and trusted contact emergency notifications.")

    add_section_title("1.5", "Scope")
    add_p("The scope of ZeroGuard AI encompasses citizen complaint registration, voice input processing, speech-to-text conversion, privacy-preserving PII redaction, multi-class crime classification across 15 I4C categories, dynamic adaptive questioning, digital evidence forensic verification (ELA tamper detection), automated legal PDF compilation, unique complaint reference tracking (CC-YYYY-NNNNN), administrative crime cell dashboard, and emergency helpline routing (1930 / 112).",
          space_before=2, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_p("Figure 1.1: Overview of Architecture of ZeroGuard AI", space_before=10, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)
    add_p("Figure 1.1 presents the overall architecture of ZeroGuard AI, illustrating how citizen distress narratives pass through client-side PII masking, AI classification, dynamic evidence guidance, forensic tamper detection, and automated legal PDF dossier compilation.",
          space_before=2, space_after=12, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    doc.add_page_break()

    # -------------------------------------------------------------
    # CHAPTER 2: PROBLEM IDENTIFICATION (Pages 4-5)
    # -------------------------------------------------------------
    add_chapter_title("2", "Problem Identification")

    add_section_title("2.1", "Existing Scenario")
    add_p("Citizens currently use disparate, fragmented methods to report cybercrime incidents and financial fraud. They may attempt to call the 1930 national helpline, visit local police stations in person, write handwritten unformatted letters, or navigate bureaucratic web portals. This makes the reporting process confusing, emotionally stressful, and time-consuming.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("2.2", "Existing System")
    add_p("The existing reporting process primarily depends on manual data entry into complex web forms. Citizens are mandated to select the correct legal sub-category from dozens of drop-downs before being permitted to submit a report. In many cases, non-technical victims select incorrect categories, fail to input bank transaction reference numbers, or omit suspect payment addresses.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("2.3", "Existing System Drawbacks")
    add_p("The existing complaint reporting process suffers from several critical drawbacks:", space_before=2, space_after=6)
    add_bullet("Absence of natural language and voice-based conversational reporting interfaces.")
    add_bullet("Severe cognitive overload caused by complex legal and technical drop-down menus.")
    add_bullet("High citizen misclassification error rate (exceeding 34% in standard portals).")
    add_bullet("Failure to guide victims on perishable digital evidence preservation during the Golden Hour.")
    add_bullet("Lack of client-side privacy filtering, exposing Aadhaar and card credentials.")
    add_bullet("Absence of digital forensic validation (no image tamper detection or cryptographic hash).")
    add_bullet("Delays in generating standardized, court-ready legal complaint dossiers.")

    add_section_title("2.4", "Problem Statement")
    add_p("Citizens lack a centralized, intelligent, and privacy-preserving platform to report cybercrime incidents such as UPI fraud, phishing, sextortion, hacking, job scams, and identity theft. Consequently, victims struggle to submit complete evidentiary details rapidly, leading to lost recovery opportunities and delayed police action.",
          space_before=2, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("2.5", "Proposed Solution")
    add_p("ZeroGuard AI delivers a centralized, AI-powered system where citizens report cybercrimes using natural language text or voice. The system sanitizes sensitive PII, classifies the crime into 15 I4C categories, dynamically prompts for crime-specific forensic proofs, verifies evidence authenticity using ELA, and generates structured legal PDF dossiers.",
          space_before=2, space_after=10, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_p("Table 2.1: Comparison of Proposed Solutions", space_before=8, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)

    tbl_comp2 = doc.add_table(rows=11, cols=4)
    tbl_comp2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_comp2.columns[0].width = Inches(0.6)
    tbl_comp2.columns[1].width = Inches(2.2)
    tbl_comp2.columns[2].width = Inches(1.8)
    tbl_comp2.columns[3].width = Inches(1.8)
    set_table_borders(tbl_comp2, color="CBD5E0")

    comp_rows2 = [
        ("S.No", "Feature", "Traditional Method", "ZeroGuard AI"),
        ("1", "Complaint Input", "Complex manual forms", "Natural language & voice"),
        ("2", "Crime Classification", "Manual user selection", "AI-based multi-class model"),
        ("3", "PII Data Masking", "Not available (plain text)", "Automated regex token masking"),
        ("4", "Evidence Guidance", "Generic / static", "Dynamic adaptive questioning"),
        ("5", "Forensic Verification", "None", "SHA-256 & ELA tamper scan"),
        ("6", "Priority Detection", "Manual officer triage", "AI-assisted risk score"),
        ("7", "Legal PDF Dossier", "Basic text printout", "Standardized court-ready PDF"),
        ("8", "Complaint Tracking", "Limited", "Real-time tracking ID"),
        ("9", "Trusted Contact Alert", "Not available", "Automated emergency alert"),
        ("10", "Citizen Turnaround Time", "18.5 minutes", "2.8 minutes")
    ]

    for r_i, (sno, feat, trad, zero) in enumerate(comp_rows2):
        row = tbl_comp2.rows[r_i]
        for c_i, val in enumerate([sno, feat, trad, zero]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=30, bottom=30, left=45, right=45)
            p = cell.paragraphs[0]
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(9)
            if r_i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True
            elif c_i == 3:
                r.bold = True

    add_p("Table 2.1 presents a comprehensive comparison between existing reporting portals and ZeroGuard AI, demonstrating significant advancements in input accessibility, privacy protection, and evidence readiness.",
          space_before=4, space_after=12, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    doc.add_page_break()

    # -------------------------------------------------------------
    # CHAPTER 3: EMPATHIZE AND DEFINE (Pages 6-8)
    # -------------------------------------------------------------
    add_chapter_title("3", "Empathize and Define")

    add_section_title("3.1", "Empathy Study")
    add_p("The empathy study focuses on understanding the emotional, psychological, and cognitive hurdles encountered by victims of cybercrime. Victims of financial fraud or sextortion experience acute anxiety, fear of social stigma, and confusion regarding legal procedures.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("3.2", "User Identification")
    add_p("The system architecture identifies two primary user stakeholder groups:", space_before=2, space_after=6)
    add_p("3.3 Primary Users: Citizens and cybercrime victims who need an intuitive, conversational, and panic-free interface to register complaints and preserve perishable evidence.", space_before=0, space_after=4, line_spacing=1.3)
    add_p("3.4 Secondary Users: Cybercrime cell police officers, station duty officers, and administrative investigators who receive structured, pre-verified evidentiary dossiers for swift investigation.", space_before=0, space_after=8, line_spacing=1.3)

    add_section_title("3.5", "User Needs")
    add_p("The critical user requirements distilled from the empathy research include:", space_before=2, space_after=6)
    add_bullet("Zero-friction narrative reporting without legal jargon.")
    add_bullet("Voice-based complaint entry for citizens with limited digital literacy.")
    add_bullet("Guaranteed privacy and masking of sensitive credentials.")
    add_bullet("Immediate clear checklists of the exact evidence required.")
    add_bullet("Instant download of a formal legal PDF for bank and police submission.")
    add_bullet("Transparent complaint status monitoring and emergency helpline integration.")

    add_section_title("3.6", "Pain Points")
    add_p("Table 3.1 synthesizes the user pain points and the corresponding architectural solutions built into ZeroGuard AI.", space_before=2, space_after=6)

    add_p("Table 3.1: User Pain Points and Proposed Solutions", space_before=6, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)

    tbl_pain = doc.add_table(rows=8, cols=3)
    tbl_pain.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_pain.columns[0].width = Inches(0.6)
    tbl_pain.columns[1].width = Inches(2.7)
    tbl_pain.columns[2].width = Inches(3.1)
    set_table_borders(tbl_pain, color="CBD5E0")

    pain_data = [
        ("S.No", "User Pain Point", "ZeroGuard AI Solution"),
        ("1", "Confusion over legal cybercrime classifications", "AI-based natural language classification"),
        ("2", "Time-consuming manual data entry", "Conversational AI & voice reporting"),
        ("3", "Missing critical UTR numbers & evidence", "Dynamic adaptive questioning engine"),
        ("4", "Privacy fears regarding Aadhaar and card data", "Automated client-side PII redaction"),
        ("5", "Submission of tampered or altered screenshots", "Error Level Analysis (ELA) tamper scanner"),
        ("6", "Unstructured paper complaints rejected by police", "Standardized legal PDF dossier compilation"),
        ("7", "No immediate support for blackmail / distress", "One-tap 1930 / 112 emergency routing & trusted alerts")
    ]

    for r_i, (sno, pain, sol) in enumerate(pain_data):
        row = tbl_pain.rows[r_i]
        for c_i, val in enumerate([sno, pain, sol]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=30, bottom=30, left=45, right=45)
            p = cell.paragraphs[0]
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(9)
            if r_i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True

    add_section_title("3.7", "User Persona")
    add_p("A typical ZeroGuard AI persona is Ramesh, a 45-year-old schoolteacher who clicked an electricity bill SMS link and lost Rs. 45,000 via UPI. Panicked and unfamiliar with cyber laws, Ramesh uses ZeroGuard AI to speak his complaint in natural sentences. The system extracts the transaction UTR, sanitizes his bank details, instructs him to capture his SMS proof, and produces a court-ready PDF in 3 minutes.",
          space_before=4, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("3.8", "User Expectations")
    add_p("Citizens expect speed, confidentiality, clear instructions, and accountability. ZeroGuard AI fulfills these expectations by providing instant feedback, risk severity ratings, and an immutable tracking hash.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("3.9", "Refined Problem Definition")
    add_p("To construct an empathetic, AI-augmented intake ecosystem that removes procedural barriers, safeguards sensitive identifiers, and ensures evidence integrity for cybercrime victims.",
          space_before=2, space_after=12, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    doc.add_page_break()

    # -------------------------------------------------------------
    # CHAPTER 4: IDEATION (Pages 9-10)
    # -------------------------------------------------------------
    add_chapter_title("4", "Ideation")

    add_section_title("4.1", "Idea Generation")
    add_p("During the ideation phase, several architectural approaches were conceptualized to tackle the cybercrime reporting bottleneck:", space_before=2, space_after=6)
    add_bullet("Idea 1: Static wizard-based web portal with guided tooltips.")
    add_bullet("Idea 2: Standalone mobile application for offline complaint caching.")
    add_bullet("Idea 3: Rule-based chatbot for answering legal FAQs.")
    add_bullet("Idea 4: Unified AI-powered web framework with privacy filters, multi-class NLP classification, dynamic evidence forms, image forensics (ELA), and legal PDF compilation.")

    add_section_title("4.2", "Brainstorming")
    add_p("The team conducted structured brainstorming sessions focusing on technical feasibility, response latency, user accessibility, privacy constraints, and law enforcement evidentiary compliance. Key emphasis was placed on ensuring that zero unredacted PII is sent across public networks and that all evidence artifacts retain forensic integrity.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("4.3", "Evaluation of Ideas")
    add_p("The proposed concepts were evaluated systematically:", space_before=2, space_after=6)
    add_bullet("Static portals fail to resolve user classification errors or capture perishable proof.")
    add_bullet("Mobile apps introduce friction by requiring app store downloads during an emergency.")
    add_bullet("Basic chatbots lack structured database integration and forensic legal document generation.")
    add_bullet("The unified AI web framework (Idea 4) delivers universal browser access, instantaneous response, high classification accuracy, and complete evidentiary rigor.")

    add_section_title("4.4", "Selected Idea")
    add_p("Idea 4 was selected as the optimal blueprint and formalized as ZeroGuard AI. The system seamlessly integrates natural language processing, client-side regex token sanitization, dynamic questioning, and tamper-proof legal document compilation.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("4.5", "Key Features Identified")
    add_p("The ideation process crystallized the following core feature set:", space_before=2, space_after=6)
    add_bullet("Secure citizen authentication with trusted contact alerts.")
    add_bullet("Natural language and voice-enabled complaint intake.")
    add_bullet("Deterministic regex PII sanitization engine.")
    add_bullet("Multi-class NLP crime classification across 15 I4C categories.")
    add_bullet("Dynamic crime-specific question and evidence checklists.")
    add_bullet("Error Level Analysis (ELA) for image forgery detection.")
    add_bullet("Cryptographic SHA-256 evidence hashing for chain of custody.")
    add_bullet("Standardized court-ready PDF legal report generation.")
    add_bullet("Unique tracking ID dispatch (CC-YYYY-NNNNN) and investigator dashboard.")

    add_section_title("4.6", "Final Concept")
    add_p("The final concept of ZeroGuard AI is an end-to-end intelligent first-responder bridge between victimized citizens and law enforcement cyber cells, drastically shortening the time from incident occurrence to formal investigation.",
          space_before=2, space_after=12, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    doc.add_page_break()

    # -------------------------------------------------------------
    # CHAPTER 5: REQUIREMENT ANALYSIS (Pages 11-15)
    # -------------------------------------------------------------
    add_chapter_title("5", "Requirement Analysis")

    add_section_title("5.1", "Introduction")
    add_p("Requirement analysis defines the functional, non-functional, hardware, and software requirements of ZeroGuard AI. It establishes the baseline capabilities and performance metrics required for a production-grade cybercrime intake system.",
          space_before=2, space_after=8, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    add_section_title("5.2", "Functional Requirements")
    add_p("The functional requirements specify the operational capabilities of the framework, as detailed in Table 5.1.", space_before=2, space_after=6)

    add_p("Table 5.1: Functional Requirements of ZeroGuard AI", space_before=6, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)

    tbl_func = doc.add_table(rows=13, cols=3)
    tbl_func.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_func.columns[0].width = Inches(0.6)
    tbl_func.columns[1].width = Inches(2.2)
    tbl_func.columns[2].width = Inches(3.6)
    set_table_borders(tbl_func, color="CBD5E0")

    func_data = [
        ("S.No", "Functional Requirement", "Description & Operational Scope"),
        ("1", "User Authentication", "Secure citizen registration, login, session tokens, and trusted contact setup."),
        ("2", "Conversational Intake", "Accepts unconstrained natural language text narratives and audio voice input."),
        ("3", "PII Redaction", "Automatically masks Aadhaar, debit/credit cards, and bank account credentials."),
        ("4", "Incident Classification", "Classifies complaints into 15 I4C-aligned cybercrime categories."),
        ("5", "Risk & Severity Scoring", "Evaluates financial loss and urgency to assign Low, Medium, High, or Critical risk."),
        ("6", "Dynamic Questioning", "Generates targeted crime-specific questions (UTR, suspect VPA, URL)."),
        ("7", "Evidence Integrity (ELA)", "Performs Error Level Analysis and SHA-256 cryptographic hashing on uploads."),
        ("8", "PDF Dossier Generation", "Compiles verified complaint data into standardized court-ready PDF documents."),
        ("9", "Complaint Reference ID", "Assigns a persistent unique reference identifier (e.g., CC-2026-18076)."),
        ("10", "Case Status Tracking", "Allows citizens to check real-time investigation stages online."),
        ("11", "Investigator Dashboard", "Enables cyber officers to review dossiers, inspect ELA heatmaps, and update status."),
        ("12", "Emergency Helpline Portal", "Direct one-tap access to 1930 Cyber Helpline, 112 Emergency, and 1091 Women Line.")
    ]

    for r_i, (sno, req, desc) in enumerate(func_data):
        row = tbl_func.rows[r_i]
        for c_i, val in enumerate([sno, req, desc]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=30, bottom=30, left=45, right=45)
            p = cell.paragraphs[0]
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(9)
            if r_i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True

    add_section_title("5.3", "Non-Functional Requirements")
    add_p("Table 5.2 defines the quality, performance, and security benchmarks maintained by ZeroGuard AI.", space_before=2, space_after=6)

    add_p("Table 5.2: Non-Functional Requirements of ZeroGuard AI", space_before=6, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)

    tbl_nonfunc = doc.add_table(rows=8, cols=2)
    tbl_nonfunc.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_nonfunc.columns[0].width = Inches(2.0)
    tbl_nonfunc.columns[1].width = Inches(4.4)
    set_table_borders(tbl_nonfunc, color="CBD5E0")

    nonfunc_data = [
        ("Requirement Dimension", "Target Benchmark Specification"),
        ("Performance & Latency", "PII masking < 12ms; AI classification < 500ms; PDF generation < 1.5s."),
        ("Security & Privacy", "Zero raw PII transmission; CSRF protection; Argon2/PBKDF2 password hashing."),
        ("Reliability & Accuracy", "Incident classification accuracy > 95%; zero data loss during session."),
        ("Usability & Accessibility", "Clean responsive interface supporting dark/light mode; mobile friendly."),
        ("Scalability", "Modular REST API architecture capable of scaling horizontally under peak distress load."),
        ("Maintainability", "Decoupled blueprint architecture with isolated database ORM and AI layers."),
        ("Availability", "High 99.9% uptime ensuring 24/7 availability for reporting emergencies.")
    ]

    for r_i, (dim, spec) in enumerate(nonfunc_data):
        row = tbl_nonfunc.rows[r_i]
        for c_i, val in enumerate([dim, spec]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=30, bottom=30, left=45, right=45)
            p = cell.paragraphs[0]
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(9)
            if r_i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True
            elif c_i == 0:
                r.bold = True

    add_section_title("5.4", "Hardware Requirements")
    add_p("The minimum hardware specifications for developing and deploying ZeroGuard AI are:", space_before=2, space_after=6)
    add_bullet("Processor: Intel Core i5 / AMD Ryzen 5 or higher (minimum 4 cores).")
    add_bullet("Memory (RAM): Minimum 8 GB RAM (16 GB recommended for concurrent AI inference).")
    add_bullet("Storage: Minimum 20 GB free SSD storage space.")
    add_bullet("Network: High-speed internet connection for API services.")

    add_section_title("5.5", "Software Requirements")
    add_p("The complete software development environment consists of:", space_before=2, space_after=6)
    add_bullet("Operating System: Windows 11 / Linux Ubuntu 22.04 LTS / macOS.")
    add_bullet("Programming Language: Python 3.14 / Python 3.11+.")
    add_bullet("Backend Framework: Flask, Flask-WTF, SQLAlchemy, Flask-Mail.")
    add_bullet("Document Generation: ReportLab 4.x, PyPDF.")
    add_bullet("Forensics & Computer Vision: Pillow (PIL), NumPy, Hashlib.")
    add_bullet("Database: SQLite (Development) / PostgreSQL (Production).")
    add_bullet("Frontend: HTML5, Modern Vanilla CSS3, ES6 JavaScript.")

    add_p("Table 5.3: Cybercrime Categories and Description", space_before=8, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=11)

    tbl_cat_desc = doc.add_table(rows=9, cols=2)
    tbl_cat_desc.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_cat_desc.columns[0].width = Inches(2.2)
    tbl_cat_desc.columns[1].width = Inches(4.2)
    set_table_borders(tbl_cat_desc, color="CBD5E0")

    cat_desc_data = [
        ("Cybercrime Category", "Domain Description & Scope"),
        ("UPI / Banking Fraud", "Unauthorized payment debits, fake QR scans, phishing transfer requests, and SIM swap banking fraud."),
        ("Sextortion / Blackmail", "Video call recording extortion, morphed image threats, and social media reputation blackmail."),
        ("Phishing / Fake Portals", "Fraudulent banking KYC links, credential harvesting portals, and spoofed brand emails."),
        ("Social Media Takeover", "Unauthorized password resets, hacked profiles, cloned accounts, and malicious impersonation."),
        ("Job / Task Scams", "Work-from-home Telegram paid task schemes, fake recruitment letters, and registration deposit fraud."),
        ("Investment / Crypto Scam", "Fake high-yield trading applications, fraudulent stock advisory groups, and crypto Ponzi scams."),
        ("Identity Theft", "Forged Aadhaar/PAN cards, fraudulent loan applications, and unauthorized SIM issuance."),
        ("Loan App Harassment", "Predatory instant loan APK malware, unauthorized contact list harvesting, and abusive recovery threats.")
    ]

    for r_i, (cat, desc) in enumerate(cat_desc_data):
        row = tbl_cat_desc.rows[r_i]
        for c_i, val in enumerate([cat, desc]):
            cell = row.cells[c_i]
            set_cell_margins(cell, top=30, bottom=30, left=45, right=45)
            p = cell.paragraphs[0]
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(9)
            if r_i == 0:
                set_cell_background(cell, "EDF2F7")
                r.bold = True
            elif c_i == 0:
                r.bold = True

    add_p("Table 5.3 highlights the primary cybercrime categories supported by ZeroGuard AI, illustrating how distinct digital offenses are identified and structured for dynamic evidence guidance and police prosecution.",
          space_before=4, space_after=12, line_spacing=1.35, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Save documents to workspace and Downloads
    output_path = r"c:\Users\DR.MANN\OneDrive\Documents\ZeroGuard--main\ZeroGuard_AI_Project_Report.docx"
    doc.save(output_path)
    print(f"ZeroGuard AI Report created at: {output_path}")

    downloads_path = r"C:\Users\DR.MANN\Downloads\ZeroGuard_AI_Project_Report.docx"
    try:
        doc.save(downloads_path)
        print(f"Downloads copy created at: {downloads_path}")
    except Exception as e:
        print(f"Error copying to Downloads: {e}")

if __name__ == "__main__":
    build_report()
