# ⚖️ NyayaSahayak — Grounded Everyday Indian AI Lawyer & Legal Action Engine

Submission for **Kuku AI Generalist Assignment — Problem 2: Build an AI Lawyer**, built specifically for ordinary citizens in India facing high-frequency everyday legal disputes (**Rental Security Deposit Recovery**, **Unpaid Salary / F&F & Bond Hostage**, **Consumer E-Commerce Refund Refusal**, **Unauthorized UPI / Digital Banking Fraud**, and **Intimidating Notice / Recovery Agent Bluff Triage**).

Features a **3-Layer Deterministic Citation Firewall** (auto-upgrades pre-July-2024 IPC to Bharatiya Nyaya Sanhita (BNS) 2023), Contract Trap Decoder, Limitation/Court ROI Calculator, Printable A4 Legal Demand Notice PDF Generator, and Opponent Sparring Coach.

---

## 🚀 Quick Start (Runs Out-of-the-Box with Zero Hallucinations)

### 1. Launch Interactive Web App (Streamlit)
```powershell
pip install -r requirements.txt
python -m streamlit run app.py
```
*(Note: Using `python -m streamlit run app.py` instead of `streamlit run app.py` avoids Windows Application Control / Smart App Control policies blocking unsigned pip `.exe` wrapper shims.)*

- **Backend `.env` & Streamlit `st.secrets` Authentication (Zero Keys Exposed in UI):** Add your `GEMINI_API_KEY` (or `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`, `OPENAI_API_KEY`) to `.env` locally or to Streamlit Cloud `Secrets`. API keys are never shown or editable in the UI.
- **Dynamic Router, Model & Legal Strategy Switching (Auto Re-Runs on Change):** Open `⚙️ AI Model Settings` in the left sidebar to select from active `.env` routers (`gemini`, `groq`, `openrouter`, `mistral`, `openai`), choose specific models (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`, `llama-3.3-70b-versatile`, etc.), and switch legal strategies (`Balanced Legal Strategy`, `Aggressive Maximum Penalty`, `Conciliatory 48-Hour Amicable Settlement`)—automatically re-running while enforcing the **3-Layer Deterministic Citation Firewall** (`src/statute_verifier.py`).
- **4-Tier Validity & "No-Law-Case" Merits Gate:** Rejects random gibberish (`GIBBERISH_OR_TOO_SHORT`, `₹0`) and off-topic queries (`OFF_TOPIC_NON_LEGAL`), and honestly flags non-actionable claims (`NO_CLAIM_TRIVIAL_SOCIAL` under BNS Sec 33 *De minimis*, `NO_CLAIM_SELF_FAULT` under CPA Sec 2(11) with a Polite Goodwill Request instead of a fake legal notice, `NO_CLAIM_TIME_BARRED` under Limitation Act Sec 3 & 18, and `NO_CLAIM_LAWFUL_DEDUCTION`), plus full support for **Dishonoured Cheques (`CHEQUE_BOUNCE_RECOVERY`, NI Act Sec 138 & 142)** and **"Digital Arrest" Cyber Scams**.

### 2. Run Verification & Benchmark Suites
```powershell
# 1. Run all 8 benchmark test cases (Generates raw_outputs/ & printable PDFs in <0.2s)
python run_test_suite.py

# 2. Run real-world human interactive simulation across 6 realistic disputes
python tests_human_interactive.py

# 3. Run headless Streamlit AppTest suite
python -m pytest tests_app_ui.py
```

---

## 🖥️ Clean 3-Tab Legal Action Layout

The Streamlit UI has been streamlined into a clean, distraction-free **3-tab layout**:

1. **Tab 1: ⚖️ Legal Triage & Assessment**
   - **Intake:** Choose from 8 pre-loaded realistic Indian test cases (English, Hindi Devanagari, Hinglish, Red-Line FIRs) OR select **"✍️ Write My Own Problem"** to type any custom dispute.
   - **Dynamic Custom Intake:** Weighted multi-keyword classifier automatically tags the domain (`TENANCY_DEPOSIT`, `UNPAID_SALARY`, `CONSUMER_REFUND`, `UPI_BANKING_FRAUD`, `NOTICE_AND_CRIMINAL_TRIAGE`), extracts the claim amount (e.g. `refund of 28000`), and generates a unique case ID without inheriting landlord/deposit defaults.
   - **Structured Legal Standing:** Chronological fact timeline, Evidence Readiness score (`/100`), plain-language standing in English & Hindi, statutory basis with BNS 2023 citations, and a practical **Pre-Notice WhatsApp Evidence Trap** to lock in admissions.
   - **Limitation & Court ROI Calculator:** Compares pre-litigation notice (Rs. 0), e-Daakhil / SAMADHAN portal (Rs. 0), and court litigation (advocate fees, court fees, timeline, financial viability).
2. **Tab 2: 📄 Legal Demand Notice (PDF)**
   - **Smart Party Defaults:** Automatically populates sender and recipient titles based on domain (`Tenant / Landlord`, `Employee / Employer`, `Consumer / Seller`) while allowing full custom edits.
   - **Instant Printable A4 PDF:** Generates a formal `WITHOUT PREJUDICE` Legal Demand Notice citing **Order XXXVII CPC Summary Suits** with a mandatory 15-day cure period and 18% p.a. interest claims.
   - **Escalation Kit:** Ready-to-copy WhatsApp formal reminder and official government portal filing synopsis (`e-Daakhil`, `SAMADHAN`, `CMS RBI`, `Cybercrime 1930`).
3. **Tab 3: 🥊 Opponent Sparring & Trap Decoder**
   - **Tool 1 (Threat / Notice Decoder):** Scans pasted opponent notices or contract clauses for illegal intimidation bluffs (void non-compete clauses under Sec 27 ICA, arbitrary wage forfeiture, e-commerce blanket disclaimers, or fake WhatsApp arrest warrants).
   - **Tool 2 (Opponent Sparring Coach):** Interactive chat sparring against an aggressive opponent persona matched to the dispute (`Vikram HR Head`, `Mr. Sharma Landlord`, `Customer Escalation Desk`, `Branch Operations Manager`, or `Recovery Agent`). The built-in Legal Coach evaluates replies, catches tactical mistakes (e.g. conceding money without writing 'WITHOUT PREJUDICE'), and suggests stronger statutory counter-arguments.

---

## 🛡️ 3-Layer Zero-Hallucination Citation Firewall

```
[Raw Model / User Output]
           │
           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 1: Legacy IPC -> BNS 2023 Auto-Upgrader          │
│ Intercepts pre-July-2024 IPC sections (e.g. IPC 420)   │
│ and upgrades to Bharatiya Nyaya Sanhita (BNS Sec 318)  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 2: Case Law Hallucination Stripper               │
│ Strips unverified "Party A v. Party B" case citations   │
│ (pre-litigation notices rely strictly on statutes)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ Layer 3: Statutory Whitelist Validator                │
│ Matches all remaining "Section N" against curated KB;  │
│ unverified sections are safely excised and logged      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
[100% Verified, Grounded Legal Document / Notice PDF]
```

* **Hard Red-Line Safety Stop:** Immediately halts self-help drafting when active criminal custody (FIR/arrest), domestic violence, or complex family litigation is detected, routing the citizen to **NALSA Toll-Free Helpline `15100`** under **Section 12 of the Legal Services Authorities Act, 1987**.

---


## ⚙️ Architecture & Code Map (`src/`)

- [`src/statute_verifier.py`](file:///d:/projects/KukuFM/project2_ai_lawyer/src/statute_verifier.py): 3-Layer Citation Firewall with IPC to BNS 2023 auto-upgrade and AST/regex validation.
- [`src/case_builder.py`](file:///d:/projects/KukuFM/project2_ai_lawyer/src/case_builder.py): Multilingual intake (English, Hindi Devanagari, Hinglish), weighted domain classification, context-aware amount parsing, Red-Line safety trigger, and Court ROI calculator.
- [`src/notice_decoder.py`](file:///d:/projects/KukuFM/project2_ai_lawyer/src/notice_decoder.py): Contract & intimidation notice scanner checking against 5 illegal Indian bluffs and eCourts 16-digit CNR verification.
- [`src/document_generator.py`](file:///d:/projects/KukuFM/project2_ai_lawyer/src/document_generator.py): Typesets formal A4 `WITHOUT PREJUDICE` Legal Demand Notice PDFs citing Order XXXVII CPC using ReportLab.
- [`src/roleplay_coach.py`](file:///d:/projects/KukuFM/project2_ai_lawyer/src/roleplay_coach.py): Opponent sparring engine with domain-matched personas and real-time legal mistake coaching.
- [`src/llm_layer.py`](file:///d:/projects/KukuFM/project2_ai_lawyer/src/llm_layer.py): Swappable LLM integration layer supporting Groq, Gemini, OpenRouter, Mistral, and OpenAI.
