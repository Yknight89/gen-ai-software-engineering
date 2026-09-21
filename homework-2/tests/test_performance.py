"""Performance benchmarks (5). Thresholds are generous to avoid flakiness."""
import os
import time
from conftest import valid_ticket

DEMO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo")


def test_create_100_tickets_fast(client):
    start = time.perf_counter()
    for i in range(100):
        client.post("/tickets", json=valid_ticket(customer_id=f"C-{i}"))
    elapsed = time.perf_counter() - start
    assert client.get("/tickets").json()["count"] == 100
    assert elapsed < 5.0, f"took {elapsed:.2f}s"


def test_import_50_csv_fast(client):
    with open(os.path.join(DEMO, "sample_tickets.csv"), "rb") as f:
        data = f.read()
    start = time.perf_counter()
    r = client.post("/tickets/import", files={"file": ("s.csv", data, "text/csv")})
    elapsed = time.perf_counter() - start
    assert r.json()["successful"] == 50
    assert elapsed < 2.0, f"took {elapsed:.2f}s"


def test_list_is_fast(client):
    for i in range(100):
        client.post("/tickets", json=valid_ticket(customer_id=f"C-{i}"))
    start = time.perf_counter()
    client.get("/tickets")
    assert (time.perf_counter() - start) < 1.0


def test_classify_throughput():
    import classifier
    start = time.perf_counter()
    for _ in range(200):
        classifier.classify("Cannot access account", "Locked out, urgent and critical, production down.")
    assert (time.perf_counter() - start) < 1.0


def test_get_by_id_fast(client):
    tid = client.post("/tickets", json=valid_ticket()).json()["id"]
    start = time.perf_counter()
    client.get(f"/tickets/{tid}")
    assert (time.perf_counter() - start) < 0.2
