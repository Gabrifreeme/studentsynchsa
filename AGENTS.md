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
