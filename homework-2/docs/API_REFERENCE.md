# 📖 API Reference

Base URL: `http://localhost:8000` · All request/response bodies are JSON
(except file upload for import). Interactive docs: `/docs`.

## Ticket model

```json
{
  "id": "uuid",
  "customer_id": "string",
  "customer_email": "email",
  "customer_name": "string",
  "subject": "string (1-200)",
  "description": "string (10-2000)",
  "category": "account_access | technical_issue | billing_question | feature_request | bug_report | other",
  "priority": "urgent | high | medium | low",
  "status": "new | in_progress | waiting_customer | resolved | closed",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601",
  "resolved_at": "ISO 8601 | null",
  "assigned_to": "string | null",
  "tags": ["string"],
  "metadata": { "source": "web_form|email|api|chat|phone", "browser": "string", "device_type": "desktop|mobile|tablet" },
  "classification_confidence": "number | null"
}
```

## Error format

Validation failures return **400** with:

```json
{ "error": "Validation failed", "details": [ { "field": "customer_email", "message": "Invalid email format" } ] }
```

Missing resources return **404** with `{ "error": "Not found", "message": "..." }`.

---

## Endpoints

### POST /tickets
Create a ticket. Query: `auto_classify=true` to auto-set category/priority (explicit values win). Returns **201**.

```bash
curl -X POST http://localhost:8000/tickets -H "Content-Type: application/json" -d '{
  "customer_id":"CUST-1001","customer_email":"jane@example.com","customer_name":"Jane Doe",
  "subject":"Cannot log in","description":"Locked out after a password reset, blocking my work.",
  "category":"account_access","priority":"high"}'
```

### POST /tickets/import
Bulk import from CSV / JSON / XML (multipart file upload; format inferred from extension). Returns **201** with a summary.

```bash
curl -X POST http://localhost:8000/tickets/import -F "file=@demo/sample_tickets.csv"
# -> {"total":50,"successful":49,"failed_count":1,"failed":[{"row":12,"errors":[...]}],"created_ids":[...]}
```

### GET /tickets
List tickets. Optional filters: `category`, `priority`, `status`, `customer_id`, `assigned_to` (combinable).

```bash
curl "http://localhost:8000/tickets?category=billing_question&priority=high"
```

### GET /tickets/{id}
Fetch one ticket. **200** or **404**.

```bash
curl http://localhost:8000/tickets/<id>
```

### PUT /tickets/{id}
Partial update (any subset of fields). Setting `status=resolved` sets `resolved_at`. Metadata is merged. **200/400/404**.

```bash
curl -X PUT http://localhost:8000/tickets/<id> -H "Content-Type: application/json" -d '{"status":"in_progress","assigned_to":"agent-7"}'
```

### DELETE /tickets/{id}
Delete a ticket. **200** `{"deleted": "<id>"}` or **404**.

```bash
curl -X DELETE http://localhost:8000/tickets/<id>
```

### POST /tickets/{id}/auto-classify
Classify a ticket. Query `apply=false` previews without saving. Returns category, priority, confidence, reasoning, keywords_found.

```bash
curl -X POST http://localhost:8000/tickets/<id>/auto-classify
# -> {"ticket_id":"...","applied":true,"category":"technical_issue","priority":"high","confidence":0.8,"reasoning":"...","keywords_found":["crash","error"]}
```

### GET /classification-log
Return the log of all classification decisions (audit trail).
