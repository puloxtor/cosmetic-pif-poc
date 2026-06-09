# Test Fixture Schema

Every file in `tests/fixtures/*.yaml` is a product fixture. The parametric test suite
(`test_fixtures_parametric.py`) loads them automatically — no code changes needed to
add a new product.

---

## Minimal structure (mandatory fields)

```yaml
product:
  name: "Product Name (internal code)"
  product_type: "leave-on"   # or "rinse-off"
  sale_countries: ["BG"]     # ISO-3166-1 alpha-2 list; [] = EU default

raw_materials:
  - name: "Supplier trade name"
    dose_pct: 69.5            # percentage in finished formula
    composition:
      - { inci_name: "Prunus Amygdalus Dulcis Oil", cas: "8007-69-0", pct: 100 }
```

## Optional product fields

| Field | Default | Meaning |
|---|---|---|
| `applied_amount_g` | 10.46 | grams applied per use (for SED/MoS) |
| `retention_factor` | 0.01 | fraction retained on skin (1.0 for leave-on) |
| `body_weight_kg` | 60.0 | assessor body weight for MoS |
| `cpnp_code` | — | CPNP notification number (appears in product name) |

## Raw material variants

### Standard (multi-component) raw material

```yaml
- name: "Oleophen Cosmos"
  dose_pct: 3.0
  composition:
    - { inci_name: "Helianthus Annuus Seed Oil", cas: "8001-21-6", range: [45, 55] }
    - { inci_name: "Olea Europaea Fruit Oil",    cas: "8001-25-0", pct: 35 }
    - { inci_name: "Tocopherol",                 cas: "59-02-9",   at_most: 1.0 }
    - { inci_name: "Aqua",                       cas: "7732-18-5", remainder: true }
```

Amount spec options (pick one per line):
- `pct: X` — exact value
- `range: [low, high]` — engine uses the **upper bound** (worst-case)
- `at_most: X` — engine uses X
- `remainder: true` — engine computes 100 % minus all other lower bounds

### Fragrance raw material

```yaml
- name: "Parfum Peace on Earth (Symrise 212878)"
  dose_pct: 3.0
  is_fragrance: true
  allergens:
    - { name: "Limonene",    cas: "138-86-3",  pct_in_fragrance: 4.000 }
    - { name: "Linalool",    cas: "78-70-6",   pct_in_fragrance: 1.565 }
    # ... all allergens declared on the IFRA certificate, copy verbatim
```

**Important:** list ALL allergens from the IFRA certificate, even those below the
declaration threshold. The engine applies the threshold; omitting borderline entries
risks a silent miss if concentrations change. Use the exact name from the certificate
— the engine normalises via `declarable_name()`. If the engine emits an
"непознат за енджина алерген" warning, the name is not in `DECLARABLE_ALLERGENS`
and must be added to `nomenclature.py` (see Finding B, SK5071025).

### Denaturant raw material

```yaml
- name: "SD Alcohol 40-B"
  dose_pct: 70.0
  composition:
    - { inci_name: "Alcohol Denat.", cas: "64-17-5", function: "denaturant", pct: 100 }
```

Ingredients with `function: denaturant` are suppressed from the INCI label per
Article 19 but appear in the CPSR Part A audit note.

---

## `expected:` block (optional, enables parametric assertions)

Add an `expected:` key at the top level to enable automatic assertions in
`test_fixtures_parametric.py`:

```yaml
expected:
  allergen_count: 15          # exact number of declared allergens (above threshold)
  sum_alarm: true             # true if formula sum ≠ 100% (expect a sum warning)
  no_silent_drops: true       # assert zero "непознат за енджина алерген" warnings
  inci_list:                  # exact ordered INCI list (omit to skip order check)
    - "Prunus Amygdalus Dulcis Oil"
    - "Ricinus Communis Seed Oil"
    - "Parfum"
    - "Limonene"
    # ...
```

All keys are optional. A fixture without `expected:` is still loaded and smoke-tested
(build_product must not raise; sum alarm emitted if sum ≠ 100 %).

---

## How to add a new product from a Drive folder

1. Collect the documents: formulation sheet, SDS for each raw material, IFRA
   certificate(s) for any fragrance, CoA if available.
2. Copy `tests/fixtures/beard_oil_sk5071025.yaml` as a template.
3. Fill in `product:` and `raw_materials:` from the formulation sheet literally
   (do **not** normalise concentrations — the engine handles that).
4. For each fragrance, copy every allergen row from the IFRA certificate verbatim.
5. Run `python validation/validate_product.py tests/fixtures/<your_fixture>.yaml` to
   get the computed INCI list and allergen count.
6. Verify the output against the ground-truth INCI (from a previous CPSR or manual
   calculation). Investigate every discrepancy — do not adjust `expected:` to match
   wrong output.
7. Once verified, fill in the `expected:` block and commit.
8. If the engine emits an unknown-allergen warning, add the entry to
   `pif_engine/nomenclature.py` → `_DECLARABLE_EXTRA` with its Annex III reference,
   then re-run. Log the finding in `validation/log.yaml`.

---

## Thresholds (EU Regulation 1223/2009, Article 19)

| Product type | Declaration threshold |
|---|---|
| Leave-on | > 0.001 % in finished product |
| Rinse-off | > 0.01 % in finished product |
