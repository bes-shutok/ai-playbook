# Contract Blueprint Example (minimum detail bar)

Neutral illustration of the **minimum** §5 contract depth for implementation-ready Design RFCs. Prefer this shape over prose-only API descriptions.

Pattern source: company service RFCs under `docs/history/feature-notes/` (Layer 3); use fictitious values only in this file.

## §5.1 APIs (structure)

### Endpoint inventory

List every in-scope endpoint first (`METHOD /path`), split by implementation status when needed:

- Implemented in OpenAPI: `POST /v1/widgets`, `GET /v1/widgets/{widgetId}`
- Agreed MVP, not yet in OpenAPI: `PATCH /v1/widget-updates/{externalId}`

### MVP priority (when multiple endpoints)

Label each endpoint `Must`, `Optional`, or `Later` with a **one-line reason** tied to a caller or UI slice. Do not bury priority in paragraphs.

### Contract notes

Short bullets only (idempotency, conflict codes, headers, enum constraints). Reference concrete status codes and error `code` values, not "handles errors appropriately."

Example note: `` `POST /v1/widgets` returns `409 CONFLICT` with `code: "EXTERNAL_ID_CONFLICT"` when `externalId` already exists. ``

### §5.1.1 Example request / response bodies (required for in-scope APIs)

One subsection **per endpoint**. Each subsection includes:

1. `##### `METHOD /path`` heading
2. **Request body:** JSON fence, or `none`
3. **Response body:** JSON fence (happy path)
4. **Error bodies** for non-obvious failures (at least one per write endpoint when status semantics matter)

Planned or proposed endpoints: mark `(proposed)` in the heading or intro line.

---

##### `POST /v1/widgets`

Request body:

```json
{
  "externalId": "ext-10001",
  "widgetType": "STANDARD",
  "labels": {
    "tier": "gold",
    "region": "eu-west"
  },
  "settings": {
    "notifyOnChange": true,
    "maxItems": 10
  }
}
```

Response body (`201 Created`):

```json
{
  "widgetId": "202607080001wdg00000001",
  "externalId": "ext-10001",
  "widgetType": "STANDARD",
  "status": "ACTIVE",
  "labels": {
    "tier": "gold",
    "region": "eu-west"
  },
  "settings": {
    "notifyOnChange": true,
    "maxItems": 10
  },
  "version": 1,
  "createdAt": "2026-07-08T10:00:00Z",
  "updatedAt": "2026-07-08T10:00:00Z"
}
```

Error body (`409 Conflict`, duplicate `externalId`):

```json
{
  "code": "EXTERNAL_ID_CONFLICT",
  "message": "A widget with this externalId already exists",
  "details": {
    "externalId": "ext-10001",
    "existingWidgetId": "202607070001wdg00000009"
  }
}
```

##### `GET /v1/widgets/{widgetId}`

Request body: none.

Response body (`200 OK`):

```json
{
  "widgetId": "202607080001wdg00000001",
  "externalId": "ext-10001",
  "widgetType": "STANDARD",
  "status": "ACTIVE",
  "labels": {
    "tier": "gold",
    "region": "eu-west"
  },
  "settings": {
    "notifyOnChange": true,
    "maxItems": 10
  },
  "version": 1,
  "createdAt": "2026-07-08T10:00:00Z",
  "updatedAt": "2026-07-08T10:00:00Z"
}
```

---

## §5.2 Events (when in scope)

Same rule: **payload JSON first**, metadata bullets second.

##### `WidgetStatusChanged`

Payload:

```json
{
  "widgetId": "202607080001wdg00000001",
  "previousStatus": "ACTIVE",
  "newStatus": "SUSPENDED",
  "changedAt": "2026-07-08T11:00:00Z"
}
```

Producer / consumers / delivery semantics: one line each after the payload.

## §5.3 Database (when in scope)

Prefer **DDL or full hot-path SQL** over table descriptions in prose.

```sql
CREATE TABLE widget (
  widget_id     VARCHAR(24) PRIMARY KEY,
  external_id   VARCHAR(128) NOT NULL,
  widget_type   VARCHAR(32) NOT NULL,
  status        VARCHAR(16) NOT NULL,
  labels_json   JSONB NOT NULL,
  settings_json JSONB NOT NULL,
  version       INTEGER NOT NULL DEFAULT 1,
  created_at    TIMESTAMPTZ NOT NULL,
  updated_at    TIMESTAMPTZ NOT NULL,
  CONSTRAINT uq_widget_external_id UNIQUE (external_id)
);

CREATE INDEX idx_widget_status_updated ON widget (status, updated_at DESC);
```

When there is no schema change, still include the **full hot-path read query** and covering index name (see `rfc-sections.md` §5.3).

## Anti-patterns (too thin for §5)

- "The service exposes CRUD endpoints for widgets" without method/path list
- "Request includes widget metadata" without a JSON example
- "Returns the created resource" without response field names and types
- Describing error handling only in §4 flows without `4xx/5xx` JSON bodies in §5
- Replacing §5.1.1 with OpenAPI links only (links may supplement; they do not replace in-RFC bodies)
