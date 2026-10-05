"""End-to-end integration tests (5)."""
import os
import concurrent.futures
from conftest import valid_ticket

DEMO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo")


def _upload(client, filename, ctype):
    with open(os.path.join(DEMO, filename), "rb") as f:
        return client.post("/tickets/import", files={"file": (filename, f.read(), ctype)})


def test_full_lifecycle(client):
    tid = client.post("/tickets", json=valid_ticket()).json()["id"]
    assert client.get(f"/tickets/{tid}").status_code == 200
    client.put(f"/tickets/{tid}", json={"status": "in_progress"})
    assert client.post(f"/tickets/{tid}/auto-classify").status_code == 200
    resolved = client.put(f"/tickets/{tid}", json={"status": "resolved"}).json()
    assert resolved["resolved_at"]
    assert client.delete(f"/tickets/{tid}").status_code == 200
    assert client.get(f"/tickets/{tid}").status_code == 404


def test_bulk_import_csv_then_classify(client):
    r = _upload(client, "sample_tickets.csv", "text/csv")
    assert r.status_code == 201 and r.json()["successful"] == 50
    # classify one imported ticket and confirm it applied
    tid = client.get("/tickets").json()["tickets"][0]["id"]
    res = client.post(f"/tickets/{tid}/auto-classify").json()
    assert res["applied"] is True and res["category"]


def test_import_all_three_formats(client):
    _upload(client, "sample_tickets.csv", "text/csv")
    _upload(client, "sample_tickets.json", "application/json")
    _upload(client, "sample_tickets.xml", "application/xml")
    assert client.get("/tickets").json()["count"] == 100


def test_concurrent_creates(client):
    def create(i):
        return client.post("/tickets", json=valid_ticket(customer_id=f"C-{i}")).status_code
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        codes = list(ex.map(create, range(25)))
    assert codes.count(201) == 25
    assert client.get("/tickets").json()["count"] == 25


def test_combined_filtering(client):
    _upload(client, "sample_tickets.csv", "text/csv")
    both = client.get("/tickets?category=billing_question&priority=high").json()
    for t in both["tickets"]:
        assert t["category"] == "billing_question" and t["priority"] == "high"
