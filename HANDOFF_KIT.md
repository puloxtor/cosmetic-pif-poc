# HANDOFF_KIT — преносим механизъм за смяна между акаунти

Дроп-ин kit, който позволява на ДВА акаунта да се редуват по ЕДИН общ клон в
кой да е репо. Чат-историята не се прехвърля; този kit прави git + `HANDOFF.md`
единствения мост, а нов сесия автоматично се синхронизира и показва състоянието.

Kit-ът е **branch/repo-agnostic** — едни и същи файлове работят навсякъде;
само съдържанието на `HANDOFF.md` е различно за всяко репо.

## Какво съдържа
1. `.claude/hooks/session_start.sh` — SessionStart hook: ff-pull на текущия клон
   (ако е чист и има upstream) + показва `HANDOFF.md` и последните 5 комита. Без тестове.
2. `.claude/settings.json` — регистрира hook-а.
3. `HANDOFF.md` — живо състояние (обновява се при всеки комит).
4. Секция в `CLAUDE.md` — „Протокол за смяна между акаунти".

## Инсталиране в ново репо (пусни в корена на репото)

```bash
mkdir -p .claude/hooks

cat > .claude/hooks/session_start.sh <<'SH'
#!/usr/bin/env bash
# SessionStart: sync the current branch to its upstream (if clean) and surface state.
# Repo/branch-agnostic — safe to drop into any repo. No tests (saves credits).
set -u
UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)"
if [ -n "$UPSTREAM" ] && [ -z "$(git status --porcelain 2>/dev/null)" ]; then
  git fetch -q 2>/dev/null \
    && git merge --ff-only "$UPSTREAM" -q 2>/dev/null \
    && echo "✓ synced with $UPSTREAM"
else
  echo "⚠ no upstream or local changes present — skipping auto-pull"
fi
echo; echo "===== HANDOFF.md ====="
[ -f HANDOFF.md ] && cat HANDOFF.md || echo "(no HANDOFF.md yet)"
echo; echo "===== last 5 commits ====="
git log --oneline -5 2>/dev/null
SH
chmod +x .claude/hooks/session_start.sh

cat > .claude/settings.json <<'JSON'
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": ".claude/hooks/session_start.sh" } ] }
    ]
  }
}
JSON

# HANDOFF.md — попълни за КОНКРЕТНОТО репо (клон, последен комит, какво следва).
cat > HANDOFF.md <<'MD'
# HANDOFF — текущо състояние (мост между акаунти)

## Последна синхронизация
- Репо: <repo>
- Клон: <branch>
- Комит: <hash + subject>
- Дата: <date>
- Тестове: <статус>

## Какво беше направено последно
- ...

## Какво следва (подреден списък)
1. ...

## Блокери / отворени въпроси
- ...

## Свързани репо-та
- ...

## Внимавай (gotchas)
- ...
MD
```

После добави в `CLAUDE.md` (създай го, ако липсва) секцията „🔄 Протокол за смяна
между акаунти" (виж CLAUDE.md в `cosmetic-pif-poc`), комитни и пушни към общия клон:

```bash
git add -A && git commit -m "Add portable two-account handoff kit" && git push
```

## „Сочене" на другата сесия — автоматично
Щом kit-ът е комитнат в репото, ВСЯКА нова сесия там сама пуска hook-а и чете
този `HANDOFF.md`. Няма допълнително свързване. Единствената дисциплина е:
обнови `HANDOFF.md` и пушни при всеки комит.

> Бележка: първия път hook-ът може да поиска еднократно одобрение (project hook).
