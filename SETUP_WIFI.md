# ACEsi Persistent WiFi Connection Setup

## Quick Start (Every Session)

Run: `connect_wifi.bat`

This script will:
1. Connect ADB over WiFi to the tablet
2. Launch StudentSyncSA if not running
3. Start ACEsi server if not running

## One-Time Tablet Setup

### Option A: Keep WiFi ADB Always On (Recommended)

1. On the tablet, go to **Settings > About tablet**
2. Tap **Build number** 7 times to enable Developer Options
3. Go to **Settings > Developer options**
4. Enable **USB debugging** (required for initial setup)
5. Enable **Wireless debugging**
6. In Wireless debugging settings:
   - Tap **Pair device with pairing code**
   - Note the IP address and port shown
   - On PC: `adb pair <ip>:<port>` then enter the pairing code
   - After pairing: `adb connect <ip>:<port>`

### Option B: Auto-Launch StudentSyncSA on Boot (Optional)

If the tablet is rooted or you have ADB access:
```bash
adb shell am start -n com.studentsyncsa.studentsyncsa/.MainActivity
```

Or use a startup manager app on the tablet to launch StudentSyncSA on boot.

## Auto-Start ACEsi on Windows Boot

1. Press `Win + R`, type `shell:startup`
2. Create a shortcut to `C:\Users\chris\StudentSyncSA\start_acesi.bat`
3. ACEsi will now start automatically when Windows boots

## Troubleshooting

### "adb: no devices/emulators found"
- Ensure tablet and PC are on the same WiFi network
- Check tablet's IP: Settings > About tablet > Status > IP address
- Update `TABLET_IP` in `connect_wifi.bat`

### "Connection refused"
- Wireless debugging might have been disabled on tablet
- Re-enable in Developer options
- The port may have changed - check Wireless debugging settings

### StudentSyncSA won't start
- Check if the app is installed: `adb shell pm list packages | findstr studentsyncsa`
- Install APK if missing: `adb install path/to/app.apk`
