# ROADMAP — Gaps and Deferred Work

This document tracks known limitations, deferred features, and work items that affect the engine
and/or the UX (`cosmetic-pif-ux`). It is the **canonical cross-repo knowledge home** (together with
`validation/log.yaml`); the UX repo links here by **GitHub URL**, not a relative path (Finding R7).

## Current State / Handoff (Finding R9)

> Update this block at the end of every session so a fresh Claude instance (or teammate) can resume
> without prior context. Read live SHAs from `git log -1` here and the `@<sha>` pin in
> `cosmetic-pif-ux/requirements.txt`.

- **Active branch (both repos):** `claude/epic-mccarthy-nW68A` (authoritative per both `CLAUDE.md`).
  Ignore other harness-suggested branches.
- **In-flight task:** implementing the 11 integration-review findings (G1, G2, R1–R9) from
  `INTEGRATION_STRATEGY.md`, engine-first. Engine side (R1–R5 contract/warnings/provenance, R8 log
  guard, CI) lands first; UX consumes the new contract after the pin bump.
- **Pin reconciliation:** UX `requirements.txt` lagged engine HEAD (`@88eaea4`); it is bumped to the
  new engine SHA as part of this work. G1 CI now fails loudly on future skew.
- **Unresolved decisions:** the two pending regulatory fixes (`normalized_concentrations`, Art.19(1)(g)
  allergen placement — see `cosmetic-pif-ux/docs/ENGINE_HANDOFF.md`) are **NOT yet landed** and are
  out of scope for the findings work; decide whether to land them next.

**Current state:**
- ✅ Engine: 210 tests pass; validated against 1 product (SK5071025 Beard Oil)
- ✅ UX: deployed on Railway; integrates with engine via direct Python import
- ✅ Findings A–D logged in `validation/log.yaml` and fixed / documented
- ✅ Findings E–F logged and marked deferred / flagged for assessor
- ⚠️ **Gaps below must be closed for production readiness**

**Notation:**
- **(E)** = affects engine; **(U)** = affects UX; **(E+U)** = both repos need updates
- `validation/log.yaml:E` = update engine's findings; `cosmetic-pif-ux/CLAUDE.md` = update UX docs

---

## Open Findings (from validation/log.yaml)

### Finding E — BHT (Annex III/325) fragrance secondary table **(E)**
**Status:** deferred  
**Severity:** medium  
**What:** IFRA certificates have a secondary restricted substances table (1 ppm limit) that the engine ignores. BHT at 0.5882% in fragrance → 0.01765% in product **exceeds leave-on threshold (0.001%)** and should be declared in INCI.

**Work:**
- [ ] Model `fragrance_restricted_substances` list in `RawMaterial` / `FormulaLine`
- [ ] Parse from IFRA certificate secondary table in extraction
- [ ] Add BHT + other secondary Annex III substances to `DECLARABLE_ALLERGENS` (with proper thresholds)
- [ ] Modify `generate_inci()` to include fragrance-carried restricted substances after Parfum
- [ ] Add regression test in `tests/test_allergen_db_coverage.py` for secondary table substances
- [ ] Update `validation/log.yaml` status to `fixed` + commit SHA when done

**Affects:** Engine core logic + extraction + tests  
**Blocks:** Full regulatory compliance for fragrance-based products

---

### Finding F — Safrole (Annex II/360) trace-level flagging **(E+U)**
**Status:** documented; flagging automation deferred  
**Severity:** low  
**What:** Safrole (prohibited substance, Annex II) present at 0.000087% in product — below all thresholds but **must be flagged to the qualified assessor** in CPSR Part B.

**Current behavior:** Engine handles concentration correctly; assessor must manually note in CPSR.

**Work:**
- [ ] Add `prohibited_substances` list to `Product` model (Annex II substances actually present, even at trace)
- [ ] Modify `generate_cpsr()` to auto-generate assessor alert paragraph in Part B when prohibited substances present
- [ ] Add test in `tests/test_engine.py::test_prohibited_substance_flagging_in_cpsr`
- [ ] Update UX `app/main.py` to show a warning banner when `/compute` returns CPSR with prohibited substance flags
- [ ] Update both repos' CLAUDE.md to document this auto-flagging behavior
- [ ] Update `validation/log.yaml` status to `fixed` when done

**Affects:** Engine (CPSR generation) + UX (UI warning)  
**Blocks:** CPSR automation — currently manual assessor work

---

## Deferred Features (not in validation/log.yaml yet)

### Real toxicology data (PoD, DAp, correction factors) **(E)**
**Status:** blocked on data acquisition  
**Severity:** critical  
**What:** SED / MoS calculations in `pif_engine/toxicology.py` use **placeholder NOAEL values**, not real data. Cannot validate MoS logic without real `PoD` / `DAp` from toxicology studies.

**Work:**
- [ ] Acquire PoD / DAp / study type / correction factors for 3–5 real products from existing CPSR dosies
- [ ] Refactor `ToxProfile` in `models.py` to accept `(study_type, correction_factors)` tuple
- [ ] Update `toxicology.py` SED/MoS calculations to apply real correction factors (e.g., 3× for 28-day studies)
- [ ] Create test fixtures with real numbers; validate against signed CPSR documents
- [ ] Document in `CLAUDE.md` where the numbers come from + version control

**Affects:** Engine core toxicology module  
**Blocks:** MoS validation; production use for safety-sensitive products

---

### Packaging (TTC / Cramer) module **(E)**
**Status:** scoped but not implemented  
**Severity:** medium  
**What:** Cramer classification and TTC (Threshold of Toxicological Concern) limits for packaging migration (46 / 2.3 µg/kg bw/day) not yet modeled.

**Work:**
- [ ] Create `pif_engine/packaging.py` with Cramer class detection + TTC thresholds
- [ ] Add `packaging_risk` field to `Product` model
- [ ] Integrate into MoS calculation pathway
- [ ] Add tests in `tests/test_packaging.py`

**Affects:** Engine  
**Blocks:** Full risk characterisation for all ingredient types

---

### Multi-product validation suite **(E)**
**Status:** scoped but not implemented  
**Severity:** medium  
**What:** Validated against 1 product (SK5071025). Need 5–10 real, signed CPSR documents to ensure engine logic is generic, not tuned to one case.

**Work:**
- [ ] Collect 5–10 real CPSR dosies (different product types, countries, suppliers)
- [ ] Create fixtures in `tests/fixtures/` for each (named product_<type>_<country>.yaml)
- [ ] Parameterized test in `tests/test_fixtures_parametric.py` that validates INCI + allergen count for each
- [ ] Document each finding (if any divergence from real CPSR) in `validation/<PRODUCT>_FINDINGS.md`
- [ ] Update `validation/log.yaml` with findings for each new product

**Affects:** Engine (test coverage)  
**Blocks:** Confidence that engine is truly generic

---

### CPSR .docx output formatting **(E+U)**
**Status:** not started  
**Severity:** medium  
**What:** Engine generates CPSR text (Part B, Section 1); no .docx output yet. UX shows HTML; assessor must manually copy/format into Word.

**Work:**
- [ ] Use `python-docx` library to generate `.docx` from `generate_cpsr()` output
- [ ] Template: EU Form (CPSR structure per Annex I of Reg. 1223/2009)
- [ ] UX `/compute` endpoint: add optional query param `?format=docx` → return .docx file for download
- [ ] Update `cosmetic-pif-ux/app/main.py` and UX CLAUDE.md

**Affects:** Engine (CPSR module) + UX (route + UI)  
**Blocks:** Direct CPSR file delivery to assessor

---

### Extraction robustness (secondary IFRA table parsing) **(E)**
**Status:** partially done  
**Severity:** medium  
**What:** Extraction currently reads main IFRA allergen table (pdfplumber). Secondary table (restricted substances) is not automatically extracted; Finding E requires this.

**Work:**
- [ ] Extend `pif_engine/extraction/parse.py` to detect and parse 2-table IFRA format
- [ ] Return both main + secondary tables in `extract_drafts()` output
- [ ] Update extraction tests to cover secondary table parsing
- [ ] Document IFRA certificate format in `pif_engine/extraction/README.md` (table structure, CAS matching, units)

**Affects:** Engine extraction layer  
**Blocks:** Finding E implementation

---

## Working items (in progress)

- [ ] Document the official branch (`epic-mccarthy-nW68A`) in both repos' CLAUDE.md ✅ **DONE (2026-06-10)**
- [ ] Update both repos to be synchronized on `epic-mccarthy-nW68A` ✅ **DONE (2026-06-10)**
- [ ] Port Findings E–F to `epic-mccarthy` branch ✅ **DONE (2026-06-10)**

---

## How to use this document

1. **For Claude Code sessions:** Both `cosmetic-pif-poc/CLAUDE.md` and `cosmetic-pif-ux/CLAUDE.md` reference this file. When starting work on a gap, read the "Work" section of that gap.
2. **To mark progress:** Check off items in the "Work" subsection; when all items ✅, change status from `deferred` / `blocked` to `fixed`, add commit SHA to `validation/log.yaml`, and update both repos' CLAUDE.md if UI changes are needed.
3. **PR template:** When opening a PR for a gap, link the relevant finding/feature and the work items completed.

---

## Verification checklist for each closed gap

Before marking a gap as fixed:
1. All work items checked ✅
2. New tests pass: `python3 -m pytest tests/ -v`
3. UX tests pass (if affected): `cd ../cosmetic-pif-ux && pytest tests/ -v`
4. Update `validation/log.yaml` status + commit SHA
5. Update CLAUDE.md in affected repos (note new feature / behavior)
6. Commit with message: `fix(validation): close Finding [A-F] — [description]`
7. Push to `claude/epic-mccarthy-nW68A`
8. Both repos aware (if E+U gap, update CLAUDE.md in both)
