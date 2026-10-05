# CLAUDE.md — Editor / AI rules for this project

Project behavior rules for Claude Code (and compatible agents) working in
`homework-3/`. This is the single editor-rules set for the project (the `.claude/`
option from the assignment).

## What this project is
A **specification-only** package for a virtual corporate card lifecycle feature.
Deliverables are Markdown docs. **Do not write application code, APIs, or UI here.**

## Working style
- Be concise and direct. Suggest solutions I didn't ask for when they help. Treat me
  as an expert. Flag disagreements rather than agreeing by default.
- Use simplified technical English. Avoid double dashes in prose.
- When logic or requirements change, edit `specification.md` — it is the source of
  truth. Keep `agents.md` and this file in sync; do not let docs drift.

## Spec conventions to enforce
- Keep the layered structure: high-level objective → mid-level objectives →
  non-functional & policy → implementation notes → context → low-level tasks, plus
  edge cases, verification, and performance.
- Every low-level task must trace to a mid-level objective (M1 to M9). Keep the
  traceability matrix in §8 current when objectives, tasks, edges, or tests change.
- Money is integer minor units + ISO 4217 — never floats, even in examples.
- No real or realistic card numbers / PII anywhere, including samples.

## Domain guardrails (must hold in any future implementation)
- Never store, log, or return full PAN / CVV / expiry; token reference + last four only.
  Card details are shown only in the processor-hosted display via a reveal session.
- Authorize every mutating action at the company boundary (`card:manage`), deny by
  default, no cross-tenant access. Other-company card ids return 404, not 403.
- Card state changes only via the allowed transitions; `cancelled` and `expired` are
  terminal for spend.
- Safe direction rule: freeze, cancel, expire, and limit decrease apply locally and
  never wait for the network. Unfreeze and limit increase wait for confirmation.
- Reconciliation never re-enables a card: it converges to the network only when the
  network is more restrictive.
- All mutations idempotent; `issue` also needs a permanent `client_reference`. Mask PII
  in logs; attach a `correlation_id` everywhere.
- State change and its event are committed together (outbox). No change without an
  event, no event without a change.

## Quality gates
- A change is "done" only when the spec stays internally consistent: objectives,
  tasks, edge cases, verification, and performance targets still line up.
- Prefer brevity, concrete commands, explicit rules, and references over prose.
