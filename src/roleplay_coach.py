"""
Power Feature 2D: Interactive Opponent Negotiation Simulator & Live Legal Coach.
Allows the citizen to practice arguing their case against a realistic stubborn Landlord,
HR Manager, Bank Nodal Officer, or Customer Support Lead while receiving instant tactical coaching.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from .llm_router import UniversalLLMRouter


@dataclass
class SparringTurnEvaluation:
    persona_name: str
    opponent_reply: str
    coach_score_100: int
    coach_critique: str
    mistake_detected: str
    suggested_stronger_comeback: str


PERSONAS = {
    "TENANCY_DEPOSIT": {
        "name": "Mr. Sharma (Stubborn Bengaluru/Mumbai Landlord)",
        "opening_stance": "Dekho bhai, ₹45,000 toh painting, deep cleaning aur geyser repair mein hi kat gaya. Baaki paise jab naya tenant aayega tab dekhunga, jo karna hai kar lo!",
    },
    "UNPAID_SALARY": {
        "name": "Vikram (Aggressive Company HR Head)",
        "opening_stance": "Your Full & Final settlement is on hold because management wasn't happy with your handover, and if you join a competitor we will enforce the ₹2 Lakh bond and block your relieving letter!",
    },
    "CONSUMER_REFUND": {
        "name": "Customer Escalation Desk (E-Commerce Platform)",
        "opening_stance": "Sir/Madam, our system shows the product was delivered in an intact box. As per our strict No-Refund policy, we have closed your ticket.",
    },
    "UPI_BANKING_FRAUD": {
        "name": "Branch Operations Manager",
        "opening_stance": "Since the UPI debit went through from your mobile device, the bank is not responsible. You have to wait 90 days for our internal investigation.",
    },
    "CHEQUE_BOUNCE_RECOVERY": {
        "name": "Defaulting Business Drawer / Debtor",
        "opening_stance": "Market mein payment fasa hua hai, isliye cheque stop-payment karwaya. Abhi paise nahi hain, 6 mahine baad dekhenge!",
    },
    "NOTICE_AND_CRIMINAL_TRIAGE": {
        "name": "Aggressive Recovery Agent / Opponent Legal Counsel",
        "opening_stance": "Aapke khilaf police complaint aur legal notice draft ho chuka hai. Agar aaj sham tak settlement nahi kiya toh direct court warrant niklega!",
    },
    "NO_LEGAL_CLAIM_OR_NON_JUSTICIABLE": {
        "name": "Counterparty / Store Manager",
        "opening_stance": "As we explained earlier, there is no legal breach on our part under the policy/timeline, so we cannot accept a statutory demand.",
    },
}


def evaluate_sparring_turn(
    domain_key: str,
    user_argument: str,
    router: Optional[UniversalLLMRouter] = None,
) -> Dict:
    persona = PERSONAS.get(domain_key, PERSONAS["TENANCY_DEPOSIT"])
    u_clean = (user_argument or "").strip()
    u_low = u_clean.lower()
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

    # Check if a live LLM is configured
    if router and router.is_live_llm():
        sys_prompt = (
            f"You are roleplaying as {persona['name']} in an Indian legal dispute ({domain_key}). "
            f"Your opening position was: '{persona['opening_stance']}'. "
            "A citizen has sent you their argument. Respond realistically in character. "
            "Then acting as an Indian Senior Legal Coach, evaluate their reply: "
            "rate their legal strength (0-100), identify mistakes (e.g., self-incrimination, emotional threats, lack of 'WITHOUT PREJUDICE'), "
            "and provide a strictly verified stronger statutory comeback under Indian law. "
            "Return valid JSON with keys: 'opponent_reply', 'coach_score_100', 'coach_critique', 'mistake_detected', 'suggested_stronger_comeback'."
        )
        try:
            live_res = router.complete_json(sys_prompt, f"Citizen argument: {user_argument}")
            if isinstance(live_res, dict) and "opponent_reply" in live_res and "coach_score_100" in live_res:
                return {
                    "persona_name": persona["name"],
                    "opponent_reply": str(live_res["opponent_reply"]),
                    "coach_score_100": int(live_res["coach_score_100"]),
                    "coach_critique": str(live_res.get("coach_critique", "Strategic feedback based on Indian law.")),
                    "mistake_detected": str(live_res.get("mistake_detected", "None")),
                    "suggested_stronger_comeback": str(live_res.get("suggested_stronger_comeback", "")),
                    "model_used": f"{router.config.provider} ({router.config.model})",
                }
        except Exception:
            pass  # Fall through to deterministic engine

    # 1. Check for gibberish / ultra-short / non-responsive sparring input
    words = re.findall(r"[a-zA-Z\u0900-\u097F]+", u_clean)
    joined_alpha = "".join(re.findall(r"[a-zA-Z]+", u_low))
    is_keysmash = bool(re.search(r"(asdf|qwert|zxcv|[bcdfghjklmnpqrstvwxz]{6,})", joined_alpha))
    if len(words) < 3 or is_keysmash:
        return asdict(
            SparringTurnEvaluation(
                persona_name=persona["name"],
                opponent_reply="Kya bol rahe ho? Agar aapke paas koi thos kanooni jawab ya saboot nahi hai, toh humari baat yahin khatam hoti hai!",
                coach_score_100=18,
                coach_critique="Your message was too short or unclear to establish legal leverage. Always state (1) the exact date/fact, (2) the Indian Act/Section violated, and (3) a clear deadline.",
                mistake_detected="⚠️ UNCLEAR / NON-SUBSTANTIVE REPLY: Sending one-word or garbled replies signals weakness to the opposite party.",
                suggested_stronger_comeback="WITHOUT PREJUDICE: Please place your refusal in writing. My claim is backed by documentary receipts and statutory provisions, and I require a written resolution within 48 hours.",
            )
        )

    # Detect self-sabotaging admissions by the user
    mistake = "None — Clean, assertive legal positioning."
    score = 82

    if any(p in u_low for p in ("i give up", "keep all", "forget the money", "main haar manta", "rehndo")):
        mistake = (
            "⚠️ TOTAL WAIVER TRAP: Never state in writing that you are giving up or waiving your claim! "
            "That acts as an estoppel and bars recovery."
        )
        score = 25
    elif any(p in u_low for p in ("keep half", "keep 20000", "keep 15000", "keep 30%", "chalo aadha rakh lo", "kaat lo baaki", "bina bill")):
        if "without prejudice" not in u_low:
            mistake = (
                "⚠️ SELF-SABOTAGE TRAP: You offered to give up part of your claim without writing 'WITHOUT PREJUDICE'! "
                "The opponent can use your message in court to claim you admitted fault."
            )
            score -= 28

    if any(p in u_low for p in ("i will beat", "expose on twitter", "defame", "thappad", "gaali", "destroy your", "burn your")):
        mistake = (
            "⚠️ LEGAL RISK: Avoid personal threats or public defamation warnings—stick strictly to statutory notices "
            "(otherwise they can counter-threaten BNS Sec 351/356)."
        )
        score -= 25

    if any(p in u_low for p in ("section", "act", "108", "73", "74", "27", "138", "e-daakhil", "samadhan", "rbi", "ombudsman", "order 37", "utr", "invoice", "bill")):
        score = min(98, score + 14)

    if is_aggressive:
        score = min(100, score + 4)

    # Generate realistic opponent pushback + coach's stronger comeback based on engine profile
    if domain_key == "TENANCY_DEPOSIT":
        if is_aggressive:
            opp_reply = (
                "Dekho, aap Order XXXVII Summary Suit aur 18% interest ki baat kar rahe ho... mere paas saare bills abhi ready nahi hain. "
                "Agar aap seedhe Court jaoge toh dono ka time waste hoga. 2 din ka time do, let me check with the owner."
            )
            coach_tip = (
                "High-pressure stance working! Demand GST invoices for every single deduction within 24 hours. "
                "Warn them that arbitrary deductions violate Model Tenancy Act Sec 11 and constitute wrongful loss under Indian Contract Act Sec 73."
            )
            comeback = (
                "WITHOUT PREJUDICE: Mr. Sharma, under Model Tenancy Act Sec 11, routine painting is natural wear-and-tear. "
                "Unless GST-stamped contractor invoices and the balance deposit with 18% p.a. interest are refunded within 24 hours, "
                "I will file an Order XXXVII Summary Suit with full litigation costs."
            )
        elif is_conciliatory:
            opp_reply = (
                "Theek hai, agar aap mutual resolution chahte ho toh let us sit and settle. Main maintenance ka minimal 5,000 deduct karke "
                "baaki deposit kal subah transfer kar deta hoon, agreement close karte hain."
            )
            coach_tip = (
                "Amicable resolution open! Accept a nominal bona fide charge only if they provide a formal receipt, or demand the full principal refund with a waiver of delay interest."
            )
            comeback = (
                "WITHOUT PREJUDICE: I am open to an immediate amicable settlement if the full deposit is credited to my UPI by tomorrow noon. "
                "In return, I will provide a clean no-dues receipt and waive interest claims."
            )
        else:
            opp_reply = (
                "Acha? Tum mujhe Transfer of Property Act sikhoge? Flat ki deewarein gandi thi, maine apne local painter ko cash diya tha, uska GST bill kahan se laaun? "
                "(Wait—if you press me for move-out photos and Order 37 interest, I know I'll lose in court...)"
            )
            coach_tip = (
                "Pin the landlord on TWO facts: (1) You handed over vacant possession on a specific date without any joint inspection damage note, and "
                "(2) Under Indian Contract Act Sec 73-74, cash claims without GST invoices cannot be deducted from a security deposit."
            )
            comeback = (
                "WITHOUT PREJUDICE: Mr. Sharma, routine repainting is normal wear-and-tear under Model Tenancy Act Sec 11 and Indian Contract Act Sec 73. "
                "Unless you share GST repair bills and refund my principal via UPI by 5 PM tomorrow, my Order XXXVII Summary Suit notice goes out with 18% interest."
            )
    elif domain_key == "UNPAID_SALARY":
        if is_aggressive:
            opp_reply = (
                "Please do not escalate to SAMADHAN portal or file a Labour Commissioner petition. Our management is reviewing your relieving letter and pending wages today."
            )
            coach_tip = (
                "High-pressure labor strategy active! Post-employment bonds are completely void under Section 27 ICA 1872. Holding relieving letters is unlawful coercion under Section 15 ICA."
            )
            comeback = (
                "WITHOUT PREJUDICE: Withholding earned wages violates Section 5 of the Payment of Wages Act, and employment bonds are void under Section 27 Indian Contract Act. "
                "Release my full F&F and Relieving Letter within 24 hours or I file criminal breach of trust under BNS Section 316 and petition SAMADHAN."
            )
        elif is_conciliatory:
            opp_reply = (
                "We appreciate your contribution and want to conclude your exit amicably. If you complete the online handover checklist today, finance can process your F&F this week."
            )
            coach_tip = (
                "Safe off-ramp available. Confirm completion of the handover in writing and ask for an exact payment date within 5 working days."
            )
            comeback = (
                "WITHOUT PREJUDICE: All handover assets have been formally returned on [Date]. Please confirm that the Full & Final credit and Relieving Letter will be issued by this Friday."
            )
        else:
            opp_reply = (
                "You signed the appointment letter with the ₹2 Lakh bond clause! How can you say it isn't valid? "
                "(Though if you go to the SAMADHAN portal or Labour Inspector, our legal team told us post-employment restraints don't hold up...)"
            )
            coach_tip = (
                "Call their bluff directly using Section 27 (post-employment restraint is void) and Section 74 (bonds require proof of actual external training expense) of the Indian Contract Act."
            )
            comeback = (
                "WITHOUT PREJUDICE: Under Section 27 of the Indian Contract Act, 1872, post-employment non-compete clauses are void, and under Section 74 you cannot withhold earned wages under the Payment of Wages Act Sec 5. "
                "Please release my F&F and relieving letter within 48 hours or I am filing on samadhan.labour.gov.in."
            )
    elif domain_key == "CONSUMER_REFUND":
        if is_aggressive:
            opp_reply = (
                "Sir, we understand you are threatening an e-Daakhil filing and penal damages under Section 89 of CPA 2019. We have prioritized your case to Executive Support."
            )
            coach_tip = (
                "Aggressive consumer stance working! Demand an immediate refund transaction UTR number plus ₹10,000 compensation for harassment."
            )
            comeback = (
                "Refusing return for defective goods is an Unfair Trade Practice under Section 2(47)(vii) Consumer Protection Act, 2019. "
                "Provide my refund UTR number within 48 hours or face formal proceedings before the District Consumer Disputes Redressal Commission."
            )
        elif is_conciliatory:
            opp_reply = (
                "We apologize for the inconvenience with your order. As a goodwill gesture, we can arrange an immediate pickup tomorrow and initiate a full refund upon verification."
            )
            coach_tip = (
                "Good outcome. Insist that the refund is credited to the original payment source and get the courier tracking ID in writing."
            )
            comeback = (
                "Thank you. Please generate the pickup courier manifest today and confirm that 100% of the order value will be refunded directly to my original payment source."
            )
        else:
            opp_reply = (
                "Okay, let me escalate this to our Grievance Officer team since you cited Rule 4(4) of the E-Commerce Rules 2020 and e-Daakhil..."
            )
            coach_tip = (
                "Great job! Always demand the Grievance Officer Ticket Number mandated within 48 hours under Rule 4(4) of the Consumer Protection (E-Commerce) Rules, 2020."
            )
            comeback = (
                "Please provide the mandatory Grievance Officer ticket number under Rule 4(4) of the E-Commerce Rules, 2020. "
                "Refusing a refund for defective goods is an Unfair Trade Practice under Section 2(47)(vii) of the Consumer Protection Act, 2019."
            )
    elif domain_key == "UPI_BANKING_FRAUD":
        if is_aggressive:
            opp_reply = (
                "Understood. Since you have invoked the RBI Ombudsman Banking Scheme 2021 and ₹100/day delay penalty, we have logged a Priority Nodal ticket."
            )
            coach_tip = (
                "Maximum pressure! Under RBI Master Direction on Customer Protection, unauthorized electronic debits reported within 3 days carry ZERO liability."
            )
            comeback = (
                "Under RBI Circular DBR.No.Leg.BC.78/09.07.005/2017-18, I hold Zero Liability as this fraud was reported within 72 hours. "
                "Provide shadow reversal within 10 days or I escalate to the RBI Banking Ombudsman under Clause 11 of the Ombudsman Scheme, 2021."
            )
        elif is_conciliatory:
            opp_reply = (
                "We have verified your 1930 cybercrime acknowledgment and UTR number. Our branch is forwarding your file to the Fraud Risk Management desk for provisional shadow credit."
            )
            coach_tip = (
                "Cooperative response achieved. Share the written dispute form and keep the stamped acknowledgment copy for the 10-working-day shadow credit window."
            )
            comeback = (
                "Thank you. I have attached the 12-digit UTR and 1930 complaint copy. Please share the Nodal ticket reference so we can track the 10-working-day shadow reversal."
            )
        else:
            opp_reply = (
                "We have registered your escalation with the Nodal Desk and are checking the RBI Turn-Around-Time (TAT) circular..."
            )
            coach_tip = (
                "Cite RBI Circular DPSS.CO.PD No.629/02.01.014/2019-20 (₹100/day penalty for delayed failed-UPI reversal) or the 3-day Zero Liability rule."
            )
            comeback = (
                "Please note my complaint timestamp falls within the 3-day Zero Liability window under RBI Circular DBR.No.Leg.BC.78/09.07.005/2017-18, requiring shadow credit within 10 working days."
            )
    elif domain_key == "CHEQUE_BOUNCE_RECOVERY":
        if is_aggressive:
            opp_reply = (
                "Arre Section 138 criminal case mat file karo! Main 50% abhi RTGS kar raha hoon aur baaki agle hafte de dunga."
            )
            coach_tip = (
                "High-pressure Section 138 NI Act warning worked! Do not withdraw your 30-day statutory notice unless 100% of the cheque amount is credited."
            )
            comeback = (
                "WITHOUT PREJUDICE: Under Section 138 of the Negotiable Instruments Act, 1881, dishonour of cheque carries up to twice the cheque amount as fine or 2 years imprisonment. Clear 100% via RTGS within 15 days of notice."
            )
        elif is_conciliatory:
            opp_reply = (
                "Agar aap criminal complaint hold kar lo toh main is hafte RTGS se poora payment clear kar deta hoon."
            )
            coach_tip = (
                "Keep the 15-day statutory clock running while accepting immediate RTGS payment against a written receipt."
            )
            comeback = (
                "WITHOUT PREJUDICE: If 100% of the dishonoured cheque amount is credited via RTGS within 7 days, I will return the original cheque and close the dispute amicably."
            )
        else:
            opp_reply = (
                "Bank Return Memo aa gaya kya? Thoda time do, court mat jaana..."
            )
            coach_tip = (
                "Serve the statutory Demand Notice within 30 days of the Bank Return Memo under Section 138(b) of the Negotiable Instruments Act, 1881."
            )
            comeback = (
                "WITHOUT PREJUDICE: I hold the original dishonoured cheque and Bank Return Memo. Unless the full amount is paid within 15 days of my Section 138 NI Act notice, Magistrate Court proceedings will be filed."
            )
    else:
        if is_aggressive:
            opp_reply = (
                "Please calm down. We did not mean to threaten you. We are willing to recall the recovery notice if you verify the account details."
            )
            coach_tip = (
                "Private threat callers panic when met with BNS criminal intimidation citations. Never yield to unverified digital warrants."
            )
            comeback = (
                "Issuing forged court warrants on WhatsApp is forgery under BNS Section 336 and extortion under BNS Section 308. "
                "Cease all contact immediately or face prosecution before the Cyber Crime Police."
            )
        elif is_conciliatory:
            opp_reply = (
                "Theek hai, hum recovery agent calls band karwa rahe hain aur aapko official email par ledger statement bhej rahe hain."
            )
            coach_tip = (
                "Good de-escalation. Insist that all future communication happens strictly via official company email during RBI-permitted hours (8 AM – 7 PM)."
            )
            comeback = (
                "WITHOUT PREJUDICE: Please route any legitimate statement of account strictly via official email. All unverified WhatsApp threats must cease immediately."
            )
        else:
            opp_reply = (
                "Dekho, humare legal department ne draft ready rakha hai. Lekin agar aap CNR number aur NALSA helpline 15100 ki baat kar rahe ho, toh pehle mutually settle karne ka option dekh lete hain..."
            )
            coach_tip = (
                "Hold your ground! Private callers count on panic. Civil or loan disputes are not arrest offenses, and demanding money through criminal threats is punishable under BNS Section 351."
            )
            comeback = (
                "Please share the 16-digit CNR number verifiable on ecourts.gov.in. Issuing arrest threats without lawful court process is criminal intimidation under BNS Section 351, which I am escalating to DLSA and police authorities."
            )

    return asdict(
        SparringTurnEvaluation(
            persona_name=persona["name"],
            opponent_reply=opp_reply,
            coach_score_100=score,
            coach_critique=coach_tip,
            mistake_detected=mistake,
            suggested_stronger_comeback=comeback,
        )
    )
