"""CSV import tests (6)."""
import importers, storage
from conftest import valid_ticket

CSV_HEADER = "customer_id,customer_email,customer_name,subject,description,category,priority,tags,source,device_type\n"
GOOD_ROW = "CUST-2,bob@example.com,Bob,Billing issue here,I was charged twice this month and need a refund please,billing_question,medium,billing;refund,email,desktop\n"
BAD_ROW = "CUST-3,bademail,Bad,Too short,short,other,low,,web_form,desktop\n"


def test_parse_csv_rows():
    rows = importers.parse_csv(CSV_HEADER + GOOD_ROW)
    assert len(rows) == 1 and rows[0]["customer_id"] == "CUST-2"

def test_import_csv_success():
    summary = importers.import_records(importers.parse_csv(CSV_HEADER + GOOD_ROW))
    assert summary["successful"] == 1 and summary["failed_count"] == 0

def test_import_csv_reports_failures():
    summary = importers.import_records(importers.parse_csv(CSV_HEADER + GOOD_ROW + BAD_ROW))
    assert summary["total"] == 2 and summary["successful"] == 1 and summary["failed_count"] == 1
    assert summary["failed"][0]["row"] == 2

def test_csv_tags_are_split():
    importers.import_records(importers.parse_csv(CSV_HEADER + GOOD_ROW))
    t = storage.list_tickets()[0]
    assert "billing" in t.tags and "refund" in t.tags

def test_csv_metadata_flattened_into_object():
    importers.import_records(importers.parse_csv(CSV_HEADER + GOOD_ROW))
    t = storage.list_tickets()[0]
    assert t.metadata.get("source") == "email" and t.metadata.get("device_type") == "desktop"

def test_import_csv_via_endpoint(client):
    content = CSV_HEADER + GOOD_ROW
    r = client.post("/tickets/import", files={"file": ("t.csv", content, "text/csv")})
    assert r.status_code == 201 and r.json()["successful"] == 1
