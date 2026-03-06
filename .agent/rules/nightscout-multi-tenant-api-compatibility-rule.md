---
trigger: always_on
---

## Nightscout Multi-Tenant API Compatibility Rule

You are working on a Python/FastAPI multi-tenant rewrite of the Nightscout CGM monitoring
platform. The `cgm-remote-monitor/` folder is the original single-tenant Node.js reference
implementation. A significant portion of the rewrite is already complete.

The rule is simple: every API endpoint must be 100% wire-compatible with the original.
A Nightscout client pointed at this rewrite must not be able to tell the difference.

---

### Before implementing or modifying ANY endpoint

1. Find the original handler in `cgm-remote-monitor/` (usually under `lib/api/` or `lib/api3/`)
2. Trace: middleware → route → mongo query → response serialization
3. Verify your implementation matches on every dimension below before writing a single line

---

### Compatibility checklist (zero exceptions)

**URL & method** — path, HTTP verb, and query parameter names must be identical to the original

**Authentication** — the original uses `api-secret` (SHA1) via header or query param; replicate
the same mechanism in the same positions; tenant identification via subdomain slug is the only
addition and must be invisible to the API consumer

**Request body** — field names, types, and nesting must be identical

**Response body** — field names, types, nesting, array vs object shape, and HTTP status codes
must be identical; do not wrap a bare array in an object or vice versa

**MongoDB documents** — same collection names, same field names, same types; the only permitted
addition is `tenant_id` on every document

---

### What exists only in the rewrite (invisible to API consumers)

- `tenant_id` on all Mongo documents
- User management in a separate SQL database
- Subdomain slug routing to resolve the tenant (`<slug>.domain.com`)

---

### Hard stops — do not proceed if any of these are true

- A response field name differs from the original by even one character
- A query parameter was renamed for clarity
- Auth is checked in a different order or position
- An error response shape differs from the original
- A bare array response is wrapped in an object (or the reverse)

---

### Working with existing code

The rewrite is partially complete. When adding or modifying an endpoint, first check whether
a similar endpoint is already implemented and follow the same patterns already established in
the codebase. Consistency within the rewrite matters, but compatibility with the original
always takes priority over internal consistency.