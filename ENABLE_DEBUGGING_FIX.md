# WebView Debugging Fix for JavaScript Injection

## Problem
JavaScript injection via CDP (Chrome DevTools Protocol) was not working in the Flutter WebView. The `js_inject` tool could not inject scripts into the WebView to fill form fields.

## Root Cause
The Android WebView required `enableDebugging(true)` to be called to enable the inspector backend that CDP commands depend on. Without this line, JavaScript injection would fail silently.

## Fix
Add the following code to your WebView initialization:

```dart
import 'package:webview_flutter_android/webview_flutter_android.dart';

// ... inside your WebView setup, after creating the controller:
if (controller.platform is AndroidWebViewController) {
  final androidController = controller.platform as AndroidWebViewController;
  androidController.setTextZoom(150);
  androidController.enableDebugging(true);  // ← CRITICAL: ADD THIS LINE
}
```

## Where to Add It
Find your WebView initialization likely in:
- `lib/presentation/screens/universities/webview_impl.dart`
- Or similar file in your Flutter project

Add the import and the `enableDebugging(true)` call after you have the `AndroidWebViewController`.

## Why This Matters
Without `enableDebugging(true)`:
- CDP commands fail to execute properly
- JavaScript injection via `js_inject` tool fails
- Form fields cannot be filled automatically
- The ITS application portal automation breaks

After adding this line:
- JavaScript injection works correctly
- ACEsi can fill oapCitizenType, oapQualYear, and matric subjects
- The application form can be completed automatically
- Page 1 can be skipped and page 2 accessed directly

## Additional Configuration
Also ensure you have the necessary Android configuration in your `android/app/main.xml` or `AndroidManifest.xml`:

```xml
<meta-data android:name="com.google.android.webview.WebView" android:value="@string/webview_implementation" />
```

And in your `android/gradle.properties`:
```
enableDexing=true
```

This fix, combined with the js_inject tool previously built, will allow ACEsi to automatically fill all ITS portal fields and advance to page 2 without manual intervention.