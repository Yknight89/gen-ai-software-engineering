# Specification: Virtual Card Lifecycle Management

> **Feature**: Issue, control, and retire virtual corporate cards
> **Author**: Adewale (Wale) Adetiba
> **Framework**: Superpowers (spec-driven development, specification only, no code)
> **Status**: Revised after pressure-test review (see "Design decisions" at the end)

---

## 1. High-Level Objective

Enable an authorized company administrator to **issue, control, and retire virtual
corporate cards** through their lifecycle, from creation, to active spending under
policy limits, to freezing, expiry, and permanent cancellation. Every state change must
be auditable, authorized, and reconcilable against the card network. Risk-reducing
actions (freeze, cancel, limit decrease) must take effect immediately and must keep
working when the network is slow or down.

**Scope boundary**
- **In scope**: the lifecycle state machine of a *virtual* card, spending-limit
  configuration, bulk freeze, a secure-reveal session for card details, and the
  audit/event trail for each transition.
- **Out of scope**: physical card manufacturing/shipping, the authorization engine
  that approves individual purchases in real time, ledger/accounting posting, rewards,
  FX, and cardholder offboarding workflows. These are adjacent systems this feature
  *integrates with* but does not implement. The assumptions this feature makes about
  them are listed in §5.

---

## 2. Mid-Level Objectives (observable, testable "what")

Each is phrased so success is observable without reference to implementation.

1. **Issue a card (M1)**: An admin can create a virtual card scoped to a cardholder,
   with a caller-supplied `client_reference`, a currency, an initial spending limit, and
   an optional expiry. The card is created in `pending_issuance` and moves to `active`
   with a network token reference and last four digits. If the network answers within
   the issue timeout the caller gets the `active` card (`201`). Otherwise the caller
   gets `202` with `pending_issuance`, and the card is completed or cancelled by
   reconciliation.
2. **Enforce a card state machine (M2)**: A card can only move along the allowed
   transitions in §4. Any other transition is rejected with `invalid_transition` and a
   clear reason. Repeating an action that already holds (freeze on `frozen`, cancel on
   `cancelled`) is an explicit no-op success.
3. **Adjust spending controls (M3)**: An admin can change a card's spending limit and
   per-period cap (daily/monthly) while the card is `active` or `frozen`. A decrease
   applies at local commit. An increase applies only after network confirmation. An
   increase above the company's approval threshold also needs a second approver.
   Changes affect subsequent authorizations only.
4. **Freeze / unfreeze (M4)**: An admin can freeze an active card, which blocks new
   authorizations at local commit and does not wait for the network. An admin can
   unfreeze a frozen card, which takes effect only after network confirmation. Until
   then the card stays frozen.
5. **End of life: cancel and expire (M5)**: An admin can permanently cancel a card. A
   card also moves to `expired` when its expiry passes. Neither `cancelled` nor
   `expired` can return to `active`. Sensitive residuals are erased after the network
   confirms the end of life.
6. **Produce an auditable history (M6)**: Every lifecycle action yields an immutable
   audit event (who, what, when, before→after, correlation id) retrievable by
   compliance. Denied attempts are recorded as separate security events.
7. **Reconcile with the network (M7)**: The system detects, classifies, and resolves
   divergence between its own card state and the network's reported state, in the
   direction that keeps the card safe (see §8).
8. **Read a card and its history, and reveal card details securely (M8)**: An
   authorized admin can read a card, list its history, and request a short-lived,
   single-use reveal session. The session lets the cardholder view card details in the
   processor-hosted display. This service never handles PAN, CVV, or expiry.
9. **Bulk freeze (M9)**: An admin can freeze many cards in one request, by explicit
   card ids or by cardholder/admin scope, with a per-card result. This supports an
   emergency response such as a credential breach.

---

## 3. Non-Functional & Policy Requirements

**Safe direction rule (central design principle)**
- *Restrictive* actions are freeze, cancel, expire, and limit decrease. They are
  acknowledged at local commit, are authoritative for blocking at once, and are pushed to
  the network with retries. They never wait for the network and are never blocked by
  `pending_network`.
- *Permissive* actions are unfreeze and limit increase. They fail closed. They take
  effect only after the network confirms, and are rejected with `operation_pending`
  while any other network operation on the card is unconfirmed.
- Local card state is the source of truth for blocking spend. The authorization
  engine's obligation to read it is stated in §5.

**Security**
- All lifecycle actions require an authenticated admin principal with an explicit
  `card:manage` entitlement scoped to the owning company. Approving a large limit
  increase needs `card:approve`, held by a different principal than the requester.
- Entitlement is evaluated at request start and re-checked inside the commit.
  Revocation mid-request results in `not_authorized`.
- Full PAN / CVV / expiry are never stored, logged, or returned by this service. Only a
  network token reference and the last four digits are kept. Card details are visible
  only in the processor-hosted display opened through a reveal session. The service
  is therefore out of PCI DSS scope for cardholder data, and this must hold for every
  response, log line, and event.
- All mutating actions are authorized at the company boundary, enforced on every
  request with deny-by-default. A card id from another company returns
  `card_not_found` (404), not `not_authorized`, so card existence does not leak.
  `not_authorized` (403) is used only for a missing entitlement within the caller's own
  company.

**Privacy & data protection**
- Cardholder PII is minimized to what the feature needs (an opaque cardholder
  reference, not a full profile) and is masked in all logs (`mask PII in all logs`).
- Audit records carry only opaque ids (actor, company, card, cardholder reference).
  Erasing the PII mapping therefore does not alter audit records, and the audit
  retention below stays compatible with erasure duties.
- Erasure of residual sensitive fields starts only after the network confirms the card
  is cancelled or expired, and completes within the retention window.

**Auditability and integrity**
- **Outbox invariant**: there is never a state change without an event, and never an
  event without a state change. The state change and its audit/domain event are
  committed in one local transaction. A relay then delivers them at least once to the
  append-only audit store and the event bus. Consumers deduplicate on `event_id`.
  Relay lag is monitored and alerted.
- Audit records are append-only and tamper-evident (each record includes the hash of
  the previous record for its card, or the store is write-once). They are independently
  queryable from the operational store.
- Retention: audit records are kept **7 years from the event timestamp**. Operational
  card records are kept for the card's life plus the retention window.
- Idempotent no-ops (§4) emit no event. Denied attempts emit an `access_denied`
  security event, which is not counted as a lifecycle action.

**Reliability**
- All mutating operations are **idempotent** (see §4), so retries never double-apply.
- A network failure never fails a restrictive action. The card is restricted locally
  and marked `pending_network` until the network confirms (§4, §8).

**Latency, availability, and rate-limit targets**: see §9.

---

## 4. Implementation Notes (rules, not code)

**Statuses and sub-status**
- `status`: `pending_issuance`, `active`, `frozen`, `expired`, `cancelled`.
- `sub_status`: `pending_network` or none. It records an unconfirmed network operation
  and a `pending_action` (`freeze`, `unfreeze`, `limit_decrease`, `limit_increase`,
  `cancel`, `issue`) and a `pending_since` timestamp.

**State transitions (explicit allow-list; the only way card state changes)**

| From | To | Notes |
|------|----|-------|
| (none) | `pending_issuance` | issue accepted |
| `pending_issuance` | `active` | network token obtained |
| `pending_issuance` | `cancelled` | issuance failed or aborted (reason recorded) |
| `active` | `frozen` | restrictive; effective at local commit |
| `frozen` | `active` | permissive; effective only after network confirmation |
| `active`, `frozen` | `expired` | expiry reached |
| `active`, `frozen`, `expired` | `cancelled` | terminal; `expired`→`cancelled` triggers erasure and network cancel |
| `frozen` | `frozen` | no-op success on repeat freeze; no event |
| `cancelled` | `cancelled` | no-op success on repeat cancel; no second erasure |

Everything else returns `invalid_transition`. A limit change on a status that does
not allow it returns `invalid_state`, because it is not a transition.

**Unfreeze and limit increase pending confirmation**: the card keeps `status = frozen`
(or the old limit) with `sub_status = pending_network` until the network confirms, then
the change is applied and an event is emitted. If the network confirms nothing within
the maximum pending age (§9), an alert fires and reconciliation takes over. A restrictive
action always supersedes a pending permissive one.

**Idempotency and duplicate prevention**
- Every mutating endpoint accepts an `Idempotency-Key`, scoped to
  `company + operation + key`. The stored fingerprint covers the normalized body and the
  target card id. Keys are retained ≥ 24h.
- A replay with the same key and body returns the original result and does not count
  against rate limits. The same key with a different body returns `409
  idempotency_conflict`. A second request while the first is still running returns `409
  request_in_progress`.
- `issue` additionally requires a `client_reference`, unique per company for the life of
  the data and enforced by a database constraint. Reuse with the same body returns the
  original card. Reuse with a different body returns `409 idempotency_conflict`. This
  prevents duplicate cards after the key window expires.

**Concurrency**
- Reads return a card `version`. Limit changes, unfreeze, and approvals must send it
  (`If-Match`). A stale version returns `412 version_conflict`. The server never
  retries on the caller's behalf, because a stale intent is not safe to replay.
- Freeze, cancel, and bulk freeze are commutative and safe-direction, so they are exempt
  from the version check.

**Money handling**: all amounts use a minor-unit integer (no floats) with an explicit
ISO 4217 currency, stored as `{amount_minor, currency}`. The currency is fixed at
issue. The per-period cap uses UTC day and month boundaries. A limit lowered below
spend already made applies to new authorizations only. It is neither rejected nor
applied retroactively.

**Approval rule**: a limit increase above the company's configured threshold (in minor
units per currency) creates an approval request. A different principal with
`card:approve` approves it, within 24h, after which the request lapses. The requester
can never approve their own request.

**Reveal session**: `card:manage` or the card's own cardholder may request a session
for an `active` card. The service returns a single-use token with a TTL of 60 seconds.
The token opens the processor-hosted display and contains no card data. Reuse,
expiry, or a card that is not `active` returns `forbidden_reveal`. Every request is
audited.

**Bulk freeze**: accepts up to 1,000 explicit card ids, or a cardholder/admin scope.
It is idempotent per card and returns a per-card result (`frozen`, `already_frozen`,
`not_found`, `invalid_transition`). A failure on one card does not stop the others.

**Error semantics**: consistent machine-readable error codes with a human-readable
message and a `correlation_id`. `4xx` for caller faults, `5xx` only for genuine
server/network faults. Catalogue:

| Code | HTTP | Meaning |
|------|------|---------|
| `card_not_found` | 404 | unknown card, or card belongs to another company |
| `not_authorized` | 403 | missing entitlement within own company |
| `invalid_transition` | 409 | status change not on the allow-list |
| `invalid_state` | 409 | operation not valid in the card's current status |
| `limit_invalid` | 422 | zero, negative, or malformed limit or cap |
| `currency_not_enabled` | 422 | company is not enabled for the currency |
| `expiry_invalid` | 422 | expiry in the past or beyond the network maximum |
| `idempotency_conflict` | 409 | same key or client_reference, different body |
| `request_in_progress` | 409 | same key still running |
| `version_conflict` | 412 | stale `If-Match` version |
| `operation_pending` | 409 | permissive action while a network operation is unconfirmed |
| `approval_required` | 202 | limit increase waiting for a second approver |
| `forbidden_reveal` | 403 | reveal session reuse, expiry, or card not `active` |
| `rate_limited` | 429 | rate limit exceeded (§9) |
| `network_unavailable` | 503 | only for operations that cannot proceed locally |

**Eventing**: each transition emits a domain event
(`card.issued|frozen|unfrozen|limit_changed|expired|cancelled|reveal_requested`)
carrying before→after and a correlation id. Events are written through the outbox
(§3) and are the audit trail.

**Network calls**: potentially slow and failure-prone. They are wrapped with timeouts,
bounded retries with backoff, and a maximum pending age (§9). When a restrictive
action commits locally but the network call fails, the card is restricted locally,
parked as `pending_network`, and surfaced to reconciliation. The caller receives `202`
with the sub-status, never a failure.

**Conventions**: snake_case fields; UTC ISO-8601 timestamps; all IDs are opaque,
non-sequential strings; every response carries the `correlation_id`.

---

## 5. Context

**Beginning (workspace state before)**
- A company and at least one admin principal with `card:manage` already exist. A second
  principal with `card:approve` exists where large increases are used.
- Company configuration holds the enabled currencies and the approval threshold.
- An identity/authorization service can validate the principal and entitlement.
- A card-network/issuer-processor integration is available (tokenized issuance,
  freeze/cancel, state query, enumeration of cards issued for the company, and a
  hosted card-details display opened by a session token).
- Data stores exist: an operational store for card records, an append-only audit
  store, and an event bus for domain events.

**Assumptions about adjacent systems (this feature depends on them, does not build them)**
- The authorization engine reads the local card `status` and *effective* limits, with
  staleness of at most 1 second at p99. Without this, a local freeze protects nothing.
- Late clearing, refunds, and chargebacks still post on `cancelled` and `expired`
  cards. Pending holds are not released by this feature.

**Ending (workspace state after)**
- Cards can be moved through their full lifecycle via the specified operations.
- Every transition has produced an immutable audit event and a domain event.
- A reconciliation routine compares local and network state, applies the safe-direction
  rules, and reports divergence.
- No card secrets are persisted or logged anywhere in this service.

**Specific services & data stores touched**
- Identity/AuthZ service (read) · Card network/issuer processor (read+write) ·
  Operational card store (read+write, includes the outbox) · Audit store (append-only) ·
  Event bus (publish).

---

## 6. Low-Level Tasks (tied to mid-level objectives)

> Granular slices. Each names the mid-level objective(s) it serves. No code: these are
> the decomposed units a plan/implementation would pick up.

1. **Define the card domain model** (M1, M3, M8): fields, value objects
   (`SpendingLimit`, `Money`), `status`, `sub_status`, `pending_action`, `version`,
   and `client_reference`.
2. **Define the lifecycle state machine** (M2, M4, M5): the transition allow-list, guard
   conditions, self-transitions, and the single rejection path for invalid transitions.
3. **Specify the issue operation** (M1): inputs, authorization, `client_reference`
   rule, network token request, `201`/`202` behavior, returned shape (no card data).
4. **Specify freeze / unfreeze** (M4): local-first freeze, confirmation-gated
   unfreeze, `operation_pending` rule, network push, audit and event emission.
5. **Specify limit change and approval** (M3): validation, decrease vs increase
   timing, second-approver flow, "applies to future authorizations only".
6. **Specify cancel and expiry** (M5): terminality, expiry job, erasure after network
   confirmation, network cancel, post-conditions.
7. **Specify bulk freeze** (M9): scopes, size limit, per-card results, partial failure.
8. **Specify read, history, and reveal session** (M8): read shape, history query,
   session issuance, TTL and single-use rules.
9. **Specify the audit event contract and outbox** (M6): event schema, chaining,
   outbox relay and dedupe, `access_denied` events, query surface.
10. **Specify the reconciliation routine** (M7): cadences, the direction rules in §8,
    divergence classes, the surfaced report, and orphan handling.
11. **Specify authorization & tenancy enforcement** (M1-M5, M8, M9): where the
    company-boundary, `card:manage`, and `card:approve` checks sit, the 404-vs-403 rule.
12. **Specify idempotency and concurrency handling** (M1, M3, M4, M5, M9): key storage,
    scope, replay, in-flight and conflict rules, `If-Match` versioning.
13. **Specify the error catalogue** (all objectives): code list, HTTP mapping, message
    conventions.
14. **Specify the authorization-engine integration contract** (M4, M5): what local state
    is exposed, the staleness bound, and the fail-safe behavior.
15. **Specify observability** (all objectives): the metrics and log fields needed to
    measure the §9 targets and to investigate a divergence, including relay lag and
    pending age.

---

## 7. Edge Cases & Failure Modes

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| 1 | Issue with a limit of 0 or negative | Reject `limit_invalid`; no card created |
| 2 | Issue in a currency the company isn't enabled for | Reject `currency_not_enabled` |
| 3 | Issue with expiry in the past or beyond the network maximum | Reject `expiry_invalid` |
| 4 | Issue: network does not answer within the timeout | `202`, card `pending_issuance`; reconciliation completes it or cancels it with reason `issuance_failed`; the `client_reference` stays reserved |
| 5 | Issue: same `client_reference`, same body / different body | Original card returned / `409 idempotency_conflict` |
| 6 | Freeze an already-frozen card | No-op success, same end state, no event |
| 7 | Cancel an already-cancelled card | No-op success; no second erasure, no new event |
| 8 | Unfreeze a cancelled or expired card | Reject `invalid_transition` (terminal) |
| 9 | Freeze commits locally, network call times out | Card is `frozen` and blocks spend now; `pending_network`; `202`; retries continue; alert when pending age exceeds the maximum |
| 10 | Unfreeze while the network is down | Card stays `frozen`, `pending_network`; becomes `active` only on confirmation |
| 11 | Unfreeze or limit increase while a network operation is unconfirmed | Reject `operation_pending` (409). Freeze and cancel are always accepted |
| 12 | Edit with a stale `version` | Reject `412 version_conflict`; the caller re-reads and decides. Freeze and cancel are exempt |
| 13 | Network is more restrictive than local (e.g. cancelled/expired while local `active`) | Local converges to the network, with an audit event |
| 14 | Network is less restrictive than local (a failed freeze) | Local intent is re-pushed; local never converges down; alert if past max pending age |
| 15 | Card exists at the network with no local record (orphan) | Flag as high severity, restrict (freeze) it at the network, route to human review |
| 16 | Local card (not `pending_issuance`) missing at the network | Flag as high severity, restrict locally, route to human review |
| 17 | Replay of a mutating request (same key and body) | Original result returned; applied exactly once; no quota consumed |
| 18 | Same key, different body / same key still in flight | `409 idempotency_conflict` / `409 request_in_progress` |
| 19 | Caller lacks `card:manage` / card belongs to another company | `403 not_authorized` / `404 card_not_found`; both audited as `access_denied` |
| 20 | Entitlement revoked while a request is in flight | Re-check at commit fails; `not_authorized`; nothing applied |
| 21 | Limit change on `pending_issuance`, `expired`, or `cancelled` | Reject `invalid_state` |
| 22 | Limit lowered below spend already made | Accepted; applies to new authorizations only |
| 23 | Limit increase above the approval threshold | `202 approval_required`; a different `card:approve` principal approves within 24h or the request lapses; self-approval rejected |
| 24 | Expiry reached while `active` or `frozen` | Card becomes `expired` (terminal for spend), audited; lag is caught by reconciliation |
| 25 | Many cards issued by one admin | At 50/hour: `429`, alert the compliance role, which owns the review |
| 26 | Emergency: freeze 500 cards after a credential breach | Bulk freeze is exempt from the per-admin limit; per-card results; failures reported, not fatal |
| 27 | Reveal session reused, expired, or requested for a non-`active` card | Reject `forbidden_reveal`; every request audited |
| 28 | Crash between local commit and event publish | Outbox relay publishes after restart; consumers dedupe on `event_id`; no lost or duplicate effect |
| 29 | Audit store or event bus unavailable | State changes still commit (events wait in the outbox); alert on relay lag; no event lost |

---

## 8. Verification

**Test categories**
- **State-machine tests**: every allowed transition succeeds; every disallowed one is
  rejected with `invalid_transition`; self-transitions are no-ops. Include a
  property-based test over random action sequences that checks terminal states stay
  terminal (M2).
- **Safe-direction tests**: with the network down, freeze, cancel, and limit decrease
  succeed locally; unfreeze and limit increase do not take effect (M3, M4).
- **Authorization tests**: cross-tenant (404) and missing-entitlement (403) attempts
  are denied and audited; revocation mid-request (M1-M5, M8, M9).
- **Idempotency and concurrency tests**: replays apply once; conflicts; in-flight
  duplicates; `client_reference` reuse; stale-version rejection; parallel freeze and
  limit change.
- **Money/limit validation tests**: zero, negative, mismatched currency, below-spend
  limits, threshold approval, self-approval rejected (M3).
- **Audit and outbox tests**: each action emits exactly one event with correct
  before→after; crash between commit and publish; relay redelivery is deduplicated;
  chain verification detects tampering (M6).
- **Reconciliation tests**: each divergence class in the rules below is seeded and
  resolved in the correct direction; orphans are restricted (M7).
- **Failure-injection tests**: network timeout, partial outage, slow responses
  (edges 4, 9, 10).
- **Data-protection tests**: an automated scan proves no PAN, CVV, or expiry appears in
  any response, log, event, fixture, or store (M1, M8).
- **Contract tests**: against the network sandbox for issue, freeze, cancel, state
  query, enumeration, and the reveal session.

**Acceptance criteria (traceable to objectives)**
- *M1*: Issuing returns `active` (`201`) or `pending_issuance` (`202`) with a token
  ref and last four. No PAN in any response or store. A repeated `client_reference`
  never creates a second card.
- *M2*: 100% of the transition matrix behaves per the allow-list in tests.
- *M3*: A decrease takes effect at commit. An increase takes effect only after network
  confirmation. An above-threshold increase never applies without a different approver.
- *M4*: With the network unreachable, a freeze blocks spend at local commit and
  returns `202`. An unfreeze leaves the card `frozen`. Local blocking is visible to
  the authorization engine within 1 s p99.
- *M5*: After cancel or expiry, the card cannot be reactivated. Secrets are erased
  only after network confirmation, and are non-retrievable afterward.
- *M6*: For any sequence of N lifecycle actions, exactly N audit events exist with
  matching correlation ids. Denied attempts appear only as `access_denied` events.
- *M7*: Every seeded divergence is classified and resolved per the rules below. The
  report contains no unexplained divergence.
- *M8*: A reveal session works once within its TTL and never contains card data. A
  cross-company read returns 404.
- *M9*: Freezing N cards returns N per-card results. The operation is not throttled
  by the per-admin limit, and a replay changes nothing.

**Reconciliation rules**

Restrictiveness order: `cancelled`/`expired` > `frozen` > `active`; for limits, lower
is more restrictive.

| Class | Condition | Action |
|-------|-----------|--------|
| network-ahead | network more restrictive than local | converge local to network; audit event |
| local-ahead | local more restrictive than network | re-push local intent; alert past max pending age |
| pending-network | unconfirmed operation within max age | explained; recheck every minute |
| pending-overdue | unconfirmed operation past max age | a **failed check**; page on-call |
| orphan | at the network, absent locally | restrict at network; high-severity flag; human review |
| missing-at-network | local card (not `pending_issuance`) absent at network | restrict locally; high-severity flag; human review |

**Cadence**: cards with `pending_network` are checked every minute. All other non-
terminal cards are checked at least every 24h, and on demand. A daily enumeration of
network-issued cards per company detects orphans. The pass condition is zero
unexplained divergences and zero `pending-overdue` cards.

**Traceability matrix**

| Objective | Tasks (§6) | Edge cases (§7) | Test categories (§8) |
|-----------|-----------|-----------------|----------------------|
| M1 Issue | 1, 3, 11, 12, 13 | 1-5, 17-19, 25 | state machine, authorization, idempotency, money, data-protection, contract |
| M2 State machine | 2, 13 | 6-8, 21 | state machine (incl. property-based) |
| M3 Limits | 1, 5, 11, 12, 13 | 11, 12, 21-23 | money, safe-direction, idempotency, concurrency |
| M4 Freeze/unfreeze | 2, 4, 12, 14 | 6, 9-11 | safe-direction, failure-injection, state machine |
| M5 Cancel/expire | 2, 6, 12, 14 | 7, 8, 24 | state machine, reconciliation, data-protection |
| M6 Audit | 9, 15 | 19, 20, 28, 29 | audit and outbox |
| M7 Reconcile | 10, 15 | 13-16 | reconciliation, failure-injection |
| M8 Read/reveal | 1, 8, 11, 13 | 19, 27 | authorization, data-protection, contract |
| M9 Bulk freeze | 7, 11, 12 | 17, 26 | safe-direction, idempotency |

---

## 9. Expected Performance

| Metric | Target |
|--------|--------|
| Issue card, API work excluding network | p95 < 300 ms, p99 < 600 ms |
| Issue card, end to end including network | p95 < 3 s; after a 10 s timeout the caller gets `202` |
| Freeze / unfreeze request acknowledged | p95 < 250 ms (local commit) |
| Freeze visible to the authorization engine | ≤ 1 s p99 after local commit |
| Freeze confirmed by the network | < 5 s p95, < 30 s p99 |
| Maximum pending age (`pending_network`) | 5 minutes, then alert and failed check |
| Bulk freeze, 1,000 cards | acknowledged p95 < 5 s; every card result returned |
| Lifecycle read (get card / history) | p95 < 150 ms |
| Reveal session issued | p95 < 200 ms; TTL 60 s |
| Outbox relay lag | p99 < 5 s; alert at 60 s |
| Reconciliation freshness | `pending_network` every 1 min; other non-terminal cards ≥ once / 24h |
| Availability, local lifecycle operations (acknowledged at local commit) | 99.9% monthly |
| Network confirmation SLO (separate measure) | 99% of freezes confirmed within 30 s |
| Rate limit, risk-increasing mutations (issue, unfreeze, limit increase) | 100 / minute per admin (burst 20), excess `429` |
| Rate limit, card issuance | 50 / hour per admin (fraud guard); breach blocks and alerts compliance |
| Restrictive actions (freeze, cancel, bulk freeze) | exempt from the per-admin limit; backstop of 1,000 / minute per company |
| Reveal sessions | 10 / minute per card |

The audit/outbox guarantee is an invariant (§3), not a performance target.

---

## Design decisions (from the pressure-test review)

| Decision | Choice | Reason |
|----------|--------|--------|
| Network slow or down | Restrictive actions apply locally and never wait; permissive actions wait for confirmation | A freeze exists to stop fraud, so it must not depend on the network |
| Reconciliation direction | Converge to the network only when it is more restrictive; otherwise re-push local intent | Never let reconciliation re-enable a card |
| Card details | Never handled by this service; processor-hosted reveal via session token | Keeps the service out of PCI scope and keeps M1 consistent |
| Expiry | `expired` is terminal, can still move to `cancelled` for erasure | Records end of life and keeps erasure triggered |
| Audit consistency | Transactional outbox with at-least-once relay | A single transaction cannot span two stores |
| Duplicate issuance | Permanent `client_reference` per company | A 24h key window alone allows duplicates |
| Rate limits | Restrictive actions exempt; bulk freeze added | A breach response must not be throttled |

<div align="center">

*Homework 3: Specification-Driven Design. Specification only; no implementation code.*

</div>
