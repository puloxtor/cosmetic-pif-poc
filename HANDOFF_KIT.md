# HANDOFF_KIT — преносим механизъм за смяна между акаунти

Дроп-ин kit, който позволява на ДВА акаунта да се редуват по ЕДИН общ клон в
кой да е репо. Чат-историята не се прехвърля; този kit прави git + `HANDOFF.md`
единствения мост, а нов сесия автоматично се синхронизира и показва състоянието.

Kit-ът е **branch/repo-agnostic** — едни и същи файлове работят навсякъде;
само съдържанието на `HANDOFF.md` е различно за всяко репо.

## Какво съдържа
1. `.claude/hooks/session_start.sh` — SessionStart hook: показва `HANDOFF.md` и
   последните 5 комита; ff-pull на текущия клон **само ако auto-pull е включен**
   (виж по-долу). Без тестове.
2. `.claude/settings.json` — регистрира hook-а.
3. `HANDOFF.md` — живо състояние (обновява се при всеки комит).
4. Секция в `CLAUDE.md` — „Протокол за смяна между акаунти".

## Auto-pull е OPT-IN (важно при инсталиране по време на работа)

Hook-ът прави ff-pull САМО ако съществува файл `.claude/handoff-sync-on`.
Така можеш да инсталираш kit-а по средата на работа — той остава „спящ" и не
докосва нищо (само показва състояние). Когато си готов да го включиш:

```bash
touch .claude/handoff-sync-on
git add -A && git commit -m "Enable handoff auto-pull" && git push
```

(Дори включен, hook-ът никога не трие работа: прескача при мръсно дърво и прави
само fast-forward.)

## Инсталиране в ново репо (пусни в корена на репото)

```bash
mkdir -p .claude/hooks

cat > .claude/hooks/session_start.sh <<'SH'
#!/usr/bin/env bash
# SessionStart: surface handoff state, and (only when enabled) sync the current
# branch to its upstream. Repo/branch-agnostic — safe to drop into any repo.
#
# Auto-pull is OPT-IN: it runs only if the file .claude/handoff-sync-on exists.
# This lets you install the kit while mid-work without it touching anything;
# enable later with:  touch .claude/handoff-sync-on && git add -A && git commit && git push
# Even when enabled it never discards work: it skips a dirty tree and only fast-forwards.
set -u
if [ -f .claude/handoff-sync-on ]; then
  UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)"
  if [ -n "$UPSTREAM" ] && [ -z "$(git status --porcelain 2>/dev/null)" ]; then
    git fetch -q 2>/dev/null \
      && git merge --ff-only "$UPSTREAM" -q 2>/dev/null \
      && echo "✓ synced with $UPSTREAM"
  else
    echo "⚠ no upstream or local changes present — skipping auto-pull"
  fi
else
  echo "ℹ auto-pull disabled (no .claude/handoff-sync-on) — surfacing state only"
fi
echo; echo "===== HANDOFF.md ====="
[ -f HANDOFF.md ] && cat HANDOFF.md || echo "(no HANDOFF.md yet)"
echo; echo "===== last 5 commits ====="
git log --oneline -5 2>/dev/null
SH
chmod +x .claude/hooks/session_start.sh

# NB: no .claude/handoff-sync-on created here on purpose — the kit stays DORMANT
# (surface-only) so it can't touch in-progress work. Enable it when your plan is done.

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
