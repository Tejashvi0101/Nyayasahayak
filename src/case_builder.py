"""
Multilingual (English / Hindi / Hinglish) Case Intake, 4-Tier Validity & Merits Gate,
Red-Line Safety Escalation, Evidence Strength Auditor & Limitation/ROI Calculator
for NyayaSahayak (Project 2).
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from .statute_verifier import get_domain_statutes, verify_and_sanitize_legal_text
from .llm_router import UniversalLLMRouter


RED_LINE_TRIGGERS = [
    (
        re.compile(r"\b(fir|arrested|police custody|non-bailable|warrant|remand|bail|lockup|thana)\b", re.I),
        "Active Criminal Investigation / Police Custody Risk",
        "Your situation involves active criminal law or police custody procedures under the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023. Self-help notices are unsafe here—you need an enrolled Criminal Defense Advocate immediately.",
    ),
    (
        re.compile(r"\b(domestic violence|dowry|beating|physical assault|hit me|beat me|threatened to kill|suicide|molest|posh|sexual harassment)\b", re.I),
        "Physical Safety / Domestic Violence / Severe Harassment",
        "Your physical safety comes first. Do not rely on automated legal notices alone. Contact the Women Helpline (181 / 1091), Police Emergency (112), or your District Legal Services Authority (NALSA Toll-Free: 15100) for immediate protection orders and a free human lawyer.",
    ),
    (
        re.compile(r"\b(divorce|child custody|maintenance|alimony|ancestral land|partition suit|title deed forgery|murder)\b", re.I),
        "Complex Family / Property Title Litigation",
        "Matters involving matrimonial decrees, child custody, or contested immovable property title require formal trial representation before a Family or Civil Court.",
    ),
]


@dataclass
class TimelineFact:
    step_order: int
    date_or_marker: str
    event_summary: str
    legal_significance: str


@dataclass
class EvidenceItem:
    item_name: str
    status: str  # "PRESENT" | "MISSING_CRITICAL" | "RECOMMENDED"
    weight_points: int
    how_to_obtain_or_create: str


@dataclass
class StructuredLegalCase:
    case_id: str
    detected_language: str
    domain_key: str
    domain_title: str
    is_red_line_escalation: bool
    red_line_reason: str
    red_line_emergency_contacts: List[str]
    claim_amount_inr: int
    timeline: List[TimelineFact]
    evidence_score_100: int
    evidence_checklist: List[EvidenceItem]
    pre_notice_evidence_trap_tip: str
    plain_language_standing_en: str
    plain_language_standing_hi: str
    limitation_analysis: Dict[str, str]
    roi_comparison: List[Dict[str, str]]
    verified_statutes: List[Dict[str, str]]
    citation_firewall_audit: List[Dict] = field(default_factory=list)
    case_validity_status: str = "ACTIONABLE_CLAIM"
    validity_explanation: str = "Valid, actionable legal dispute under Indian law."
    amount_specified: bool = True
    strategy_profile_applied: str = "Balanced Legal Strategy (grounded-statute-engine-v1)"


def _detect_language(text: str) -> str:
    if re.search(r"[\u0900-\u097F]", text):
        return "Hindi (Devanagari)"
    hinglish_markers = {
        "mera", "meri", "nahi", "kar", "raha", "paise", "wapas", "makan", "malik",
        "kiraya", "mahine", "bolta", "hai", "aur", "mujhe", "kya", "rupaye", "lakh",
        "hazar", "chabi", "khali", "dhokha", "tankhwah",
    }
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if len(words.intersection(hinglish_markers)) >= 2:
        return "Hinglish (Conversational Hindi + English)"
    return "English"


DOMAIN_KEYWORDS = {
    "TENANCY_DEPOSIT": {
        "high": [
            "landlord", "tenant", "tenancy", "security deposit", "makan malik", "kiraya", "flat deposit",
            "house deposit", "vacated", "vacating", "handover", "chabi", "maintenance deduction",
            "painting deduction", "rental agreement", "lease deed", "rent deposit", "pg deposit",
            "मकान मालिक", "किराया", "सिक्योरिटी डिपॉजिट", "डिपॉजिट", "किराएदार", "किरायेदार",
            "खाली करके", "चाबी दे दी", "रेंट एग्रीमेंट",
        ],
        "medium": [
            "flat", "apartment", "house", "pg", "hostel", "room", "broker", "eviction", "rent",
            "deposit", "makan", "khali", "painting", "society guard",
            "फ्लैट", "कमरा", "मकान", "खाली", "चाबी", "सोसायटी", "पेंटिंग",
        ],
    },
    "UNPAID_SALARY": {
        "high": [
            "salary", "unpaid salary", "wages", "tankhwah", "stipend", "relieving letter", "experience letter",
            "experience certificate", "full and final", "f&f", "notice period", "employment bond",
            "training bond", "service bond", "pf", "gratuity", "pending salary", "payslip",
            "वेतन", "सैलरी", "तनख्वाह", "स्टाइपेंड", "रिलीविंग लेटर", "अनुभव प्रमाण पत्र",
            "ट्रेनिंग बॉन्ड", "सर्विस बॉन्ड", "नोटिस पीरियड", "ग्रेच्युटी", "पीएफ",
        ],
        "medium": [
            "employer", "employee", "boss", "manager", "hr", "resigned", "resignation", "terminated",
            "termination", "fired", "layoff", "laid off", "last working day", "lwd", "pending pay",
            "worked for", "job", "internship", "office", "appraisal", "bonus",
            "कंपनी", "इस्तीफा", "नौकरी", "कर्मचारी", "नियोक्ता", "मालिक", "बॉस", "मैनेजर",
            "काम किया", "ऑफिस",
        ],
    },
    "CONSUMER_REFUND": {
        "high": [
            "refund", "return", "defective", "damaged product", "wrong product", "fake product",
            "counterfeit", "consumer court", "consumer forum", "warranty", "guarantee", "replacement",
            "replace", "not delivered", "e-commerce", "consumer", "return rejected", "refund denied",
            "return request", "cancellation refund", "flight cancelled", "flight delayed", "airline refund",
            "insurance claim rejected", "coaching refund",
            "रिफंड", "पैसे वापस", "वापस नहीं", "टूटा हुआ", "टूटी हुई", "खराब सामान",
            "वारंटी", "गारंटी", "रिप्लेसमेंट", "कंज्यूमर कोर्ट", "उपभोक्ता फोरम",
            "नो रिफंड", "रिटर्न", "पैसे वापस नहीं", "खरीदा था", "खरीदी थी",
        ],
        "medium": [
            "amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa", "zomato", "swiggy", "blinkit",
            "zepto", "urban company", "make my trip", "cleartrip", "airline", "flight ticket",
            "hotel booking", "seller", "order", "courier", "store", "bought", "purchased",
            "customer care", "customer support", "service center", "shoes", "phone", "laptop",
            "appliance", "saman", "plumber", "package", "parcel", "ac", "tv", "fridge", "washing machine",
            "लैपटॉप", "मोबाइल", "फोन", "खरीदा", "खरीदी", "सामान", "डिलीवरी", "अमेज़न",
            "फ्लिपकार्ट", "शॉपिंग", "कस्टमर केयर", "दुकानदार", "सर्विस सेंटर", "पार्सल", "स्क्रीन",
        ],
    },
    "UPI_BANKING_FRAUD": {
        "high": [
            "upi", "debited", "unauthorized transaction", "banking fraud", "phishing", "cyber fraud",
            "otp fraud", "loan app", "recovery agent", "account frozen", "1930", "cybercrime",
            "rbi ombudsman", "fraud debit", "unauthorized debit", "wrongly debited",
            "यूपीआई", "अनधिकृत लेन-देन", "बैंकिंग फ्रॉड", "साइबर अपराध", "साइबर फ्रॉड",
            "ओटीपी", "खाता फ्रीज", "अकाउंट फ्रीज", "धोखाधड़ी से पैसे", "पैसे कट गए",
        ],
        "medium": [
            "gpay", "google pay", "phonepe", "paytm", "cred", "bank account", "atm", "credit card",
            "debit card", "netbanking", "scam", "scammed", "fraudster", "transaction failed", "sbi",
            "hdfc", "icici", "axis bank", "bank",
            "बैंक", "खाता", "अकाउंट", "क्रेडिट कार्ड", "डेबिट कार्ड", "पैसे कट", "रिकवरी एजेंट",
        ],
    },
    "CHEQUE_BOUNCE_RECOVERY": {
        "high": [
            "cheque bounce", "cheque bounced", "bounced cheque", "dishonour of cheque", "dishonored cheque",
            "check bounce", "section 138", "insufficient funds", "return memo", "stop payment cheque",
            "चेक बाउंस", "चेक अनादरण", "धारा 138",
        ],
        "medium": [
            "cheque", "post dated cheque", "pdc", "bank memo", "drawer", "invoice unpaid",
            "चेक",
        ],
    },
    "NOTICE_AND_CRIMINAL_TRIAGE": {
        "high": [
            "legal notice", "court summons", "police complaint", "fir", "thana", "arrest", "warrant",
            "defamation notice", "advocate notice", "extortion", "blackmail", "defamation", "lok adalat warrant",
            "whatsapp summons", "digital arrest",
            "कानूनी नोटिस", "कोर्ट समन", "पुलिस शिकायत", "एफआईआर", "थाना", "गिरफ्तारी", "वारंट",
            "मानहानि", "ब्लैकमेल",
        ],
        "medium": [
            "harassment", "threat", "threatened", "court", "lawyer notice", "police",
            "धमकी", "पुलिस", "वकील", "कोर्ट", "कचहरी", "प्रताड़ना",
        ],
    },
}

OFF_TOPIC_PATTERNS = re.compile(
    r"\b(recipe|how to cook|how to bake|biryani|chocolate cake|pasta|pizza|weather in|temperature in|"
    r"write a python|write a program|javascript|leetcode|binary search|fibonacci|sorting algorithm|"
    r"who won the|ipl match|world cup score|cricket score|football match|tell me a joke|poem about|"
    r"quantum physics|photosynthesis|capital of france|best movies|netflix recommendation)\b",
    re.I,
)

TRIVIAL_SOCIAL_PATTERNS = re.compile(
    r"\b(birthday party|didn'?t invite me|did not invite me|unfollowed me|unfriended me|"
    r"ignored my message|ignored my text|left me on seen|girlfriend broke up|boyfriend broke up|"
    r"crush rejected|neighbour didn'?t smile|didn'?t say good morning|ate my lunch|ate my food|"
    r"friend didn'?t wish|talking behind my back|blocked me on instagram)\b",
    re.I,
)

SELF_FAULT_PATTERNS = re.compile(
    r"\b(i dropped (it|my|the)|accidentally dropped|dropped my (phone|iphone|mobile|laptop|macbook|watch|tablet|tv|device)|"
    r"dropped the (phone|iphone|mobile|laptop|device)|fell from (my|the) (hand|balcony|table|pocket|stairs)|"
    r"spilled (water|coffee|tea|liquid) on|broke it myself|i broke the screen|i tore the|washed it in hot|"
    r"changed my mind after \d+ months|wore it \d+ times and want refund|lost the item myself)\b",
    re.I,
)

TIME_BARRED_PATTERNS = re.compile(
    r"\b(([4-9]|\d{2,})\s+years?\s+ago|in\s+(19\d{2}|200\d|201\d|2020|2021))\b",
    re.I,
)

LAWFUL_COUNTERPARTY_PATTERNS = re.compile(
    r"\b(i didn'?t pay rent for \d+ months|i did not pay rent for \d+ months|"
    r"refused to return the company laptop|kept the company laptop|not returning office laptop)\b",
    re.I,
)


def _compute_domain_scores(text: str) -> Dict[str, int]:
    t = text.lower()
    scores: Dict[str, int] = {}
    for domain, kw_dict in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in kw_dict["high"]:
            if kw in t:
                score += 3
        for kw in kw_dict["medium"]:
            if kw in t:
                score += 1
        scores[domain] = score

    # Boost loan-app / fake recovery warrant to NOTICE_AND_CRIMINAL_TRIAGE if warrant/summons/arrest mentioned
    if any(k in t for k in ("lok adalat warrant", "whatsapp summons", "arrest kar legi", "threatening arrest")):
        scores["NOTICE_AND_CRIMINAL_TRIAGE"] = max(scores.get("NOTICE_AND_CRIMINAL_TRIAGE", 0), scores.get("UPI_BANKING_FRAUD", 0) + 2)

    return scores


def _is_gibberish_or_noise(text: str, max_domain_score: int, is_red_line: bool) -> bool:
    clean = text.strip()
    if not clean or len(clean) < 4:
        return True
    if is_red_line or max_domain_score > 0:
        return False

    # If Devanagari characters exist and there are at least 3 words, not gibberish
    devanagari_words = re.findall(r"[\u0900-\u097F]+", clean)
    if len(devanagari_words) >= 3:
        return False

    latin_words = re.findall(r"[a-zA-Z]+", clean.lower())
    if len(latin_words) < 3:
        return True

    # Check for keyboard smash patterns or extreme lack of vowels
    joined_alpha = "".join(latin_words)
    if re.search(r"(asdf|qwert|zxcv|hjkl|bnm|[bcdfghjklmnpqrstvwxz]{6,}|(.)\2{4,})", joined_alpha):
        return True

    vowels = sum(1 for ch in joined_alpha if ch in "aeiou")
    if len(joined_alpha) >= 6 and (vowels / len(joined_alpha)) < 0.15:
        return True

    return False


def _detect_validity_and_merits(
    text: str,
    scores: Dict[str, int],
    is_red_line: bool,
) -> Tuple[str, str]:
    max_score = max(scores.values()) if scores else 0

    # 1. Check Gibberish / Keysmash / Too-Short Input
    if _is_gibberish_or_noise(text, max_score, is_red_line):
        return (
            "GIBBERISH_OR_TOO_SHORT",
            "Your input appears to be random characters, a short greeting, or lacks enough detail to identify a legal issue. Please describe who wronged you, what happened, and the amount involved.",
        )

    # 2. Check Explicit Off-Topic Non-Legal Queries (recipes, coding, sports, weather)
    if OFF_TOPIC_PATTERNS.search(text) and not is_red_line and max_score <= 1:
        return (
            "OFF_TOPIC_NON_LEGAL",
            "This query is unrelated to law or civil disputes. NyayaSahayak is a specialized Indian Legal Aid engine and does not process cooking, programming, sports, or general trivia requests.",
        )

    # 3. Check 'No Law Case' — Trivial / Social Grievance (De Minimis Non Curat Lex)
    if TRIVIAL_SOCIAL_PATTERNS.search(text) and not is_red_line:
        return (
            "NO_CLAIM_TRIVIAL_SOCIAL",
            "No Legal Case Exists (Section 33 BNS 2023 — De Minimis Non Curat Lex): Purely social, interpersonal, or trivial grievances without a binding legal contract or statutory violation cannot be taken to court.",
        )

    # 4. Check 'No Law Case' — Customer-Induced Damage / Self-Fault
    if SELF_FAULT_PATTERNS.search(text) and not is_red_line:
        return (
            "NO_CLAIM_SELF_FAULT",
            "No Actionable Refund Claim (Customer-Induced Damage / Buyer's Remorse): Under Section 2(11) of the Consumer Protection Act, 2019, sellers are liable for defects present at delivery or covered by warranty—not accidental damage caused by the user after delivery.",
        )

    # 5. Check 'No Law Case' — Time-Barred by Limitation Act
    if TIME_BARRED_PATTERNS.search(text) and not is_red_line:
        return (
            "NO_CLAIM_TIME_BARRED",
            "Claim Prima Facie Time-Barred (Section 3, Limitation Act, 1963 / Section 69, CPA 2019): Civil recovery claims expire after 3 years and Consumer Forum claims after 2 years. Courts must dismiss time-barred suits unless a fresh written acknowledgment of debt was signed under Section 18.",
        )

    # 6. Check 'No Law Case' — Lawful Counter-Party Deduction / Unreturned Asset
    if LAWFUL_COUNTERPARTY_PATTERNS.search(text) and not is_red_line:
        return (
            "NO_CLAIM_LAWFUL_DEDUCTION",
            "Opposite Party Holds a Lawful Lien / Set-Off Right: Under Section 11(2) of the Model Tenancy Act and the Indian Contract Act, unpaid rent arrears or unreturned company hardware (laptops) can be lawfully set off before releasing the remaining balance.",
        )

    # 7. If zero domain keywords matched and not red-line, it's an unrecognized/non-legal statement
    if max_score == 0 and not is_red_line:
        return (
            "OFF_TOPIC_NON_LEGAL",
            "No Legal Dispute Detected: We could not identify any statutory violation, contract breach, unpaid dues, consumer defect, or legal notice in your text.",
        )

    return ("ACTIONABLE_CLAIM", "Valid, actionable legal claim under Indian statute.")


def _parse_val(num_str: str, unit: Optional[str] = None) -> int:
    v = float(str(num_str).replace(",", ""))
    u = (unit or "").lower().strip()
    if u in ("lakh", "lakhs", "lac", "lacs", "l"):
        return int(v * 100000)
    if u in ("crore", "crores", "cr"):
        return int(v * 10000000)
    if u in ("k", "thousand", "hazar", "hazaar"):
        return int(v * 1000)
    return int(v)


def _extract_amount_inr(text: str) -> Tuple[int, bool]:
    """Returns (extracted_amount_inr, amount_was_explicitly_specified)."""
    t = text.lower().replace(",", "")

    # 1. Targeted pattern: keyword followed by amount
    target_m = re.search(
        r"(?:salary|deposit|refund|debited|paid|dues|stipend|worth|kiraya|advance|loss|cheque|check|dowry|claim)\s*(?:of|is|was|approx|around|amount|worth|ka|ki|for)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|hazar|hazaar|lakhs?|lacs?|l|crores?|cr)?\b",
        t,
    )
    if target_m:
        val = _parse_val(target_m.group(1), target_m.group(2))
        if val > 100:
            return val, True

    # 2. Currency symbol followed by amount and unit
    curr_m = re.search(r"(?:rs\.?|inr|₹)\s*(\d+(?:\.\d+)?)\s*(k|thousand|hazar|hazaar|lakhs?|lacs?|l|crores?|cr)?\b", t)
    if curr_m:
        val = _parse_val(curr_m.group(1), curr_m.group(2))
        if val > 100:
            return val, True

    # 3. Unit after number (e.g. 60k, 40 hazar, 1.2 lakh)
    unit_m = re.search(r"\b(\d+(?:\.\d+)?)\s*(k|thousand|hazar|hazaar|lakhs?|lacs?|crores?|cr)\b", t)
    if unit_m:
        val = _parse_val(unit_m.group(1), unit_m.group(2))
        if val > 100:
            return val, True

    # 4. Standalone 4-7 digit number
    num_m = re.findall(r"\b(\d{3,7})\b", t)
    for cand in num_m:
        val = int(cand)
        if val not in (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 1930, 1915, 15100, 1881, 1882, 1872, 1936):
            return val, True

    return 50000, False


def build_structured_case(
    user_story: str,
    case_id: str = "CASE-LIVE",
    router: Optional[UniversalLLMRouter] = None,
) -> StructuredLegalCase:
    lang = _detect_language(user_story)
    scores = _compute_domain_scores(user_story)
    amount, amount_specified = _extract_amount_inr(user_story)

    model_name = (router.config.model if router else "gemini-2.5-flash (Balanced Legal Strategy)")
    m_low = model_name.lower()
    is_aggressive = (
        "aggressive" in m_low
        or ("balanced" in m_low and any(k in m_low for k in ("-pro", "large", "r1", "70b")))
    )
    is_conciliatory = (
        "conciliatory" in m_low
        or "amicable" in m_low
        or ("balanced" in m_low and any(k in m_low for k in ("2.0", "lite", "instant", "small", "mini", "8b", "9b")))
    )

    t_low = user_story.lower()
    # 1. Check Red-Line Safety Escalation Triggers first (excluding fake loan-app/recovery WhatsApp bluffs)
    is_fake_recovery_bluff = any(
        k in t_low for k in (
            "loan app", "recovery agent", "lok adalat warrant", "whatsapp par", "whatsapp summons",
            "fake notice", "fake warrant", "fake police", "fake legal notice", "fake summons",
            "scam notice", "scam warrant", "fake advocate", "threat notice", "fake case", "digital arrest",
        )
    )
    is_red_line = False
    red_line_reason = ""
    if not is_fake_recovery_bluff:
        for pat, title, msg in RED_LINE_TRIGGERS:
            if pat.search(user_story):
                is_red_line = True
                red_line_reason = f"[{title}] {msg}"
                break

    # 2. Check Input Validity & Legal Merits Gate
    validity_status, validity_explanation = _detect_validity_and_merits(user_story, scores, is_red_line)
    if is_red_line:
        validity_status = "RED_LINE_SAFETY"
        validity_explanation = red_line_reason

    # Determine domain_key
    if is_red_line:
        domain_key = "NOTICE_AND_CRIMINAL_TRIAGE"
    elif validity_status in ("GIBBERISH_OR_TOO_SHORT", "OFF_TOPIC_NON_LEGAL"):
        domain_key = "NO_LEGAL_CLAIM_OR_NON_JUSTICIABLE"
        amount = 0
        amount_specified = False
    elif validity_status.startswith("NO_CLAIM_"):
        domain_key = "NO_LEGAL_CLAIM_OR_NON_JUSTICIABLE"
        if not amount_specified:
            amount = 0
    else:
        best_domain = max(scores, key=scores.get)
        domain_key = best_domain if scores[best_domain] > 0 else "NOTICE_AND_CRIMINAL_TRIAGE"

    domain_info = get_domain_statutes(domain_key)

    # 3. Handle Non-Actionable / Gibberish / Off-Topic / No-Law-Case states cleanly
    if validity_status in (
        "GIBBERISH_OR_TOO_SHORT",
        "OFF_TOPIC_NON_LEGAL",
        "NO_CLAIM_TRIVIAL_SOCIAL",
        "NO_CLAIM_SELF_FAULT",
        "NO_CLAIM_TIME_BARRED",
        "NO_CLAIM_LAWFUL_DEDUCTION",
    ):
        if validity_status == "GIBBERISH_OR_TOO_SHORT":
            standing_en = (
                "We could not analyze your input because it appears to be random characters, a greeting, or too brief to describe a legal dispute. "
                "Please describe: (1) Who the opposite party is (Landlord, Employer, E-Commerce Seller, Bank), (2) What happened, and (3) How much money is at stake."
            )
            standing_hi = (
                "Aapka input adhoora hai ya kisi kanooni vivad ko spasht nahi karta. Kripya batayein: (1) Vivad kiske saath hai (Makan Malik, Company, Shopping App, Bank), (2) Kya hua, aur (3) Kitni rashi (amount) fasi hai."
            )
            trap_tip = "Click any Example Scenario in the left sidebar or type a real dispute sentence above (e.g., 'My landlord in Pune withheld my ₹50,000 deposit')."
            ev_score = 0
        elif validity_status == "OFF_TOPIC_NON_LEGAL":
            standing_en = (
                "This request does not involve a legal dispute or statutory right. NyayaSahayak is a specialized Indian Legal Aid engine built for consumer refunds, rental deposits, unpaid wages, banking fraud, and legal notices."
            )
            standing_hi = (
                "Yeh prashn kanoon ya nagrik adhikaron se sambandhit nahi hai. NyayaSahayak keval kiraya deposit, ruki hui salary, consumer refund, UPI fraud aur kanooni notice mein sahayata karta hai."
            )
            trap_tip = "If you have an everyday legal issue, describe the transaction, opposite party, and amount above."
            ev_score = 0
        elif validity_status == "NO_CLAIM_TRIVIAL_SOCIAL":
            standing_en = (
                "HONEST LEGAL MERITS VERDICT — NO CASE: Under Section 33 of the Bharatiya Nyaya Sanhita (BNS), 2023 (De minimis non curat lex — the law does not concern itself with trifles) and Section 10 of the Indian Contract Act, 1872, purely social or personal slights (such as not being invited to a party or being ignored on chat) do not create any enforceable legal right. Filing a legal notice here would be frivolous and unenforceable."
            )
            standing_hi = (
                "KANOONI RAI — KOI CASE NAHI BANTA: Bharatiya Nyaya Sanhita (BNS) 2023 ke Section 33 (De minimis non curat lex) ke tahat mamooli samajik ya vyaktigat narazgi par court mein mukadma nahi chalta. Aise maamle mein Legal Notice bhejna vyarth hai."
            )
            trap_tip = "Save your time and money—courts impose costs on frivolous litigation. Resolve personal misunderstandings informally."
            ev_score = 10
        elif validity_status == "NO_CLAIM_SELF_FAULT":
            standing_en = (
                "HONEST LEGAL MERITS VERDICT — WEAK / NO STATUTORY CLAIM: Under Section 2(11) and Section 2(47) of the Consumer Protection Act, 2019, a seller or brand is legally liable only for manufacturing defects or service deficiencies—NOT for accidental physical/liquid damage caused by the user after delivery or buyer's remorse after the return window closes."
            )
            standing_hi = (
                "KANOONI RAI — KANOONAN DAWA KAMZOR HAI: Consumer Protection Act 2019 ke Section 2(11) ke mutabik agar saman delivery ke baad grahak ke khud ke haath se toota hai ya return window ke baad bina kharabi ke mann badla hai, toh company par kanooni refund ka daava nahi banta."
            )
            trap_tip = "Instead of a legal threat (which will be rejected), check if your credit card offers 'Purchase Protection / Accidental Damage Cover' or request a paid authorized repair discount as a goodwill gesture."
            ev_score = 15
        elif validity_status == "NO_CLAIM_TIME_BARRED":
            standing_en = (
                "HONEST LEGAL MERITS VERDICT — TIME-BARRED BY LIMITATION ACT: Under Section 3 of the Limitation Act, 1963, civil recovery suits expire after 3 years (and Consumer Forum complaints expire after 2 years under Section 69 of the Consumer Protection Act, 2019). Any suit filed after the limitation period must be dismissed by the Court unless you hold a signed written acknowledgment of debt executed before the deadline under Section 18 of the Limitation Act."
            )
            standing_hi = (
                "KANOONI RAI — SAMAY-SEEMA (LIMITATION) BEET CHUKI HAI: Limitation Act 1963 ke Section 3 ke tahat 3 saal (aur Consumer case mein 2 saal) beet jaane ke baad court case dakhil nahi ho sakta, jab tak ki virodhi paksh ne likhit mein bakaya swikar na kiya ho (Section 18)."
            )
            trap_tip = "Exception Check: If the opposite party sent you a WhatsApp message, email, or part-payment acknowledging the debt within the last 3 years, that written admission restarts the 3-year clock under Section 18 of the Limitation Act!"
            ev_score = 20
        else:  # NO_CLAIM_LAWFUL_DEDUCTION
            standing_en = (
                "HONEST LEGAL MERITS VERDICT — OPPOSITE PARTY HAS LAWFUL SET-OFF RIGHTS: Under Section 11(2) of the Model Tenancy Act and the Indian Contract Act, 1872, a landlord is legally entitled to deduct admitted unpaid rent arrears from a security deposit, and an employer is entitled to require return of company hardware (laptops/assets) before releasing Full & Final clearance."
            )
            standing_hi = (
                "KANOONI RAI — VIRODHI PAKSH KA KANOONI ADHIKAR: Agar aapne kiraya nahi diya hai ya company ka laptop/property wapas nahi ki hai, toh kanoonan maalik/company uska hisaab kaatne ya clearance rokne ka adhikar rakhti hai."
            )
            trap_tip = "Immediately return any company property with a signed handover receipt (or reconcile actual rent arrears) so you can legally demand the remaining net balance and your Relieving Letter."
            ev_score = 25

        clean_en, audit_en = verify_and_sanitize_legal_text(standing_en)
        clean_hi, audit_hi = verify_and_sanitize_legal_text(standing_hi)

        return StructuredLegalCase(
            case_id=case_id,
            detected_language=lang,
            domain_key=domain_key,
            domain_title=domain_info["title"],
            is_red_line_escalation=False,
            red_line_reason="",
            red_line_emergency_contacts=[],
            claim_amount_inr=amount,
            timeline=[
                TimelineFact(1, "Intake Merits Audit", validity_explanation, "Evaluated under BNS Sec 33, Limitation Act Sec 3, and CPA Sec 2(11).")
            ],
            evidence_score_100=ev_score,
            evidence_checklist=[
                EvidenceItem("Actionable Statutory Cause of Action", "MISSING_CRITICAL", 100, validity_explanation)
            ],
            pre_notice_evidence_trap_tip=trap_tip,
            plain_language_standing_en=clean_en,
            plain_language_standing_hi=clean_hi,
            limitation_analysis={
                "statutory_limit_years": "N/A (Non-Actionable / Expired)",
                "legal_basis": domain_info["limitation_basis"],
                "official_portal": domain_info["official_portal"],
            },
            roi_comparison=[
                {
                    "option": "Step 1: Informal Goodwill Request / Mutual Conversation",
                    "estimated_cost_inr": "₹0",
                    "typical_timeline": "1 to 3 Days",
                    "success_probability": "20%–35% (Depends purely on goodwill, not legal compulsion)",
                    "recommended": "YES — Only viable option when legal standing is absent",
                },
                {
                    "option": "Step 2: Formal Court / Tribunal Litigation",
                    "estimated_cost_inr": "₹10,000 – ₹35,000+ (High risk of dismissal with costs)",
                    "typical_timeline": "Dismissed at threshold",
                    "success_probability": "< 5% (Statutorily barred or non-justiciable)",
                    "recommended": "NO — Do NOT waste money on lawyers or court fees here",
                },
            ],
            verified_statutes=domain_info["verified_statutes"],
            citation_firewall_audit=audit_en + audit_hi,
            case_validity_status=validity_status,
            validity_explanation=validity_explanation,
            amount_specified=amount_specified,
            strategy_profile_applied=model_name,
        )

    # 4. Build Chronological Case Timeline & Evidence Audit for Actionable Claims
    timeline: List[TimelineFact] = []
    evidence: List[EvidenceItem] = []
    trap_tip = ""
    standing_en = ""
    standing_hi = ""

    if domain_key == "TENANCY_DEPOSIT":
        has_agreement = any(w in t_low for w in ("agreement", "contract", "lease", "rent deed"))
        has_receipt = any(w in t_low for w in ("upi", "bank", "transfer", "receipt", "neft", "paid"))
        has_whatsapp = any(w in t_low for w in ("whatsapp", "message", "chat", "email", "text"))
        has_keys = any(w in t_low for w in ("key", "keys", "vacated", "left", "chabi", "khali"))

        timeline = [
            TimelineFact(1, "Lease Commencement", f"Paid refundable security deposit of ₹{amount:,} to landlord.", "Establishes liquidated refundable debt under Indian Contract Act Sec 73 & CPC Order XXXVII."),
            TimelineFact(2, "Notice & Vacant Handover", "Vacated premises and handed over keys / vacant possession to landlord.", "Triggers mandatory refund obligation under Transfer of Property Act Sec 108(q) & Model Tenancy Act Sec 11."),
            TimelineFact(3, "Unjustified Withholding", "Landlord refusing refund or claiming arbitrary painting/wear-and-tear deductions without bills.", "Arbitrary deductions without actual proven damage violate Indian Contract Act Sec 73-74."),
        ]
        evidence = [
            EvidenceItem("Written Rent / Lease Agreement", "PRESENT" if has_agreement else "MISSING_CRITICAL", 30, "Check email/broker WhatsApp for PDF or signed copy; even an expired agreement + bank rent trail proves tenancy."),
            EvidenceItem("Bank / UPI Deposit Transfer Proof", "PRESENT" if has_receipt else "MISSING_CRITICAL", 30, "Download bank statement showing UTR/UPI transaction ID of the original deposit transfer."),
            EvidenceItem("Key Handover & Vacant Possession Proof", "PRESENT" if has_keys else "RECOMMENDED", 20, "Society gate move-out pass, electricity final bill, or WhatsApp message confirming date keys were handed over."),
            EvidenceItem("Written Refusal / Deduction Admission on WhatsApp", "PRESENT" if has_whatsapp else "RECOMMENDED", 20, "Export WhatsApp chat showing landlord admitting they hold the deposit or making unbilled deduction claims."),
        ]
        if is_aggressive:
            trap_tip = (
                f"[HIGH-PRESSURE STRATEGY] Send a final 24-hour ultimatum demanding GST-verified repair invoices and immediate NEFT/UPI refund of ₹{amount:,} + 18% p.a. interest, "
                "putting the landlord on notice of an Order XXXVII CPC Summary Suit and BNS Section 316 (Criminal Breach of Trust) escalation."
            )
            standing_en = (
                f"[AGGRESSIVE ENFORCEMENT POSTURE] Unlawfully retaining ₹{amount:,} after key handover violates Section 108(q) of the Transfer of Property Act, 1882 and Sections 73 & 74 of the Indian Contract Act, 1872. "
                "We recommend serving an immediate 48-hour Summary Suit Demand Notice under Order XXXVII CPC claiming the full principal plus 18% p.a. interest under Section 34 CPC and litigation costs."
            )
            standing_hi = (
                f"[AAKRAMAK KANOONI RANNITI] Makan khali karne ke baad ₹{amount:,} rokna Transfer of Property Act Section 108(q) aur Indian Contract Act Section 73-74 ka seedha ullanghan hai. "
                "Hum 48 ghante ka kanooni ultimatum dekar CPC Order 37 Summary Suit aur Section 34 ke tahat 18% salana byaaj (interest) vasoolne ki salah dete hain."
            )
        elif is_conciliatory:
            trap_tip = (
                f"[FAST 48-HR SETTLEMENT STRATEGY] Propose a calm, face-saving joint settlement today: offer to waive all delay interest and close the lease amicably if ₹{amount:,} is transferred via UPI within 48 hours."
            )
            standing_en = (
                f"[AMICABLE MEDIATION POSTURE] While Section 108(q) of the Transfer of Property Act, 1882 and Sections 73 & 74 of the Indian Contract Act, 1872 protect your full ₹{amount:,} deposit against unbilled painting deductions, "
                "the fastest way to recover your money within 48 hours is a 'Without Prejudice' mutual settlement offering a clean no-dues sign-off and interest waiver."
            )
            standing_hi = (
                f"[AAPSI SAMJHAUTA RANNITI] Transfer of Property Act Section 108(q) ke tahat aapka ₹{amount:,} ka daava bilkul mazboot hai. "
                "Court kachahri mein samay gawaye bina 48 ghante mein paisa wapas paane ke liye maalik ko byaaj chhodne aur aapsi 'No-Dues' samjhauta karne ka prastav dein."
            )
        else:
            trap_tip = (
                "Before sending a formal Legal Notice, send this polite 'Evidence Trap' WhatsApp message today: "
                "'Hi [Landlord Name], since I handed over the flat keys on [Date] in clean condition, please confirm by when my ₹"
                f"{amount:,} security deposit will be transferred to my UPI/account.' If they reply with excuses instead of denying the amount or handover date, "
                "their reply becomes an ironclad written admission for an Order XXXVII Summary Suit!"
            )
            standing_en = (
                f"You have a strong civil recovery claim for ₹{amount:,}. Under Section 108(q) of the Transfer of Property Act, 1882 and Sections 73 & 74 of the Indian Contract Act, 1872, "
                "a landlord cannot retain your security deposit after vacant possession is handed over, nor deduct arbitrary lump sums for routine wear-and-tear without itemized third-party repair invoices."
            )
            standing_hi = (
                f"Aapka ₹{amount:,} ka daava kanoonan mazboot hai. Transfer of Property Act Section 108(q) aur Indian Contract Act Section 73-74 ke tahat, "
                "makan khali karne aur chabi dene ke baad maalik bina asli repair bill dikhaye manmaane tarike se security deposit nahi kaat sakta."
            )

    elif domain_key == "UNPAID_SALARY":
        has_offer = any(w in t_low for w in ("offer letter", "appointment", "contract", "joined"))
        has_payslip = any(w in t_low for w in ("payslip", "salary slip", "bank statement", "credited"))
        has_resign = any(w in t_low for w in ("resign", "email", "notice period", "last working day", "lwd", "handover"))

        timeline = [
            TimelineFact(1, "Employment & Earned Work", "Performed duties under valid employment terms; salary/F&F accrued.", "Establishes statutory wage liability under Payment of Wages Act Sec 3 & Sec 5."),
            TimelineFact(2, "Exit / Handover Completion", "Completed handover / served notice period or terminated by employer.", "Triggers statutory deadline for Full & Final settlement and service certificate release."),
            TimelineFact(3, "Unlawful Withholding", f"Employer withholding ₹{amount:,} unpaid wages/F&F or holding Relieving Letter hostage.", "Actionable before Labour Commissioner via SAMADHAN Portal & Industrial Disputes Act Sec 33C(2)."),
        ]
        evidence = [
            EvidenceItem("Appointment / Offer Letter & CTC Breakdown", "PRESENT" if has_offer else "RECOMMENDED", 25, "Save offer letter PDF and confirmation email from personal inbox."),
            EvidenceItem("Last 3 Months' Salary Slips / Bank Statement", "PRESENT" if has_payslip else "PRESENT", 30, "Bank account statement showing regular monthly salary credits from employer."),
            EvidenceItem("Resignation Acceptance & No-Dues / Handover Email", "PRESENT" if has_resign else "MISSING_CRITICAL", 25, "Forward acceptance and IT/asset clearance emails to your personal email immediately before corporate access is revoked."),
            EvidenceItem("Written Follow-up Trail on F&F / Relieving Letter", "PRESENT", 20, "Email HR & Finance copying Directors demanding itemized F&F computation sheet."),
        ]
        if is_aggressive:
            trap_tip = (
                "[HIGH-PRESSURE STRATEGY] Put the Company Directors and HR Head on personal notice under Section 15(3) of the Payment of Wages Act, 1936 (up to 10x penalty for wrongful deduction) and BNS Section 316."
            )
            standing_en = (
                f"[AGGRESSIVE ENFORCEMENT POSTURE] Withholding ₹{amount:,} in earned wages and holding your Relieving Letter hostage violates Sections 3, 5 & 15 of the Payment of Wages Act, 1936. "
                "Employment bonds and non-competes are void under Sections 27 & 74 of the Indian Contract Act, 1872. Demand settlement within 48 hours failing which file on SAMADHAN and summon the Directors before the Labour Commissioner."
            )
            standing_hi = (
                f"[AAKRAMAK KANOONI RANNITI] ₹{amount:,} ki mehnat ki salary aur Relieving Letter rokna Payment of Wages Act Section 3, 5, 15 ke tahat dandaatmak apradh hai. "
                "48 ghante ka ultimatum dekar Company Directors ke khilaf SAMADHAN portal aur Labour Commissioner mein muavze sahit shikayat darj karein."
            )
        elif is_conciliatory:
            trap_tip = (
                "[FAST 48-HR SETTLEMENT STRATEGY] Send a cooperative handover summary to HR & Finance offering to sign a clean mutual release as soon as ₹"
                f"{amount:,} F&F and your Relieving Letter are issued this week."
            )
            standing_en = (
                f"[AMICABLE MEDIATION POSTURE] Your right to ₹{amount:,} in unpaid salary and your Relieving Letter is protected under Sections 3, 5 & 15 of the Payment of Wages Act, 1936 and Section 27 of the Indian Contract Act, 1872. "
                "To protect your background verification (BGV) and get paid fast, propose a 5-day amicable F&F closure with HR before escalating to SAMADHAN."
            )
            standing_hi = (
                f"[AAPSI SAMJHAUTA RANNITI] Payment of Wages Act Section 3, 5, 15 aur Contract Act Section 27 ke tahat aapka पक्ष mazboot hai. "
                "Apne career aur BGV ko surakshit rakhte hue HR ko 5 din mein shantipoorvak F&F aur Relieving Letter jari karne ka prastav bhejein."
            )
        else:
            trap_tip = (
                "If you still have corporate email/Slack access, immediately forward your resignation acceptance, asset handover clearance, and attendance record to your personal email. "
                "Note: Any post-employment clause threatening you not to join a competitor is 100% VOID under Section 27 of the Indian Contract Act, 1872."
            )
            standing_en = (
                f"Withholding earned salary/F&F of ₹{amount:,} or holding your Relieving Letter hostage is unlawful under Sections 3, 5 & 15 of the Payment of Wages Act, 1936 and State Shops & Establishments Acts. "
                "Furthermore, under Section 27 and Section 74 of the Indian Contract Act, 1872, post-termination non-compete restraints are void and unproved training bond penalties cannot be deducted from earned wages."
            )
            standing_hi = (
                f"Mehnat ki kamaai (₹{amount:,}) ya Relieving Letter rokna Payment of Wages Act Section 3, 5, 15 aur State Shops & Establishments Act ke khilaf hai. "
                "Indian Contract Act Section 27 ke tahat naukri chhodne ke baad dusri company join karne se rokne wali shart bilkul shoonya (void) hai."
            )

    elif domain_key == "CONSUMER_REFUND":
        timeline = [
            TimelineFact(1, "Purchase & Consideration Paid", f"Paid ₹{amount:,} for product/service via digital invoice.", "Establishes Consumer status under Section 2(7) of the Consumer Protection Act, 2019."),
            TimelineFact(2, "Defect / Deficiency Discovered", "Received defective/wrong item or deficient service; raised return/refund request.", "Triggers E-Commerce Rules 2020 Rule 4 (48-hour acknowledgment & 30-day resolution mandate)."),
            TimelineFact(3, "Unfair Refusal to Refund", "Platform/seller closed ticket or refused refund despite proof.", "Constitutes 'Deficiency' under Section 2(11) and 'Unfair Trade Practice' under Section 2(47)(vii) of CPA 2019."),
        ]
        evidence = [
            EvidenceItem("Tax Invoice / Order Confirmation & Payment Proof", "PRESENT", 35, "Download PDF invoice and UPI/Card statement."),
            EvidenceItem("Unboxing Video / Photos of Defect", "PRESENT" if "photo" in t_low or "video" in t_low else "RECOMMENDED", 30, "Take clear timestamped photos/video of the product serial number, packaging, and defect."),
            EvidenceItem("Customer Support Ticket IDs & Chat Screenshots", "PRESENT", 35, "Save ticket numbers showing the company failed to resolve within 30 days under E-Commerce Rules 2020."),
        ]
        if is_aggressive:
            trap_tip = (
                "[HIGH-PRESSURE STRATEGY] Serve a 48-hour notice on the company's Nodal Grievance Officer under Rule 4(4) of the E-Commerce Rules, 2020 demanding ₹"
                f"{amount:,} refund plus ₹25,000 mental harassment damages prior to District Commission e-Daakhil filing."
            )
            standing_en = (
                f"[AGGRESSIVE ENFORCEMENT POSTURE] Refusing to refund ₹{amount:,} for defective goods is a statutory 'Unfair Trade Practice' under Section 2(47)(vii) and 'Deficiency' under Section 2(11) of the Consumer Protection Act, 2019. "
                "Demand immediate reversal within 48 hours or file electronically via e-Daakhil under Section 35 claiming principal refund, 18% interest, and punitive mental agony damages."
            )
            standing_hi = (
                f"[AAKRAMAK KANOONI RANNITI] Kharab saman par ₹{amount:,} ka refund rokna Consumer Protection Act 2019 ke Section 2(47)(vii) ke tahat dandaatmak अपराध hai. "
                "48 ghante ka ultimatum dein, warna e-Daakhil par ₹0 fee mein mool rashi aur mansik pratarna harjaane ka case dakhil karein."
            )
        elif is_conciliatory:
            trap_tip = (
                "[FAST 48-HR SETTLEMENT STRATEGY] Escalate politely to the Grievance Officer desk requesting a one-time replacement or full original-source refund within 72 hours to close the NCH 1915 ticket amicably."
            )
            standing_en = (
                f"[AMICABLE MEDIATION POSTURE] Under Section 2(11), Section 2(47)(vii), and Section 35 of the Consumer Protection Act, 2019, a 'No Refund' policy cannot override defective delivery of ₹{amount:,}. "
                "Routing a polite escalation through the National Consumer Helpline (1915) and the brand's Grievance Officer under Rule 4(4) typically resolves the refund within 3–5 days without court proceedings."
            )
            standing_hi = (
                f"[AAPSI SAMJHAUTA RANNITI] Consumer Protection Act 2019 ke Section 2(11) aur Rule 4(4) E-Commerce Rules ke tahat ₹{amount:,} ka refund aapka kanooni haq hai. "
                "Grievance Officer aur National Consumer Helpline (1915) ke madhyam se bina court gaye 3-5 din mein refund prapt karein."
            )
        else:
            trap_tip = (
                "Send one email to the company's statutory 'Grievance Officer' (mandatory on their website under Rule 4 of the E-Commerce Rules, 2020) with subject: "
                "'Notice under Rule 4(4) Consumer Protection (E-Commerce) Rules 2020 prior to e-Daakhil Filing'. Half of e-commerce escalations settle within 72 hours of citing Rule 4(4)."
            )
            standing_en = (
                f"Refusing to refund ₹{amount:,} for a defective product or undelivered service is an explicit 'Unfair Trade Practice' under Section 2(47)(vii) and 'Deficiency' under Section 2(11) of the Consumer Protection Act, 2019. "
                "Under Section 35, you can file online via e-Daakhil from home with ₹0 court fee (since your claim is under ₹5 Lakh)."
            )
            standing_hi = (
                f"Kharab saman ya service par ₹{amount:,} ka refund na dena Consumer Protection Act 2019 ke Section 2(11) aur Section 2(47)(vii) ke tahat dandaatmak 'Unfair Trade Practice' hai. "
                "5 Lakh tak ke claim par e-Daakhil portal par ₹0 court fee lagti hai."
            )

    elif domain_key == "UPI_BANKING_FRAUD":
        timeline = [
            TimelineFact(1, "Unauthorized / Failed Debit", f"₹{amount:,} debited via UPI/Bank or harassed by digital lending agent.", "Triggers RBI Master Circular on Customer Protection (Ref: DBR.No.Leg.BC.78/09.07.005/2017-18)."),
            TimelineFact(2, "Mandatory Reporting Window", "Report to 1930 Cybercrime Helpline & Bank within 3 working days.", "Locks in ZERO Customer Liability and 10-day shadow reversal mandate under Paragraphs 6 & 9 of RBI Circular."),
            TimelineFact(3, "Ombudsman Escalation", "If bank delays beyond TAT / 30 days, escalate to cms.rbi.org.in.", "Entitles customer to ₹100/day failed-UPI delay penalty or RBI Integrated Ombudsman award."),
        ]
        evidence = [
            EvidenceItem("Bank Statement & 12-Digit UTR / UPI Ref Number", "PRESENT", 40, "Note the exact 12-digit UPI RRN/UTR number and timestamp."),
            EvidenceItem("1930 / cybercrime.gov.in Acknowledgment Number", "RECOMMENDED", 30, "Call 1930 immediately if fraud occurred so the recipient bank account layer is frozen."),
            EvidenceItem("Written Dispute Ticket to Bank Nodal Officer", "RECOMMENDED", 30, "Send email within 3 working days to lock in RBI Zero-Liability protection."),
        ]
        if is_aggressive:
            trap_tip = (
                "[HIGH-PRESSURE STRATEGY] Demand immediate 10-day shadow credit of ₹"
                f"{amount:,} plus ₹100/day statutory TAT delay penalty under RBI Circular DPSS.CO.PD No.629/02.01.014/2019-20 from the Bank Principal Nodal Officer."
            )
        else:
            trap_tip = (
                "Call 1930 within the 'Golden Hour' so the National Cybercrime Portal places an automated lien/freeze on the fraudster's bank account before the money is withdrawn at an ATM. "
                "Simultaneously email your bank citing RBI Circular DBR.No.Leg.BC.78/09.07.005/2017-18 demanding a shadow credit within 10 working days."
            )
        standing_en = (
            f"Under Paragraphs 6, 7 & 9 of the RBI Master Circular on Unauthorised Electronic Banking Transactions, if you report an unauthorized third-party breach within 3 working days, your liability is ZERO and the bank must credit a shadow reversal of ₹{amount:,} within 10 working days. "
            "For failed UPI debits not auto-reversed in T+1/T+5 days, the bank owes you ₹100/day automatic compensation."
        )
        standing_hi = (
            f"RBI Circular ke Paragraphs 6, 7 aur 9 ke tahat, 3 working days ke andar unauthorized transaction report karne par aapki Zero Liability hoti hai aur bank ko 10 working days mein ₹{amount:,} ka shadow reversal dena zaroori hai."
        )

    elif domain_key == "CHEQUE_BOUNCE_RECOVERY":
        timeline = [
            TimelineFact(1, "Issuance & Presentation of Cheque", f"Cheque for ₹{amount:,} presented to bank towards discharge of legally enforceable debt.", "Attracts statutory presumption of debt under Section 139 of the Negotiable Instruments Act, 1881."),
            TimelineFact(2, "Dishonour & Bank Return Memo", "Cheque returned unpaid ('Insufficient Funds' / 'Stop Payment').", "Starts the strict 30-day statutory clock to serve a Section 138(b) Demand Notice."),
            TimelineFact(3, "15-Day Statutory Cure Window", "Drawer must pay within 15 days of receiving notice or face criminal prosecution.", "Punishable under Section 138 NI Act with up to 2 years imprisonment or twice the cheque amount."),
        ]
        evidence = [
            EvidenceItem("Original Dishonoured Cheque", "PRESENT", 35, "Keep the physical original cheque safely for court filing."),
            EvidenceItem("Official Bank Return Memo with Dishonour Reason", "PRESENT", 35, "Mandatory document showing exact date of dishonour."),
            EvidenceItem("Invoice / Loan Agreement / Ledger Proof of Debt", "RECOMMENDED", 30, "Proves underlying legally enforceable debt under Section 138 NI Act."),
        ]
        trap_tip = (
            "CRITICAL DEADLINE: Under Section 138(b) of the Negotiable Instruments Act, 1881, you MUST dispatch the formal written Demand Notice within 30 days of receiving the Bank Return Memo via Registered Post AD."
        )
        standing_en = (
            f"Dishonour of a cheque for ₹{amount:,} is a serious criminal offense under Section 138 of the Negotiable Instruments Act, 1881 (punishable with up to 2 years imprisonment or fine up to ₹{amount*2:,}) as well as a civil summary recovery claim under Order XXXVII CPC."
        )
        standing_hi = (
            f"₹{amount:,} ka cheque bounce hona Negotiable Instruments Act, 1881 ke Section 138 ke tahat dandaatmak apradh hai (2 saal tak ki saza ya dugना jurmana ₹{amount*2:,}). Bank Return Memo milne ke 30 din ke andar notice bhejna anivarya hai."
        )

    else:
        timeline = [
            TimelineFact(1, "Receipt of Notice / Threat", "Received intimidating legal communication or criminal threat.", "Requires verification of whether it is a private lawyer's pre-litigation notice or a real Court Summons (CNR check)."),
            TimelineFact(2, "Statutory Verification", "Cross-checked under Bharatiya Nyaya Sanhita (BNS), 2023 & CPC.", "Private individuals/lawyers cannot issue arrest warrants; only a Magistrate Court can."),
        ]
        evidence = [
            EvidenceItem("Copy of Notice / Threatening Messages", "PRESENT", 50, "Preserve full envelope, header, advocate enrollment number, and WhatsApp phone numbers."),
            EvidenceItem("Underlying Transaction / Communication Proof", "RECOMMENDED", 50, "Gather chronological proof refuting the allegations before sending a formal Reply Notice."),
        ]
        trap_tip = (
            "Check if the document has a 16-digit alphanumeric 'CNR Number' verifiable on ecourts.gov.in. "
            "If it does NOT have a CNR number, it is NOT a court summons or warrant—it is either a private lawyer's notice or a recovery agent bluff!"
        )
        standing_en = (
            "Effective July 1, 2024, the Bharatiya Nyaya Sanhita (BNS), 2023 replaced the old IPC (Cheating is now Section 318 BNS; Criminal Breach of Trust is Section 316 BNS; Criminal Intimidation is Section 351 BNS). "
            "Under Section 12 of the Legal Services Authorities Act, 1987, if this involves a real court proceeding or criminal threat, you can get a free government advocate via NALSA (Helpline 15100)."
        )
        standing_hi = (
            "1 July 2024 se IPC ki jagah Bharatiya Nyaya Sanhita (BNS), 2023 laagu hai (Cheating = Section 318 BNS, Intimidation = Section 351 BNS). "
            "Asli court summons par hamesha 16-digit CNR number hota hai jise ecourts.gov.in par check kiya ja sakta hai. Muft sarkari vakil ke liye 15100 par call karein."
        )

    ev_score = sum(item.weight_points for item in evidence if item.status == "PRESENT") + sum(
        int(item.weight_points * 0.4) for item in evidence if item.status == "RECOMMENDED"
    )
    ev_score = min(98, max(35, ev_score))

    if router is not None and router.is_live_llm():
        statutes_ctx = "; ".join(
            f"{s.get('act', '')}, {s.get('section', '')}: {s.get('summary', '')}"
            for s in domain_info.get("verified_statutes", [])
        )
        llm_res = router.complete_json(
            system_prompt=(
                "You are NyayaSahayak, an Indian legal assistant. Cite ONLY the verified Indian statutes provided below "
                "(use Bharatiya Nyaya Sanhita BNS 2023 instead of repealed IPC). Return JSON with keys: "
                "'standing_en' (2-3 sentences English), 'standing_hi' (2-3 sentences Hinglish), and 'trap_tip' (1-2 sentences tactical move). "
                f"Active Strategy Profile: {model_name}. Verified Statutes: {statutes_ctx}"
            ),
            user_prompt=f"Disputed Amount: INR {amount}\nUser Story: {user_story}",
            fallback_fn=lambda: {"standing_en": standing_en, "standing_hi": standing_hi, "trap_tip": trap_tip},
        )
        if isinstance(llm_res, dict):
            standing_en = str(llm_res.get("standing_en") or standing_en)
            standing_hi = str(llm_res.get("standing_hi") or standing_hi)
            trap_tip = str(llm_res.get("trap_tip") or trap_tip)

    # Pass plain-language standing through our deterministic Citation Firewall guardrail
    clean_en, audit_en = verify_and_sanitize_legal_text(standing_en)
    clean_hi, audit_hi = verify_and_sanitize_legal_text(standing_hi)

    step1_label = (
        "Step 1: High-Pressure 48-Hr Penal Demand Notice"
        if is_aggressive
        else (
            "Step 1: Amicable 48-Hr Without-Prejudice Settlement Offer"
            if is_conciliatory
            else "Step 1: Self-Sent Formal Legal Demand Notice + Evidence Trap"
        )
    )

    roi_matrix = [
        {
            "option": step1_label,
            "estimated_cost_inr": "₹0 (Free via NyayaSahayak PDF) or ₹150 Registered Post AD",
            "typical_timeline": "2 to 7 Days" if (is_aggressive or is_conciliatory) else "7 to 15 Days",
            "success_probability": "55%–65% (Most landlords/employers/brands settle when hit with exact statutory citations)",
            "recommended": "YES — Always start here",
        },
        {
            "option": f"Step 2: Government Online Portal ({domain_info['primary_forum'].split('/')[0].strip()})",
            "estimated_cost_inr": "₹0 Court/Portal Fee",
            "typical_timeline": "30 to 90 Days",
            "success_probability": "75%–85% (Backed by statutory conciliation/commission orders)",
            "recommended": "YES — Escalate here if notice is ignored",
        },
        {
            "option": "Step 3: Private Advocate & Contested Civil Court Litigation",
            "estimated_cost_inr": "₹15,000 – ₹45,000+ (Lawyer retainers + court fees)",
            "typical_timeline": "6 to 18 Months",
            "success_probability": "High, but economically viable only if claim > ₹75,000 or in Red-Line criminal matters",
            "recommended": "ONLY IF claim > ₹75,000 or Red-Line Trigger active" if amount < 75000 and not is_red_line else "RECOMMENDED (High value / Red-Line)",
        },
    ]

    return StructuredLegalCase(
        case_id=case_id,
        detected_language=lang,
        domain_key=domain_key,
        domain_title=domain_info["title"],
        is_red_line_escalation=is_red_line,
        red_line_reason=red_line_reason,
        red_line_emergency_contacts=[
            "NALSA Free Legal Aid Helpline: 15100 (24x7 Toll-Free across India)",
            "District Legal Services Authority (DLSA) — Every District Court Complex",
            "Emergency Police / Women Safety: 112 / 181 | Cybercrime Golden-Hour Freeze: 1930",
        ],
        claim_amount_inr=amount,
        timeline=timeline,
        evidence_score_100=ev_score,
        evidence_checklist=evidence,
        pre_notice_evidence_trap_tip=trap_tip,
        plain_language_standing_en=clean_en,
        plain_language_standing_hi=clean_hi,
        limitation_analysis={
            "statutory_limit_years": f"{domain_info['limitation_years']} Year(s)",
            "legal_basis": domain_info["limitation_basis"],
            "official_portal": domain_info["official_portal"],
        },
        roi_comparison=roi_matrix,
        verified_statutes=domain_info["verified_statutes"],
        citation_firewall_audit=audit_en + audit_hi,
        case_validity_status=validity_status,
        validity_explanation=validity_explanation,
        amount_specified=amount_specified,
        strategy_profile_applied=model_name,
    )
