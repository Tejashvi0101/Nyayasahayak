import tempfile
from pathlib import Path
from src.case_builder import build_structured_case
from src.notice_decoder import decode_notice_or_clause
from src.document_generator import generate_legal_action_kit
from src.roleplay_coach import evaluate_sparring_turn, PERSONAS
from src.statute_verifier import verify_and_sanitize_legal_text
from src.llm_router import LLMConfig, UniversalLLMRouter

def test_full_human_experience():
    print("=================================================================")
    print("SIMULATING HUMAN USER EXPERIENCE ON PROJECT 2 (NYAYASAHAYAK)")
    print("=================================================================")

    scenarios = [
        {
            "name": "Custom User Story 1: Unpaid Startup Salary with Bond Bluff",
            "text": "My manager at a tech startup in Noida withheld my 2 months salary of Rs 1,20,000 and is threatening to enforce a 2 lakh bond because I resigned.",
            "expected_domain": "UNPAID_SALARY",
            "expected_amt": 120000,
            "test_notice": "Your F&F of Rs 120000 is forfeited and we are enforcing Rs 2 Lakh Training Bond liquidated damages.",
            "test_reply": "Sir please release my salary, I worked very hard.",
        },
        {
            "name": "Custom User Story 2: Defective E-Commerce Phone Refund",
            "text": "I ordered a phone for 28000 on Flipkart, received broken screen, return rejected stating no refund policy.",
            "expected_domain": "CONSUMER_REFUND",
            "expected_amt": 28000,
            "test_notice": "Ticket closed: Electronics items fall under strict No Refund Policy.",
            "test_reply": "Under Section 2(47)(vii) of CPA 2019, refusing refund is unfair trade practice. Share Grievance ticket under Rule 4.",
        },
        {
            "name": "Custom User Story 3: Unauthorized UPI Debit",
            "text": "45k debited from my SBI account via UPI without any OTP. Bank says they are not responsible.",
            "expected_domain": "UPI_BANKING_FRAUD",
            "expected_amt": 45000,
            "test_notice": "Bank is not responsible for UPI debit as transaction was authenticated through mobile device.",
            "test_reply": "I reported within 3 days under RBI Zero Liability circular DBR.No.Leg.BC.78/09.07.005/2017-18.",
        },
        {
            "name": "Custom User Story 4: Hinglish Tenancy Deposit Withholding",
            "text": "Makan malik ne 2 mahine se mera 80 hazar ka security deposit rok rakha hai aur WhatsApp par bol raha hai ki 30000 painting ka katega.",
            "expected_domain": "TENANCY_DEPOSIT",
            "expected_amt": 80000,
            "test_notice": "Dear tenant, deducting Rs 30,000 for full house repainting and deep cleaning wear and tear.",
            "test_reply": "Chalo bhaiya 15000 kaat lo baaki wapas kar do.",  # Testing self-sabotage concession trap!
        },
        {
            "name": "Custom User Story 5: Fake Recovery Agent WhatsApp Threat",
            "text": "Loan app recovery agent sent WhatsApp Lok Adalat warrant demanding 15000 and threatening arrest tomorrow.",
            "expected_domain": "NOTICE_AND_CRIMINAL_TRIAGE",
            "expected_amt": 15000,
            "test_notice": "URGENT LOK ADALAT ARREST WARRANT: Police will arrest within 24 hours via WhatsApp summons.",
            "test_reply": "Lok Adalat never issues arrest warrants and you have no CNR number on ecourts.",
        },
        {
            "name": "Custom User Story 6: Domestic Violence / Physical Danger (Red-Line)",
            "text": "My husband beat me and threatened to kill me if I ask for maintenance.",
            "expected_domain": "NOTICE_AND_CRIMINAL_TRIAGE",
            "expected_amt": 50000,
            "is_red_line": True,
        },
    ]

    all_passed = True
    for sc in scenarios:
        print(f"\n--- Testing: {sc['name']} ---")
        case = build_structured_case(sc["text"], case_id="CUSTOM-TEST")
        print(f"Domain: {case.domain_key} (Expected: {sc['expected_domain']})")
        print(f"Amount: INR {case.claim_amount_inr:,} (Expected: INR {sc['expected_amt']:,})")
        print(f"Red-Line: {case.is_red_line_escalation}")
        print(f"Limitation: {case.limitation_analysis['statutory_limit_years']}")

        assert case.domain_key == sc["expected_domain"], f"Domain mismatch: got {case.domain_key}, expected {sc['expected_domain']}"
        assert case.claim_amount_inr == sc["expected_amt"], f"Amount mismatch: got {case.claim_amount_inr}, expected {sc['expected_amt']}"

        if sc.get("is_red_line"):
            assert case.is_red_line_escalation is True, "Expected red-line escalation!"
            print(">> RED-LINE SAFETY TRIGGERED: Immediate human lawyer required. Free helplines displayed.")
            continue

        # Test PDF Notice Generation
        tmp_pdf = Path(tempfile.gettempdir()) / f"test_{case.domain_key}.pdf"
        kit = generate_legal_action_kit(case, pdf_output_path=tmp_pdf)
        assert tmp_pdf.exists() and tmp_pdf.stat().st_size > 1000, "PDF failed to generate or is empty!"
        print(f">> PDF Notice generated successfully ({tmp_pdf.stat().st_size} bytes).")
        print(f">> WhatsApp template snippet: {kit['whatsapp_escalation_template'][:120]}...")

        # Test Notice Decoder
        if "test_notice" in sc:
            decoded = decode_notice_or_clause(sc["test_notice"])
            print(f">> Threat Decoder: {decoded['summary_assessment']}")
            for flag in decoded["decoded_flags"]:
                print(f"   [{flag['verdict']}] {flag['clause_or_threat_type']}")

        # Test Sparring Simulator
        if "test_reply" in sc:
            eval_res = evaluate_sparring_turn(case.domain_key, sc["test_reply"])
            print(f">> Sparring Coach Score: {eval_res['coach_score_100']}/100")
            print(f"   Opponent: {eval_res['persona_name']}")
            print(f"   Mistake Detected: {eval_res['mistake_detected']}")
            print(f"   Suggested Comeback: {eval_res['suggested_stronger_comeback'][:100]}...")

    # Test Edge Cases: Cheque Bounce, Gibberish, Off-Topic, and No-Law-Case scenarios
    print("\n--- Testing Edge Cases & Validity Gate ---")

    # 7. Cheque Bounce (NI Act Sec 138)
    cb_case = build_structured_case(
        "My client issued a cheque of Rs 1,50,000 which bounced with memo Insufficient Funds.",
        case_id="EC-CHEQUE",
    )
    assert cb_case.domain_key == "CHEQUE_BOUNCE_RECOVERY"
    assert cb_case.case_validity_status == "ACTIONABLE_CLAIM"
    assert cb_case.claim_amount_inr == 150000
    print(">> Cheque Bounce (NI Act Sec 138) classified and verified!")

    # 8. Random Gibberish
    gib_case = build_structured_case("asdfghjkl 12345 qwertyuiop", case_id="EC-GIB")
    assert gib_case.case_validity_status == "GIBBERISH_OR_TOO_SHORT"
    assert gib_case.claim_amount_inr == 0
    gib_kit = generate_legal_action_kit(gib_case, pdf_output_path=Path(tempfile.gettempdir()) / "gib.pdf")
    assert not gib_kit["pdf_path"]
    print(">> Random Gibberish rejected cleanly with INR 0 and PDF blocked!")

    # 9. Off-Topic Non-Legal Query
    off_case = build_structured_case("How to cook Hyderabadi chicken biryani at home step by step", case_id="EC-OFF")
    assert off_case.case_validity_status == "OFF_TOPIC_NON_LEGAL"
    assert off_case.claim_amount_inr == 0
    off_kit = generate_legal_action_kit(off_case, pdf_output_path=Path(tempfile.gettempdir()) / "off.pdf")
    assert not off_kit["pdf_path"]
    print(">> Off-Topic Non-Legal query rejected cleanly with INR 0 and PDF blocked!")

    # 10. No Law Case — Trivial Social Grievance (BNS Sec 33 De Minimis)
    triv_case = build_structured_case("My friend didn't invite me to his birthday party and ignored my texts", case_id="EC-TRIV")
    assert triv_case.case_validity_status == "NO_CLAIM_TRIVIAL_SOCIAL"
    assert triv_case.domain_key == "NO_LEGAL_CLAIM_OR_NON_JUSTICIABLE"
    print(">> Trivial Social Grievance flagged as NO_CLAIM_TRIVIAL_SOCIAL (BNS Sec 33 De Minimis)!")

    # 11. No Law Case — Customer Self-Fault (CPA Sec 2(11) Exclusion)
    self_case = build_structured_case("I dropped my iPhone worth Rs 65,000 in water after 8 months and service center refused free warranty", case_id="EC-SELF")
    assert self_case.case_validity_status == "NO_CLAIM_SELF_FAULT"
    self_kit = generate_legal_action_kit(self_case, pdf_output_path=Path(tempfile.gettempdir()) / "self.pdf")
    assert not self_kit["pdf_path"]
    assert "GOODWILL" in self_kit["whatsapp_escalation_template"].upper()
    print(">> Customer Self-Fault flagged as NO_CLAIM_SELF_FAULT with Goodwill Request instead of invalid legal notice!")

    # 12. No Law Case — Time-Barred Claim (Limitation Act Sec 3 & 18)
    tb_case = build_structured_case("My old landlord in Pune did not return my deposit of Rs 40,000 when I vacated 6 years ago in 2019", case_id="EC-TB")
    assert tb_case.case_validity_status == "NO_CLAIM_TIME_BARRED"
    print(">> Time-Barred 2019 claim flagged under Limitation Act Sec 3 & Sec 18 revival strategy!")

    # 13. Model Profile Switching verification across all 3 engines
    r_bal = UniversalLLMRouter(LLMConfig(provider="deterministic", model="rule-indian-statute-v1 (Balanced Statutory Notice)"))
    r_agg = UniversalLLMRouter(LLMConfig(provider="deterministic", model="rule-strict-litigation-v2 (Aggressive Penal Interest & Filing)"))
    r_con = UniversalLLMRouter(LLMConfig(provider="deterministic", model="rule-mediation-settlement-v1 (Amicable Pre-Suit Conciliation)"))

    c_bal = build_structured_case(scenarios[0]["text"], router=r_bal)
    c_agg = build_structured_case(scenarios[0]["text"], router=r_agg)
    c_con = build_structured_case(scenarios[0]["text"], router=r_con)
    assert c_bal.plain_language_standing_en != c_agg.plain_language_standing_en
    assert c_agg.plain_language_standing_en != c_con.plain_language_standing_en
    print(">> Model Engine Profile switching verified across Balanced, Aggressive, and Conciliatory modes!")

    print("\n=================================================================")
    print("ALL HUMAN SCENARIOS VERIFIED SUCCESSFULLY!")
    print("=================================================================")

if __name__ == "__main__":
    test_full_human_experience()
