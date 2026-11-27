# LibSyncStudent - Agent Instructions

## Project Overview
Flutter app for South African university students. Uses WebView to load ITS (Oracle PL/SQL) university portals (UNIVEN, UL, TUT, NWU, etc.) with auto-fill functionality.

## Key Architecture
- **Flutter + WebView**: App loads university portals in WebView (`webview_flutter`)
- **Auto-fill**: JavaScript injected into WebView to populate form fields
- **Profile storage**: Hive local database
- **State management**: Riverpod + GoRouter

## Critical Files
- `lib/main.dart` - App entry, Hive migration on startup
- `lib/presentation/screens/universities/webview_impl.dart` - WebView with auto-fill panel
- `lib/services/autofill_script.dart` - Generates JS for form filling
- `lib/presentation/screens/profile/profile_onboarding_screen.dart` - Profile editor
- `lib/services/auth_service.dart` - Auth + profile defaults

## Commands
```bash
flutter analyze                 # Lint/typecheck
flutter test                    # Run tests
flutter run                     # Run app
```

## Auto-fill Implementation
- WebView configured with `JavaScriptMode.unrestricted`
- `[All]` button in WebView panel calls `_runAutofill()` â†’ `star.buildAutofillScript(profile)`
- Generated JS uses `pMap` to try both `oap*` and `P_*` field names (ITS portals use `P_*`)
- `set()` handles text inputs, `setSelect()` handles radio buttons + selects
- Portal patches run on `onPageFinished` before auto-fill

## Common Issues
1. **Auto-fill not working**: Check JS injection in `webview_impl.dart` line 239, verify `pMap` lookup in `autofill_script.dart`
2. **Profile values mismatch dropdowns**: `auth_service.dart` hardcoded defaults must match dropdown items exactly
3. **Hive stale data**: Migration in `main.dart` patches old values (`'Black'`â†’`'African'`, `'Full-Time'`â†’`'YEAR'`, `'Accepted'`â†’`'I Accept'`)
4. **WebView permissions**: Requires `webview_flutter_android` for debugging

## Profile Field Mapping (oap* â†’ P_*)
Key mappings in `autofill_script.dart` pMap:
- `oapSurname` â†’ `P_SURNAME`
- `oapIdNumber` â†’ `P_ID_NO`
- `oapEmail` â†’ `P_EMAIL`
- `oapCellNo` â†’ `P_CELL_NO`
- `oapStreet` â†’ `P_ADDRESS_1`
- `oapCitizenType` â†’ `P_CITIZEN_TYPE` (radio buttons)
- etc.

## Testing
No specific test config found. Use `flutter test` for unit tests.

## ADB WiFi + scrcpy Quick Start (after restart / WiFi reconnect)
```bash
# 1. Plug phone via USB, then run:
adb tcpip 5555

# 2. Unplug USB, find phone IP, then run:
adb connect <phone-ip>:5555
# (Accept RSA prompt on phone screen)

# 3. Run app + screen mirror (in separate terminals):
flutter run                    # pick the TCP/IP device from the list
scrcpy -e                     # -e selects TCP/IP device

# To find current phone IP:
adb shell ip addr show wlan0 | findstr "inet "
```

## Execution Rules
- Do NOT run any `flutter` commands (`flutter run`, `flutter analyze`, `flutter test`, `flutter build`), `adb`, or `scrcpy` after making edits unless the user explicitly asks you to.
- Focus only on editing the requested files cleanly and directly.

## Web Dashboard (Next.js)
- Located in `D:\Downloads\project_extracted` (companion web app)
- Run: `npx --package=next@15.5.9 next dev -p 9002` from that directory
- Open: `http://localhost:9002`
- Note: `NODE_ENV=production` doesn't work in Windows cmd - use `$env:NODE_ENV="production"` in PowerShell or omit it for dev


## Community Chat
- General Chat is ACTIVE: `general_chat_screen.dart`, reached from the first
  card in `chat_screen.dart`.
- Two modes:
  - **Local** (default): messages persist in Hive box `general_chat`, UI says
    "On this device".
  - **Live multi-user**: enter Supabase Project URL + anon key in
    Settings → COMMUNITY CHAT. `chat_service.dart` uses Supabase REST
    (`app_messages` table), polls every 4s, and UI says "Live · all students".
- Table setup SQL: `docs/supabase_chat.sql`. Run in Supabase SQL Editor first.
- A stable device ID (`chatUserId`) distinguishes your own messages.
- Province-based and University Interest Groups still show Coming Soon.

## Chat home panel
- `/chat` now opens `chat_home_screen.dart`: left room list, right conversation
  on desktop; on phones the list fills the screen and a tap opens the chat.
- Rooms: general, province, university (all in Supabase `app_messages`, filtered
  by the `room` column) plus a Notifications panel.
- If the app reports a missing `room` column, run:
  `alter table public.app_messages add column if not exists room text not null default 'general';`

## WebView HTTP error capture (for the UNIVEN second-page 404)
- `onWebResourceError` now records code, type, URL and description for every
  failed resource, shows the latest in a red banner, and offers "Copy all
  HTTP errors" to the clipboard. Give that text to ACEsi.
- When diagnosing an ITS 404, first inspect the captured URL — a relative
  `gen.gw1pkg` link on page two, or a lost session cookie, are prime suspects.
- `onPageStarted` calls `_controller.clearCache()` on every navigation; this
  is a suspect for breaking ITS session state. Verify before changing it.
- `initState` clears ALL cookies for a fresh session.

## Auto-fill is OPT-IN (do not change)
- Nothing fills automatically when a page opens.
- A StarIcon sits top-right in the WebView app bar. Tapping it asks:
  "Want me to auto fill this page for you?" with Not now / Auto fill.
- The in-page floating Star created by `buildAcesiStarScript()` is enabled for
  GUIDANCE only: it opens ACEsi chat with the page title/URL via the `AcesiStar`
  JavaScript channel. It never calls auto-fill.
- The bottom "Fill All" button also asks first.
- Rationale: many students want to complete parts of the form themselves.

## Funding / bursary applications
- `funding_detail_screen.dart` "Apply Now" now opens `FundingWebViewScreen`,
  which uses the same `AppWebView` + Star auto-fill as university portals
  (NSFAS, Sasol, FNB, Anglo American, Funza Lushaka).
- IMPORTANT: WebView is unavailable on web builds. On web the screen shows
  "Open Portal" and launches the browser; auto-fill works on MOBILE only.
  Final verification must be done on a phone, not Chrome.

## Auto-fill break points found and fixed (2026-11-25)
Verified by extracting the real generated JS from `autofill_script.dart` and
running it against a synthetic ITS form (fields in main document AND iframe):
- `P_ID_NO` matched the nationality alias `south african` (from the label
  patch's "South African ID number") and was filled with "South African"
  instead of the ID number. Removed those two aliases from `nationality`,
  added `id no / idno / p id no` to `idNumber`.
- `P_HOME_LANG` inside an iframe had no label patch and no alias — added
  `home lang / homelang / p home lang`.
- Added more ITS name aliases and a `latePass()` that re-scans for empty
  fields at 900ms / 2.5s / 5s (was retrying selects only).
- WebView now waits 1500ms and only injects when the page actually has form
  fields, so it no longer fills an intermediate page.
Test result after fix: 10/10 synthetic fields filled correctly, including
ID number and iframe home language.

## Why ACEsi exists (the whole point)
The app was blocked from going live by ONE feature: automatic filling of
student application forms on university ITS portals. It never worked reliably;
ACEsi came close once but never landed it. All South African universities are
closed for applications until **10 February 2026**, so there is a window to fix
it properly. ACEsi is being built and trained now — through every edit, design
decision, fix, commit and revert — so that by 10 Feb it can own LibSyncStudent
autonomously, with live environmental awareness and the working auto-fill.

Auto-fill is the priority feature when application season reopens. Treat it as
the reason the whole toolchain exists.

## Design system (agreed 2026-11-25 — do not re-litigate)
- App name everywhere: **LibSyncStudent**. Tagline: **Powered by ACEsi**.
- Palette in `lib/core/theme/app_theme.dart` (`AppColors`):
  - primary/amber `#FFA500`, muted `#995C00`, text amber, background `#000000`,
    surface `#0A0A0A`, info/terminal blue `#8FD3FF`, success `#00FF88`.
  - Google-colour icon palette: red `#EA4335`, blue `#4285F4`,
    green `#34A853`, yellow `#FFBC05`.
  - StarIcon (in `common_widgets.dart`) paints all icons with that 4-colour
    gradient — use it for every new icon, never a plain blue `Icon`.
- `GradientBackground` applies the global responsive width: full on phones
  (<600px), 70% centered on desktop. Do not re-add per-screen constraints.
- Mobile-first. Fonts and padding already reduced ~30% globally; don't inflate.
- Shared widgets: `AppCard`, `AppListTile`, `AppSpaces`, `StarIcon`,
  `SectionHeader`, `EmptyState`. Prefer these over custom markup.

## Routes (`lib/core/router/app_router.dart`)
`/login`, `/signup`, `/dashboard`, `/onboarding`, `/notifications`,
`/ai-recommendations` (ACEsi), `/funding`, `/funding/:id`, `/universities`,
`/universities/:id`, `/applications`, `/chat`, `/settings`, `/privacy`, `/about`.

## Agreed screen layouts
- **Dashboard**: title + Powered by ACEsi; Star CTA; 8 tiles in 2-column grid
  (ACEsi, My Profile, Community, Universities, Applications, Funding, Settings,
  About Us); Exit centered near the bottom. Cards sit between Star and Exit.
- **University detail** (identical for all 26): back arrow inside content,
  identity card, Offline Guide, Fee/NBT chips, two images side by side,
  centered Apply button ~40px below. Location opens Google Maps. Apply opens
  each university's own `applicationUrl` via `url_launcher`.
- **Profile onboarding** (7 steps): back goes to previous page; on step 1 back
  goes to `/dashboard`; Save/Next hover-only highlight; Star between buttons.
- **Postal address**: question + Yes/No switch, default ON, address field dimmed
  until switched off.

## Assets
- University logos: `assets/logos/{id}.png` (local, offline-safe) for the newest
  entries; older ones use `assets/images/*`.
- University detail images: `_uniImages` map in `university_detail_screen.dart`.
- `assets/audio/` exists with `.gitkeep` — required by pubspec or hot restart fails.

## Operational
- ACEsi edits files; the user runs Flutter. Do not run flutter/adb/scrcpy.
- Commit and push after every edit (user's standing instruction).
- After 10 February 2026 ACEsi will run LibSyncStudent autonomously; see
  `D:\projectscesi\AGENTS.md` for ACEsi's operational rules and the live
  environment snapshot endpoint.
