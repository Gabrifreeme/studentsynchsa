# StudentSyncSA - Agent Instructions

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
- `[All]` button in WebView panel calls `_runAutofill()` → `star.buildAutofillScript(profile)`
- Generated JS uses `pMap` to try both `oap*` and `P_*` field names (ITS portals use `P_*`)
- `set()` handles text inputs, `setSelect()` handles radio buttons + selects
- Portal patches run on `onPageFinished` before auto-fill

## Common Issues
1. **Auto-fill not working**: Check JS injection in `webview_impl.dart` line 239, verify `pMap` lookup in `autofill_script.dart`
2. **Profile values mismatch dropdowns**: `auth_service.dart` hardcoded defaults must match dropdown items exactly
3. **Hive stale data**: Migration in `main.dart` patches old values (`'Black'`→`'African'`, `'Full-Time'`→`'YEAR'`, `'Accepted'`→`'I Accept'`)
4. **WebView permissions**: Requires `webview_flutter_android` for debugging

## Profile Field Mapping (oap* → P_*)
Key mappings in `autofill_script.dart` pMap:
- `oapSurname` → `P_SURNAME`
- `oapIdNumber` → `P_ID_NO`
- `oapEmail` → `P_EMAIL`
- `oapCellNo` → `P_CELL_NO`
- `oapStreet` → `P_ADDRESS_1`
- `oapCitizenType` → `P_CITIZEN_TYPE` (radio buttons)
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