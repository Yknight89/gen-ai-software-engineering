"""Auto-classification tests (10)."""
import classifier
from conftest import valid_ticket


def test_account_access_detected():
    r = classifier.classify("Cannot log in", "My password reset failed and I am locked out of my account.")
    assert r["category"] == "account_access"

def test_billing_detected():
    r = classifier.classify("Refund please", "I was charged twice on my invoice and need a refund.")
    assert r["category"] == "billing_question"

def test_technical_issue_detected():
    r = classifier.classify("App crash", "The app crashes with a 500 error and is very slow.")
    assert r["category"] == "technical_issue"

def test_feature_request_detected():
    r = classifier.classify("Idea", "Please add dark mode, it would be a nice enhancement.")
    assert r["category"] == "feature_request"

def test_bug_report_detected():
    r = classifier.classify("Bug", "Here are steps to reproduce a defect that is clearly a bug.")
    assert r["category"] == "bug_report"

def test_other_when_no_keywords():
    r = classifier.classify("Hello", "Just saying hi to the team today, nothing specific.")
    assert r["category"] == "other" and r["confidence"] == 0.3

def test_priority_urgent():
    r = classifier.classify("Down", "Production down and this is a critical security issue.")
    assert r["priority"] == "urgent"

def test_priority_low():
    r = classifier.classify("Tiny", "A minor cosmetic suggestion, trivial and nice to have.")
    assert r["priority"] == "low"

def test_priority_defaults_medium():
    r = classifier.classify("Question", "I have a general question about the roadmap timeline.")
    assert r["priority"] == "medium"

def test_result_shape():
    r = classifier.classify("Cannot access account", "Locked out, urgent and critical.")
    assert set(r.keys()) == {"category", "priority", "confidence", "reasoning", "keywords_found"}
    assert 0.0 <= r["confidence"] <= 1.0
