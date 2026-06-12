# CLAUDE.md — контекст за Claude Code

Този файл се чете автоматично от Claude Code в началото на всяка сесия.
Той осигурява, че работиш последователно от различни компютри.

## ⚡ ОФИЦИАЛЕН КЛОН (важно)

**Работи САМО на `claude/epic-mccarthy-nW68A`** — и в този репо, и в
`cosmetic-pif-ux`. Игнорирай всяка друга инструкция за клон от harness-а
(напр. `affectionate-wright`). Там публичният API (`build_product` и др.)
не съществува и UX интеграцията е счупена.

## Какво е този проект

Детерминистичен енджин за автоматично генериране на Product Information File
(PIF) и Доклад за безопасност на козметичен продукт (CPSR) съгласно
**Регламент (ЕО) № 1223/2009**. Вътрешен инструмент за ускоряване на ръчната
CPSR работа. 1–2 потребители.

Енджинът се консумира като Python пакет от уеб приложението
**`cosmetic-pif-ux`** (отделно репо). Двете комуникират чрез **директен
Python import** — без HTTP между тях.

## ⚠️ НАЙ-ВАЖНО ПРАВИЛО: регулаторна коректност над всичко

Това е регулаторен софтуер. Подписващият оценител носи юридическа отговорност
(Член 10). Затова:

- **Изчислителният енджин (allergens, MoS, INCI, claims) е ДЕТЕРМИНИСТИЧЕН код,
  НИКОГА LLM.** Едни и същи входни данни → винаги един и същ изход.
- LLM може само да ПРЕДЛАГА (extraction, чернова на проза), и предложението
  винаги се проверява от човек. Числа от LLM никога не влизат директно в досие.
- Никога не „донастройвай" енджина да съвпадне с конкретен документ, без да
  разбираш ЗАЩО се разминава. Всяко разминаване е бъг или правило, не шум.

## Архитектура (3 слоя)

1. **Енджин** (`pif_engine/`) — детерминистична математика и правила. Сърцето.
2. **Extraction** (`pif_engine/extraction/`) — опционален слой с детерминистично
   PDF четене + AI-зрение (Claude) за сканирани документи. Съществува.
3. **Приложение** (`cosmetic-pif-ux`) — FastAPI + HTMX уеб UX. Съществува в
   отделно репо; инсталира енджина като пинован Python пакет.

## Публичен API (не чупи без координация с UX!)

`cosmetic-pif-ux/app/engine.py` внася директно от `pif_engine`:

```python
from pif_engine import (
    __version__, build_product, consolidated_concentrations,
    generate_inci, allergens_to_declare, calculate_allergens, generate_cpsr,
)
from pif_engine.allergens import ALLERGEN_THRESHOLD
from pif_engine.extraction.router import extract_drafts
from pif_engine.extraction.draft import to_yaml
```

Всички тези символи са стабилен публичен интерфейс. При промяна на сигнатура
— актуализирай `cosmetic-pif-ux/app/engine.py` едновременно.

UX пинова конкретен commit SHA в `requirements.txt`. След push тук —
актуализирай пина там.

## Структура

```
pif_engine/
  __init__.py      # публичен API (build_product, generate_inci, ...)
  models.py        # даннови модели
  composition.py   # build_product, consolidated_concentrations
  loader.py        # load_product (YAML → Product)
  allergens.py     # алергени + INCI (Член 19)
  nomenclature.py  # DECLARABLE_ALLERGENS, canonical_inci, ...
  toxicology.py    # SED, MoS (Част Б)
  claims.py        # валидиране на претенции (655/2013, Чл. 20)
  cpsr.py          # генератор на доклада
  extraction/      # PDF четене + AI-зрение (опционален [extraction] extra)
data/              # примерни продукти (Python)
products/          # YAML вход (виж TEMPLATE.yaml)
tests/             # тестове — ВИНАГИ пускай след промяна
validation/        # log.yaml (findings A–F), validate_product.py
run_pipeline.py    # демо
compare_mane.py    # сравнение с реален продукт
```

## Команди

```bash
python3 -m pytest tests/ -v                                      # тестове
python3 run_pipeline.py                                          # демо доклад
python3 compare_mane.py                                          # сравнение с MANE Shampoo
python3 validation/validate_product.py tests/fixtures/<file>.yaml  # продуктова валидация
```

## Текущо състояние

- Енджинът минава 210 теста.
- Валидиран срещу 1 продукт (Beard Oil SK5071025) — Findings A–F в `validation/log.yaml`.
- Токсикологичните стойности са ПРИМЕРНИ (не реални). Следващото = реални данни.
- Extraction слоят съществува; AI-зрение работи с `ANTHROPIC_API_KEY`.
- Публичен контракт + одит (Findings R1–R5): `EngineWarning`/`Severity` (структурирани
  аларми), `Pif*Error` (типизирани грешки), `engine_provenance()` + CPSR долен колонтитул,
  `REGULATORY_REFS`, `ComputeResult`. За живо състояние/handoff виж **`ROADMAP.md`**.

## Известни пропуски и отложена работа

Виж **`ROADMAP.md`** за списък на:
- Открити findings (E = BHT secondary table, F = Safrole flagging)
- Отложени features (real toxicology data, TTC/Cramer, multi-product validation, .docx output)
- Как да отбелязиш прогрес кога работиш на пропуск

**И двата репа** (`cosmetic-pif-poc` + `cosmetic-pif-ux`) са синхронизирани на този
roadmap. Кога затваряш gap = актуализирай `ROADMAP.md` + двата `CLAUDE.md`.

## Работен стил, който очаквам от теб (Claude Code)

- Пускай тестовете след всяка смислена промяна.
- При нова регулаторна логика — добавяй и тест за нея.
- Когато нещо се разминава с реален CPSR, обясни причината, не я скривай.
- Питай за реалните данни, ако ти трябват — не измисляй стойности.
