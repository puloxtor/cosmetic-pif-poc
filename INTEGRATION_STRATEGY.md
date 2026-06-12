# Integration Strategy — `cosmetic-pif-poc` (engine) ↔ `cosmetic-pif-ux` (UX)

> **Scope.** How the deterministic PIF/CPSR engine and the FastAPI/HTMX UX
> integrate: the shared contract, synchronization, validation/warnings, the
> knowledge/learning loop, and cross-session handoff. Grounded in the actual
> code, not a generic template.
>
> **Canonical home.** This file lives in the engine repo (single source of
> truth for regulatory logic *and* cross-repo knowledge). The UX repo should
> link to it by GitHub URL, not a relative path (see §6, R7).

---

## 0. Reality check (the architecture, stated plainly)

This is **not** two networked services exchanging JSON over REST/gRPC/events
with shared mutable state. It is:

> The engine (`cosmetic-pif-poc`) is a **deterministic Python package**,
> installed into the UX (`cosmetic-pif-ux`) **pinned to a git commit SHA**
> (`requirements.txt`: `pif-engine[extraction] @ git+…@<SHA>`), and consumed
> via **in-process Python `import`** through a single bridge module,
> `app/engine.py`. There is no network boundary and no shared database.

This is the correct shape for a 1–2-user regulatory tool, and it satisfies the
hardest constraints by construction:

- **No data duplication** — the UX is stateless (one session = one product),
  stores no calculation results, and re-derives everything per request.
- **Single source of truth** — `app/engine.py` is the *only* module that may
  import `pif_engine`; the UX contains zero regulatory logic.
- **Deterministic & auditable** — same input → same output (CLAUDE.md top
  rule). LLMs only *suggest* (extraction/matching/canonicalization); a human
  confirms before any number enters a dossier.

Adding HTTP between the repos would **reintroduce** the version-skew and
duplication risks we are trying to eliminate. This strategy hardens the
existing contract instead.

---

## 1. Shared Data Contract

The contract is three layers, not a wire format:

| Layer | What it is | Owner | Defined in |
|---|---|---|---|
| **A. Input schema** | Product YAML (`product`, `raw_materials[]`, `claims[]`) | Engine | `products/TEMPLATE.yaml`, parsed by `build_product()` |
| **B. Public API surface** | The importable symbols | Engine | `pif_engine/__init__.py` `__all__` |
| **C. Result shape** | The dict returned to the UX | Engine | `compute_from_yaml()` in UX `app/engine.py` |

**B — stable public symbols (do not break without a coordinated UX update):**

```python
__version__, build_product, consolidated_concentrations, generate_inci,
allergens_to_declare, calculate_allergens, generate_cpsr          # pif_engine
ALLERGEN_THRESHOLD                                                # pif_engine.allergens
extract_drafts                                                    # pif_engine.extraction.router
to_yaml                                                           # pif_engine.extraction.draft
```

**C — the result contract returned to the browser layer:**

```python
{
  "name": str,                  # engine-owned (may include "(CPNP …)")
  "product_type": str,          # "leave-on" | "rinse-off"
  "warnings": list[str],        # engine-owned — never dropped (see §5)
  "table": [{"inci": str, "pct": float}],   # engine-owned, desc by pct
  "total": float,               # engine-owned
  "sum_ok": bool,               # abs(total-100) <= 0.5
  "inci": list[str],            # engine-owned (Art. 19 order)
  "declared": list[str],        # allergens over threshold
  "allergens": [{"name","cas","conc_pct","threshold_pct","declared"}],
  "cpsr": str                   # optional markdown, engine-owned
}
```

**Data ownership (unambiguous):**

- **Engine owns** every number, rule, INCI name, allergen decision, MoS, claim
  verdict, and warning. All of it.
- **UX owns** presentation and I/O only: upload limits (`MAX_FILES`,
  `ALLOWED_EXT`), document classification (`intake.py`), the non-INCI candidate
  filter at the UX boundary (`filter_candidates`), error humanization
  (`friendly_error`), and the LLM *suggestion* layers (`matching.py`,
  `canonical.py`).
- **Neither owns persistent product state** — there is none, by design.

> **R1 — Formalize the result contract.** The dict in §1.C is built inline in
> `compute_from_yaml`. Promote it to a typed contract in the engine (a
> `@dataclass`/`TypedDict`, e.g. `pif_engine.api.ComputeResult`) and import it
> in the UX, so a breaking change is a type error at install time, not a silent
> `KeyError` in production.

---

## 2. Communication Protocol

There is no message protocol — there are function calls. The two real flows:

```
# Extraction (LLM-assisted, suggestion only)
POST /extract (multipart, ≤20 files × 10MB, PDF/PNG/JPG/WEBP)
  → engine.extract_structured()
  → pif_engine.extraction.router.extract_drafts()
  → [optional Claude vision fallback if no payload + ANTHROPIC_API_KEY]
  → filter_candidates()   # UX boundary: drop non-INCI rows, with a note
  → draft YAML → human reviews/edits

# Computation (deterministic, authoritative)
POST /compute (form: formula=YAML, cpsr=?)
  → engine.compute_from_yaml(yaml_text, include_cpsr)
  → build_product → consolidated_concentrations / generate_inci
                  / allergens_to_declare / allergen_table / generate_cpsr
  → result dict (§1.C) → _results.html
```

**Request/response (the actual contract):**

```
POST /compute   formula=<product YAML>   cpsr=on
→ 200 HTML (_results.html) rendering the §1.C result dict
  OR 200 HTML (_error.html) with friendly_error(exc) — never a 500
```

**Error handling (already strong — keep it):**

- Engine **raises** typed exceptions with regulatory context; it never
  normalizes silently.
- UX **catches at the boundary** and translates via `friendly_error()`
  (rate-limit → wait/use digital PDF; missing API key → manual entry;
  `yaml.YAMLError` → line number; `KeyError` → which field). Raw message kept as
  fallback.
- `/extract` isolates per-file failures (`_process_one`) so one bad file can't
  kill the batch.
- `/match` and `/canonicalize` **never 500** — they degrade to
  `available=False` and fall back to heuristics (correct: they are advisory).

> **R2 — Typed exceptions.** Have the engine raise a small hierarchy
> (`PifInputError`, `PifDataGapError`) instead of bare `ValueError`/`KeyError`,
> so `friendly_error` branches on *type* rather than string-sniffing
> `str(exc)`, which is brittle across engine versions.

---

## 3. State Management Strategy

**Single source of truth:** the engine package, pinned by **immutable git SHA**
in UX `requirements.txt`. That SHA *is* the synchronization mechanism. There is
no runtime state to reconcile, so there are no conflicts to resolve.

**Synchronization is pull-based and explicit, by design:**

1. Engine change lands on the engine repo + tests pass.
2. Engine pushed; new SHA recorded.
3. UX bumps the SHA in `requirements.txt`; if the public API signature changed,
   `app/engine.py` is updated **in the same commit**.
4. `/healthz` and the startup log expose `engine_version` + `engine_pin` so the
   running deployment self-reports exactly which rules it is using.

**Gaps:**

> **G1 — Latent version skew.** `docs/ENGINE_HANDOFF.md` and
> `docs/COMBINED_SESSION_PLAN.md` (UX repo) describe two regulatory fixes
> (`normalized_concentrations`, Art. 19(1)(g) allergen placement) that are
> supposed to land and then bump the pin. `normalized_concentrations` is not yet
> in `__init__.py.__all__`, so those fixes are still pending and the displayed
> label table still uses worst-case (`consolidated_concentrations`).
> **Fix:** a CI check in the UX that imports every symbol it depends on at the
> pinned SHA and fails the build if any is missing — turning "sync" from a
> discipline into a gate.

> **G2 — "Automatic propagation" is intentionally manual.** Auto-upgrading a
> regulatory engine under a signed dossier is unsafe. Bridge the gap with a
> **Dependabot/Renovate** rule on the engine dependency: open a PR on every
> engine push, run the full UX suite, require green + human merge. Propagation
> becomes one-click and *audited*, never silent.

**Conflict resolution rule (regulatory):** when the worst-case view and the
label view diverge (the pending normalization fix), the **safety/MoS path keeps
worst-case** (`consolidated_concentrations`); only the **label/INCI view** is
normalized. The engine is always authoritative over the UX; the UX must never
"correct" an engine number.

---

## 4. Regulatory Rule Engine Design

**Stored** as deterministic Python: thresholds (`ALLERGEN_THRESHOLD` keyed by
`ProductType`), the Annex III declarable set (`DECLARABLE_ALLERGENS` /
`nomenclature.py`, incl. Reg. (EU) 2023/1545), worst-case resolution
(`resolve_amount`: `range`→upper, `at_most`→value, `remainder`→balance),
documentation gates (`check_documentation_gates`), claims (`claims.py`, Reg.
655/2013), MoS (`toxicology.py`).

**Versioned** by `__version__` **plus** git SHA — the SHA is the real version
key.

**Applied** per request, deterministically, with no caching of results.

> **R3 — Embed provenance in every generated document.** `generate_cpsr()`
> stamps `date.today()` but not the engine version/SHA or the thresholds used.
> For a document signed under Article 10 liability, the dossier must state which
> rule set produced it. Add an engine-version + commit + key-thresholds footer
> to the CPSR. **This is the most important compliance gap found.**

> **R4 — Machine-traceable rule provenance.** Rule sources live in code
> comments today. A `pif_engine/regulatory_refs.py` mapping each rule constant
> to its legal citation, surfaced in `/healthz` and the CPSR footer, makes
> "which regulation, which version" queryable.

**Rule deployment workflow (codifies the `ROADMAP.md` process):**

1. Change rule in engine + add a regression test (CLAUDE.md mandates a test for
   new regulatory logic).
2. Log it in `validation/log.yaml` with `category`/`severity`/`status` and a
   `regression_guard` test path.
3. Commit `fix(validation): close Finding X — …`; push; record SHA.
4. Bump UX pin; update `app/engine.py` if the signature changed; update **both**
   `CLAUDE.md` for `(E+U)` items.

---

## 5. Warning & Validation System

| Validation | Where | Mechanism |
|---|---|---|
| Sum ≠ 100%, range/remainder assumptions, unknown allergen, suppressed-from-INCI | **Engine** | `warnings[]` from `build_product`, prefixed ⚠️/ℹ️ |
| Allergen over/under threshold | **Engine** | `allergen_table` / `allergens_to_declare` vs `ALLERGEN_THRESHOLD` |
| Missing CoA/SDS/IFRA, restricted-% exceeded | **Engine** | `check_documentation_gates` → ⛔ BLOCKER in CPSR |
| MoS < 100, claim blocked/needs-evidence | **Engine** | `product_is_safe`, `validate_all_claims` |
| File type/size, too many files | **UX** | `_process_one`, `MAX_*` |
| Non-INCI rows from extraction | **UX boundary** | `filter_candidates` (+ "проверете дали не липсва съставка") |
| Human-readable error text | **UX** | `friendly_error` |

**No silent failures — a first-class principle.** An unrecognized supplier
allergen is surfaced as a warning, never dropped (a silent drop = missing
mandatory label declaration). `suppressed_ingredients` is the *single source*
feeding both the INCI filter and the CPSR audit trail, so nothing vanishes
without an audit line.

> **R5 — Structure the warnings.** `warnings` is `list[str]` with emoji-encoded
> severity (⚠️/ℹ️/⛔). Replace with `list[Warning]` where
> `Warning = {severity, code, message, subject}`. The UX then renders blockers
> red, warnings amber, info collapsible — *deterministically* instead of
> emoji-sniffing. Directly enables deferred **Finding F** (Safrole / Annex II)
> banner.

> **R6 — Escalation rule, explicit.** Any `⛔` documentation gate or `MoS<100`
> must **block** the "Generate CPSR / sign" action in the UX, not just render
> text. Make the blocker state machine-checkable (R5 enables this).

---

## 6. Knowledge & Learning System

The problem-solution log already exists; it needs to be made truly cross-repo.

| Artifact | Role | Location |
|---|---|---|
| `validation/log.yaml` | Machine-readable findings index (A–F): `category`/`severity`/`status`/`fix_commit`/`regression_guard` | engine |
| `validation/schema.md` | Field definitions + enums + workflow + query snippet | engine |
| `validation/<ID>_FINDINGS.md` | Human narrative per product | engine |
| `ROADMAP.md` | Gaps & deferred work, tagged `(E)`/`(U)`/`(E+U)` | engine (referenced by both) |
| `CLAUDE.md` ×2 | Per-repo session context, rules, public API | both |
| `docs/ENGINE_HANDOFF.md`, `docs/COMBINED_SESSION_PLAN.md` | Cross-session task handoffs with exact `file:line` targets | UX |

The `log.yaml` categories (`extraction_failure`, `engine_db_gap`,
`engine_logic_bug`, `test_infrastructure`, `data_error`) make "flag repeated
patterns" queryable. Finding B is the model entry: missing Annex III allergens →
silent drop → `regression_guard` test added so it cannot recur.

**Problem-log entry format (the real version):**

```yaml
- id: B
  category: engine_db_gap
  severity: critical          # would cause a missing mandatory label declaration
  summary: 5 Annex III allergens (Reg. 2023/1545) missing → silently dropped…
  status: fixed
  fix_commit: dedf9b4
  regression_guard: tests/test_allergen_db_coverage.py::test_sk5071025_previously_dropped_allergens
```

> **R7 — Single canonical home for cross-repo knowledge.** The UX references the
> log via a relative path (`../cosmetic-pif-poc/ROADMAP.md`), which only
> resolves when both repos are checked out side-by-side. Make the engine the
> canonical owner of `log.yaml` + `ROADMAP.md` + this file, and have the UX link
> by **GitHub URL**.

> **R8 — Enforce the fix→test loop.** CI rule: any `log.yaml` finding with
> `status: fixed` **must** have a `regression_guard`. Mechanically prevents
> "fixed but can regress" — the failure mode behind Finding C.

---

## 7. Handoff & Continuity Protocol

🚩 **Known friction: conflicting branch instructions across accounts/sessions.**
Three different "official branch" signals have appeared in practice:
`CLAUDE.md` (both repos) + all handoff docs insist on
`claude/epic-mccarthy-nW68A` (where the public API exists); harness sessions
have designated other branches (`keen-sagan-unh3cf`, and a known-wrong
`affectionate-wright`). A fresh instance cannot resolve this from the artifacts
alone — the textbook "information lost on handoff." **Resolution:** treat the
checked-in `CLAUDE.md` as authoritative for branch selection.

**Continuity mechanisms (the good parts):**

- `CLAUDE.md` is auto-loaded at session start in both repos → every instance
  starts with purpose, the deterministic-engine rule, the public API list,
  structure, and test commands.
- `ROADMAP.md` + `validation/log.yaml` carry state between sessions: open,
  deferred, validator, SHA.
- `docs/ENGINE_HANDOFF.md` / `docs/COMBINED_SESSION_PLAN.md` are purpose-built
  cross-account handoffs: paste-ready prompts, exact `file:line` targets,
  sequencing, "report the new SHA back."

**Session-resumption checklist:**

1. Read both `CLAUDE.md`. Confirm the **branch** (resolve the conflict above
   before touching code).
2. `git log -1` each repo; check UX `requirements.txt` pin vs engine `HEAD` —
   **are they in sync?** (See G1.)
3. Read `ROADMAP.md` "Open Findings" + `validation/log.yaml` for `status: open`.
4. Check `docs/*HANDOFF*.md` / `*SESSION_PLAN*.md` for an in-flight task.
5. Run both test suites (engine `pytest`; UX `pytest` + `jest`) to establish a
   green baseline **before** changing anything.
6. On finishing an `(E+U)` item: update `log.yaml`, `ROADMAP.md`, **both**
   `CLAUDE.md`, bump the pin, report the new SHA.

> **R9 — "Current state" header.** Add a top block (here or in `ROADMAP.md`)
> recording, on every session end: active branch, engine SHA, UX pin SHA,
> in-flight task, unresolved decisions. Would have prevented the branch
> ambiguity above.

---

## Recommendations summary

| # | Recommendation | Area | Priority |
|---|---|---|---|
| G1 | CI check: UX imports all pinned engine symbols; reconcile the pending fixes/pin | Sync | High |
| R3 | Embed engine version/SHA + thresholds in every generated CPSR | Compliance | High |
| R5 | Structure `warnings` with machine-readable severity (unblocks Finding F) | Validation | High |
| R6 | Blockers/`MoS<100` block the sign action, not just render text | Validation | High |
| R7 | Engine = canonical home for cross-repo knowledge; UX links by URL | Knowledge | Medium |
| R1 | Typed `ComputeResult` contract imported by the UX | Contract | Medium |
| R2 | Typed engine exception hierarchy for `friendly_error` | Errors | Medium |
| R8 | CI: `status: fixed` requires a `regression_guard` | Knowledge | Medium |
| G2 | Dependabot/Renovate PR on every engine push (audited propagation) | Sync | Medium |
| R4 | `regulatory_refs.py` legal-citation map, surfaced in `/healthz` + CPSR | Compliance | Low |
| R9 | "Current state" handoff header | Continuity | Low |

**Top 3, in order:** (1) reconcile the branch + pin (G1); (2) stamp engine
version/SHA + thresholds into every CPSR (R3); (3) structured warning severity
(R5).
