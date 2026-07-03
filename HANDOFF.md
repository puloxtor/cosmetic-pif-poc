# HANDOFF — текущо състояние (мост между акаунти)

> Този проект се develop-ва от ДВА акаунта последователно, по ЕДИН общ клон.
> Чат-историята НЕ се прехвърля между акаунтите — **единственият мост е git +
> този файл**. Обновявай го при ВСЕКИ комит (виж „Протокол за смяна" в CLAUDE.md).

## Последна синхронизация
- Репо: `cosmetic-pif-poc` (енджин)
- Клон: `claude/fervent-ramanujan-vNg22`
- Комит: (виж `git log -1`) — Add MCP server (pif-mcp)
- Дата: 2026-07-03
- Тестове: минават — 53 (`python3 -m pytest tests/ -q`)

## Какво беше направено последно
- **MCP сървър** (`pif_engine/mcp_server.py`, CLI `pif-mcp`, extra `mcp`):
  инструменти `compute_product` / `validate_claims` / `product_template`.
  stdio за Desktop/Code; `--transport http` (streamable, endpoint `/mcp`) за
  claude.ai custom connector. `Procfile` + ред `.[mcp]` в `requirements.txt`
  правят репото директно деплойваемо на Railway. Без auth — URL-ът да е частен.
- По-рано: portable handoff kit (`.claude/hooks/session_start.sh` + `settings.json`
  + този файл + `HANDOFF_KIT.md`); auto-pull е opt-in чрез `.claude/handoff-sync-on`
  (тук включен; в UX репото kit-ът се инсталира без него → спящ).

## Какво следва (подреден списък)
1. **Master Composition Table + Annex проверки** — нови sibling модули
   `pif_engine/report.py` (консолидирана таблица) + `pif_engine/annex.py`
   (Annex II/III/V/VI рамка с известни лимити, флагнати). Engine-side
   двойник на UX TDS функцията. Отблокирано (публични регулаторни данни).
2. `.docx` форматиран изход (ROADMAP Задача 6).
3. TTC/Cramer модул за опаковка (ROADMAP Задача 5).
4. Реална токсикология + точен MoS (ROADMAP Задачи 1–2) — **БЛОКИРАНО**:
   нужни са реални PoD/DAp стойности от потребителя (не измисляме числа).

## Блокери / отворени въпроси
- Токсикологичните стойности в кода са placeholder-и — чакат реални данни.
- TDS-merge фиксът е в **другото репо** (`cosmetic-pif-ux`), не тук.

## Свързани репо-та
- UX: `cosmetic-pif-ux` (FastAPI + HTMX) — пинова този енджин по комит SHA в
  `requirements.txt`. При вдигане на версия → смени SHA там на актуалния тук.
- Текущ пинван енджин SHA в UX: `e3273e9` (обнови при нов релевантен комит).

## Внимавай (gotchas)
- Изчислителният енджин е ДЕТЕРМИНИСТИЧЕН код, НИКОГА LLM. Едни и същи входни → същи изходи.
- Не „донастройвай" енджина да съвпадне с конкретен документ без да разбираш ЗАЩО.
- Extraction зависимостите (pdfplumber/anthropic) са опционални — не ги внасяй в ядрото.
