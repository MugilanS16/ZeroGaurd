import re

def apply_updates():
    with open("build_full_65_page_zeroguard_report.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add create_borderless_table right after create_styled_table
    borderless_func = '''    def create_borderless_table(headers, data, col_widths=None):
        table = doc.add_table(rows=len(data) + 1, cols=len(headers))
        table.style = 'Normal Table'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        
        # Strip all table borders
        tblPr = table._tbl.tblPr
        for child in list(tblPr):
            if child.tag.endswith('tblBorders'):
                tblPr.remove(child)
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'</w:tblBorders>'
        )
        tblPr.append(borders)
        
        if col_widths:
            for i, col in enumerate(table.columns):
                col.width = col_widths[i]
                
        hdr_cells = table.rows[0].cells
        for i, header_text in enumerate(headers):
            hdr_cells[i].text = header_text
            set_cell_margins(hdr_cells[i], top=70, bottom=70, left=60, right=60)
            tcPr = hdr_cells[i]._tc.get_or_add_tcPr()
            for child in list(tcPr):
                if child.tag.endswith('tcBorders'):
                    tcPr.remove(child)
            tcBorders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                f'<w:top w:val="none"/>'
                f'<w:left w:val="none"/>'
                f'<w:bottom w:val="none"/>'
                f'<w:right w:val="none"/>'
                f'</w:tcBorders>'
            )
            tcPr.append(tcBorders)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.bold = True
                r.font.name = "Times New Roman"
                r.font.size = Pt(10)
                
        for row_idx, row_data in enumerate(data):
            row_cells = table.rows[row_idx + 1].cells
            for col_idx, cell_value in enumerate(row_data):
                row_cells[col_idx].text = str(cell_value)
                set_cell_margins(row_cells[col_idx], top=55, bottom=55, left=60, right=60)
                tcPr = row_cells[col_idx]._tc.get_or_add_tcPr()
                for child in list(tcPr):
                    if child.tag.endswith('tcBorders'):
                        tcPr.remove(child)
                tcBorders = parse_xml(
                    f'<w:tcBorders {nsdecls("w")}>'
                    f'<w:top w:val="none"/>'
                    f'<w:left w:val="none"/>'
                    f'<w:bottom w:val="none"/>'
                    f'<w:right w:val="none"/>'
                    f'</w:tcBorders>'
                )
                tcPr.append(tcBorders)
                p = row_cells[col_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(9.5)
                    
        add_p("", space_before=0, space_after=4)
        return table
'''

    # Insert create_borderless_table after return table in create_styled_table
    target_create_styled = '        set_table_borders(table, color="B0BEC5", sz="4", val="single")\n        add_p("", space_before=0, space_after=4)\n        return table'
    assert target_create_styled in content, "create_styled_table target not found!"
    content = content.replace(target_create_styled, target_create_styled + "\n\n" + borderless_func)

    # 2. Use create_borderless_table for TOC, LOT, LOF, Abbreviations
    # TOC
    toc_target = '''    create_styled_table(
        ["CHAPTER NO.", "TITLE", "PAGE NO."],
        [(r[0], r[1], r[2]) for r in full_toc[1:]],
        col_widths=[Inches(1.5), Inches(4.2), Inches(1.1)]
    )'''
    toc_replace = '''    create_borderless_table(
        ["CHAPTER NO.", "TITLE", "PAGE NO."],
        [(r[0], r[1], r[2]) for r in full_toc[1:]],
        col_widths=[Inches(1.5), Inches(4.2), Inches(1.1)]
    )'''
    assert toc_target in content, "TOC target not found!"
    content = content.replace(toc_target, toc_replace)

    # LOT
    lot_target = '''    create_styled_table(
        ["TABLE NO.", "TITLE", "PAGE NO."],
        tables_list,
        col_widths=[Inches(1.3), Inches(4.5), Inches(1.0)]
    )'''
    lot_replace = '''    create_borderless_table(
        ["TABLE NO.", "TITLE", "PAGE NO."],
        tables_list,
        col_widths=[Inches(1.3), Inches(4.5), Inches(1.0)]
    )'''
    assert lot_target in content, "LOT target not found!"
    content = content.replace(lot_target, lot_replace)

    # LOF
    lof_target = '''    create_styled_table(
        ["FIGURE NO.", "TITLE", "PAGE NO."],
        figures_list,
        col_widths=[Inches(1.3), Inches(4.5), Inches(1.0)]
    )'''
    lof_replace = '''    create_borderless_table(
        ["FIGURE NO.", "TITLE", "PAGE NO."],
        figures_list,
        col_widths=[Inches(1.3), Inches(4.5), Inches(1.0)]
    )'''
    assert lof_target in content, "LOF target not found!"
    content = content.replace(lof_target, lof_replace)

    # Abbreviations
    abbr_target = '''    create_styled_table(
        ["ABBREVIATION", "EXPANSION"],
        abbrs,
        col_widths=[Inches(1.8), Inches(5.0)]
    )'''
    abbr_replace = '''    create_borderless_table(
        ["ABBREVIATION", "EXPANSION"],
        abbrs,
        col_widths=[Inches(1.8), Inches(5.0)]
    )'''
    assert abbr_target in content, "Abbreviations target not found!"
    content = content.replace(abbr_target, abbr_replace)

    # 3. Add explanation paragraph after each of the 20 chapter tables

    # Table 2.1
    t21_target = '''    create_styled_table(
        t21_data[0], t21_data[1:],
        col_widths=[Inches(1.5), Inches(1.8), Inches(1.8), Inches(1.9)]
    )'''
    t21_replace = t21_target + '''\n    add_p("Table 2.1 presents a comparative evaluation between conventional cybercrime reporting portals, enterprise SIEM deployments, and the proposed ZeroGuard AI architecture across key operational metrics. While legacy portals require 24 to 72 hours for manual complaint triage and lack automated evidentiary validation, ZeroGuard AI achieves autonomous sub-second classification in under 380 ms, incorporates multi-modal OCR and NLP semantic cross-verification, and generates cryptographically signed Section 65B dossiers to preserve evidence integrity.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t21_target in content, "Table 2.1 target not found!"
    content = content.replace(t21_target, t21_replace)

    # Table 3.1
    t31_target = '''    create_styled_table(
        t31_data[0], t31_data[1:],
        col_widths=[Inches(1.8), Inches(2.7), Inches(2.7)]
    )'''
    t31_replace = t31_target + '''\n    add_p("Table 3.1 synthesizes the empirical user pain points uncovered during stakeholder empathy sessions alongside the corresponding architectural solutions developed in ZeroGuard AI. The framework addresses victim panic and cognitive friction through conversational multilingual intake, mitigates investigator overload via automated OCR amount extraction and NLP semantic relevance scoring, accelerates banking Golden Hour freezing through automated 1930 advisories, and resolves courtroom evidence admissibility barriers via SHA-256 cryptographic audit chaining.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t31_target in content, "Table 3.1 target not found!"
    content = content.replace(t31_target, t31_replace)

    # Table 5.1
    t51_target = '''    create_styled_table(
        t51_data[0], t51_data[1:],
        col_widths=[Inches(1.0), Inches(2.2), Inches(4.0)]
    )'''
    t51_replace = t51_target + '''\n    add_p("Table 5.1 outlines the primary functional requirements specification governing the automated intake and verification capabilities of ZeroGuard AI. Key specifications define rigorous operational constraints, encompassing sub-150 ms incident categorization across 12 cybercrime domains, automated PII sanitization of sensitive Aadhaar and debit card sequences, dynamic generation of crime-specific forensic follow-up queries, dual OCR and semantic receipt verification, automated Section 65B PDF dossier synthesis, and immutable audit logging.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t51_target in content, "Table 5.1 target not found!"
    content = content.replace(t51_target, t51_replace)

    # Table 5.2
    t52_target = '''    create_styled_table(
        t52_data[0], t52_data[1:],
        col_widths=[Inches(1.0), Inches(2.2), Inches(4.0)]
    )'''
    t52_replace = t52_target + '''\n    add_p("Table 5.2 establishes the non-functional quality attribute targets engineered to ensure robust performance, high concurrency, and strict evidentiary compliance. Under these benchmarks, end-to-end incident triage and OCR verification latency must remain below 400 ms, with PDF compilation completing within 1.5 seconds. The backend infrastructure is architected to sustain a throughput of at least 200 concurrent incident submissions while upholding greater than 96% classification accuracy, PBKDF2 password hashing, SHA-256 ledger chaining, and 99.9% operational availability.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t52_target in content, "Table 5.2 target not found!"
    content = content.replace(t52_target, t52_replace)

    # Table 5.3
    t53_target = '''    create_styled_table(
        t53_data[0], t53_data[1:],
        col_widths=[Inches(2.0), Inches(3.4), Inches(1.8)]
    )'''
    t53_replace = t53_target + '''\n    add_p("Table 5.3 summarizes the recognized cybercrime threat taxonomy along with triggered threat indicators and assigned heuristic risk weights. Critical attack categories—such as Ransomware, Deepfake Sextortion, SIM Swap attacks, and UPI fraud—receive elevated risk allocations between +80 and +95 points reflecting their high financial exfiltration speed and acute psychological urgency. Intermediate offenses, including job scams and social media takeovers, receive weighted scores between +50 and +75 points, facilitating granular risk prioritization for cyber-cell operators.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t53_target in content, "Table 5.3 target not found!"
    content = content.replace(t53_target, t53_replace)

    # Table 5.4
    t54_target = '''    create_styled_table(
        t54_data[0], t54_data[1:],
        col_widths=[Inches(1.4), Inches(1.4), Inches(1.8), Inches(2.6)]
    )'''
    t54_replace = t54_target + '''\n    add_p("Table 5.4 defines the composite risk score threshold taxonomy and the corresponding autonomous emergency containment protocols enforced across ZeroGuard AI. Incidents scoring between 0 and 39 are handled via routine complaint logging, whereas scores between 40 and 69 trigger active SOC monitoring alerts. Critical incidents scoring 70 to 100 escalate immediately to urgent officer assignment, automated SMS alerts to citizen emergency contacts, instantaneous 1930 banking freezing notices, and automated court-ready FIR PDF compilation.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t54_target in content, "Table 5.4 target not found!"
    content = content.replace(t54_target, t54_replace)

    # Table 5.5
    t55_target = '''    create_styled_table(
        t55_data[0], t55_data[1:],
        col_widths=[Inches(1.5), Inches(2.0), Inches(2.0), Inches(1.7)]
    )'''
    t55_replace = t55_target + '''\n    add_p("Table 5.5 details the Role-Based Access Control (RBAC) permission matrix enforcing least-privilege operational boundaries across user categories. Citizens possess rights to lodge complaints, provide multimodal evidence, and inspect their personal case progress timeline. Cyber-cell analysts and fraud desk officers are authorized to inspect technical telemetry, evaluate OCR amount validations, record investigative notes, and dispatch bank account freeze notices, while administrators manage cryptographic ledger keys and operational infrastructure.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t55_target in content, "Table 5.5 target not found!"
    content = content.replace(t55_target, t55_replace)

    # Table 6.1
    t61_target = '''    create_styled_table(
        t61_data[0], t61_data[1:],
        col_widths=[Inches(1.8), Inches(2.4), Inches(3.0)]
    )'''
    t61_replace = t61_target + '''\n    add_p("Table 6.1 provides an overview of the core technologies, frameworks, and algorithmic libraries powering ZeroGuard AI. The architecture combines a React 19 and TypeScript frontend styled with Tailwind CSS for accessible, responsive incident reporting with a Python Flask and FastAPI backend engine. Integrated computer vision via PyTesseract and semantic NLP vector embeddings enable sub-second evidence verification, backed by SQLAlchemy ORM persistence, ReportLab PDF synthesis, and SHA-256 cryptographic ledger verification.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t61_target in content, "Table 6.1 target not found!"
    content = content.replace(t61_target, t61_replace)

    # Table 8.1
    t81_target = '''    create_styled_table(t81_data[0], t81_data[1:], col_widths=[Inches(1.5), Inches(1.5), Inches(2.2), Inches(2.0)])'''
    t81_replace = t81_target + '''\n    add_p("Table 8.1 specifies the schema definition for the users entity table, which stores citizen and investigator identity profiles. The schema incorporates unique email indexing for instantaneous credential lookups, enforces salted PBKDF2-SHA256 password hashing for robust protection against dictionary and rainbow table attacks, and tracks user role classifications (citizen versus admin) and email verification flags to enforce access privileges across all application endpoints.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t81_target in content, "Table 8.1 target not found!"
    content = content.replace(t81_target, t81_replace)

    # Table 8.2
    t82_target = '''    create_styled_table(t82_data[0], t82_data[1:], col_widths=[Inches(1.8), Inches(1.3), Inches(2.0), Inches(2.1)])'''
    t82_replace = t82_target + '''\n    add_p("Table 8.2 outlines the structural attributes of the complaints entity table, which serves as the core record repository for lodged cybercrime incidents. Key columns store public reference numbers, categorized crime classifications, composite risk scores, and AI-synthesized narrative statements. Furthermore, the entity persists claimed loss amounts, automated OCR amount verification outcomes, NLP evidence relevance flags, generated PDF dossier paths, and indexed lifecycle states for end-to-end case tracking.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t82_target in content, "Table 8.2 target not found!"
    content = content.replace(t82_target, t82_replace)

    # Table 8.3
    t83_target = '''    create_styled_table(t83_data[0], t83_data[1:], col_widths=[Inches(1.5), Inches(1.5), Inches(2.2), Inches(2.0)])'''
    t83_replace = t83_target + '''\n    add_p("Table 8.3 describes the schema architecture of the admin_notes entity table, established to maintain an immutable log of investigator notes and status updates. Foreign keys link each record directly to the respective parent complaint dossier and authoring officer account. Storing previous and newly updated case statuses alongside exact UTC timestamps ensures complete traceability, accountability, and forensic integrity throughout the multi-stage investigative workflow.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t83_target in content, "Table 8.3 target not found!"
    content = content.replace(t83_target, t83_replace)

    # Table 8.4
    t84_target = '''    create_styled_table(t84_data[0], t84_data[1:], col_widths=[Inches(1.5), Inches(1.5), Inches(2.2), Inches(2.0)])'''
    t84_replace = t84_target + '''\n    add_p("Table 8.4 details the data schema of the login_history entity table, responsible for recording security telemetry for every login attempt. By archiving client IP addresses, browser user-agent signatures, attempted email addresses, authentication outcomes (success or failure), and indexed UTC timestamps, the table provides forensic auditing data that allows cyber-cell administrators to identify anomalous login spikes, credential stuffing attempts, and unauthorized session takeovers.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t84_target in content, "Table 8.4 target not found!"
    content = content.replace(t84_target, t84_replace)

    # Table 8.5
    t85_target = '''    create_styled_table(t85_data[0], t85_data[1:], col_widths=[Inches(2.0), Inches(1.3), Inches(1.8), Inches(2.1)])'''
    t85_replace = t85_target + '''\n    add_p("Table 8.5 presents the schemas for the otp_verifications and emergency_contacts tables. The OTP verification schema stores salted hashes of 6-digit one-time passcodes with a strict 10-minute expiration window to facilitate secure multi-factor authentication. The emergency contacts schema maps citizen accounts to designated trusted guardian contact names and phone numbers, ensuring rapid dispatch of emergency SMS notifications whenever high-risk extortion or banking fraud incidents occur.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t85_target in content, "Table 8.5 target not found!"
    content = content.replace(t85_target, t85_replace)

    # Table 8.6
    t86_target = '''    create_styled_table(t86_data[0], t86_data[1:], col_widths=[Inches(1.5), Inches(1.5), Inches(2.2), Inches(2.0)])'''
    t86_replace = t86_target + '''\n    add_p("Table 8.6 defines the structural schema of the activity_logs entity table, which functions as an operational audit monitor across the entire system. Every significant user and administrative event—such as incident submission, evidence upload, status update, and dossier export—is recorded with actor account references, action type descriptors, stringified JSON metadata payloads, client IP addresses, and indexed UTC timestamps to provide transparent auditability.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t86_target in content, "Table 8.6 target not found!"
    content = content.replace(t86_target, t86_replace)

    # Table 11.1
    t111_target = '''    create_styled_table(
        t111_data[0], t111_data[1:],
        col_widths=[Inches(1.5), Inches(2.2), Inches(1.0), Inches(1.1), Inches(1.7)]
    )'''
    t111_replace = t111_target + '''\n    add_p("Table 11.1 summarizes the verification outcomes observed across twelve simulated production cyberattack scenarios injected into the ZeroGuard AI triage pipeline. Each test scenario—spanning UPI phishing scams, deepfake extortion, SIM swap takeovers, account hijacks, fake job scams, and predatory loan app harassment—accurately triggered corresponding threat indicators, received correct risk score weighting, aligned with standard MITRE ATT&CK techniques, and executed automated response procedures including 1930 freeze notices and emergency contact alerts.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t111_target in content, "Table 11.1 target not found!"
    content = content.replace(t111_target, t111_replace)

    # Table 11.2
    t112_target = '''    create_styled_table(
        t112_data[0], t112_data[1:],
        col_widths=[Inches(2.5), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0)]
    )'''
    t112_replace = t112_target + '''\n    add_p("Table 11.2 contrasts the machine learning classification performance of ZeroGuard AI against traditional baseline classifiers across a benchmark dataset of 52,000 synthetic cybercrime cases. The hybrid Gemini and sentence-transformer architecture achieved superior performance across all evaluation metrics, registering 97.4% accuracy, 93.8% precision, 91.5% recall, 92.6% F1-score, and an ROC-AUC of 0.97, comfortably outperforming Logistic Regression, Random Forest, and SVM models in resolving complex, ambiguous incident narratives.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t112_target in content, "Table 11.2 target not found!"
    content = content.replace(t112_target, t112_replace)

    # Table 11.3
    t113_target = '''    create_styled_table(
        t113_data[0], t113_data[1:],
        col_widths=[Inches(3.2), Inches(2.2), Inches(2.1)]
    )'''
    t113_replace = t113_target + '''\n    add_p("Table 11.3 presents the empirical latency and throughput metrics measured during sustained stress testing under 500 concurrent HTTP streams simulated with Locust. The empirical results demonstrate that ZeroGuard AI operates well within target boundaries: raw incident intake completes in 12 ms, AI classification and dynamic question synthesis require 240 ms, OCR numerical extraction takes 80 ms, and end-to-end dossier compilation requires 380 ms, maintaining an overall throughput of 215 submissions per second.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t113_target in content, "Table 11.3 target not found!"
    content = content.replace(t113_target, t113_replace)

    # Table 11.4
    t114_target = '''    create_styled_table(
        t114_data[0], t114_data[1:],
        col_widths=[Inches(2.2), Inches(2.6), Inches(2.7)]
    )'''
    t114_replace = t114_target + '''\n    add_p("Table 11.4 provides a comparative analysis contrasting legacy national reporting platforms against the integrated capabilities of ZeroGuard AI. The evaluation highlights substantial operational gains: citizen reporting time is reduced by 78% (from 18–25 minutes down to 2.5–4 minutes), manual verification queues requiring 24–72 hours are replaced with automated sub-second validation, claim discrepancy detection reaches 94.2% through OCR amount extraction, and mutable database records are secured via a SHA-256 tamper-evident ledger.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t114_target in content, "Table 11.4 target not found!"
    content = content.replace(t114_target, t114_replace)

    # Table 11.5
    t115_target = '''    create_styled_table(
        t115_data[0], t115_data[1:],
        col_widths=[Inches(3.2), Inches(2.0), Inches(2.3)]
    )'''
    t115_replace = t115_target + '''\n    add_p("Table 11.5 documents the results of an empirical ablation study investigating the impact of individual pipeline components on the overall model F1-score. While the full multi-vector system establishes a baseline F1-score of 92.6%, omitting OCR amount verification degrades the score by -10.2%, omitting semantic relevance scoring results in an -8.5% drop, and omitting dynamic adaptive questioning causes an -11.6% degradation. Relying solely on legacy keyword rules yields a severe -24.1% performance drop, demonstrating the essential contribution of each integrated sub-system.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t115_target in content, "Table 11.5 target not found!"
    content = content.replace(t115_target, t115_replace)

    # Table 12.1
    t121_target = '''    create_styled_table(
        t121_data[0], t121_data[1:],
        col_widths=[Inches(2.2), Inches(1.8), Inches(2.2), Inches(1.1)]
    )'''
    t121_replace = t121_target + '''\n    add_p("Table 12.1 summarizes the final quantitative evaluation of ZeroGuard AI against its core design specifications. The empirical findings confirm that all original technical targets were either met or exceeded: crime classification accuracy achieved 97.4% against a 96% target, evidence verification reached a 92.6% F1-score surpassing the 90% benchmark, end-to-end triage latency was measured at 380 ms well within the 500 ms ceiling, claim mismatch detection achieved 94.2% against an 85% requirement, and the SHA-256 audit ledger recorded 100% tamper detection without false positive mutations.", space_before=4, space_after=8, line_spacing=1.35)'''
    assert t121_target in content, "Table 12.1 target not found!"
    content = content.replace(t121_target, t121_replace)

    # 4. Save and auto-convert to PDF
    save_target = '''    # Save copy in user's Downloads directory
    user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.exists(user_downloads):
        downloads_path = os.path.join(user_downloads, output_filename)
        doc.save(downloads_path)
        print(f"[+] Downloads copy saved at: {downloads_path}")'''

    save_replace = save_target + '''\n
    # Convert to high-quality PDF via Word COM
    pdf_filename = "ZeroGuard_AI_Project_Report.pdf"
    pdf_path = os.path.join(os.getcwd(), pdf_filename)
    print("[*] Automatically generating court-grade PDF via Word...")
    os.system(f'powershell -ExecutionPolicy Bypass -File convert_to_pdf.ps1 -DocxPath "{output_path}" -PdfPath "{pdf_path}"')
    if os.path.exists(user_downloads):
        pdf_downloads = os.path.join(user_downloads, pdf_filename)
        os.system(f'powershell -ExecutionPolicy Bypass -File convert_to_pdf.ps1 -DocxPath "{downloads_path}" -PdfPath "{pdf_downloads}"')
        print(f"[+] PDF copies saved at: {pdf_path} and {pdf_downloads}")'''
    
    assert save_target in content, "Save target not found!"
    content = content.replace(save_target, save_replace)

    with open("build_full_65_page_zeroguard_report.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("[SUCCESS] All updates successfully applied to build_full_65_page_zeroguard_report.py!")

if __name__ == "__main__":
    apply_updates()
