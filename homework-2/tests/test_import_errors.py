"""Import error handling + update metadata merge (edge coverage)."""
from conftest import valid_ticket


def test_import_malformed_json_400(client):
    r = client.post("/tickets/import", files={"file": ("bad.json", "{bad json", "application/json")})
    assert r.status_code == 400
    assert r.json()["error"] == "Validation failed"

def test_import_unsupported_format_400(client):
    r = client.post("/tickets/import", files={"file": ("data.txt", "hello", "text/plain")})
    assert r.status_code == 400

def test_import_malformed_xml_400(client):
    r = client.post("/tickets/import", files={"file": ("bad.xml", "<tickets><ticket>", "application/xml")})
    assert r.status_code == 400

def test_update_merges_metadata(client):
    tid = client.post("/tickets", json=valid_ticket(metadata={"source": "web_form", "browser": "Chrome"})).json()["id"]
    client.put(f"/tickets/{tid}", json={"metadata": {"device_type": "mobile"}})
    md = client.get(f"/tickets/{tid}").json()["metadata"]
    assert md["source"] == "web_form" and md["device_type"] == "mobile"
