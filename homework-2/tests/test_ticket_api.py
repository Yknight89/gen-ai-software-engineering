"""API endpoint tests (11)."""
from conftest import valid_ticket


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200 and "service" in r.json()

def test_create_ticket_201(client):
    r = client.post("/tickets", json=valid_ticket())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] and body["status"] == "new"

def test_create_validation_400(client):
    r = client.post("/tickets", json={"customer_id": "C", "customer_email": "bad", "customer_name": "X", "subject": "hi", "description": "short"})
    assert r.status_code == 400
    assert r.json()["error"] == "Validation failed"

def test_missing_body_field_maps_to_400(client):
    r = client.post("/tickets", json={"customer_id": "C"})
    assert r.status_code == 400

def test_get_ticket_200(client):
    tid = client.post("/tickets", json=valid_ticket()).json()["id"]
    r = client.get(f"/tickets/{tid}")
    assert r.status_code == 200 and r.json()["id"] == tid

def test_get_ticket_404(client):
    assert client.get("/tickets/does-not-exist").status_code == 404

def test_list_tickets(client):
    client.post("/tickets", json=valid_ticket())
    client.post("/tickets", json=valid_ticket(customer_id="CUST-2", category="billing_question"))
    r = client.get("/tickets")
    assert r.status_code == 200 and r.json()["count"] == 2

def test_list_filter_by_category(client):
    client.post("/tickets", json=valid_ticket())
    client.post("/tickets", json=valid_ticket(category="billing_question"))
    r = client.get("/tickets?category=billing_question")
    assert r.json()["count"] == 1

def test_update_ticket(client):
    tid = client.post("/tickets", json=valid_ticket()).json()["id"]
    r = client.put(f"/tickets/{tid}", json={"status": "resolved"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "resolved" and body["resolved_at"]

def test_update_404_and_empty(client):
    assert client.put("/tickets/nope", json={"status": "resolved"}).status_code == 404
    tid = client.post("/tickets", json=valid_ticket()).json()["id"]
    assert client.put(f"/tickets/{tid}", json={}).status_code == 400

def test_delete_ticket(client):
    tid = client.post("/tickets", json=valid_ticket()).json()["id"]
    assert client.delete(f"/tickets/{tid}").status_code == 200
    assert client.get(f"/tickets/{tid}").status_code == 404
    assert client.delete(f"/tickets/{tid}").status_code == 404
