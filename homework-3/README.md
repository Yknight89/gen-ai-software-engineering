# 📐 Homework 3: Specification-Driven Design — Virtual Card Lifecycle

> **Student Name**: Adewale (Wale) Adetiba
> **Date Submitted**: 2026-10-05
> **Framework used**: Superpowers (spec-driven development)
> **AI Tools Used**: Claude (Cowork), Claude Code + Superpowers plugin

---

## 📋 Summary

This homework delivers a **specification package** — documentation only, no code — for
a **virtual corporate card lifecycle** feature: issuing a virtual card, controlling it
(spending limits, freeze/unfreeze), and retiring it (cancel), all in a regulated,
auditable, API-first context. The domain was chosen deliberately: it maps to
corporate-card infrastructure and exercises the hard parts of a finance feature —
state machines, authorization boundaries, idempotency, audit trails, and
reconciliation with an external card network.

## 📁 Deliverables

| File | Purpose |
|------|---------|
| `specification.md` | The layered specification — the core deliverable |
| `agents.md` | AI guidelines: stack, domain rules, testing, security, edge cases |
| `CLAUDE.md` | Editor/AI rules set for project behavior (the `.claude/` option) |
| `README.md` | This summary and rationale |

## 🧱 Why this spec structure

The specification follows the assignment's layered decomposition so requirements are
**traceable from vision down to implementable slices**:

1. **High-level objective** — one crisp outcome plus an explicit scope boundary, so
   it's clear what is *not* being built (no auth-engine, no ledger).
2. **Mid-level objectives** — observable, testable "what succeeds" statements, each
   later referenced by the low-level tasks and the §8 traceability matrix
   (`M1`–`M9`).
3. **Non-functional & policy** — security, privacy, audit, reliability, and latency,
   because in a regulated finance feature these *are* requirements, not extras.
4. **Implementation notes** — the rules (idempotency, money as minor units, error
   semantics, eventing, network-failure handling) that keep an implementation honest
   without prescribing code.
5. **Context (beginning/ending)** — the concrete workspace state, services, and data
   stores before and after, so an implementer knows the boundaries.
6. **Low-level tasks** — granular slices, each tagged with the mid-level objective it
   serves, giving full goal-to-task traceability.

Three cross-cutting concerns are integrated throughout rather than bolted on:
**edge cases & failure modes** (§7 table), **verification** (§8, tied back to
objectives), and **expected performance** (§9, measurable targets).

## 🏛️ Industry best practices applied

- **Spec-driven / "specify before build"** — a single source of truth that logic
  changes flow into, avoiding documentation drift (`specification.md`; drift guardrail
  in `CLAUDE.md`).
- **Explicit state machine** over ad-hoc status fields — transitions are the only way
  state changes (`specification.md` §2, §4, §6 task 2).
- **Idempotency keys** for safe retries on all mutations (`specification.md` §4, §7
  rows 9–10).
- **Audit-by-design & least-data** — immutable event trail, 7-year retention, no PAN
  at rest, PII masking (`specification.md` §3; `agents.md` domain rules).
- **Tenancy isolation / deny-by-default authorization** at the company boundary
  (`specification.md` §3, §6 task 9).
- **Reconciliation with the external system of record** to detect divergence, with
  direction rules so it never re-enables a card (`specification.md` §8).
- **Safe direction rule** — risk-reducing actions apply locally and never wait for the
  network; risk-increasing ones fail closed (`specification.md` §3, §4).
- **Transactional outbox** for audit consistency, and **PCI scope reduction** through
  a processor-hosted reveal (`specification.md` §3, §4).
- **Measurable NFRs** — latency percentiles, rate limits, and time-to-consistency
  instead of vague "fast" (`specification.md` §9).

## 🔧 How this was produced

Drafted using the **Superpowers** spec-driven workflow (brainstorm → write-plan →
specification), keeping strictly to documentation. The draft was then pressure-tested
in a brainstorming session focused on edge cases, failure modes, and verification. The
resulting decisions are recorded at the end of `specification.md`. The `agents.md` and `CLAUDE.md`
files encode the project's guardrails so any future implementation stays within the
domain and security constraints defined here.

<div align="center">

*Completed as part of the AI-Assisted Development course. Specification only — no code.*

</div>
