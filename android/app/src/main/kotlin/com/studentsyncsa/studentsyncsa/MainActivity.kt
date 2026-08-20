package com.studentsyncsa.studentsyncsa

import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebResourceRequest
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import android.view.View
import android.view.ViewGroup

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // Enable Android WebView remote debugging so Chrome DevTools Protocol
        // tools (CDP over ws://) can inspect console logs, network and the DOM.
        // Must be set before the Flutter/WebView engine inflates any WebView.
        android.webkit.WebView.setWebContentsDebuggingEnabled(true)
        super.onCreate(savedInstanceState)
        
        // Clear cookies for Venda specifically to avoid "Cookie Bloat" / URL length limit
        // Venda's server has a stricter URL length limit, and accumulated cookies
        // can cause the request header to exceed the server's limit, resulting in 404.
        clearVendaCookies()
        
        // Set up a listener to find and patch WebViews after they're created
        val flutterView = findViewById<android.view.View>(android.R.id.content)
        if (flutterView != null) {
            setupWebViewInterception(flutterView)
        }
    }
    
    /// Clear cookies for Venda specifically to prevent "Cookie Bloat" / URL length limit
    /// Venda's server has a stricter URL length limit, and accumulated cookies
    /// can cause the request header to exceed the server's limit, resulting in 404.
    private fun clearVendaCookies() {
        val cookieManager = CookieManager.getInstance()
        // Remove all cookies for Venda's domain
        cookieManager.removeSessionCookies(null)
        CookieManager.getInstance().removeAllCookies(null)
        CookieManager.getInstance().flush()
        
        // Also clear cache
        val webView = android.webkit.WebView(this)
        webView.clearCache(true)
        webView.clearHistory()
        webView.clearFormData()
    }
    
    private fun setupWebViewInterception(view: android.view.View) {
        // Traverse the view hierarchy to find WebViews and set custom WebViewClient
        if (view is android.webkit.WebView) {
            setupWebViewClient(view)
        } else if (view is ViewGroup) {
            for (i in 0 until view.childCount) {
                setupWebViewInterception(view.getChildAt(i))
            }
        }
    }
    
    private fun setupWebViewClient(webView: android.webkit.WebView) {
        val client = object : android.webkit.WebViewClient() {
            override fun shouldOverrideUrlLoading(view: android.webkit.WebView, request: android.webkit.WebResourceRequest): Boolean {
                val url = request.url.toString()
                
                // Also intercept navigation requests
                if (isItsHost(url)) {
                    val fixedUrl = fixItsUrl(url)
                    if (fixedUrl != url) {
                        view.loadUrl(fixedUrl)
                        return true
                    }
                }
                
                return super.shouldOverrideUrlLoading(view, request)
            }
            
            override fun shouldInterceptRequest(view: android.webkit.WebView, request: android.webkit.WebResourceRequest): android.webkit.WebResourceResponse? {
                val url = request.url.toString()
                
                // Only intercept ITS portal URLs
                if (isItsHost(url)) {
                    val fixedUrl = fixItsUrl(url)
                    if (fixedUrl != url) {
                        // URL was truncated - rewrite and intercept
                        val fixedUrlObj = android.net.Uri.parse(fixedUrl)
                        // We can't easily rebuild WebResourceRequest, so we rely on
                        // shouldOverrideUrlLoading for navigation requests.
                        // For resource requests, we let them through and rely on
                        // the navigation fix in shouldOverrideUrlLoading.
                    }
                }
                
                return super.shouldInterceptRequest(view, request)
            }
        }
        webView.webViewClient = client
    }
    
    private fun isItsHost(url: String): Boolean {
        return url.contains("univenierp01") ||
            url.contains("univenerp01") ||
            url.contains("univenerip01") ||
            url.contains("unlvenierp01") ||
            url.contains("/pls/prodi41") ||
            url.contains("/pls/")
    }
    
    private fun fixItsUrl(url: String): String {
        var out = url
        // Fix domain typos
        out = out
            .replace("unlven", "univen")
            .replace("univenerp01", "univenierp01")
            .replace("univenerp01", "univenierp01") // duplicate but harmless
            .replace("univenerip01", "univenierp01")
            .replace("unlvenierp01", "univenierp01")
        
        // Fix protocol
        if (out.startsWith("http://")) {
            out = out.replaceFirst("http://", "https://")
        }
        
        // Fix procedure truncation
        // Full marker: gen.gw1pkg.gw1
        val fullMarker = "gen.gw1pkg.gw1"
        var i = out.indexOf(fullMarker)
        if (i != -1) {
            return expandFromMarker(out, i, fullMarker.length, true)
        }
        
        // Short marker: gen.gw1pkg.gw (truncated marker)
        val shortMarker = "gen.gw1pkg.gw"
        val shortIdx = out.indexOf(shortMarker)
        if (shortIdx != -1) {
            return expandFromMarker(out, shortIdx, shortMarker.length, false)
        }
        
        return url
    }
    
    private fun expandFromMarker(url: String, markerPos: Int, markerLen: Int, fullMarker: Boolean): String {
        val restStart = markerPos + markerLen
        val rest = url.substring(restStart)
        val q = rest.indexOf('?')
        val sl = rest.indexOf('/')
        val hash = rest.indexOf('#')
        val cut = if (q == -1 && sl == -1 && -1 == url.indexOf('#', restStart)) rest.length
        else {
            var c = rest.length
            if (q != -1 && q < c) c = q
            if (sl != -1 && sl < c) c = sl
            val h = url.indexOf('#', restStart)
            if (h != -1 && h < c) c = h - restStart
            c
        }
        val proc = rest.substring(0, cut)
        val tail = url.substring(cut)
        
        if (fullMarker) {
            // Full marker "gen.gw1pkg.gw1" - expect "view" or "proc" (or truncations 'v', 'p')
            when (proc) {
                "v", "vi", "vie", "view" -> return url.substring(0, restStart) + "view" + tail
                "p", "pr", "pro", "proc" -> return url.substring(0, restStart) + "proc" + tail
                else -> return url
            }
        } else {
            // Short marker "gen.gw1pkg.gw" - remainder should start with "1view"/"1proc" or truncations
            if (proc.startsWith("1v") || proc.startsWith("1gwa") || proc.startsWith("1gwav") ||
                proc.startsWith("1gwas") || proc == "1" || proc.isEmpty()) {
                return url.substring(0, restStart) + "1view" + tail
            }
            if (proc.startsWith("1p") || proc == "1") {
                return url.substring(0, restStart) + "1proc" + tail
            }
            return url
        }
    }
}