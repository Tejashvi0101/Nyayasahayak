"""
NyayaSahayak — Clean, Focused Everyday Indian AI Lawyer (Project 2).
Run locally:
    python -m streamlit run app.py
"""

from __future__ import annotations
import importlib
import os
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st

import src.llm_router
import src.statute_verifier
import src.case_builder
import src.notice_decoder
import src.document_generator
import src.roleplay_coach

for _mod in (
    src.llm_router,
    src.statute_verifier,
    src.case_builder,
    src.notice_decoder,
    src.document_generator,
    src.roleplay_coach,
):
    importlib.reload(_mod)

from src.llm_router import (
    LLMConfig,
    UniversalLLMRouter,
    PROVIDER_DEFAULTS,
    PROVIDER_MODELS,
    get_available_providers_from_env,
)
from src.case_builder import build_structured_case
from src.notice_decoder import decode_notice_or_clause
from src.document_generator import generate_legal_action_kit
from src.roleplay_coach import evaluate_sparring_turn, PERSONAS
from src.statute_verifier import verify_and_sanitize_legal_text
from run_test_suite import BENCHMARK_TEST_CASES


st.set_page_config(
    page_title="NyayaSahayak — Everyday Indian AI Lawyer",
    page_icon="⚖️",
    layout="wide",
)

DOMAIN_LABELS = {
    "TENANCY_DEPOSIT": "🏠 Rental & Deposit",
    "UNPAID_SALARY": "💼 Salary & Employment",
    "CONSUMER_REFUND": "🛒 Consumer Refund",
    "UPI_BANKING_FRAUD": "🏦 UPI & Bank Fraud",
    "CHEQUE_BOUNCE_RECOVERY": "📝 Cheque Bounce (Sec 138)",
    "NOTICE_AND_CRIMINAL_TRIAGE": "🚨 Notice / Harassment",
    "CRIMINAL_OR_NOTICE_TRIAGE": "🚨 Notice / Harassment",
    "NO_LEGAL_CLAIM_OR_NON_JUSTICIABLE": "⚖️ No Actionable Claim",
}

VALIDITY_BADGES = {
    "ACTIONABLE_CLAIM": ("✅ Actionable Legal Claim", "Strong statutory standing detected under Indian law."),
    "RED_LINE_SAFETY": ("🚨 Red-Line Safety Stop", "Criminal custody or physical safety risk — immediate human lawyer / helpline required."),
    "GIBBERISH_OR_TOO_SHORT": ("⚠️ Unrecognized / Gibberish Input", "Input is random text or too brief to identify a legal dispute."),
    "OFF_TOPIC_NON_LEGAL": ("🧭 Non-Legal / Off-Topic Query", "Query is unrelated to Indian law or civil disputes."),
    "NO_CLAIM_TRIVIAL_SOCIAL": ("⚖️ No Law Case (Trivial / Social)", "Excluded under BNS Section 33 (De minimis non curat lex — law ignores trifles)."),
    "NO_CLAIM_SELF_FAULT": ("⚖️ No Law Case (Self-Inflicted Damage)", "No seller deficiency under Section 2(11) Consumer Protection Act, 2019."),
    "NO_CLAIM_TIME_BARRED": ("⏳ Time-Barred Claim (Limitation Expired)", "Barred under Section 3 of the Limitation Act, 1963 / Section 69 CPA 2019."),
    "NO_CLAIM_LAWFUL_DEDUCTION": ("⚖️ Lawful Counterparty Set-Off", "Opposite party holds a valid statutory right to set off unpaid dues/unreturned assets."),
}

EDGE_CASE_PRESETS = [
    {
        "case_id": "EC01_CHEQUE_BOUNCE_138",
        "title": "Cheque Bounce: Dishonoured ₹2,50,000 Client Cheque (Sec 138 NI Act)",
        "user_input": "A business client issued a cheque of Rs 2,50,000 for my completed invoice, which bounced yesterday with a bank return memo stating Insufficient Funds.",
        "pasted_opponent_notice": "Do not present the cheque again. We have stopped payment and will settle whenever market conditions improve.",
        "sample_sparring_arg": "WITHOUT PREJUDICE: I have the original dishonoured cheque and Bank Return Memo. Under Section 138 of the Negotiable Instruments Act, 1881, clear Rs 2,50,000 within 15 days of my statutory notice or face Magistrate Court prosecution.",
    },
    {
        "case_id": "EC02_NO_CASE_TRIVIAL_SOCIAL",
        "title": "No Law Case #1 (Trivial/Social): Friend Didn't Invite Me to Birthday Party",
        "user_input": "My best friend did not invite me to his birthday party and ignored my message on WhatsApp. I am hurt and want to sue him for Rs 50,000.",
        "pasted_opponent_notice": "I don't want to talk to you anymore.",
        "sample_sparring_arg": "I will sue you in court for not inviting me!",
    },
    {
        "case_id": "EC03_NO_CASE_SELF_FAULT",
        "title": "No Law Case #2 (Self-Fault): Dropped Phone Myself After 8 Months",
        "user_input": "I bought a phone for Rs 35,000 on Amazon 8 months ago. Yesterday I accidentally dropped my phone from the balcony and broke the screen myself, and the company refuses a free refund.",
        "pasted_opponent_notice": "Physical damage caused by customer accidental drop is not covered under standard manufacturing warranty.",
        "sample_sparring_arg": "Give me a free replacement even though I dropped it.",
    },
    {
        "case_id": "EC04_NO_CASE_TIME_BARRED",
        "title": "No Law Case #3 (Time-Barred): Deposit Claim From 6 Years Ago (2019)",
        "user_input": "My landlord in Delhi did not return my Rs 45,000 security deposit 6 years ago in 2019 when I vacated the flat, and I never sent any message since then.",
        "pasted_opponent_notice": "This matter is from 2019 and closed long ago.",
        "sample_sparring_arg": "Pay my 2019 deposit now.",
    },
    {
        "case_id": "EC05_OFF_TOPIC_NON_LEGAL",
        "title": "Off-Topic Query: How to Cook Chicken Biryani (Non-Legal)",
        "user_input": "How to cook Hyderabadi chicken biryani at home step by step with basmati rice?",
        "pasted_opponent_notice": "Add saffron and cardamom.",
        "sample_sparring_arg": "How much salt should I add?",
    },
]

ALL_SCENARIOS = BENCHMARK_TEST_CASES + EDGE_CASE_PRESETS

DOMAIN_PARTY_DEFAULTS = {
    "TENANCY_DEPOSIT": {
        "sender_name": "Aarav Verma",
        "sender_addr": "Flat 402, Indiranagar, Bengaluru - 560038",
        "recip_name": "Mr. Rajesh Sharma (Landlord)",
        "recip_addr": "12th Main, Koramangala, Bengaluru - 560034",
    },
    "UNPAID_SALARY": {
        "sender_name": "Rohan Mehta",
        "sender_addr": "H-12, Baner Road, Pune - 411045",
        "recip_name": "Managing Director / HR Head, TechCorp Pvt Ltd",
        "recip_addr": "Cyber City, Magarpatta, Pune - 411028",
    },
    "CONSUMER_REFUND": {
        "sender_name": "Priya Sharma",
        "sender_addr": "B-404, Mayur Vihar Phase 1, Delhi - 110091",
        "recip_name": "Grievance Officer, E-Commerce Platform / Seller",
        "recip_addr": "Registered Corporate Office, Cyber Hub, Gurugram - 122002",
    },
    "UPI_BANKING_FRAUD": {
        "sender_name": "Aditya Roy",
        "sender_addr": "A-101, Bandra West, Mumbai - 400050",
        "recip_name": "Principal Nodal Officer / Branch Manager, Bank",
        "recip_addr": "Zonal Office, Nariman Point, Mumbai - 400021",
    },
    "CHEQUE_BOUNCE_RECOVERY": {
        "sender_name": "Vikramaditya Traders (Prop. K. Nair)",
        "sender_addr": "Plot 14, MIDC Andheri East, Mumbai - 400093",
        "recip_name": "Authorized Signatory / Drawer of Dishonoured Cheque",
        "recip_addr": "Commercial Complex, Nariman Point, Mumbai - 400021",
    },
    "NOTICE_AND_CRIMINAL_TRIAGE": {
        "sender_name": "Sunita Devi",
        "sender_addr": "Civil Lines, Jaipur - 302006",
        "recip_name": "Opposite Party / Legal Counsel",
        "recip_addr": "District Court Chambers, Jaipur - 302001",
    },
    "NO_LEGAL_CLAIM_OR_NON_JUSTICIABLE": {
        "sender_name": "Citizen Applicant",
        "sender_addr": "New Delhi - 110001",
        "recip_name": "Counterparty / Customer Care",
        "recip_addr": "India",
    },
}


def main():
    st.markdown("## ⚖️ NyayaSahayak — Everyday Indian Legal Helper")
    st.caption("Plain-language legal standing, verified Indian laws (BNS 2023 / Consumer / Tenancy / Labour / NI Act 138), honest merits triage, and ready-to-send notices.")

    # Minimal Sidebar
    with st.sidebar:
        st.markdown("### 🧪 Try an Example Case")
        preset_options = ["✍️ Write My Own Problem"] + [f"{tc['case_id']}: {tc['title']}" for tc in ALL_SCENARIOS]
        selected_preset = st.selectbox("Choose a scenario", options=preset_options, index=1, label_visibility="collapsed")

        with st.expander("🎙️ Voice Input (Optional)", expanded=False):
            audio_input = st.audio_input("Record your problem")
            if audio_input:
                st.success("Voice note captured!")

        with st.expander("⚙️ AI Model Settings (Optional)", expanded=False):
            available_routers, env_configured = get_available_providers_from_env()
            provider = st.selectbox(
                "AI Router (from .env)",
                options=available_routers,
                index=0,
            )
            available_models = PROVIDER_MODELS.get(provider, PROVIDER_MODELS["gemini"])
            selected_model = st.selectbox(
                "Select Model",
                options=available_models,
                index=0,
            )
            selected_profile = st.selectbox(
                "Model Engine Profile",
                options=[
                    "Balanced Legal Strategy",
                    "Aggressive Maximum Penalty",
                    "Conciliatory 48-Hour Amicable Settlement",
                ],
                index=0,
            )
            model_name = f"{selected_model} ({selected_profile})"
            if env_configured:
                st.caption(f"🔒 Active `.env` Routers: `{', '.join(env_configured)}` · StatuteVerifier & Safety Guardrails Active")
            else:
                st.caption("🔒 Add `GEMINI_API_KEY` / `GROQ_API_KEY` / `OPENROUTER_API_KEY` in `.env` to unlock more routers · Guardrails Active")

    router = UniversalLLMRouter(LLMConfig(provider=provider, model=model_name))

    # Manage session state for presets vs custom typing
    if "current_preset" not in st.session_state or selected_preset != st.session_state["current_preset"]:
        st.session_state["current_preset"] = selected_preset
        if selected_preset == "✍️ Write My Own Problem":
            curr_text = st.session_state.get("main_user_story_textarea", "").strip()
            preset_texts = [tc["user_input"].strip() for tc in ALL_SCENARIOS]
            # Only reset if the text area was populated with an example preset
            if not curr_text or curr_text in preset_texts:
                st.session_state["main_user_story_textarea"] = ""
            st.session_state["notice_decoder_input_box"] = ""
            st.session_state["sparring_user_arg_box"] = ""
        else:
            cid = selected_preset.split(":")[0]
            matched = next((t for t in ALL_SCENARIOS if t["case_id"] == cid), ALL_SCENARIOS[0])
            st.session_state["main_user_story_textarea"] = matched["user_input"]
            st.session_state["notice_decoder_input_box"] = matched.get("pasted_opponent_notice", "")
            st.session_state["sparring_user_arg_box"] = matched.get("sample_sparring_arg", "")
        # Reset party overrides so new domain defaults take effect
        st.session_state.pop("active_domain_key", None)
        st.session_state.pop("sender_name_input", None)
        st.session_state.pop("sender_addr_input", None)
        st.session_state.pop("recip_name_input", None)
        st.session_state.pop("recip_addr_input", None)

    user_story = st.text_area(
        "🗣️ Describe what happened (in English, हिंदी, or Hinglish):",
        height=95,
        placeholder="Example: My landlord in Bengaluru is refusing to return my Rs. 1,50,000 security deposit two months after I handed over the keys...",
        key="main_user_story_textarea",
    )

    btn_col1, btn_col2 = st.columns([1, 4])
    with btn_col1:
        st.button("⚖️ Analyze Case", type="primary", use_container_width=True)
    with btn_col2:
        st.caption(f"Press **Ctrl+Enter** or click **Analyze Case** · Active Engine: `{model_name}`")

    if not user_story.strip():
        st.info("👆 Type your situation above or select one of the example cases from the left sidebar to begin.")
        return

    # Determine if this is an unmodified preset or a custom case
    active_tc = None
    if selected_preset != "✍️ Write My Own Problem":
        cid = selected_preset.split(":")[0]
        matched = next((t for t in ALL_SCENARIOS if t["case_id"] == cid), None)
        if matched and user_story.strip() == matched["user_input"].strip():
            active_tc = matched

    case_id = active_tc["case_id"] if active_tc else f"CUSTOM_{abs(hash(user_story)) % 10000:04d}"
    case = build_structured_case(user_story, case_id=case_id, router=router)

    # Compact 4-Metric Summary Bar
    k1, k2, k3, k4 = st.columns(4)
    if case.case_validity_status in ("GIBBERISH_OR_TOO_SHORT", "OFF_TOPIC_NON_LEGAL"):
        k1.metric("Category", "⚠️ Non-Legal / Unclear")
        k2.metric("Disputed Amount", "N/A")
        k3.metric("Proof Readiness", "0/100")
        k4.metric("Time Limit to File", "N/A")
    elif case.case_validity_status.startswith("NO_CLAIM_"):
        k1.metric("Category", "⚖️ No Actionable Claim")
        k2.metric("Disputed Amount", f"₹{case.claim_amount_inr:,}" if case.amount_specified else "N/A")
        k3.metric("Legal Merits Score", f"{case.evidence_score_100}/100")
        k4.metric("Time Limit to File", "Expired / Barred" if "TIME_BARRED" in case.case_validity_status else "Non-Justiciable")
    else:
        k1.metric("Category", DOMAIN_LABELS.get(case.domain_key, case.domain_key))
        k2.metric("Disputed Amount", f"₹{case.claim_amount_inr:,}" if case.amount_specified else f"₹{case.claim_amount_inr:,} (Est.)")
        k3.metric("Proof Readiness", f"{case.evidence_score_100}/100")
        k4.metric("Time Limit to File", case.limitation_analysis["statutory_limit_years"].split("(")[0].strip())

    # Show Validity / Merits / Safety Banner
    badge_title, badge_sub = VALIDITY_BADGES.get(case.case_validity_status, ("✅ Actionable Claim", ""))
    if case.is_red_line_escalation:
        st.error(
            f"### 🚨 Safety Stop: Immediate Human Lawyer / Helpline Required\n\n"
            f"**Why Self-Help Drafting is Paused:** {case.red_line_reason}\n\n"
            "**Free Official Helplines (Section 12, Legal Services Authorities Act, 1987):**\n"
            + "\n".join(f"- **{c}**" for c in case.red_line_emergency_contacts)
        )
    elif case.case_validity_status in ("GIBBERISH_OR_TOO_SHORT", "OFF_TOPIC_NON_LEGAL"):
        st.warning(
            f"### {badge_title}\n\n"
            f"**Why Analysis Paused:** {case.validity_explanation}\n\n"
            "💡 **Try typing a real legal problem**, such as:\n"
            "- *\"Ordered AC for Rs 34,000 on Flipkart, delivered defective, company refused return\"*\n"
            "- *\"Landlord in Pune not returning 75,000 deposit claiming painting charges without bills\"*\n"
            "- *\"Company laid me off without paying 2 months salary of 1,20,000\"*"
        )
    elif case.case_validity_status.startswith("NO_CLAIM_"):
        st.warning(
            f"### {badge_title} — Honest Legal Merits Warning\n\n"
            f"**Why You Should Not Spend Money on Court Litigation Here:** {case.validity_explanation}"
        )

    tab_plan, tab_docs, tab_tools = st.tabs([
        "🧭 1. Where You Stand & Action Plan",
        "📄 2. Legal Notice PDF & Messages",
        "🛡️ 3. Scam Decoder, Practice & Law Checker",
    ])

    # =========================================================================
    # TAB 1: WHERE YOU STAND & ACTION PLAN
    # =========================================================================
    with tab_plan:
        col_en, col_hi = st.columns(2)
        with col_en:
            st.info(f"**🇬🇧 Plain-English Summary**\n\n{case.plain_language_standing_en}")
        with col_hi:
            st.success(f"**🇮🇳 हिंदी / Hinglish Summary**\n\n{case.plain_language_standing_hi}")

        st.warning(f"**💡 Smart First Move ({case.strategy_profile_applied}):** {case.pre_notice_evidence_trap_tip}")

        st.markdown("#### 🛣️ Recommended Escalation Path (Cost vs. Time)")
        clean_roi = [
            {
                "Step": r["option"],
                "Cost": r["estimated_cost_inr"],
                "Timeline": r["typical_timeline"],
                "Success Rate": r["success_probability"],
                "Recommendation": r["recommended"],
            }
            for r in case.roi_comparison
        ]
        st.dataframe(pd.DataFrame(clean_roi), width="stretch", hide_index=True)

        st.markdown("#### 📚 Verified Indian Laws Governing This Situation")
        clean_statutes = [
            {
                "Act": s["act"],
                "Section": s["section"],
                "What the Law Says (English)": s["summary"],
                "हिंदी / Hinglish": s["plain_hindi"],
            }
            for s in case.verified_statutes
        ]
        st.dataframe(pd.DataFrame(clean_statutes), width="stretch", hide_index=True)

        with st.expander("📂 View Evidence Checklist & Case Timeline"):
            c_ev, c_tl = st.columns(2)
            with c_ev:
                st.markdown("**Evidence Checklist**")
                df_ev = pd.DataFrame([
                    {
                        "Proof Needed": e.item_name,
                        "Status": e.status,
                        "How to Get It": e.how_to_obtain_or_create,
                    }
                    for e in case.evidence_checklist
                ])
                st.dataframe(df_ev, width="stretch", hide_index=True)
            with c_tl:
                st.markdown("**Extracted Case Timeline**")
                df_tl = pd.DataFrame([
                    {
                        "Step": f"#{t.step_order}",
                        "Fact": t.event_summary,
                        "Legal Impact": t.legal_significance,
                    }
                    for t in case.timeline
                ])
                st.dataframe(df_tl, width="stretch", hide_index=True)

    # =========================================================================
    # TAB 2: LEGAL NOTICE PDF & MESSAGES
    # =========================================================================
    with tab_docs:
        if case.is_red_line_escalation:
            st.warning("Automated notice drafting is disabled for criminal custody and physical safety cases. Please call **NALSA 15100** above.")
        elif case.case_validity_status in ("GIBBERISH_OR_TOO_SHORT", "OFF_TOPIC_NON_LEGAL", "NO_CLAIM_TRIVIAL_SOCIAL"):
            kit = generate_legal_action_kit(case, router=router)
            st.error(kit["formal_legal_notice_md"])
        elif case.case_validity_status in ("NO_CLAIM_SELF_FAULT", "NO_CLAIM_TIME_BARRED", "NO_CLAIM_LAWFUL_DEDUCTION"):
            party_defaults = DOMAIN_PARTY_DEFAULTS.get(case.domain_key, DOMAIN_PARTY_DEFAULTS["NO_LEGAL_CLAIM_OR_NON_JUSTICIABLE"])
            kit = generate_legal_action_kit(
                case,
                sender_name=party_defaults["sender_name"],
                sender_address=party_defaults["sender_addr"],
                recipient_name=party_defaults["recip_name"],
                recipient_address=party_defaults["recip_addr"],
                router=router,
            )
            st.warning(kit["formal_legal_notice_md"])
            st.markdown("##### 🤝 Copy & Send Polite Goodwill Resolution Request (Without Prejudice)")
            st.code(kit["whatsapp_escalation_template"], language="text")
        else:
            party_defaults = DOMAIN_PARTY_DEFAULTS.get(case.domain_key, DOMAIN_PARTY_DEFAULTS["TENANCY_DEPOSIT"])
            if st.session_state.get("active_domain_key") != case.domain_key:
                st.session_state["active_domain_key"] = case.domain_key
                st.session_state["sender_name_input"] = party_defaults["sender_name"]
                st.session_state["sender_addr_input"] = party_defaults["sender_addr"]
                st.session_state["recip_name_input"] = party_defaults["recip_name"]
                st.session_state["recip_addr_input"] = party_defaults["recip_addr"]

            with st.expander("✏️ Customize Names & Addresses on Notice (Optional)", expanded=False):
                d1, d2 = st.columns(2)
                with d1:
                    sender_name = st.text_input("Your Name", key="sender_name_input")
                    sender_addr = st.text_input("Your Address", key="sender_addr_input")
                with d2:
                    recip_name = st.text_input("Opposite Party Name", key="recip_name_input")
                    recip_addr = st.text_input("Opposite Party Address", key="recip_addr_input")

            tmp_pdf = Path(tempfile.gettempdir()) / f"{case.case_id}_Legal_Notice.pdf"
            kit = generate_legal_action_kit(
                case,
                sender_name=sender_name,
                sender_address=sender_addr,
                recipient_name=recip_name,
                recipient_address=recip_addr,
                pdf_output_path=tmp_pdf,
                router=router,
            )

            col_btn, col_hint = st.columns([1, 2])
            with col_btn:
                if tmp_pdf.exists():
                    st.download_button(
                        "⬇️ Download Printable Legal Notice (A4 PDF)",
                        data=tmp_pdf.read_bytes(),
                        file_name=f"{case.case_id}_Legal_Demand_Notice.pdf",
                        mime="application/pdf",
                        type="primary",
                    )
            with col_hint:
                st.caption("Print on plain A4 paper, sign, and send via **India Post Registered Post with Acknowledgment Due (RPAD)** plus email/WhatsApp.")

            doc_view = st.radio(
                "Choose document to preview:",
                options=[
                    "📱 Step 1: WhatsApp / Email Final Warning",
                    "📜 Step 2: Formal Legal Demand Notice",
                    "🏛️ Step 3: Government Portal Complaint Text",
                ],
                horizontal=True,
                label_visibility="collapsed",
            )

            with st.container(border=True):
                if doc_view.startswith("📱"):
                    st.markdown("##### Copy & Send on WhatsApp or Email First")
                    st.code(kit["whatsapp_escalation_template"], language="text")
                elif doc_view.startswith("📜"):
                    st.markdown(kit["formal_legal_notice_md"])
                else:
                    st.markdown(kit["portal_complaint_synopsis_md"])

    # =========================================================================
    # TAB 3: SCAM DECODER, PRACTICE & LAW CHECKER
    # =========================================================================
    with tab_tools:
        tool_choice = st.radio(
            "Select Tool:",
            options=[
                "🕵️ 1. Threat / Contract Clause Decoder",
                "🥊 2. Practice Arguing (Roleplay Coach)",
                "🛡️ 3. Anti-Hallucination & IPC→BNS Firewall",
            ],
            horizontal=True,
            label_visibility="collapsed",
        )

        st.divider()

        if tool_choice.startswith("🕵️"):
            st.markdown("#### 🕵️ Is Their Threat or Contract Clause Legal?")
            st.caption("Paste any scary WhatsApp threat, 'Digital Arrest' scam message, employment bond clause, or landlord email to check if it holds up under Indian law.")

            if "notice_decoder_input_box" not in st.session_state:
                st.session_state["notice_decoder_input_box"] = active_tc["pasted_opponent_notice"] if active_tc else ""

            notice_input = st.text_area(
                "Opponent's message or clause:",
                height=85,
                placeholder="Paste their threatening WhatsApp message, email, or employment bond clause here...",
                key="notice_decoder_input_box",
            )

            col_dec_btn1, col_dec_btn2 = st.columns([1, 4])
            with col_dec_btn1:
                st.button("🔍 Decode Threat", type="primary", use_container_width=True)
            with col_dec_btn2:
                st.caption("Press **Ctrl+Enter** or click **Decode Threat** to verify legality under Indian law.")

            if not notice_input.strip():
                st.info("👆 Paste any message, WhatsApp threat, bond clause, or legal notice from your opponent above to check if it's legally enforceable or an illegal bluff.")
            else:
                decoded = decode_notice_or_clause(notice_input, router=router)
                st.info(f"**Overall Verdict:** {decoded['summary_assessment']}")

                for flag in decoded["decoded_flags"]:
                    with st.container(border=True):
                        st.markdown(f"**{flag['verdict']}** — *{flag['clause_or_threat_type']}*")
                        st.markdown(f"- **What the Law Actually Says:** {flag['statutory_reality']}")
                        if flag["verdict"] == "UNRECOGNIZED_NON_LEGAL_TEXT":
                            st.warning(f"**Guidance:** {flag['recommended_counter_move']}")
                        else:
                            st.success(f"**Your Counter-Move:** {flag['recommended_counter_move']}")

        elif tool_choice.startswith("🥊"):
            st.markdown("#### 🥊 Practice Your Argument Before Talking to Them")
            persona_info = PERSONAS.get(case.domain_key, PERSONAS["TENANCY_DEPOSIT"])
            st.chat_message("assistant", avatar="😠").write(f"**{persona_info['name']}:** \"{persona_info['opening_stance']}\"")

            if "sparring_user_arg_box" not in st.session_state:
                st.session_state["sparring_user_arg_box"] = active_tc["sample_sparring_arg"] if active_tc else ""

            user_arg = st.text_area(
                "Your reply:",
                height=80,
                placeholder="Type how you want to respond to them (e.g. demanding your refund or citing the law)...",
                key="sparring_user_arg_box",
            )

            col_sp_btn1, col_sp_btn2 = st.columns([1, 4])
            with col_sp_btn1:
                st.button("🥊 Send to Opponent", type="primary", use_container_width=True)
            with col_sp_btn2:
                st.caption("Press **Ctrl+Enter** or click **Send to Opponent** to roleplay and get coaching score.")

            if not user_arg.strip():
                st.caption("💡 Type your reply above to see how they would respond and get instant coaching on how to strengthen your legal position.")
            else:
                eval_res = evaluate_sparring_turn(case.domain_key, user_arg, router=router)

                st.chat_message("user", avatar="🧑").write(user_arg)
                st.chat_message("assistant", avatar="😠").write(f"**{eval_res['persona_name']}:** \"{eval_res['opponent_reply']}\"")

                with st.container(border=True):
                    st.markdown(f"**🎯 Coach Score: `{eval_res['coach_score_100']}/100`** — {eval_res['mistake_detected']}")
                    st.caption(eval_res["coach_critique"])
                    st.info(f"**Stronger Reply to Use:** \"{eval_res['suggested_stronger_comeback']}\"")

        else:
            st.markdown("#### 🛡️ Zero-Hallucination Citation Firewall (IPC → BNS 2023)")
            st.caption(
                "Automatically upgrades outdated pre-July-2024 IPC sections (`IPC 420` → `BNS 318`), blocks invented `Section N` numbers, and strips fake court cases."
            )
            test_raw = st.text_area(
                "Test any AI legal text with fake or outdated laws:",
                value=(
                    "File a complaint under IPC Section 420 and IPC Section 506, "
                    "claim triple damages under Section 999B of the Tenant Penalty Act, and cite "
                    "Ramesh Kumar vs Evil Landlord (2024) alongside Section 108(q) of the Transfer of Property Act, 1882."
                ),
                height=80,
                key="citation_firewall_test_box",
            )
            sanitized_text, audit_log = verify_and_sanitize_legal_text(test_raw)
            st.success(f"**Cleaned & Verified Output:**\n\n{sanitized_text}")
            st.dataframe(pd.DataFrame(audit_log), width="stretch", hide_index=True)


if __name__ == "__main__":
    main()
