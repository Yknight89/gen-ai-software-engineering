"""XML import tests (5)."""
import importers, storage

XML = """<tickets>
 <ticket>
  <customer_id>CUST-7</customer_id>
  <customer_email>ed@example.com</customer_email>
  <customer_name>Ed</customer_name>
  <subject>Refund not received yet</subject>
  <description>I requested a refund two weeks ago and still have not received it.</description>
  <category>billing_question</category>
  <priority>high</priority>
  <tags><tag>refund</tag><tag>billing</tag></tags>
  <metadata><source>phone</source><device_type>desktop</device_type></metadata>
 </ticket>
</tickets>"""

BAD_XML = "<tickets><ticket><customer_id>only</customer_id></ticket></tickets>"


def test_parse_xml_rows():
    recs = importers.parse_xml(XML)
    assert len(recs) == 1 and recs[0]["customer_id"] == "CUST-7"

def test_xml_tags_and_metadata_parsed():
    recs = importers.parse_xml(XML)
    assert recs[0]["tags"] == ["refund", "billing"]
    assert recs[0]["metadata"]["source"] == "phone"

def test_import_xml_success():
    summary = importers.import_records(importers.parse_xml(XML))
    assert summary["successful"] == 1

def test_import_xml_incomplete_record_fails():
    summary = importers.import_records(importers.parse_xml(BAD_XML))
    assert summary["successful"] == 0 and summary["failed_count"] == 1

def test_import_xml_via_endpoint(client):
    r = client.post("/tickets/import", files={"file": ("t.xml", XML, "application/xml")})
    assert r.status_code == 201 and r.json()["successful"] == 1
