package com.studentsyncsa.studentsyncsa

import android.os.Bundle
import android.webkit.WebView
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // Enable Android WebView remote debugging so Chrome DevTools Protocol
        // tools (CDP over ws://) can inspect console logs, network and the DOM.
        // Must be set before the Flutter/WebView engine inflates any WebView.
        WebView.setWebContentsDebuggingEnabled(true)
        super.onCreate(savedInstanceState)
    }
}
