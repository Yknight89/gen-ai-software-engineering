"""JSON import tests (5)."""
import json
import importers
from conftest import valid_ticket


def test_parse_json_array():
    text = json.dumps([valid_ticket(), valid_ticket(customer_id="CUST-9")])
    assert len(importers.parse_json(text)) == 2

def test_parse_json_wrapped_object():
    text = json.dumps({"tickets": [valid_ticket()]})
    assert len(importers.parse_json(text)) == 1

def test_parse_json_invalid_type():
    import pytest
    with pytest.raises(ValueError):
        importers.parse_json(json.dumps({"nope": 1}))

def test_import_json_success():
    text = json.dumps([valid_ticket(), valid_ticket(customer_id="CUST-9", category="bug_report")])
    summary = importers.import_records(importers.parse_json(text))
    assert summary["successful"] == 2

def test_import_json_via_endpoint(client):
    text = json.dumps([valid_ticket()])
    r = client.post("/tickets/import", files={"file": ("t.json", text, "application/json")})
    assert r.status_code == 201 and r.json()["successful"] == 1
