# agents.md — AI Guidelines for the Virtual Card Lifecycle Spec

This file tells any AI coding agent how to work in this project. It is a specification
project: the deliverable is documentation, not code. Keep that boundary.

## Project context
- **Domain**: Virtual corporate card lifecycle management (`pending_issuance` →
  `active` ↔ `frozen` → `expired` / `cancelled`) for a regulated, API-first card
  platform.
- **Nature**: Specification-driven design homework. Produce and refine specs,
  `agents.md`, editor rules, and README — **never** implementation code, APIs, or UI.

## Intended tech stack (for when this spec is later built — not now)
- Language/runtime: Python 3.11+ (FastAPI) or Node.js (TypeScript) — pick one at build
  time; the spec stays language-neutral.
- Data: a relational operational store (e.g. PostgreSQL 15) + an append-only audit
  store; an event bus for domain events.
- Money: integer minor units + ISO 4217 currency — never floats.

## Domain rules the AI must always respect
- Full PAN / CVV / expiry are **never** stored, logged, or returned by the service —
  only a network token reference + last four digits. Details appear only in the
  processor-hosted display opened by a single-use reveal session.
- Every mutating action is authorized at the **company boundary** with a `card:manage`
  entitlement; deny by default; no cross-tenant access (other-company ids return 404).
  Large limit increases need a different principal with `card:approve`.
- Card state changes **only** through the allowed state-machine transitions.
- `cancelled` and `expired` are **terminal** for spend. Erasure of residual secrets
  starts only after the network confirms the end of life.
- **Safe direction rule**: freeze, cancel, expire, limit decrease apply locally and
  never wait for the network. Unfreeze and limit increase wait for network
  confirmation. Reconciliation never re-enables a card.
- All mutating operations are **idempotent** via `Idempotency-Key`; `issue` also needs
  a permanent per-company `client_reference`.
- State change and event commit together (transactional outbox, at-least-once relay).
- Mask PII in all logs; log every action with a `correlation_id`.

## Testing expectations (for the eventual build)
- State-machine coverage of the full transition matrix (allowed + rejected).
- Authorization, idempotency and concurrency, money-validation, audit-emission and
  outbox, safe-direction, reconciliation, and no-PAN-in-logs scan tests. Target > 85%
  coverage; contract tests against the network integration. Keep the §8 traceability
  matrix in `specification.md` current.

## Security constraints
- Secrets via environment/secret manager only — never in files or logs.
- No sensitive card data in fixtures, examples, or documentation.
- Validate and bound all inputs; explicit, machine-readable error codes.

## Edge-case handling expectations
- Treat the table in `specification.md` §7 as the minimum set to address.
- Network calls can fail or be slow: timeouts, bounded retries, and a
  `pending_network` compensating path with a maximum pending age — never silently
  diverge from the network. Restrictive actions never fail because of the network.

## How the AI should behave here
- Be terse and concrete; anticipate needs; flag disagreements inline.
- When asked to change behavior, change the **specification**, not downstream code
  (spec is the source of truth — avoid documentation drift).
- Do not introduce code into this homework directory.
