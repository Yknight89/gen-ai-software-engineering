"""Data validation tests (9)."""
import validators as V
from conftest import valid_ticket


def test_valid_ticket_passes():
    assert V.validate_ticket(valid_ticket()) == []

def test_missing_required_fields():
    errs = V.validate_ticket({})
    fields = {e["field"] for e in errs}
    assert {"customer_id", "customer_email", "customer_name", "subject", "description"} <= fields

def test_invalid_email():
    errs = V.validate_ticket(valid_ticket(customer_email="not-an-email"))
    assert any(e["field"] == "customer_email" for e in errs)

def test_subject_too_long():
    errs = V.validate_ticket(valid_ticket(subject="x" * 201))
    assert any(e["field"] == "subject" for e in errs)

def test_description_too_short():
    errs = V.validate_ticket(valid_ticket(description="short"))
    assert any(e["field"] == "description" for e in errs)

def test_invalid_category_enum():
    errs = V.validate_ticket(valid_ticket(category="nope"))
    assert any(e["field"] == "category" for e in errs)

def test_invalid_priority_and_status():
    errs = V.validate_ticket(valid_ticket(priority="huge", status="weird"))
    fields = {e["field"] for e in errs}
    assert "priority" in fields and "status" in fields

def test_tags_must_be_list_of_strings():
    errs = V.validate_ticket(valid_ticket(tags="notalist"))
    assert any(e["field"] == "tags" for e in errs)

def test_metadata_sub_enums():
    errs = V.validate_ticket(valid_ticket(metadata={"source": "carrier-pigeon", "device_type": "toaster"}))
    fields = {e["field"] for e in errs}
    assert "metadata.source" in fields and "metadata.device_type" in fields

def test_partial_update_skips_required():
    # partial=True should not flag missing required fields
    assert V.validate_ticket({"status": "resolved"}, partial=True) == []
