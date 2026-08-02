import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

class AppWebView extends StatefulWidget {
  final String url;
  final String universityName;
  final StudentProfile? profile;

  const AppWebView({
    super.key,
    required this.url,
    required this.universityName,
    this.profile,
  });

  @override
  State<AppWebView> createState() => _AppWebViewState();
}

class _AppWebViewState extends State<AppWebView> {
  late final WebViewController _controller;
  bool _loading = true;
  StudentProfile? _profile;
  bool _isUniven = false;
  int _loadCount = 0;

  String? _profileJson;

  @override
  void initState() {
    super.initState();
    _profile = widget.profile;
    _isUniven = widget.universityName.toUpperCase() == 'UNIVEN';
    _loadProfileIfMissing();

    // DO NOT clearCookies() here — it races with the page load and can destroy
    // the APEX session cookie the portal just set, causing 404 on form submit.

    if (_profile != null) {
      _profileJson = jsonEncode(_profile!.toJson());
    }

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(true)
      ..setUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      )
      ..addJavaScriptChannel(
        'FlutterNavigation',
        onMessageReceived: (JavaScriptMessage message) {
          final targetUrl = message.message;
          debugPrint("🔴 JavaScript navigation: $targetUrl");
          if (targetUrl.startsWith('http') && mounted) {
            _controller.loadRequest(Uri.parse(targetUrl));
          }
        },
      )
      ..addJavaScriptChannel(
        'FlutterLog',
        onMessageReceived: (JavaScriptMessage message) {
          debugPrint("🟢 JS: ${message.message}");
        },
      );

    if (_controller.platform is AndroidWebViewController) {
      final androidController = _controller.platform as AndroidWebViewController;
      androidController.setTextZoom(150);
      // Third-party cookies handled by User-Agent
    }

    _controller
      ..addJavaScriptChannel(
        'AutofillResult',
        onMessageReceived: (JavaScriptMessage message) {
          try {
            final data = jsonDecode(message.message);
            if (data['diag'] != null) {
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('DIAG: ${data['diag']}'),
                    duration: const Duration(seconds: 12),
                    backgroundColor: Colors.blue,
                  ),
                );
              }
              return;
            }
            final filled = data['filled'] as int;
            final total = data['total'] as int;
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    '$filled of $total fields filled. Complete the reCAPTCHA, then tap "Open in Chrome" to submit.',
                  ),
                  duration: const Duration(seconds: 5),
                  backgroundColor: Colors.green,
                ),
              );
            }
          } catch (_) {}
        },
      )
      ..setNavigationDelegate(
       .onNavigationRequest: (request) {
  final url = request.url.toString();
  debugPrint("◉ NAVIGATION: $url");

  // FIX: Rewrite gw1p to gw1proc
  if (url.contains('gw1p') && !url.contains('gw1proc')) {
    final fixedUrl = url.replaceAll('gw1p', 'gw1proc');
    debugPrint("◉ REWRITING: $url -> $fixedUrl");
    return NavigationDecision.navigate;
  }

  if (url.contains('univenierp01') || url.contains('gw1pkg')) {
    debugPrint("◉ ITS PORTAL DETECTED!");
  }

  return NavigationDecision.navigate;
}

            // Allow gw1proc URLs through without modification
            if (url.contains('gw1proc')) return NavigationDecision.navigate;

            // Fix truncated URL: gw1p → gw1proc
            if (url.contains('gw1pkg.gw1p') && !url.contains('gw1proc')) {
              final fixedUrl = url.replaceAll('gw1pkg.gw1p', 'gw1pkg.gw1proc');
              debugPrint('🔧 Fixing truncated URL: $url → $fixedUrl');
              if (mounted) {
                _controller.loadRequest(Uri.parse(fixedUrl));
              }
              return NavigationDecision.prevent;
            }

            return NavigationDecision.navigate;
          },
          onPageStarted: (url) {
            debugPrint("📄 Page started: $url");
            setState(() => _loading = true);
          },
          onPageFinished: (url) async {
            debugPrint("✅ Page finished: $url");
            setState(() => _loading = false);

            _loadCount++;
            debugPrint("📊 Page load #$_loadCount");

            await _injectAllScripts(url);
          },
          onWebResourceError: (error) {
            debugPrint("🔴 ERROR: ${error.description}");
          },
          onProgress: (progress) {
            if (progress == 100) {
              debugPrint("✅ Loaded 100%");
            }
          },
        ),
      )
      ..loadRequest(Uri.parse(_getInitialUrl()));
  }

  Future<void> _injectAllScripts(String currentUrl) async {
    debugPrint("💉 Injecting scripts on: $currentUrl");

    try {
      await _controller.runJavaScript(star.buildNavigationFixScript());
      debugPrint("✅ Navigation fix injected");

      await _runPortalPatches();
      debugPrint("✅ Portal patches injected");

      // Autofill script is now loaded on-demand via star button
      // to prevent automatic form filling on page load
      debugPrint("ℹ️ Autofill script deferred (load on demand)");

      debugPrint("✅ All scripts injected successfully on: $currentUrl");

    } catch (e) {
      debugPrint("❌ Injection error: $e");
    }
  }

  String _getInitialUrl() {
    if (_isUniven) {
      return "https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP";
    }
    return widget.url;
  }

  Future<void> _runPortalPatches() async {
    try {
      await _controller.runJavaScript(star.buildViewportPatch());
      await _controller.runJavaScript(
        "var style = document.createElement('style'); style.innerHTML = '* { font-size: 16px !important; } input, select, textarea { font-size: 16px !important; }'; document.head.appendChild(style);",
      );
      await _controller.runJavaScript(star.buildBlanketAutofillSuppressScript());
      await _controller.runJavaScript(star.buildSecurityPatch());
      await _controller.runJavaScript(star.buildLabelPatch());
      await _controller.runJavaScript(star.buildAutocompletePatch());
      await _controller.runJavaScript(star.buildSelectAutocompletePatch());
      await _controller.runJavaScript(star.buildProvinceDisambiguationPatch());
      await _controller.runJavaScript(star.buildFocusPatch());
      await _controller.runJavaScript(star.buildInputmodePatch());
      await _controller.runJavaScript(star.buildFormLabelPatch());

      // WebView-specific: Enable DOM storage, fix Select2/APEX
      await _controller.runJavaScript("""
(function() {
  // Enable localStorage/sessionStorage for Select2 state persistence
  try {
    window.localStorage.setItem('webview_ready', 'true');
  } catch (e) {}

  // Fix Select2 rendering in WebView
  var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      mutation.addedNodes.forEach(function(node) {
        if (node.classList && node.classList.contains('select2-container')) {
          // Force Select2 to recalculate
          if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(node).trigger('resize');
          }
        }
      });
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });

  // Gender field auto-fix for APEX/Select2 in WebView
  function fixGenderField() {
    var select = document.querySelector('select[name="OAPGENDER"], select[name="oapGender"], #oapGender');
    if (!select) return;

    // Remove readonly/disabled
    select.removeAttribute('readonly');
    select.removeAttribute('disabled');

    // Set value
    select.value = 'F';

    // Fire events
    ['change', 'input', 'blur'].forEach(function(evt) {
      select.dispatchEvent(new Event(evt, { bubbles: true }));
    });

    // Update Select2 UI
    var container = document.querySelector('.select2-container');
    if (container) {
      var rendered = container.querySelector('.select2-selection__rendered');
      if (rendered) rendered.textContent = 'F Female';
      var placeholder = container.querySelector('.select2-selection__placeholder');
      if (placeholder) placeholder.remove();
      container.classList.remove('select2-container-error');
      if (window.jQuery && window.jQuery.fn.select2) {
        window.jQuery(container).trigger('resize');
      }
    }

    // Trigger APEX validation (critical for Next button)
    if (window.apex && window.apex.event) {
      window.apex.event.trigger(select, 'change');
      window.apex.event.trigger(select, 'apexafterrefresh');
    }
    if (window.apex && window.apex.item) {
      try { window.apex.item('OAPGENDER').refresh(); } catch(e) {}
    }
    if (window.apex && window.apex.page && window.apex.page.items) {
      try { window.apex.page.items.OAPGENDER.validate(); } catch(e) {}
    }
  }

  // Run on load and after any navigation
  fixGenderField();
  document.addEventListener('apexafterrefresh', fixGenderField);
  document.addEventListener('apexbeforepagesubmit', fixGenderField);
})();
""");

      // POSTAL CODE — replace broken section with clean HTML + portal validation
      await _controller.runJavaScript('''
(function() {
  var postalReplaced = false;

  function openPostalLookup() {
    var field = document.getElementById('oapStreetAddrPCodeRq');
    if (!field || field.value.trim() === '') {
      alert('Please enter a postal code first.');
      return;
    }
    callDynBGproc('web.ws29pkg.ws29valdata', '&x_type=POSTAL&x_name=oapStreetAddrPCodeRq&x_value=' + encodeURIComponent(field.value));
  }
  window.openPostalLookup = openPostalLookup;

  function replacePostalCode() {
    if (postalReplaced) return;

    // Find the LOV <a> tag whose onclick references oapStreetAddrPCodeRq
    var lovLinks = document.querySelectorAll('a[id^="LOVHref"]');
    var lovLink = null;
    for (var i = 0; i < lovLinks.length; i++) {
      var oc = lovLinks[i].getAttribute('onclick') || '';
      if (oc.indexOf('oapStreetAddrPCodeRq') !== -1) { lovLink = lovLinks[i]; break; }
    }
    if (!lovLink) return;

    // Walk up to the containing section
    var section = lovLink.closest('tr') || lovLink.closest('table') || lovLink.closest('fieldset') || lovLink.closest('div');
    if (!section) return;

    // Find the error div that follows this section
    var errorDiv = null;
    var el = section;
    for (var i = 0; i < 10 && el; i++) {
      el = el.nextElementSibling;
      if (!el) break;
      if (el.classList.contains('ErrorDivAndMsg') || el.classList.contains('ErrorDiv') ||
          (el.id && el.id.indexOf('Err') !== -1)) { errorDiv = el; break; }
      var inner = el.querySelector('.ErrorDivAndMsg, .ErrorDiv, [id*="Err"]');
      if (inner) { errorDiv = inner; break; }
    }

    // Delete everything from section up to (but not including) errorDiv
    var toDelete = [];
    var cur = section;
    while (cur && cur !== errorDiv) { toDelete.push(cur); cur = cur.nextElementSibling; }
    toDelete.forEach(function(d) { d.remove(); });

    // Insert clean HTML
    var parent = (errorDiv && errorDiv.parentNode) || document.body;

    var fld = document.createElement('div');
    fld.id = 'oapStreetAddrPCodeRqFld';
    fld.setAttribute('tag', 'oapStreetAddrPCodeRq');
    fld.setAttribute('pgseq', '246');
    fld.style.cssText = 'text-align:right; float:left;';

    var mainInput = document.createElement('input');
    mainInput.type = 'text';
    mainInput.name = 'oapStreetAddrPCodeRq';
    mainInput.id = 'oapStreetAddrPCodeRq';
    mainInput.style.cssText = 'display:inline-block';

    var descInput = document.createElement('input');
    descInput.type = 'hidden';
    descInput.name = 'oapStreetAddrPCodeRq_desc';
    descInput.id = 'oapStreetAddrPCodeRq_desc';
    descInput.value = '';

    var link = document.createElement('a');
    link.href = 'javascript: void(0)';
    link.setAttribute('onclick', 'openPostalLookup()');
    link.id = 'LOVHref_71';
    var img = document.createElement('img');
    img.src = '/itsimages/lov.gif';
    img.alt = 'Lookup';
    link.appendChild(img);

    fld.appendChild(mainInput);
    fld.appendChild(descInput);
    fld.appendChild(link);

    parent.insertBefore(fld, errorDiv);
    postalReplaced = true;
    console.log('POSTAL CODE REPLACED WITH CLEAN HTML');
  }

  replacePostalCode();
  setInterval(function() { if (!postalReplaced) replacePostalCode(); }, 500);
  new MutationObserver(function() { if (!postalReplaced) replacePostalCode(); }).observe(document.body, {childList: true, subtree: true});

  // Listen for desc field changes and copy to main field
  setInterval(function() {
    var desc = document.getElementById('oapStreetAddrPCodeRq_desc');
    var main = document.getElementById('oapStreetAddrPCodeRq');
    if (desc && main && desc.value && desc.value !== main.value) {
      main.value = desc.value;
      main.dispatchEvent(new Event('change', {bubbles: true}));
      console.log('POSTAL DESC COPIED: ' + desc.value);
    }
  }, 300);

  // Auto-fill street/city/province on postal code blur
  var profile = $_profileJson;
  if (profile) {
    var addr = (profile.address && profile.address.address) || '';
    var city = (profile.address && profile.address.addressLine2) || '';
    var prov = (profile.address && profile.address.province) || '';
    var postal = (profile.address && profile.address.postalCode) || '';

    document.addEventListener('blur', function(e) {
      if (e.target && e.target.id === 'oapStreetAddrPCodeRq') {
        console.log('POSTAL BLUR — filling address fields');
        // Street address
        var s1 = document.querySelector('input[name="OAPSTREETADDR1"]');
        if (s1 && !s1.value) { s1.value = addr; s1.dispatchEvent(new Event('change', {bubbles: true})); }
        // City / suburb
        var s2 = document.querySelector('input[name="OAPSTREETADDR2"]');
        if (s2 && !s2.value) { s2.value = city; s2.dispatchEvent(new Event('change', {bubbles: true})); }
        // Province (may be a select)
        var s4 = document.querySelector('input[name="OAPSTREETADDR4"], select[name="OAPSTREETADDR4"]');
        if (s4 && !s4.value) {
          if (s4.tagName === 'SELECT') {
            for (var i = 0; i < s4.options.length; i++) {
              if (s4.options[i].text.toUpperCase().indexOf(prov.toUpperCase()) !== -1) {
                s4.selectedIndex = i; break;
              }
            }
          } else {
            s4.value = prov;
          }
          s4.dispatchEvent(new Event('change', {bubbles: true}));
        }
        // Also set postal code desc if empty
        var desc = document.getElementById('oapStreetAddrPCodeRq_desc');
        if (desc && !desc.value && postal) { desc.value = postal; }
      }
    }, true);
    console.log('Auto-fill blur handler installed');
  }

  console.log('Postal code replacer installed');
})();
''');

      // Citizenship LOV - replaces broken APEX LOV with native select
      await _controller.runJavaScript('''
(function() {
  var citz = document.getElementById('oapCitzCode');
  if (!citz) return;

  var countryList = [
    'AFGHANISTAN', 'ALBANIA', 'ALGERIA', 'ANDORRA', 'ANGOLA',
    'ANTIGUA AND BARBUDA', 'ARGENTINA', 'ARMENIA', 'AUSTRALIA', 'AUSTRIA',
    'AZERBAIJAN', 'BAHAMAS', 'BAHRAIN', 'BANGLADESH', 'BARBADOS',
    'BELARUS', 'BELGIUM', 'BELIZE', 'BENIN', 'BHUTAN', 'BOLIVIA',
    'BOSNIA AND HERZEGOVINA', 'BOTSWANA', 'BRAZIL', 'BURKINA FASO',
    'BURUNDI', 'CAMEROON', 'CAPE VERDE', 'CENTRAL AFRICAN REPUBLIC',
    'CHAD', 'CORTE de VOIRE', 'DJIBOUTI', 'EGYPT', 'EQUATORIAL GUINEA',
    'ERITREA', 'ETHIOPIA', 'FRANCE', 'GABON', 'GAMBIA', 'GERMANY',
    'GHANA', 'GUINEA BISAU', 'INDIA', 'ITALY', 'KENYA', 'LESOTHO',
    'LIBERIA', 'LIBYA', 'MADAGASCAR', 'MALAWI', 'MALI', 'MAURITANIA',
    'MAURITIUS', 'MOROCCO', 'MOZAMBIQUE', 'NAMIBIA', 'NIGER', 'NIGERIA',
    'OTHER AFRICAN COUNTRIES', 'R.S.A.', 'RWANDA', 'SENEGAL', 'SEYCHELLES',
    'SIERRA LEONE', 'SUDAN', 'SWAZILAND', 'TANZANIA', 'TOGO', 'TUNISIA',
    'UGANDA', 'UNITED ARAB EMIRATES', 'ZAMBIA', 'ZIMBABWE'
  ];

  var wrapper = citz.closest('div');
  if (!wrapper) return;

  var lovBtn = wrapper.querySelector('a[onclick*="lov"], img[src*="lov.gif"]');
  if (lovBtn) lovBtn.remove();

  var select = document.createElement('select');
  select.id = 'custom-citz-code';
  select.style.cssText = 'width:100%;padding:8px;font-size:16px;border:1px solid #ccc;border-radius:4px;';

  var emptyOption = document.createElement('option');
  emptyOption.value = '';
  emptyOption.textContent = '';
  select.appendChild(emptyOption);

  countryList.forEach(function(country) {
    var opt = document.createElement('option');
    opt.value = country;
    opt.textContent = country;
    select.appendChild(opt);
  });

  select.addEventListener('change', function() {
    citz.value = this.value;
    citz.dispatchEvent(new Event('change', { bubbles: true }));
    citz.dispatchEvent(new Event('input', { bubbles: true }));
    console.log('Citizenship Code set to:', this.value);
  });

  var observer = new MutationObserver(function() {
    if (citz.value !== select.value) {
      select.value = citz.value;
    }
  });
  observer.observe(citz, { attributes: true, attributeFilter: ['value'] });
  citz.addEventListener('change', function() {
    select.value = citz.value;
  });
  citz.addEventListener('input', function() {
    select.value = citz.value;
  });

  wrapper.insertBefore(select, citz);
  console.log('Custom citizenship dropdown injected');
})();
''');

      // Heard about us LOV - replaces broken APEX LOV with native select
      await _controller.runJavaScript('''
(function() {
  var targetField = document.getElementById('oapHeard');
  if (!targetField) return;

  var options = [
    'FRIEND/FAMILY',
    'NEWSPAPER',
    'PERSONAL',
    'PUBLIC RELATION\\'S OFFICER',
    'RADIO',
    'SOCIAL MEDIA',
    'SCHOOL TEACHER',
    'TELEVISION',
    'UNIVEN WEB SITE'
  ];

  var wrapper = targetField.closest('div');
  if (!wrapper) return;

  var lovBtn = wrapper.querySelector('a[onclick*="lov"], img[src*="lov.gif"]');
  if (lovBtn) lovBtn.remove();

  var parent = targetField.parentElement;
  if (parent) {
    var parentLov = parent.querySelector('a[onclick*="lov"], img[src*="lov.gif"]');
    if (parentLov) parentLov.remove();
  }

  targetField.style.display = 'none';

  var select = document.createElement('select');
  select.style.cssText = 'width:100%;padding:8px;font-size:16px;border:1px solid #ccc;border-radius:4px;';

  var defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = '-- Select --';
  select.appendChild(defaultOption);

  options.forEach(function(option) {
    var opt = document.createElement('option');
    opt.value = option;
    opt.textContent = option;
    select.appendChild(opt);
  });

  select.addEventListener('change', function() {
    targetField.value = this.value;
    targetField.dispatchEvent(new Event('change', { bubbles: true }));
    targetField.dispatchEvent(new Event('input', { bubbles: true }));
    console.log('Selected:', this.value);
  });

  wrapper.insertBefore(select, targetField);
  console.log('Custom dropdown inserted for oapHeard');
})();
''');

      // Date picker — replace broken APEX calendar with native date input
      await _controller.runJavaScript('''
(function() {
  var dob = document.getElementById('oapBirthdate') || document.querySelector('input[name="oapBirthdate"]');
  if (!dob) return;

  var oldCustom = document.getElementById('custom-date-wrapper');
  if (oldCustom) oldCustom.remove();

  dob.removeAttribute('onfocus');
  dob.removeAttribute('onclick');
  dob.readOnly = false;
  dob.removeAttribute('readonly');
  dob.removeAttribute('disabled');
  dob.style.display = 'none';

  var row = dob.closest('div') || dob.parentElement;
  if (row) {
    row.querySelectorAll('a, img, button, span[class*="calendar"]').forEach(function(el) {
      if (!el.contains(dob)) el.style.display = 'none';
    });
  }

  var monthNames = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  var wrapper = document.createElement('div');
  wrapper.id = 'custom-date-wrapper';
  wrapper.style.cssText = 'display:inline-flex;gap:8px;align-items:flex-end;margin:8px 0;';

  function makeSelect(label, options, widthPx) {
    var div = document.createElement('div');
    div.style.cssText = 'display:flex;flex-direction:column;gap:2px;';
    var lbl = document.createElement('label');
    lbl.textContent = label;
    lbl.style.cssText = 'font-size:11px;color:#888;font-weight:bold;text-transform:uppercase;';
    var sel = document.createElement('select');
    sel.style.cssText = 'width:' + widthPx + 'px;padding:10px 8px;font-size:18px;border:1px solid #ccc;border-radius:4px;text-align:center;font-family:monospace;background:#fff;';
    var placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = label;
    placeholder.disabled = true;
    placeholder.selected = true;
    sel.appendChild(placeholder);
    options.forEach(function(opt) {
      var o = document.createElement('option');
      o.value = opt;
      o.textContent = opt;
      sel.appendChild(o);
    });
    div.appendChild(lbl);
    div.appendChild(sel);
    return {div: div, select: sel};
  }

  var days = [];
  for (var i = 1; i <= 31; i++) days.push(String(i));
  var years = [];
  for (var y = 2030; y >= 1900; y--) years.push(String(y));

  var dayPart = makeSelect('DD', days, 60);
  var monthPart = makeSelect('MON', monthNames, 80);
  var yearPart = makeSelect('YYYY', years, 100);

  dayPart.select.addEventListener('change', updateDob);
  monthPart.select.addEventListener('change', updateDob);
  yearPart.select.addEventListener('change', updateDob);

  function updateDob() {
    var d = dayPart.select.value;
    var m = monthPart.select.value;
    var y = yearPart.select.value;
    if (d && m && y) {
      var formatted = parseInt(d) + '-' + m + '-' + y;
      dob.value = formatted;
      dob.dispatchEvent(new Event('input', { bubbles: true }));
      dob.dispatchEvent(new Event('change', { bubbles: true }));
      console.log('Date set to:', formatted);
    }
  }

  wrapper.appendChild(dayPart.div);
  wrapper.appendChild(monthPart.div);
  wrapper.appendChild(yearPart.div);
  dob.parentNode.insertBefore(wrapper, dob);
  console.log('Date dropdowns added');
})();
''');
    } catch (_) {}
  }

  void _showAutofillPrompt() {
    if (_profileJson == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No profile found. Complete your profile first.')),
      );
      return;
    }
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Auto-fill'),
        content: const Text('You like me to try and auto fill this page?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('No'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              _runAutofill();
            },
            child: const Text('Yes'),
          ),
        ],
      ),
    );
  }

  Future<void> _runAutofill() async {
    if (_profileJson == null) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Attempting to autofill form...'), duration: Duration(seconds: 2)),
    );
    try {
      await _controller.runJavaScript(star.buildAutofillOnlyScript(_profileJson!));
      await Future.delayed(const Duration(milliseconds: 30));
      await _controller.runJavaScript('window.requestFlutterAutofill();');
      await _controller.runJavaScript(star.buildRemoveOldPostalPickerScript());
      await _controller.runJavaScript(star.buildPostalCodePickerScript(_profileJson!));
      debugPrint('✅ Autofill + postal picker executed on demand');
    } catch (e) {
      debugPrint('❌ Autofill execution failed: $e');
    }
  }

  Future<void> _loadProfileIfMissing() async {
    if (_profile != null) {
      _profileJson = jsonEncode(_profile!.toJson());
      return;
    }

    final repo = ProfileRepositoryImpl();
    var p = await repo.getProfile();
    if (p == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      p = await repo.getProfile();
    }
    if (p == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      p = await repo.getProfile();
    }
    if (p != null && mounted) {
      final profile = p;
      setState(() {
        _profile = profile;
        _profileJson = jsonEncode(profile.toJson());
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: Colors.blue.shade800,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.star, color: Colors.amber, size: 30),
            onPressed: _showAutofillPrompt,
            tooltip: 'Auto-fill',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _controller.reload(),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading)
            const Center(
              child: CircularProgressIndicator(),
            ),
        ],
      ),
    );
  }
}
