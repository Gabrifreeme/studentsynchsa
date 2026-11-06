// ─────────────────────────────────────────────────────────────────────────────
// apply_interceptor.dart  –  Apply-button navigation interceptor
//
// Injects a small JS bridge into the ITS WebView so that the portal's
// "Apply / Submit / Next" button reliably advances the page even when:
//   - the button is re-rendered on every sub-page (needs continuous injection)
//   - a duplicate listener would otherwise stack up (needs a de-dup guard)
//   - the button's href is a relative URL like "gw1view" or "../oap" that
//     must be resolved against the page's own base URI
//
// Design notes (why each part exists):
//   * The script is intentionally RE-INJECTION SAFE. The Dart side re-injects
//     it on every onPageFinished (and on sub-page navigation), so the JS must
//     NOT bail out just because it ran before — a previous page's button bar
//     is gone and a new one needs hooking. Instead it always re-scans and uses
//     a per-element data attribute to stop duplicate listeners.
//   * A single polling interval is guarded by a module-level flag so repeated
//     injections never stack timers.
//   * `capture: true` on the click listener runs it before other scripts and
//     before the browser's default navigation, so it can redirect reliably.
// ─────────────────────────────────────────────────────────────────────────────

/// Build the JS that hooks the Apply button. Pass [targetText] to match a
/// specific button label (case-insensitive substring), or null to match any
/// submit-like button.
String buildApplyInterceptor({String? targetText}) {
  final selector = _buildSelector(targetText);
  final target = targetText == null ? 'null' : jsonStr(targetText);
  return '${'''
(function() {
  var SELECTOR = $selector;
  var TARGET = $target;

  function resolveUrl(url) {
    try {
      // Relative URLs (common on ITS portals: "gw1view", "../oap", "?p=1")
      // must be resolved against the page's own base URI, not the app's.
      return new URL(url, document.baseURI).href;
    } catch (e) {
      return url;
    }
  }

  function matchesTarget(el) {
    if (!TARGET) return true;
    var text = (el.textContent || '').toLowerCase();
    var val  = (el.value || '').toLowerCase();
    var title = (el.getAttribute('title') || '').toLowerCase();
    var aria  = (el.getAttribute('aria-label') || '').toLowerCase();
    return text.indexOf(TARGET) !== -1
        || val.indexOf(TARGET) !== -1
        || title.indexOf(TARGET) !== -1
        || aria.indexOf(TARGET) !== -1;
  }

  function hook(el) {
    if (!el) return;
    // De-dup: never attach twice to the same element, even across
    // re-injections. This is the duplicate-listener guard.
    if (el.getAttribute('data-ssa-apply-hooked') === '1') return;
    el.setAttribute('data-ssa-apply-hooked', '1');

    el.addEventListener('click', function(e) {
      var href = el.getAttribute('href');
      if (!href) return;   // no href -> let the native submit happen
      var resolved = resolveUrl(href);
      console.log('[ssa-apply] ' + (el.textContent || '').trim() +
                   ' -> ' + href + ' (resolved: ' + resolved + ')');
      window.location.assign(resolved);
    }, true);   // capture: true -> runs before other scripts / preventDefault
  }

  function scan() {
    var nodes = document.querySelectorAll(SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (TARGET && !matchesTarget(el)) continue;
      hook(el);
    }
  }

  // Initial scan on every injection (re-injection safe: no global early return).
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scan);
  } else {
    scan();
  }

  // Re-scan on sub-page navigation: the portal re-renders the button bar and
  // a one-time injection would miss it. Guard the interval so repeated
  // injections never stack timers.
  if (!window.__ssaApplyTimer) {
    var _t = setInterval(scan, 1500);
    window.__ssaApplyTimer = true;
    setTimeout(function() {
      try { clearInterval(_t); window.__ssaApplyTimer = false; } catch (e) {}
    }, 15000);
  }

  console.log('[ssa-apply] interceptor scanned: ' + SELECTOR);
})();
'''
  .trim()}\n';
}

/// Build the CSS selector list for submit-like Apply buttons.
/// NOTE: only real `querySelectorAll` selectors are used — `:contains()`
/// would silently match nothing, so label matching is done in JS instead.
String _buildSelector(String? targetText) {
  final parts = <String>[
    'button[type="submit"]',
    'input[type="submit"]',
    'button[data-id="NEXT"]',
    '#B_NEXT',
    'button[data-id="APPLY"]',
    'button[data-id="SUBMIT"]',
    'input[value="Apply"]',
    'input[value="Submit"]',
    'input[value="Next"]',
    'button[class*="t-Button"]',
    'a[class*="t-Button"]',
    'button[class*="button"]',
  ];
  return jsonStr(parts.join(', '));
}

String jsonStr(String s) => '"${s.replaceAll('\\', '\\\\').replaceAll('"', '\\"')}"';