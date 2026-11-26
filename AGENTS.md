# ACEsi — Operational Rules (read this first)

ACEsi is the local agent that runs LibSyncStudent and drives its development.
It is a Flask server + single-page HTML UI.

## Locations
- ACEsi: `D:\projects\acesi` (`server.py`, `ACEsi.html`, `ACEsi.html.golden`)
- App under management: `C:\Users\gabri\Documents\LibSyncStudent`
- ACEsi UI: `http://127.0.0.1:5000/`
- Flutter web app: `http://127.0.0.1:55793/`
- Conversation memory: `ace_memory.db`
- Logs: `server_stdout.txt`, `audit.log`, `run_*.log` (in LibSyncStudent)

## HARD RULES
1. **After every edit: commit, push, and save.** No asking for confirmation.
   - ACEsi HTML edits: also refresh `ACEsi.html.golden` (`copy2`) in the same step.
   - If the user says a change is wrong: revert it, push the revert, say so.
2. **Verify visually before claiming a fix.** Use computed styles, pixel sampling,
   browser screenshots and logs. Never say "fixed" on assumption.
3. **Ollama is uninstalled.** Never probe it, never set `ACE_OLLAMA=1` or
   `ACESI_OFFLINE=1`. Cloud provider routing is expected (picker usually
   `gemini-3.5-flash-lite`).
4. **The user runs Flutter.** Do NOT run `flutter run`, `analyze`, `test`,
   `build`, `adb` or `scrcpy` unless explicitly asked. Edit files and tell them
   what to run.
5. **Do the edits yourself.** The user wants ACEsi to perform the work, not to
   describe it. Verify afterwards; do not silently hand-fix guessed problems.
6. **Agent Turn Summary** after real work: `Summary of Changes ✅` with a table.
7. **Settings System Prompt** stays capped at 250 words with a live counter.

## ACEsi UI invariants (do not break)
- Palette: black `#000`, bright amber `#ffa500`, muted amber `#995C00`,
  terminal blue `#8fd3ff`, green `#00ff88`, magenta/cyan tags.
- Borders: 1px; inactive muted, active panel bright. No duplicate/dim lines.
- Keep the Live System Feed and the 6 hardware sparkline cards.
- Hardware cards stretch evenly top-to-bottom in the dashboard column.
- Terminal: 300px, ACEsi tab / Flutter tab. The Flutter prompt:
  - lives inside the left pane, only on the Flutter tab, no border lines,
  - no Send button — Enter sends `r`/`R`/`q`,
  - hardware cards must fill the right column with no strip under them.
- Flutter run command: `flutter run -d web-server --web-hostname 0.0.0.0 --web-port 55793`
- Wait for `Flutter run key commands` in the log before sending `R`; pressing
  keys during startup causes hot-restart timeouts and a white page.

## Auto-fill self-test (run before any live application)
- Command: `python tools/autofill_selftest.py` (from `D:\projects\acesi`)
- Endpoint: `GET /api/autofill/selftest` (JSON with per-field PASS/FAIL)
- It extracts the REAL generated JS from `autofill_script.dart`, runs it
  against a 28-field ITS-style fixture (main doc + iframe), and reports each
  field. Current result: 28/28 PASS.
- If any field fails, fix the alias in `autofill_script.dart` and re-run.
  Never work on auto-fill blind — run this first.

## Environmental awareness
- `GET /api/environment/snapshot` returns a compact live snapshot (git state for
  both repos, Flutter run state + log tail, ports 5000/55793, ACEsi.html/golden
  match). The same block is injected into every `/chat` system prompt as
  `[LIVE ENVIRONMENT — AUTO-GATHERED]`. Trust it over assumptions.
- Useful endpoints: `/api/health`, `/api/run/status`, `/api/run/input`,
  `/api/system/metrics`, `/history`, `/memory/*`, `/journal`, `/cdp/*`,
  `/api/last_edit`, `/context`.

## Working method — "the right brain" (use this on every task)
1. **Find the real break before fixing anything.** Ask: what is the exact
   mechanism producing the symptom? Do not guess from how it looks.
2. **Test the actual artifact.** For generated code (e.g. Flutter's injected
   JS), extract the real generated output from the Dart source and run it
   against a synthetic fixture. That is how the auto-fill bugs were found:
   the toast said "8 fields filled" while the ID field held "South African".
3. **Trust pixels over computed styles when they disagree.** Sample the actual
   screenshot with PIL; a computed style can be right while the rendered line
   is still wrong (or vice versa).
4. **One change, one verification, one commit.** After each edit: verify,
   commit, push, refresh golden. If wrong, revert and push the revert.
5. **Reproduce the user's exact scene.** Screenshots are evidence. Read them
   carefully and ask what is actually visible before changing code.
6. **Record what was learned** in the playbook so the next session starts with
   the answer, not the search. This is how knowledge survives a new session.
7. **Be honest about the untested edge.** Say "verified on a synthetic form,
   not a live portal" instead of claiming complete success.

## Working style
- Be honest when unsure; prefer a certain small fix over a guessed broad one.
- When a screenshot disagrees with computed styles, sample pixels to settle it.
- Keep both repos committed and pushed at all times.


## LAN testing
- The Flutter command binds `0.0.0.0` so another device on the same Wi-Fi can
  open `http://<PC-LAN-IP>:55793`. Find the IP with:
  `Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*"}`
- Chrome on this PC still uses `http://127.0.0.1:55793`.
- Each device needs its own Supabase URL/key in Settings → Community Chat.
