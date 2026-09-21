"""Auto-classification via the API (Task 2 endpoints)."""
from conftest import valid_ticket


def test_create_with_auto_classify_fills_fields(client):
    payload = {
        "customer_id": "C1", "customer_email": "a@b.com", "customer_name": "A",
        "subject": "Cannot access my account",
        "description": "Locked out after password reset, this is critical and blocking.",
    }
    r = client.post("/tickets?auto_classify=true", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["category"] == "account_access"
    assert body["priority"] == "urgent"
    assert body["classification_confidence"] is not None

def test_auto_classify_manual_value_wins(client):
    payload = valid_ticket(category="other", subject="App crash", description="The app crashes with a 500 error every time.")
    r = client.post("/tickets?auto_classify=true", json=payload)
    assert r.json()["category"] == "other"  # explicit value preserved

def test_auto_classify_endpoint_applies(client):
    tid = client.post("/tickets", json=valid_ticket(category="other", priority="low",
          subject="Refund", description="I was charged twice and need a refund on my invoice.")).json()["id"]
    r = client.post(f"/tickets/{tid}/auto-classify")
    assert r.status_code == 200 and r.json()["applied"] is True
    assert client.get(f"/tickets/{tid}").json()["category"] == "billing_question"

def test_auto_classify_preview_does_not_change(client):
    tid = client.post("/tickets", json=valid_ticket(category="other",
          subject="Refund", description="I was charged twice and need a refund on my invoice.")).json()["id"]
    r = client.post(f"/tickets/{tid}/auto-classify?apply=false")
    assert r.json()["applied"] is False
    assert client.get(f"/tickets/{tid}").json()["category"] == "other"

def test_auto_classify_404(client):
    assert client.post("/tickets/nope/auto-classify").status_code == 404

def test_classification_log_records(client):
    client.post("/tickets?auto_classify=true", json=valid_ticket())
    r = client.get("/classification-log")
    assert r.status_code == 200 and r.json()["count"] >= 1
