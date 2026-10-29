# ACESi Status — 2026-09-29

## What Works

- **/model_chat endpoint** — bypasses the deterministic executor entirely; model runs directly with full tool schema.
- **WebView form enrichment** — native checkbox/radio labels get real tap coordinates; state shown as `[x] CHECKED` / `[ ] UNCHECKED`.
- **Atomic dump + observe** — `ui_tap` auto-dumps and reports newly appeared targets (dropdown options).
- **ADB target resolution** — collapses mDNS alias + IP duplicate into one target; fails over cleanly on transport loss.
- **Checkbox/radio coordinates** — label centres resolved via `_option_label_points` (native nodes preferred, DOM rect fallback).
- **Label resolution in ui_tap** — label-only calls resolve to coordinates from the latest dump; null/zero coords dropped.
- **Schema sizing** — domain filtering + reduced schema on 413 keeps requests under provider limits; final request is smallest.
- **E-STOP at boot** — armed by default; only the un-kill word (hashed) can disarm; threads gated accordingly.
- **Thread gating** — job_watch, task_queue, ntfy, email, summary, reminder all OFF unless `ACE_AUTO_AGENTS=1`.
- **Session-expiry guard** — detects "Your Session Has Expired!" / "login again" and stops instead of re-logging in.
- **Dump-stall guard** — 3+ consecutive `ui_dump` without a tap injects corrective nudge.
- **Select coordinate reconciliation** — native dropdown row and WebView form section now share the same tap point.
- **Closed-popup hint** — option rows say "(popup closed - tap the select row above @ tap(x,y) to open, then ui_dump again)".

## What Doesn't Work

- **gpt-oss-120b drift on multi-step UI tasks** — model loses navigation goal after a tap that doesn't visibly change the screen; defaults to "Back" and wanders off-task. Ceiling is model capability, not tooling.

## What to Try Next

1. **OpenRouter paid key + `llama-3.3-70b-versatile`** for device tasks (set `GROQ_MODEL_BROWSER` or provider chain). This model holds multi-step state far better.
2. **Different Groq account** with `llama-3.3-70b-versatile` access.
3. **Non-LLM automation** — Appium / MacroDroid / UIAutomator scripts for the deterministic parts; reserve LLM only for decision points.

## Known Remaining Bugs

- **"Back" drift on small models** — no guard prevents tapping "Back" while the target element is still visible. Fix: add a "Back guard" in the agent loop (block if target named in prompt still on screen).

## Fixed Since This File Was Written

- **/model prefix in the ACEsi UI** — `/chat` now delegates any message starting with a bypass override (`/model`, `#adaptive`, `!model`, `#model`) to the `model_chat()` handler, so the UI path is byte-for-byte identical to the `/model_chat` API. No executor hijack. Verified live: `/model Use only ui_tap...` went into the model-driven loop (not "Done — steps executed").

---

**Code change ready:** `GROQ_MODEL_BROWSER = "llama-3.3-70b-versatile"` in `server.py:120` — waiting for credentials that grant access.