"""Rule-based auto-classification for tickets: category + priority.

Deterministic keyword scoring (no external LLM) so results are reproducible and
testable. Returns category, priority, a confidence score (0-1), human-readable
reasoning, and the keywords that matched.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Category keyword banks. Order matters only for tie-break stability.
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "account_access": ["login", "log in", "log-in", "password", "2fa", "sign in",
                       "sign-in", "locked out", "can't access", "cannot access",
                       "reset", "authentication", "account access"],
    "billing_question": ["billing", "invoice", "payment", "charged", "charge",
                         "refund", "subscription", "credit card", "overcharged",
                         "receipt", "pricing"],
    "bug_report": ["bug", "defect", "reproduce", "steps to reproduce",
                   "unexpected", "regression", "broken"],
    "technical_issue": ["error", "crash", "crashes", "not working", "fails",
                        "failure", "500", "exception", "timeout", "slow",
                        "glitch", "freeze"],
    "feature_request": ["feature", "request", "enhancement", "suggestion",
                        "would be nice", "please add", "add support", "idea",
                        "improve"],
}

# Priority keyword banks.
PRIORITY_KEYWORDS: Dict[str, List[str]] = {
    "urgent": ["can't access", "cannot access", "critical", "production down",
               "security", "urgent", "outage", "data loss", "breach"],
    "high": ["important", "blocking", "asap", "as soon as possible", "high priority"],
    "low": ["minor", "cosmetic", "suggestion", "nice to have", "trivial"],
}


def _score(text: str, keywords: List[str]) -> Tuple[int, List[str]]:
    found = [kw for kw in keywords if kw in text]
    return len(found), found


def classify(subject: str, description: str) -> Dict:
    """Classify a ticket from its subject + description."""
    text = f"{subject or ''} {description or ''}".lower()

    # --- category ---
    best_cat = "other"
    best_score = 0
    cat_keywords: List[str] = []
    for cat, kws in CATEGORY_KEYWORDS.items():
        score, found = _score(text, kws)
        if score > best_score:
            best_cat, best_score, cat_keywords = cat, score, found

    # confidence: scales with number of matches, capped at 0.95; 0.3 when nothing matched
    if best_score == 0:
        cat_confidence = 0.3
    else:
        cat_confidence = min(0.95, 0.5 + 0.15 * best_score)

    # --- priority ---
    priority = "medium"
    prio_keywords: List[str] = []
    prio_reason = "no priority keywords matched — defaulted to medium"
    for level in ("urgent", "high", "low"):  # urgent wins over high over low
        score, found = _score(text, PRIORITY_KEYWORDS[level])
        if score > 0:
            priority = level
            prio_keywords = found
            prio_reason = f"matched {level} keyword(s): {', '.join(found)}"
            break

    keywords_found = cat_keywords + prio_keywords
    if best_score == 0:
        cat_reason = "no category keywords matched — defaulted to 'other'"
    else:
        cat_reason = f"matched {best_score} '{best_cat}' keyword(s): {', '.join(cat_keywords)}"

    return {
        "category": best_cat,
        "priority": priority,
        "confidence": round(cat_confidence, 2),
        "reasoning": f"{cat_reason}; {prio_reason}",
        "keywords_found": keywords_found,
    }
