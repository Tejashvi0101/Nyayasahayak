"""
Power Feature 2C: Ready-to-Send Legal Action Kit & PDF Generator (`document_generator.py`).
Generates:
1. Formal Pre-Litigation Legal Demand Notice (Markdown + Printable PDF via ReportLab)
2. Official Portal Filing Synopsis (e-Daakhil / SAMADHAN / RBI Ombudsman / NI Act 138)
3. Strategic WhatsApp/Email Final Warning Template
Dynamically adapts tone and cure window based on the active Model Engine Profile,
and blocks/warns on non-actionable, off-topic, or red-line safety cases.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

from .case_builder import StructuredLegalCase
from .statute_verifier import verify_and_sanitize_legal_text
from .llm_router import UniversalLLMRouter


def generate_legal_action_kit(
    case: StructuredLegalCase,
    sender_name: str = "[Your Full Name]",
    sender_address: str = "[Your Complete Residential Address & Pin Code]",
    recipient_name: str = "[Opposite Party Name — Landlord / Employer HR / E-Commerce Company]",
    recipient_address: str = "[Opposite Party Address / Registered Office]",
    pdf_output_path: Optional[Path] = None,
    router: Optional[UniversalLLMRouter] = None,
) -> Dict[str, str]:
    """
    Produces statute-verified legal notice text, portal complaint draft, WhatsApp template,
    and optionally renders a clean A4 PDF Legal Notice.
    """
    if case.is_red_line_escalation:
        warning_doc = (
            "### ⚠️ RED-LINE SAFETY ESCALATION ACTIVE — SELF-HELP NOTICE BLOCKED\n\n"
            f"**Reason:** {case.red_line_reason}\n\n"
            "**Immediate Action Required:**\n"
            "- Call **NALSA Free Legal Aid Helpline: `15100`** (24x7 Toll-Free) to be assigned a qualified human Advocate at ₹0 cost under **Section 12 of the Legal Services Authorities Act, 1987**.\n"
            "- If in immediate physical danger, call **Emergency `112`** or **Women Helpline `181`**.\n"
            "- Do NOT sign any blank papers, settlement deeds, or confessions without an enrolled Advocate present."
        )
        return {
            "whatsapp_escalation_template": warning_doc,
            "formal_legal_notice_md": warning_doc,
            "portal_complaint_synopsis_md": warning_doc,
            "pdf_path": "",
        }

    # Block document generation on Gibberish, Off-Topic, or Trivial Social Slights
    if case.case_validity_status in ("GIBBERISH_OR_TOO_SHORT", "OFF_TOPIC_NON_LEGAL", "NO_CLAIM_TRIVIAL_SOCIAL"):
        blocked_doc = (
            f"### 🛑 LEGAL NOTICE GENERATION BLOCKED ({case.case_validity_status})\n\n"
            f"**Why No Legal Notice Was Generated:** {case.validity_explanation}\n\n"
            "- Under **Section 33 of the Bharatiya Nyaya Sanhita (BNS), 2023** (*De minimis non curat lex*), Indian courts do not entertain non-legal queries or trivial social grievances.\n"
            "- Sending a fabricated or frivolous legal notice where no cause of action exists can expose the sender to counter-claims for harassment or costs under **Section 35A of the Code of Civil Procedure, 1908**."
        )
        return {
            "whatsapp_escalation_template": blocked_doc,
            "formal_legal_notice_md": blocked_doc,
            "portal_complaint_synopsis_md": blocked_doc,
            "pdf_path": "",
        }

    # For Self-Fault, Time-Barred, or Lawful Counterparty Deductions, generate an honest Goodwill Request instead of a statutory threat
    if case.case_validity_status in ("NO_CLAIM_SELF_FAULT", "NO_CLAIM_TIME_BARRED", "NO_CLAIM_LAWFUL_DEDUCTION"):
        goodwill_whatsapp = (
            f"WITHOUT PREJUDICE — GOODWILL RESOLUTION REQUEST\n\n"
            f"Dear {recipient_name},\n\n"
            f"I am writing to request an amicable, goodwill review regarding my matter. "
            f"While I understand the technical policy / timeline constraints ({case.validity_explanation}), "
            f"I have been a genuine customer/counterparty in good faith and would deeply appreciate a one-time goodwill waiver, repair discount, or mutual reconciliation of accounts.\n\n"
            f"Thank you for your consideration.\n"
            f"Regards,\n{sender_name}"
        )
        goodwill_md = (
            f"### ⚠️ HONEST LEGAL ADVISORY: FORMAL DEMAND NOTICE NOT RECOMMENDED (`{case.case_validity_status}`)\n\n"
            f"**Legal Merits Assessment:** {case.validity_explanation}\n\n"
            "**Why We Did Not Generate an Aggressive Legal Threat:**\n"
            "- Serving a formal statutory demand notice when the claim is time-barred (Section 3, Limitation Act, 1963) or involves customer-induced damage (Section 2(11), CPA 2019) will cause the opposite party's legal team to immediately reject your request.\n"
            "- Instead, use the **Goodwill Resolution Request** on the previous tab to seek a voluntary concession, credit-card accidental protection claim, or mutual reconciliation."
        )
        return {
            "whatsapp_escalation_template": goodwill_whatsapp,
            "formal_legal_notice_md": goodwill_md,
            "portal_complaint_synopsis_md": goodwill_md,
            "pdf_path": "",
        }

    profile_str = (router.config.model if router else case.strategy_profile_applied).lower()
    is_aggressive = (
        "aggressive" in profile_str
        or ("balanced" in profile_str and any(k in profile_str for k in ("-pro", "large", "r1", "70b")))
    )
    is_conciliatory = (
        "conciliatory" in profile_str
        or "amicable" in profile_str
        or ("balanced" in profile_str and any(k in profile_str for k in ("2.0", "lite", "instant", "small", "mini", "8b", "9b")))
    )

    cure_days = "2 (two) days (48 hours)" if is_aggressive else ("5 (five) days" if is_conciliatory else "7 (seven) days")
    if case.domain_key == "CHEQUE_BOUNCE_RECOVERY":
        cure_days = "15 (fifteen) days (Mandatory under Section 138(c) NI Act, 1881)"

    statute_bullets = "\n".join(
        f"- **{s['act']} ({s['section']}):** {s['summary']}"
        for s in case.verified_statutes
    )

    if is_aggressive:
        whatsapp_msg = (
            f"URGENT & WITHOUT PREJUDICE — FINAL 48-HOUR PRE-LITIGATION ULTIMATUM\n\n"
            f"To: {recipient_name}\n\n"
            f"Take immediate notice that your continued unlawful withholding of ₹{case.claim_amount_inr:,} ({case.domain_title}) "
            f"is in direct violation of {case.verified_statutes[0]['act']} ({case.verified_statutes[0]['section']}).\n\n"
            f"Unless the full sum of ₹{case.claim_amount_inr:,} along with 18% p.a. statutory interest is credited to my account within 48 HOURS "
            f"and the UTR number is shared, I shall immediately file formal proceedings before {case.limitation_analysis['official_portal']} "
            f"claiming maximum statutory penalties, litigation costs, and damages without further reference to you.\n\n"
            f"{sender_name}"
        )
        subject_line = f"FINAL 48-HOUR PENAL DEMAND NOTICE FOR IMMEDIATE RECOVERY OF ₹{case.claim_amount_inr:,} WITH 18% INTEREST & DAMAGES ({case.domain_title.upper()})"
        closing_demand = (
            f"Take categorical notice that should you fail to remit ₹{case.claim_amount_inr:,} within **{cure_days}**, "
            f"I shall forthwith institute coercive legal and statutory proceedings before **{case.limitation_analysis['official_portal']}** "
            f"seeking maximum statutory penalties, 18% p.a. interest, and punitive litigation costs entirely at your peril."
        )
    elif is_conciliatory:
        whatsapp_msg = (
            f"WITHOUT PREJUDICE — AMICABLE 48-HOUR SETTLEMENT PROPOSAL\n\n"
            f"Dear {recipient_name},\n\n"
            f"I am reaching out in good faith to close our pending matter regarding ₹{case.claim_amount_inr:,} ({case.domain_title}) amicably without legal escalation. "
            f"While my right to recover ₹{case.claim_amount_inr:,} is protected under {case.verified_statutes[0]['act']} ({case.verified_statutes[0]['section']}), "
            f"I prefer a fast, mutually respectful closure.\n\n"
            f"If the principal amount of ₹{case.claim_amount_inr:,} is transferred within 5 working days, I will gladly waive all delay interest claims and issue a full No-Dues confirmation.\n\n"
            f"Warm regards,\n{sender_name}"
        )
        subject_line = f"WITHOUT PREJUDICE — PRE-MEDIATION SETTLEMENT & DEMAND NOTICE FOR ₹{case.claim_amount_inr:,} ({case.domain_title.upper()})"
        closing_demand = (
            f"In the spirit of amicable resolution, if the principal sum of **₹{case.claim_amount_inr:,}** is remitted within **{cure_days}**, "
            f"I undertake to waive accrued interest and close the matter with a formal No-Dues receipt, failing which the claim will be referred to **{case.limitation_analysis['official_portal']}**."
        )
    else:
        whatsapp_msg = (
            f"WITHOUT PREJUDICE\n\n"
            f"Dear {recipient_name},\n\n"
            f"This is a final written reminder regarding the pending sum of ₹{case.claim_amount_inr:,} ({case.domain_title}). "
            f"All my obligations stand completed, and holding back ₹{case.claim_amount_inr:,} is directly contrary to "
            f"{case.verified_statutes[0]['act']} ({case.verified_statutes[0]['section']}).\n\n"
            f"Please process the full transfer of ₹{case.claim_amount_inr:,} within 48 hours and share the UTR reference, "
            f"failing which I will be constrained to serve a formal Legal Notice and initiate recovery proceedings before the "
            f"{case.limitation_analysis['official_portal']} along with statutory interest and costs.\n\n"
            f"Regards,\n{sender_name}"
        )
        subject_line = f"FINAL PRE-LITIGATION LEGAL NOTICE FOR RECOVERY OF ₹{case.claim_amount_inr:,} AND STATUTORY COMPLIANCE ({case.domain_title.upper()})"
        closing_demand = (
            f"Take notice that should you fail to comply within the stipulated **{cure_days}**, I shall immediately file a formal recovery petition before **{case.limitation_analysis['official_portal']}** entirely at your risk as to costs, statutory interest, and damages."
        )

    notice_md = f"""# REGISTERED A.D. / EMAIL — LEGAL DEMAND NOTICE
**WITHOUT PREJUDICE**  
**Strategy Posture:** {case.strategy_profile_applied}

**Date:** 11 November 2026  
**From:** {sender_name}, residing at {sender_address}  
**To:** {recipient_name}, having address at {recipient_address}  

**SUBJECT: {subject_line}**

Sir / Madam,

Under instructions from and on behalf of my self-represented claim, I hereby serve upon you the following categorical Legal Demand Notice:

### 1. CHRONOLOGICAL STATEMENT OF FACTS
1. {case.timeline[0].event_summary} (*{case.timeline[0].legal_significance}*)
2. {case.timeline[1].event_summary if len(case.timeline) > 1 else 'All contractual and statutory obligations on my part stand duly performed.'} (*{case.timeline[1].legal_significance if len(case.timeline) > 1 else 'Establishes clean hands.'}*)
3. {case.timeline[2].event_summary if len(case.timeline) > 2 else 'Despite repeated reminders, the lawful dues remain unpaid.'}

### 2. APPLICABLE STATUTORY PROVISIONS (VERIFIED INDIAN LAW)
Your continued failure and refusal to discharge the lawful liability of **₹{case.claim_amount_inr:,}** is in direct breach of the following statutory provisions:
{statute_bullets}

### 3. FINAL DEMAND & CONSEQUENCE OF NON-COMPLIANCE
I hereby call upon you to:
1. Remit the principal sum of **₹{case.claim_amount_inr:,}** (Rupees {case.claim_amount_inr:,} only) along with accrued interest @ 18% per annum immediately via NEFT/IMPS/UPI; and
2. Issue written confirmation of compliance within **{cure_days}** from the receipt of this Notice.

{closing_demand}

A copy of this Notice is retained in my records for production before the competent Court/Authority as Annexures.

Yours faithfully,

**{sender_name}**  
*(Claimant)*
"""

    portal_md = f"""# OFFICIAL PORTAL FILING PACKET ({case.limitation_analysis['official_portal']})

- **Portal to Open:** {case.limitation_analysis['official_portal']}
- **Strategy Posture:** {case.strategy_profile_applied}
- **Limitation Status:** WITHIN TIME ({case.limitation_analysis['statutory_limit_years']} — {case.limitation_analysis['legal_basis']})
- **Claim Amount:** ₹{case.claim_amount_inr:,}
- **Evidence Readiness Score:** {case.evidence_score_100}/100

### Synopsis of Case (Copy-Paste into Portal 'Brief Facts' Box)
{case.plain_language_standing_en}

### List of Annexures to Upload (PDF)
""" + "\n".join(
        f"- **Annexure A{idx+1}:** {ev.item_name} (*Status: {ev.status}*)"
        for idx, ev in enumerate(case.evidence_checklist)
    )

    # Pass generated notice through deterministic Citation Firewall
    clean_notice, _ = verify_and_sanitize_legal_text(notice_md)

    pdf_str = ""
    if pdf_output_path:
        pdf_output_path.parent.mkdir(parents=True, exist_ok=True)
        _render_notice_pdf(clean_notice, pdf_output_path)
        pdf_str = str(pdf_output_path)

    return {
        "whatsapp_escalation_template": whatsapp_msg,
        "formal_legal_notice_md": clean_notice,
        "portal_complaint_synopsis_md": portal_md,
        "pdf_path": pdf_str,
    }


def _render_notice_pdf(markdown_text: str, out_path: Path) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "NoticeTitle",
        parent=styles["Heading1"],
        fontSize=13,
        leading=16,
        spaceAfter=8,
    )
    h2_style = ParagraphStyle(
        "NoticeH2",
        parent=styles["Heading2"],
        fontSize=10.5,
        leading=14,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "NoticeBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13.5,
        spaceAfter=5,
    )

    story = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 2 * mm))
            continue
        html_safe = (
            line.replace("₹", "Rs. ")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        html_safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", html_safe)
        html_safe = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", html_safe)

        if line.startswith("# "):
            story.append(Paragraph(html_safe[2:], title_style))
            story.append(HRFlowable(width="100%", thickness=0.8))
            story.append(Spacer(1, 2 * mm))
        elif line.startswith("### "):
            story.append(Paragraph(html_safe[4:], h2_style))
        elif line.startswith("- ") or line[:2] in ("1.", "2.", "3."):
            story.append(Paragraph(html_safe, body_style))
        else:
            story.append(Paragraph(html_safe, body_style))

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    doc.build(story)
