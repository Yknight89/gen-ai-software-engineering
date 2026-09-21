"""Multi-format ticket importers (CSV, JSON, XML) + bulk import logic."""

from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

import storage
from models import Ticket
from validators import validate_ticket


def _split_tags(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(t).strip() for t in value if str(t).strip()]
    if isinstance(value, str) and value.strip():
        # accept comma, semicolon or pipe separated
        for sep in ("|", ";", ","):
            if sep in value:
                return [t.strip() for t in value.split(sep) if t.strip()]
        return [value.strip()]
    return []


def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Turn a flat raw record (from any format) into a ticket payload dict."""
    out: Dict[str, Any] = {}
    for k in ("customer_id", "customer_email", "customer_name", "subject",
              "description", "category", "priority", "status", "assigned_to"):
        v = raw.get(k)
        if v is not None and str(v) != "":
            out[k] = v

    if "tags" in raw:
        out["tags"] = _split_tags(raw.get("tags"))

    # metadata may be nested (JSON/XML) or flat columns (CSV): source/browser/device_type
    md = {}
    if isinstance(raw.get("metadata"), dict):
        md.update({k: v for k, v in raw["metadata"].items() if v not in (None, "")})
    for k in ("source", "browser", "device_type"):
        if raw.get(k) not in (None, ""):
            md[k] = raw[k]
    if md:
        out["metadata"] = md
    return out


def parse_csv(text: str) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def parse_json(text: str) -> List[Dict[str, Any]]:
    data = json.loads(text)
    if isinstance(data, dict) and "tickets" in data:
        data = data["tickets"]
    if not isinstance(data, list):
        raise ValueError("JSON must be an array of tickets or an object with a 'tickets' array")
    return data


def parse_xml(text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(text)
    records: List[Dict[str, Any]] = []
    # accept <tickets><ticket>...</ticket></tickets> or a list of <ticket> under root
    ticket_nodes = root.findall(".//ticket") or list(root)
    for node in ticket_nodes:
        rec: Dict[str, Any] = {}
        for child in node:
            if child.tag == "tags":
                rec["tags"] = [t.text.strip() for t in child.findall("tag") if t.text]
            elif child.tag == "metadata":
                rec["metadata"] = {c.tag: (c.text or "").strip() for c in child}
            else:
                rec[child.tag] = (child.text or "").strip()
        records.append(rec)
    return records


def parse_by_format(text: str, fmt: str) -> List[Dict[str, Any]]:
    fmt = (fmt or "").lower()
    if fmt == "csv":
        return parse_csv(text)
    if fmt == "json":
        return parse_json(text)
    if fmt == "xml":
        return parse_xml(text)
    raise ValueError(f"Unsupported format '{fmt}' (use csv, json, or xml)")


def import_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate + create each record; return a bulk-import summary."""
    total = len(records)
    successful = 0
    failed: List[Dict[str, Any]] = []
    created_ids: List[str] = []

    for i, raw in enumerate(records):
        payload = _normalize(raw)
        errors = validate_ticket(payload)
        if errors:
            failed.append({"row": i + 1, "errors": errors})
            continue
        ticket = Ticket(
            customer_id=payload["customer_id"],
            customer_email=payload["customer_email"],
            customer_name=payload["customer_name"],
            subject=payload["subject"],
            description=payload["description"],
            category=payload.get("category", "other"),
            priority=payload.get("priority", "medium"),
            status=payload.get("status", "new"),
            assigned_to=payload.get("assigned_to"),
            tags=payload.get("tags", []),
            metadata=payload.get("metadata", {}),
        )
        storage.add(ticket)
        created_ids.append(ticket.id)
        successful += 1

    return {
        "total": total,
        "successful": successful,
        "failed_count": len(failed),
        "failed": failed,
        "created_ids": created_ids,
    }
