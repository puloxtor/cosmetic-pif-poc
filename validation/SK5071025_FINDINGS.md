# SK5071025 — Beard Oil (DEMO) — Validation Findings

**Date:** 2026-06-09
**Engine commit validated:** `8164c3d` (the commit the live UX pins) → fixed on this branch.
**Source of truth:** Drive folder `11E_pvH140arlfoDy9_XZFaHAWraWIXKp` (supplier documents).
**Method:** All 9 supplier documents + the IFRA certificate (all 5 pages) were read in
full and the complete dataset was run through the deterministic engine. Allergen data
was taken from the **certificate itself**, not from the test-prompt transcription
(which was found to be incomplete — see Finding D).

---

## Finding A — UX (Haiku) extraction performed poorly. CONFIRMED.

The earlier UX run (screenshot, "PK Peace Oil") extracted only **8 allergens** via the
Haiku vision model:
Citral, Citronellol, Coumarin, Eugenol, Geraniol, Isoeugenol, Limonene, Linalool.

The real IFRA certificate (Symrise 212878 "Peace on Earth") declares **25** allergens
with concentrations. Haiku missed the **three highest-concentration allergens entirely**:

| Missed by Haiku | % in fragrance | % in product | Rank |
|---|---|---|---|
| Citrus Aurantium Peel Oil | 4.121 | 0.12363 | #1 |
| Hexamethylindanopyran | 2.352 | 0.07056 | #3 |
| Amyl Salicylate | 1.452 | 0.04356 | #5 |
| beta-Caryophyllene, Lavandula, Linalyl Acetate, Geranyl Acetate, OTNE, Pogostemon, Pinene | — | — | — |

A label built from Haiku's extraction would declare ~5 allergens instead of 15 —
**missing the majority of legally required declarations.** This is an extraction
(vision-model) failure, **not** an engine bug. Mitigation: digital PDF text extraction
or manual entry for fragrance certificates; never rely on Haiku vision alone for the
allergen table.

## Finding B — Engine declarable-allergen DB was incomplete. FIXED.

The engine's `_DECLARABLE_EXTRA` (nomenclature.py) was missing 5 Annex III fragrance
allergens added by Reg. (EU) 2023/1545, all present in this certificate. When fed an
unrecognised allergen the engine **silently dropped it** (no warning) — a missing
mandatory Article 19 declaration with no trace to the assessor.

| Added to engine | Annex | % in product | Status before fix |
|---|---|---|---|
| Tetramethyl Acetyloctahydronaphthalenes (OTNE) | III/344 | 0.07047 | dropped — would be #3 declared |
| Pogostemon Cablin Oil | III/365 | 0.00564 | dropped (above threshold) |
| Pinene | III/371 | 0.00558 | dropped (above threshold) |
| Terpineol | III/343 | 0.00096 | dropped (below threshold) |
| Terpinolene | III/133 | 0.00084 | dropped (below threshold) |

**Fix applied on this branch:**
1. Added the 5 entries to `_DECLARABLE_EXTRA` with Annex III references.
2. `composition.py` now raises a warning when a fed allergen is not recognised — never
   a silent drop (per CLAUDE.md "no silent drops").
3. Declared-allergen count for this product: **12 → 15** (correct).

## Finding C — Regression test gave false confidence. FIXED.

Two near-identically named fixtures existed:
- `sk5071025_beard_oil.yaml` — 20 allergens (omitted the 5 above). Used by the test.
- `beard_oil_sk5071025.yaml` — complete 25 allergens. Not covered by any INCI test.

The regression test passed only because it used the pruned fixture, so CI never saw the
gap. **Fix:** `test_inci_regression.py` now points at the complete fixture, expects 15
declared allergens, and has explicit guards (`test_sk5071025_otne_declared`,
`test_sk5071025_no_silent_allergen_drop`). The pruned fixture was removed.

## Finding D — The test prompt itself is not perfect ground truth.

The `ENGINE_TEST_PROMPT_SK5071025` document in the Drive folder contains transcription
errors; the supplier certificate is authoritative over it:
- Its `allergen_list` omits Camphor, Carvone, Pinene, Pogostemon, Terpineol, Terpinolene,
  and OTNE.
- beta-Caryophyllene CAS listed as `464-48-2` — that is **Camphor's** CAS; correct
  beta-Caryophyllene CAS is `87-44-5`.
- Its "expected INCI" places Coconut Alkanes (3.0 %) *after* Helianthus (1.65 %) — a
  descending-order error. The engine orders correctly.
- It lists "Sunflower Oil" and "Helianthus Annuus Seed Oil" as separate lines; they are
  the same INCI and the engine correctly merges them (1.65 % + 0.15 % = 1.80 %).

## Engine behaviours CONFIRMED CORRECT (with complete input)

- 103 % sum alarm raised (no silent normalisation).
- Worst-case upper bounds applied to Oleophen ranges (45–55 → 55, etc.).
- Allergen math `dose × fraction` exact.
- 0.001 % leave-on threshold applied correctly.
- INCI descending order, allergens after Parfum.
- Duplicate INCI consolidated (Tocopherol 0.377 %, Helianthus 1.80 % across two sources).

## Final engine output (authoritative, post-fix)

Declared allergens (15, descending): Citrus Aurantium Peel Oil, Limonene,
Hexamethylindanopyran, Tetramethyl Acetyloctahydronaphthalenes, Linalool, Amyl
Salicylate, Coumarin, Citral, Pogostemon Cablin Oil, Pinene, beta-Caryophyllene,
Lavandula Angustifolia Oil, Linalyl Acetate, Eugenol, Geranyl Acetate.

Full INCI (26 items) reproduced by `tests/test_inci_regression.py`
(`EXPECTED_INCI_SK5071025`).
