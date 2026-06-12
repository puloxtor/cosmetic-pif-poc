# Validation Log Schema

`validation/log.yaml` is the machine-readable index of all product validations.
Every entry maps to a fixture file and a human-readable narrative.

## Top-level entry fields

| Field | Type | Required | Description |
|---|---|---|---|
| `product_id` | string | yes | Short unique code (e.g. SK5071025) |
| `product_name` | string | yes | Full name including fragrance variant |
| `fixture` | path | yes | Path to `tests/fixtures/*.yaml` |
| `narrative` | path | yes | Path to `validation/*.md` human report |
| `validated_on` | ISO date | yes | Date of validation run |
| `engine_commit` | SHA | yes | Engine git commit at time of validation |
| `validator` | email | yes | Person responsible for sign-off |
| `findings` | list | yes | List of finding entries (may be empty `[]`) |

## Finding fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Letter A, B, C … within a product |
| `category` | enum | yes | See categories below |
| `severity` | enum | yes | See severities below |
| `summary` | string | yes | One-paragraph plain-language description |
| `status` | enum | yes | See statuses below |
| `fix_commit` | SHA | if fixed | Engine or UX commit that resolved the finding |
| `notes` | string | no | Additional context, mitigations, decisions |
| `regression_guard` | string | no | Test path that prevents regression |

## Enums

### category
- `extraction_failure` — LLM/OCR missed data from supplier documents
- `engine_db_gap` — allergen or INCI name missing from engine tables
- `engine_logic_bug` — incorrect calculation or ordering in engine code
- `engine_scope_gap` — correct as-is, but a regulatory case the engine does not yet model
- `test_infrastructure` — CI/fixture gave false confidence
- `data_error` — error in supplier document or test prompt
- `assessor_flag` — no engine change; the qualified assessor must note it (Article 10)

### severity
- `critical` — would cause a **missing mandatory label declaration** (Article 19)
- `high` — would cause incorrect output visible to assessor
- `medium` — suboptimal but not legally incorrect
- `low` — cosmetic / documentation only

### status
- `open` — identified, not yet resolved
- `fixed` — resolved; `fix_commit` **and** `regression_guard` are mandatory
- `deferred` — accepted as a known gap, scheduled for later (see ROADMAP.md)
- `documented_not_fixed` — out of engine scope; process mitigation documented in `notes`
- `wont_fix` — deliberate decision not to fix; rationale in `notes`

## Workflow: adding a new validation

1. Run `python validation/validate_product.py tests/fixtures/<id>.yaml`
2. Compare output to ground truth (previous CPSR, manual calculation, or supplier docs)
3. For each discrepancy, open a finding with `status: open`
4. Fix engine bugs → set `status: fixed`, record `fix_commit`
5. Add `regression_guard` pointing to the test that prevents re-occurrence
6. Write narrative in `validation/<PRODUCT_ID>_FINDINGS.md`
7. Add entry to `validation/log.yaml`
8. Commit engine fix + log update together

## Querying the log

```python
import yaml, pathlib
log = yaml.safe_load(pathlib.Path("validation/log.yaml").read_text())
open_critical = [
    (e["product_id"], f["id"], f["summary"])
    for e in log
    for f in e["findings"]
    if f["status"] == "open" and f["severity"] == "critical"
]
```
