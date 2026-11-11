"""
Power Feature 2B: Threatening Notice & Contract Clause Trap Decoder.
Decodes intimidating messages, employment bond clauses, or fake warrants pasted by a citizen,
separating legally enforceable obligations from empty bluffs, scams, and illegal intimidation.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from .llm_router import UniversalLLMRouter


@dataclass
class DecodedTrapFlag:
    clause_or_threat_type: str
    verdict: str  # "ILLEGAL_BLUFF_OR_VOID" | "PARTIALLY_ENFORCEABLE" | "GENUINE_REQUIRES_REPLY" | "UNRECOGNIZED_NON_LEGAL_TEXT"
    statutory_reality: str
    recommended_counter_move: str


TRAP_RULES = [
    (
        re.compile(r"non-compete|cannot join competitor|rival company|same industry for \d+ year|competitor organization", re.I),
        "Post-Employment Non-Compete Restraint",
        "ILLEGAL_BLUFF_OR_VOID",
        "Under Section 27 of the Indian Contract Act, 1872, any agreement restraining an employee from exercising a lawful profession after leaving employment is 100% VOID and unenforceable in India (affirmed repeatedly by the Supreme Court).",
        "Reply calmly that post-termination restraint of trade is void ab initio under Section 27 of the Indian Contract Act, 1872.",
    ),
    (
        re.compile(r"training bond|liquidated damages of rs|pay \d+ lakh.*bond|hold.*relieving letter|withhold.*experience letter|forfeit.*relieving", re.I),
        "Employment Bond Penalty / Relieving Letter Hostage",
        "ILLEGAL_BLUFF_OR_VOID",
        "Under Section 74 of the Indian Contract Act, 1872, an employer cannot enforce a fixed penalty bond unless they prove actual itemized money spent on specialized external training—and they cannot legally hold a Relieving Letter hostage as coercion.",
        "Demand an itemized receipt of actual external training expenditure under Section 74 ICA and file a conciliation claim on samadhan.labour.gov.in.",
    ),
    (
        re.compile(
            r"police warrant|arrest warrant|non-bailable.*warrant|arrest within \d+ hours|police will arrive|"
            r"lok adalat warrant|whatsapp summons|seize your passport|freeze your bank|fir registered by recovery|"
            r"before arrest|immediate arrest",
            re.I,
        ),
        "Fake Recovery / Advocate 'Arrest Warrant, Passport Seizure & Bank Freeze' Bluff",
        "ILLEGAL_BLUFF_OR_VOID",
        "Private advocates, landlords, and recovery agents CANNOT issue arrest warrants, freeze bank accounts, or seize passports. Civil debt recovery is not an arrest offense, Lok Adalats NEVER issue warrants, and genuine court summons always carry a 16-digit CNR number verifiable on ecourts.gov.in.",
        "Do not panic or pay under threat. Screenshot the message, verify absence of a 16-digit CNR number on ecourts.gov.in, and report criminal intimidation under BNS Section 351 and RBI Ombudsman (cms.rbi.org.in).",
    ),
    (
        re.compile(
            r"digital arrest|skype.*police|whatsapp video.*arrest|customs parcel.*drugs|fedex.*narcotics|"
            r"trai.*disconnect|cbi.*money laundering|aadhaar.*sim.*arrest|stay on video call",
            re.I,
        ),
        "Cyber Fraud Scam Alert: 'Digital Arrest' / Fake CBI-Customs-TRAI Extortion",
        "ILLEGAL_BLUFF_OR_VOID",
        "There is NO concept of 'Digital Arrest' or Skype/WhatsApp video interrogation under the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023. Police, CBI, Customs, and RBI never demand money transfers to 'verify' or 'clear' your bank account.",
        "Disconnect the call immediately! Do NOT transfer any money or share screen/OTP. Report the number immediately on the National Cybercrime Helpline 1930 and cybercrime.gov.in.",
    ),
    (
        re.compile(r"\b(?:ipc\s*(?:section|sec\.?)?\s*(?:420|406|499|500|506)|indian penal code)\b", re.I),
        "Outdated Pre-July-2024 IPC Citation Used for Intimidation",
        "ILLEGAL_BLUFF_OR_VOID",
        "Effective July 1, 2024, the Indian Penal Code (IPC, 1860) stands repealed and replaced by the Bharatiya Nyaya Sanhita (BNS), 2023. Threatening arrest under repealed IPC Section 420 in a routine civil or contract dispute is a classic template bluff (the Supreme Court has repeatedly held that civil breach of contract cannot be weaponized as criminal cheating).",
        "Point out in writing that IPC 1860 was repealed on July 1, 2024 by BNS 2023, and that attempting to cloak a civil dispute as criminal cheating without fraudulent inception is an abuse of process.",
    ),
    (
        re.compile(r"deduct.*painting|forfeit.*entire deposit|forfeit.*deposit|wear and tear|deep cleaning deduction|acid wash", re.I),
        "Unbilled Landlord Security Deposit Forfeiture / Painting Deduction",
        "ILLEGAL_BLUFF_OR_VOID",
        "Under Section 108(q) of the Transfer of Property Act, 1882, Model Tenancy Act Section 11, and Sections 73-74 of the Indian Contract Act, normal wear-and-tear is the landlord's responsibility and lump-sum deductions without actual third-party repair bills are unlawful.",
        "Demand GST-compliant repair invoices and comparative move-in/move-out photos within 7 days, failing which serve an Order XXXVII CPC Summary Suit demand notice.",
    ),
    (
        re.compile(r"no refund policy|final sale|store credit only|warranty void|no return policy", re.I),
        "'No Refund / No Return' Blanket Disclaimer on Defective Goods",
        "ILLEGAL_BLUFF_OR_VOID",
        "Under Section 2(47)(vii) of the Consumer Protection Act, 2019, refusing to take back defective goods or refund consideration is an actionable Unfair Trade Practice—a unilateral 'No Refund' sticker or T&C cannot override statutory consumer law.",
        "Serve a Rule 4(4) E-Commerce Rules notice to the Grievance Officer and file on e-Daakhil (₹0 fee up to ₹5 Lakh).",
    ),
    (
        re.compile(r"salary.*forfeit|withhold.*salary|f&f.*blocked|settlement.*cancelled|no salary.*notice period|forfeit.*f&f", re.I),
        "Unlawful Salary Forfeiture / Wage Withholding",
        "ILLEGAL_BLUFF_OR_VOID",
        "Under Sections 3, 5, and 15 of the Payment of Wages Act, 1936, earned wages for work already performed cannot be arbitrarily forfeited or withheld as punitive damages without statutory due process.",
        "Reply that earned wages cannot be forfeited under the Payment of Wages Act and initiate a conciliation petition on samadhan.labour.gov.in.",
    ),
    (
        re.compile(r"bank.*not responsible|customer.*sole liability|otp.*shared.*no refund|bank.*closed.*investigation|customer bears full risk", re.I),
        "Bank Disclaimer of Liability in Electronic Transaction Disputes",
        "PARTIALLY_ENFORCEABLE",
        "Under Paragraphs 6 & 9 of RBI Master Circular on Customer Protection, third-party system breaches or unauthorized debits notified within 3 working days carry ZERO customer liability, requiring a mandatory shadow reversal within 10 working days.",
        "Formalize your complaint in writing to the Principal Nodal Officer citing RBI Circular DBR.No.Leg.BC.78/09.07.005/2017-18 before escalating to the RBI Ombudsman.",
    ),
    (
        re.compile(r"defamation notice|damages of rs.*crore|legal action for bad review|delete.*tweet|delete.*review|defame.*reputation", re.I),
        "Disproportionate Defamation Threat (SLAPP) for Honest Consumer Review",
        "ILLEGAL_BLUFF_OR_VOID",
        "True statements and honest opinions expressed in good faith regarding genuine consumer grievances do not constitute defamation (Third and Ninth Exceptions to Section 356 BNS 2023 / former IPC 499). Multi-crore damage notices over reviews are intimidation bluffs.",
        "Maintain all invoices, delivery records, and proof of defects. Reply placing the factual sequence on record without retracting truthful factual statements.",
    ),
    (
        re.compile(r"exclusive jurisdiction.*courts at|arbitration in.*sole arbitrator appointed by company", re.I),
        "Unilateral Distant Jurisdiction / Sole-Company-Arbitrator Clause",
        "ILLEGAL_BLUFF_OR_VOID",
        "Under Section 34(2)(d) of the Consumer Protection Act, 2019, a consumer can file a complaint in the District Commission where the CONSUMER resides or works for gain—regardless of what city the company's T&C specifies. Moreover, unilateral appointment of a sole arbitrator by an interested party is invalid under Section 12(5) of the Arbitration and Conciliation Act, 1996.",
        "Ignore distant-city forum barriers and file directly in your home District Consumer Commission via e-Daakhil under Section 34(2)(d) CPA 2019.",
    ),
]

LEGAL_NOTICE_MARKERS = re.compile(
    r"\b(notice|advocate|counsel|clause|agreement|contract|section|act|court|summons|demand|hereby|"
    r"breach|liable|damages|pay|refund|deposit|salary|termination|legal|law|sue|litigation|arbitration)\b",
    re.I,
)


def decode_notice_or_clause(
    raw_notice_text: str,
    router: Optional[UniversalLLMRouter] = None,
) -> Dict:
    if not raw_notice_text or not raw_notice_text.strip():
        return {
            "has_verifiable_court_cnr_number": False,
            "is_real_court_summons": False,
            "summary_assessment": "No message text provided to analyze.",
            "decoded_flags": [],
        }

    clean = raw_notice_text.strip()
    model_name = (router.config.model if router else "gemini-2.5-flash").lower()
    is_aggressive = (
        "aggressive" in model_name
        or ("balanced" in model_name and any(k in model_name for k in ("-pro", "large", "r1", "70b")))
    )
    is_conciliatory = (
        "conciliatory" in model_name
        or "amicable" in model_name
        or ("balanced" in model_name and any(k in model_name for k in ("2.0", "lite", "instant", "small", "mini", "8b", "9b")))
    )

    flags: List[DecodedTrapFlag] = []
    for pat, title, verdict, reality, counter in TRAP_RULES:
        if pat.search(clean):
            adapted_counter = counter
            if is_aggressive:
                adapted_counter = f"[HIGH-PRESSURE COUNTER] {counter} Put the sender on formal 48-hour notice of counter-proceedings under BNS Section 351 (Criminal Intimidation) and statutory penalty provisions."
            elif is_conciliatory:
                adapted_counter = f"[DE-ESCALATION COUNTER] {counter} Offer a calm, 'Without Prejudice' written clarification to close the issue amicably without mutual escalation."
            flags.append(
                DecodedTrapFlag(
                    clause_or_threat_type=title,
                    verdict=verdict,
                    statutory_reality=reality,
                    recommended_counter_move=adapted_counter,
                )
            )

    has_cnr = bool(re.search(r"\b[A-Z]{4}\d{12}\b", clean))

    if not flags:
        # Check if the pasted text is gibberish or unrelated to any legal notice / contract clause
        words = re.findall(r"[a-zA-Z\u0900-\u097F]+", clean)
        if len(words) < 3 or not LEGAL_NOTICE_MARKERS.search(clean):
            flags.append(
                DecodedTrapFlag(
                    clause_or_threat_type="Unrecognized / Non-Legal Text (Not a Legal Notice or Contract Clause)",
                    verdict="UNRECOGNIZED_NON_LEGAL_TEXT",
                    statutory_reality="The text pasted above does not contain any recognizable legal threat, statutory citation, debt demand, or contract clause.",
                    recommended_counter_move="Paste the actual WhatsApp threat, recovery email, landlord message, or employment bond clause you received to verify its legality under Indian law.",
                )
            )
            return {
                "has_verifiable_court_cnr_number": False,
                "is_real_court_summons": False,
                "summary_assessment": "Input is not a recognizable legal notice, threat, or contract clause.",
                "decoded_flags": [asdict(f) for f in flags],
            }

        flags.append(
            DecodedTrapFlag(
                clause_or_threat_type="General Pre-Litigation Legal Notice / Demand",
                verdict="GENUINE_REQUIRES_REPLY",
                statutory_reality="A formal legal notice from an Advocate is a pre-litigation warning, NOT a court order. However, leaving it unanswered allows the sender to claim you had no defense.",
                recommended_counter_move="Send a para-wise Reply Notice marked 'WITHOUT PREJUDICE' within 15 days denying false allegations and placing your documentary evidence on record.",
            )
        )

    return {
        "has_verifiable_court_cnr_number": has_cnr,
        "is_real_court_summons": has_cnr,
        "summary_assessment": (
            "Contains unenforceable intimidation bluffs / void clauses under Indian law."
            if any(f.verdict == "ILLEGAL_BLUFF_OR_VOID" for f in flags)
            else "Standard pre-litigation notice requiring a structured written reply."
        ),
        "decoded_flags": [asdict(f) for f in flags],
    }
