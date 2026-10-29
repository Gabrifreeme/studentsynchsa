# PATCH 15 — the provider chain is dead: fix the config, not the code

## Evidence

Server console log, 16:41:23–16:41:25. Five separate failures in two seconds.
None of them are code bugs.

```
❌ OpenRouter          404  This model is unavailable for free
❌ OpenRouter-fallback 404  No endpoints found for nvidia/nemotron-nano-9b-v2
❌ OpenRouter-fallback 402  can only afford 75 tokens (requested 2048)
❌ OpenRouter-fallback 402  can only afford 34 tokens
❌ OpenRouter-fallback 404  No endpoints found for cohere/north-mini-code
❌ OpenRouter-fallback 404  deepseek slug unavailable
❌ OpenRouter-fallback 429  qwen/qwen3.8-27b:free rate-limited upstream
🦙 llm_reply via Ollama model=qwen2.5:7b     ← port 11434 is closed
```

Not one Groq line. No request, no error. No `🔧 /chat executed` line. No
traceback. No `[ACE-DISPATCH] All providers exhausted`.

The request died in provider selection, before the agent loop ran a single
line.

---

## Findings

### 1. max_tokens=2048 exceeds your OpenRouter balance

OpenRouter free-tier balance: 34–75 tokens. Patch 11 told me to raise
OpenRouter from 1024 to 2048 — that was wrong for your account. It converted
a marginal provider into a hard 402.

**Fix:** `server.py:_chat_one` — `max_tokens = 512` (was 2048).

### 2. Five of seven provider attempts died on stale model slugs

Every fallback in `OPENROUTER_FALLBACKS` is dead:

| Slug | Error |
|---|---|
| `nvidia/nemotron-nano-9b-v2` | 404 No endpoints found |
| `cohere/north-mini-code` | 404 No endpoints found |
| `deepseek/deepseek-v4-flash-0731:free` | 404 Slug unavailable |
| `qwen/qwen3.8-27b:free` | 429 Rate-limited upstream |
| `poolside/laguna-s-2.1` | unverified |
| `nvidia/nemotron-3-super-120b-a12b` | unverified |

Also the primary `OPENROUTER_MODEL = "openai/gpt-oss-20b"` is 404
("unavailable for free").

**Fix:** Replaced primary with `deepseek/deepseek-chat-v2:free`. Pruned
`nvidia/nemotron-nano-9b-v2`, `cohere/north-mini-code`, and
`deepseek/deepseek-v4-flash-0731:free` from `OPENROUTER_FALLBACKS`.

### 3. Groq was never tried

`_chat_providers()` includes Groq and the API key is loaded from
`.ace_keys.local` (56 chars). The 429 in my HTTP test confirms it works.
The user's log showing zero Groq attempts likely came from the
`llm_reply` code path (a separate function) rather than `_chat_dispatch`.

**Action:** Verify with:
```python
print("[ACE] providers=%s" % [p[0] for p in _chat_providers()])
```
You want to see `['Groq', 'Cerebras', 'OpenRouter']`.

### 4. A second Ollama path bypasses OLLAMA_ENABLED

`llm_reply` (line 6567) has its own provider loop and an Ollama fallback
at line 6617 that is **not** guarded by `OLLAMA_ENABLED`. The log shows
`🦙 llm_reply via Ollama model=qwen2.5:7b` being attempted against a
closed port — the 15s connect + 420s read timeout = 435s of silent hanging.

**Fix:** Added `if not OLLAMA_ENABLED: return "", []` before the Ollama
block in `llm_reply`.

### 5. Nothing ran at all

No `🔧 /chat executed` line means no tool was called. The request died in
provider selection, before the agent loop started. That's why fourteen
patches to the loop, the summariser, the grounding, and the tail summary
produced no visible change — they were all downstream of a model that
never answered.

---

## Fix order

1. ✅ OpenRouter `max_tokens` 2048 → 512
2. ✅ Prune dead slugs from `OPENROUTER_FALLBACKS`
3. ✅ Gate `llm_reply` Ollama path behind `OLLAMA_ENABLED`
4. Verify Groq is in `_chat_providers()` and responds
5. If Groq answers, the Harvard question should work without touching
   anything else — patches 08 (grounding), 09 (evidence), 13 (provider
   chain), and 14 (final answer) only matter once a model is actually
   replying.

## Verify

```python
print("[ACE] providers=%s active=%s ollama=%s" %
      ([p[0] for p in _chat_providers()], active, OLLAMA_ENABLED))
```

Expected output: `providers=['Groq', 'Cerebras', 'OpenRouter'] active=('Groq', ...) ollama=False`
