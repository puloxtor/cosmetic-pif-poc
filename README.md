# PIF/CPSR Automation — Proof of Concept

Автоматизирано генериране на Product Information File (PIF) и Доклад за
безопасност (CPSR) съгласно **Регламент (ЕО) № 1223/2009**.

> **Статус: MVP / Proof of Concept.** Доказва, че логиката работи end-to-end.
> НЕ е продукционна система и НЕ замества квалифициран оценител (Член 10).

## Какво доказва този PoC

От входни данни (формула + сертификати) автоматично се генерира:

1. **Сумиране на алергени** от ароматни компоненти (80+ вещества)
2. **Прагова логика** leave-on (0.001%) vs rinse-off (0.01%)
3. **INCI списък** в низходящ ред с алергени след Parfum (Член 19)
4. **SED + MoS** изчисление (MoS > 100 = безопасно)
5. **Валидиране на претенции** — блокира денигриращи и медицински (Рег. 655/2013, Чл. 20)
6. **CPSR Част А + Б** като готов документ

## Структура

```
pif_engine/
  models.py        # даннови модели (суровина, формула, сертификат)
  allergens.py     # алергени + INCI генериране
  toxicology.py    # SED, MoS
  claims.py        # валидиране на претенции
  cpsr.py          # генератор на доклада
data/
  example_product.py   # примерен продукт (тук влизат реални данни)
tests/
  test_engine.py   # тестове на регулаторната логика
run_pipeline.py    # главен скрипт
```

## Пускане

```bash
python3 run_pipeline.py      # генерира outputs/CPSR_report.md
python3 tests/test_engine.py # пуска тестовете
```

## MCP сървър — ползване на енджина директно от Claude

Енджинът се излага като MCP инструменти (`compute_product`, `validate_claims`,
`product_template`) — тънка обвивка, всички числа идват от детерминистичния код.

```bash
pip install '.[mcp]'
pif-mcp                    # stdio — за Claude Desktop / Claude Code
pif-mcp --transport http   # streamable HTTP на $PORT (endpoint /mcp) — за claude.ai
```

**Claude chat (claude.ai):** нужен е публичен URL. Деплой на Railway директно от
това репо — `Procfile` пуска `python -m pif_engine.mcp_server --transport http`
(модулно извикване от корена на репото, БЕЗ да разчита пакетът да е pip-инсталиран;
Railpack копира `requirements.txt` преди останалия код, затова инсталация с
локален път като `.[mcp]` там се чупи — `mcp>=1.2` е обикновена PyPI зависимост,
работи без този проблем). После в claude.ai → Settings → Connectors → **Add
custom connector** с URL `https://<домейн>/mcp`. Сървърът е без auth — дръж
URL-а частен (инструментът е калкулатор, не съхранява данни).

**Claude Code:** `claude mcp add pif-engine -- pif-mcp`

**Claude Desktop** (`claude_desktop_config.json`):
```json
{ "mcpServers": { "pif-engine": { "command": "pif-mcp" } } }
```

## Roadmap

- [x] **Фаза 1 (тук):** CLI PoC с твърди формули и примерни данни
- [ ] **Фаза 2:** четене на реални сертификати (PDF/Excel) → попълване на master таблица
- [ ] **Фаза 3:** agentic слой — LLM извлича алергени от сертификати, предлага INCI/претенции
- [ ] **Фаза 4:** web app (FastAPI + React) за Мими/Милена/Хаби/Тенчо
- [ ] **Фаза 5:** генериране на .docx/.pdf официални документи

## ⚠️ Регулаторна забележка

Изчисленията са опростени за демонстрация. Реалните SED фактори (таблици
3A/3B SCCS), DAp стойности и PoD трябва да се валидират от квалифициран
оценител на безопасността преди всякаква употреба.
