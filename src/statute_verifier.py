"""
Zero-Hallucination Statute Verifier & Citation Firewall for NyayaSahayak (Project 2).
1. Retrieves human-verified Indian statutory provisions from `data/indian_statutes_kb.json`.
2. Deterministically intercepts and upgrades outdated pre-July-2024 IPC citations to
   Bharatiya Nyaya Sanhita (BNS), 2023 equivalents.
3. Strips or flags any unverified section number or invented case law citation before it reaches the user.
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple


KB_PATH = Path(__file__).resolve().parent.parent / "data" / "indian_statutes_kb.json"

# Whitelisted section numbers present in our verified Indian law knowledge base
WHITELISTED_SECTION_NUMBERS = {
    "106", "108", "108(q)", "11", "11(1)", "11(2)", "20", "73", "74", "27", "34",
    "3", "5", "15", "15(3)", "2(s)", "25f", "33c", "33c(2)",
    "2(7)", "2(9)", "2(11)", "2(47)", "2(47)(vii)", "35", "69", "69(1)", "69(2)", "89",
    "4", "4(4)", "4(5)", "6", "7", "9", "10", "12", "18", "24", "113",
    "33", "316", "318", "319", "336", "351", "351(2)", "351(3)", "356", "308", "308(2)",
    "138", "141", "142", "xxxvii", "37",
}

IPC_PATTERN = re.compile(
    r"\b(?:IPC\s*(?:Section|Sec\.?)\s*(\d{2,3}[A-Z]?)|(?:Section|Sec\.?)\s*(\d{2,3}[A-Z]?)\s*(?:of\s+the\s+)?(?:IPC|Indian\s+Penal\s+Code))\b",
    re.IGNORECASE,
)

GENERIC_SECTION_PATTERN = re.compile(
    r"\b(?:Section|Sec\.?)\s*(\d+[A-Za-z]*(?:\([0-9a-zA-Z]+\))*)",
    re.IGNORECASE,
)

FAKE_CASE_CITATION_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z\.\s]{2,25}\s+v(?:s\.?|\.)\s+[A-Z][a-zA-Z\.\s]{2,25}(?:\s*\(\d{4}\)|\s+AIR\s+\d{4}|\s+\d+\s+SCC\s+\d+)?)\b"
)


@dataclass
class CitationAuditEvent:
    event_type: str  # "VERIFIED_STATUTE" | "IPC_TO_BNS_UPGRADED" | "UNVERIFIED_SECTION_BLOCKED" | "UNVERIFIED_CASE_BLOCKED"
    raw_citation: str
    resolved_citation: str
    action_taken: str


def load_statute_kb() -> Dict:
    return json.loads(KB_PATH.read_text(encoding="utf-8"))


def get_domain_statutes(domain_key: str) -> Dict:
    kb = load_statute_kb()
    return kb["domains"].get(domain_key, kb["domains"]["TENANCY_DEPOSIT"])


def verify_and_sanitize_legal_text(text: str) -> Tuple[str, List[Dict]]:
    """
    Scans generated legal advice or draft text through our 3-layer deterministic firewall:
    Layer 1: Upgrades legacy IPC citations to Bharatiya Nyaya Sanhita (BNS), 2023.
    Layer 2: Blocks any unverified case-law citation ('X v. Y') to prevent hallucinated precedents.
    Layer 3: Verifies every 'Section N' reference against our whitelisted Indian statutes KB.
    """
    kb = load_statute_kb()
    ipc_map: Dict[str, str] = kb.get("legacy_ipc_to_bns_map", {})
    audit_events: List[CitationAuditEvent] = []
    sanitized = text

    # Layer 1: Intercept & Upgrade outdated IPC references to BNS 2023
    def _replace_ipc(match: re.Match) -> str:
        sec_num = (match.group(1) or match.group(2) or "").strip()
        raw_str = match.group(0)
        if sec_num in ipc_map:
            replacement = ipc_map[sec_num]
            audit_events.append(
                CitationAuditEvent(
                    event_type="IPC_TO_BNS_UPGRADED",
                    raw_citation=raw_str,
                    resolved_citation=replacement,
                    action_taken="Auto-upgraded pre-July-2024 IPC section to current Bharatiya Nyaya Sanhita (BNS), 2023 provision.",
                )
            )
            return replacement
        else:
            replacement = "[Unverified Criminal Provision Removed — Consult BNS 2023 / Human Advocate]"
            audit_events.append(
                CitationAuditEvent(
                    event_type="UNVERIFIED_SECTION_BLOCKED",
                    raw_citation=raw_str,
                    resolved_citation=replacement,
                    action_taken="Blocked unverified IPC section not in verified BNS 2023 mapping.",
                )
            )
            return replacement

    sanitized = IPC_PATTERN.sub(_replace_ipc, sanitized)

    # Layer 2: Block hallucinated case-law precedents (unless none exist)
    def _replace_case(match: re.Match) -> str:
        raw_case = match.group(1).strip()
        replacement = "[Case Precedent Omitted by Zero-Hallucination Firewall — Relying Strictly on Primary Statute]"
        audit_events.append(
            CitationAuditEvent(
                event_type="UNVERIFIED_CASE_BLOCKED",
                raw_citation=raw_case,
                resolved_citation=replacement,
                action_taken="Stripped unverified judicial case citation to prevent LLM precedent hallucination.",
            )
        )
        return replacement

    sanitized = FAKE_CASE_CITATION_PATTERN.sub(_replace_case, sanitized)

    # Layer 3: Check remaining 'Section X' references against whitelist
    def _check_sec(match: re.Match) -> str:
        sec_id = match.group(1).strip().lower()
        base_num = re.sub(r"\(.*\)", "", sec_id)
        raw_str = match.group(0)
        if sec_id in WHITELISTED_SECTION_NUMBERS or base_num in WHITELISTED_SECTION_NUMBERS:
            audit_events.append(
                CitationAuditEvent(
                    event_type="VERIFIED_STATUTE",
                    raw_citation=raw_str,
                    resolved_citation=raw_str,
                    action_taken="Verified against `indian_statutes_kb.json` whitelist.",
                )
            )
            return raw_str
        else:
            replacement = "[Unverified Section Number Removed]"
            audit_events.append(
                CitationAuditEvent(
                    event_type="UNVERIFIED_SECTION_BLOCKED",
                    raw_citation=raw_str,
                    resolved_citation=replacement,
                    action_taken=f"Blocked unverified statutory section '{raw_str}' not present in ground-truth KB.",
                )
            )
            return replacement

    sanitized = GENERIC_SECTION_PATTERN.sub(_check_sec, sanitized)

    return sanitized, [asdict(e) for e in audit_events]
