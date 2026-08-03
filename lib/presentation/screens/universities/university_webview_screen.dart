import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

class UniversityWebViewScreen extends ConsumerStatefulWidget {
  final String url;
  final String universityName;

  const UniversityWebViewScreen({
    super.key,
    required this.url,
    required this.universityName,
  });

  @override
  ConsumerState<UniversityWebViewScreen> createState() => _UniversityWebViewScreenState();
}

class _UniversityWebViewScreenState extends ConsumerState<UniversityWebViewScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  String _currentUrl = '';
  String? _profileJson;

  @override
  void initState() {
    super.initState();

    _loadProfile();

    // DO NOT clearCookies() here — it races with the page load and can destroy
    // the APEX session cookie the portal just set, causing 404 on form submit.

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(true)
      ..setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      )
      ..addJavaScriptChannel('AutofillResult', onMessageReceived: (msg) {
        try {
          final data = jsonDecode(msg.message);
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
      });

    if (_controller.platform is AndroidWebViewController) {
      (_controller.platform as AndroidWebViewController).setTextZoom(150);
      (_controller.platform as AndroidWebViewController).setOnConsoleMessage((msg) {
        debugPrint('[WebView ${msg.level}] ${msg.message}');
      });
    }

    _controller
      .setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (request) {
            final url = request.url.toString();
            debugPrint('🟡 Navigation: $url');

            // Allow gw1proc URLs through without modification.
            if (url.contains('gw1proc')) return NavigationDecision.navigate;

            // A truncated ITS URL (gw1pkg.gw1p) is a truncated report of the
            // form's own POST. The JS navfix (buildNavigationFixScript) already
            // rewrites every form action to the full .../gen.gw1pkg.gw1proc
            // BEFORE the request is built (see the 'Form action' DIAG snackbar),
            // so the real POST goes to the correct URL. Do NOT cancel it and
            // reload as a GET loadRequest — that drops the POST body and the
            // portal 404s. Just let it flow and surface the report for diagnosis.
            if (url.contains('gw1pkg.gw1p') && !url.contains('gw1proc')) {
              debugPrint('🔎 Truncated ITS URL (letting real POST flow): $url');
              _reportTruncatedUrl(url);
            }

            return NavigationDecision.navigate;
          },
          onPageStarted: (url) {
            _currentUrl = url;
            setState(() => _loading = true);
          },
          onPageFinished: (url) async {
            _currentUrl = url;
            setState(() => _loading = false);
            debugPrint('ℹ️ Autofill deferred — user must tap star to fill');
            try {
              await _controller.runJavaScript(star.buildNavigationFixScript());
              debugPrint('✅ Navigation fix injected');
            } catch (e) {
              debugPrint('❌ Navigation fix error: $e');
            }
            try {
              await _controller.runJavaScript('''
(function() {
  var citz = document.getElementById('oapCitzCode');
  if (!citz) return;
  if (document.getElementById('custom-citz-code')) return;

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
              debugPrint('✅ Citizenship dropdown injected');
            } catch (e) {
              debugPrint('❌ Citizenship dropdown error: $e');
            }
            try {
              await _controller.runJavaScript('''
(function() {
  var targetField = document.getElementById('oapHeard');
  if (!targetField) return;
  if (document.getElementById('ssa-heard-select')) return;

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

  // Also search parent for LOV button
  var parent = targetField.parentElement;
  if (parent) {
    var parentLov = parent.querySelector('a[onclick*="lov"], img[src*="lov.gif"]');
    if (parentLov) parentLov.remove();
  }

  targetField.style.display = 'none';

  var select = document.createElement('select');
  select.id = 'ssa-heard-select';
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
              debugPrint('✅ Heard about us dropdown injected');
            } catch (e) {
              debugPrint('❌ Heard about us dropdown error: $e');
            }
            try {
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

    var lovLinks = document.querySelectorAll('a[id^="LOVHref"]');
    var lovLink = null;
    for (var i = 0; i < lovLinks.length; i++) {
      var oc = lovLinks[i].getAttribute('onclick') || '';
      if (oc.indexOf('oapStreetAddrPCodeRq') !== -1) { lovLink = lovLinks[i]; break; }
    }
    if (!lovLink) return;

    var section = lovLink.closest('tr') || lovLink.closest('table') || lovLink.closest('fieldset') || lovLink.closest('div');
    if (!section) return;

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

    var toDelete = [];
    var cur = section;
    while (cur && cur !== errorDiv) { toDelete.push(cur); cur = cur.nextElementSibling; }
    toDelete.forEach(function(d) { d.remove(); });

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
    console.log('POSTAL CODE REPLACED');
  }

  replacePostalCode();
  setInterval(function() { if (!postalReplaced) replacePostalCode(); }, 500);
  new MutationObserver(function() { if (!postalReplaced) replacePostalCode(); }).observe(document.body, {childList: true, subtree: true});

  setInterval(function() {
    var desc = document.getElementById('oapStreetAddrPCodeRq_desc');
    var main = document.getElementById('oapStreetAddrPCodeRq');
    if (desc && main && desc.value && desc.value !== main.value) {
      main.value = desc.value;
      main.dispatchEvent(new Event('change', {bubbles: true}));
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
        var s1 = document.querySelector('input[name="OAPSTREETADDR1"]');
        if (s1 && !s1.value) { s1.value = addr; s1.dispatchEvent(new Event('change', {bubbles: true})); }
        var s2 = document.querySelector('input[name="OAPSTREETADDR2"]');
        if (s2 && !s2.value) { s2.value = city; s2.dispatchEvent(new Event('change', {bubbles: true})); }
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
        var desc = document.getElementById('oapStreetAddrPCodeRq_desc');
        if (desc && !desc.value && postal) { desc.value = postal; }
      }
    }, true);
  }
})();
''');
              debugPrint('✅ Postal code replaced with clean HTML');
            } catch (e) {
              debugPrint('❌ Postal code replacement error: $e');
            }
            try {
              await _controller.runJavaScript('''
(function() {
  var dob = document.getElementById('oapBirthdate') || document.querySelector('input[name="oapBirthdate"]');
  if (!dob) return;
  if (document.getElementById('ssa-date-picker')) return;

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
              debugPrint('✅ Date picker injected');
            } catch (e) {
              debugPrint('❌ Date picker error: $e');
            }
            // TEMP: Hardcode postal code for Next button testing
            try {
              await _controller.runJavaScript('''
(function() {
  var pcode = document.querySelector('[name="oapStreetAddrPCodeRq"]');
  var pdesc = document.querySelector('[name="oapStreetAddrPCodeRq_desc"]');
  if (pcode && (!pcode.value || pcode.value.length < 4)) {
    pcode.value = '2197';
    if (pdesc) {
      pdesc.value = 'JOHANNESBURG';
      pdesc.dispatchEvent(new Event('change', {bubbles: true}));
    }
    console.log('TEMP: Postal code set to 2197 / JOHANNESBURG');
  }
})();
''');
              debugPrint('✅ Temp postal code injected');
            } catch (_) {}

            // Remove old postal code picker and ensure the new picker is visible/functional.
            // Runs after the page has fully loaded and uses a MutationObserver so it survives
            // late re-injection by the portal's own scripts.
            try {
              await _controller.runJavaScript('''
(function() {
  // --- CONFIG ----------------------------------------------------------------
  // CSS selector for the new picker. Swap this for the real id/class once known.
  // Examples:
  //   '#newPostalCodePicker'
  //   '.postal-code-picker--new'
  //   '[data-picker="postal-code"]'
  var NEW_PICKER_SELECTOR = '#newPostalCodePicker';
  // ---------------------------------------------------------------------------

  function removeOldPicker() {
    var old = document.getElementById('oapStreetAddrPCodeRqFld');
    if (old) {
      old.style.setProperty('display', 'none', 'important');
      console.log('OLD POSTAL PICKER HIDDEN');
      return true;
    }
    return false;
  }

  function showNewPicker() {
    var el = document.querySelector(NEW_PICKER_SELECTOR);
    if (!el) return false;
    // Clear the content attribute FIRST (it's reflected to el.hidden), then
    // set the IDL attribute — otherwise removeAttribute would clobber a
    // freshly-assigned el.hidden = false.
    el.removeAttribute('hidden');
    el.hidden = false;
    el.style.display = '';
    el.style.visibility = 'visible';
    el.style.opacity = '1';
    // Clear any inline 'display:none' / hidden flags that may be reapplied.
    el.classList.remove('hidden', 'is-hidden', 'oap-hidden');
    console.log('NEW POSTAL PICKER VISIBLE');
    return true;
  }

  // 1) Run once now.
  removeOldPicker();
  showNewPicker();

  // 2) Run again after the load event — beats scripts that fire on window 'load'.
  window.addEventListener('load', function() {
    removeOldPicker();
    showNewPicker();
  });

  // 3) Run again after a short delay — beats scripts that run on a short timer
  //    after DOMContentLoaded.
  setTimeout(function() { removeOldPicker(); showNewPicker(); }, 250);
  setTimeout(function() { removeOldPicker(); showNewPicker(); }, 1000);
  setTimeout(function() { removeOldPicker(); showNewPicker(); }, 3000);

  // 4) Watch the DOM. The portal may re-inject the old picker via AJAX or its
  //    own onload handlers — keep removing it and keep the new picker visible.
  var observer = new MutationObserver(function() {
    removeOldPicker();
    showNewPicker();
  });
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['style', 'class', 'hidden', 'disabled']
  });

  // 5) Also re-run just before the user navigates away (form submit), so the
  //    old picker can't come back in a race with the submit.
  window.addEventListener('beforeunload', function() {
    removeOldPicker();
    showNewPicker();
  });
})();
''');
              debugPrint('✅ Old postal picker removed, new picker ensured visible');
            } catch (e) {
              debugPrint('❌ Postal picker swap error: $e');
            }
          },
          onWebResourceError: (err) => debugPrint('❌ WebView: ${err.description}'),
          onSslAuthError: (error) => error.proceed(),
        ),
      );

    _loadPortal();
  }

  Future<void> _loadPortal() async {
    await _controller.loadRequest(Uri.parse(_resolveUrl()));
  }

  void _reportTruncatedUrl(String url) {
    debugPrint('🔎 Truncated ITS URL reported: $url');
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('DIAG: truncated ITS URL seen (POST left intact): $url'),
          duration: const Duration(seconds: 6),
          backgroundColor: Colors.orange,
        ),
      );
    }
  }

  String _resolveUrl() {
    final name = widget.universityName.toUpperCase();
    if (name == 'UNIVEN' || name == 'VENDA') {
      return 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP';
    }
    return widget.url;
  }

  void _openInChrome() async {
    final uri = Uri.parse(_resolveUrl());
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('❌ launchUrl failed: $e');
    }
  }

  void _loadProfile() {
    final profile = ref.read(profileProvider).valueOrNull;
    if (profile != null) {
      _profileJson = jsonEncode(profile.toJson());
    }
  }

  Future<void> _injectAutofill(BuildContext dialogContext) async {
    if (_profileJson == null) {
      _loadProfile();
    }
    if (_profileJson != null) {
      Navigator.pop(dialogContext);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Attempting to autofill form...'), duration: Duration(seconds: 2)),
        );
      }
      try {
        await _controller.runJavaScript(star.buildAutofillOnlyScript(_profileJson!));
        await Future.delayed(const Duration(milliseconds: 30));
        await _controller.runJavaScript('window.requestFlutterAutofill();');
        await _controller.runJavaScript(star.buildRemoveOldPostalPickerScript());
        await _controller.runJavaScript(star.buildPostalCodePickerScript(_profileJson!));
        debugPrint('✅ Autofill + postal picker injected');
      } catch (e) {
        debugPrint('❌ Autofill injection failed: $e');
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No profile found. Complete your profile first.')),
        );
      }
    }
  }

  ({String title, List<(String, String)> steps}) _guidanceForPage(String url) {
    final u = url.toLowerCase();

    if (widget.universityName.toUpperCase() == 'UNIVEN' || widget.universityName.toUpperCase() == 'VENDA') {
      return (
        title: 'Venda Application Guide',
        steps: [
          ('', 'This steps are very easy, if you are a new student then you do not have a student number, tap on "Please select" and pick NO, if you are returning to complete an application form pick YES but if you new then it is NO'),
          ('', 'next if you have a Qualification Specific Token pick YES, but when you new, you don\'t have then it will be NO again.'),
          ('', 'That\'s it just do your consent to Venda university by tapping yes and next, If you like to read the POPI Clause first follow this link: https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view'),
        ],
      );
    }

    if (u.contains('gw1view') || u.contains('oap') || u.contains('biographical') || u.contains('nok')) {
      return (
        title: '📋 Application Process',
        steps: [
          ('1', 'Fill Next of Kin name, mobile, home & work phone'),
          ('2', 'Enter Next of Kin postal address lines 1-4 and code'),
          ('3', 'Enter Next of Kin email address'),
          ('4', 'Fill Account Contact name, mobile & home phone'),
          ('5', 'Enter Account Contact postal address lines 1-4 and code'),
          ('6', 'Enter Account Contact email address'),
        ],
      );
    }

    if (u.contains('id') || u.contains('persona') || u.contains('idnum') || u.contains('nationality') || u.contains('biographical')) {
      return (
        title: '🆔 Biographical Details',
        steps: [
          ('1', 'Select SA Citizen status'),
          ('2', 'Enter Citizenship Code'),
          ('3', 'Select Gender, Date of Birth (DD-MON-YYYY), Title'),
          ('4', 'Enter Initials, Surname, First Names'),
          ('5', 'Maiden name (optional)'),
          ('6', 'Select Marital Status, Home Language, Ethnic Group'),
          ('7', 'Select Employed? and Bursary required?'),
          ('8', 'Where did you hear about us?'),
          ('9', 'Street Address Line 1-4, Postal Code'),
          ('10', 'Tick if Postal Address differs from Street'),
          ('11', 'SA Cell Phone Number?'),
          ('12', 'Work Telephone, Home Telephone'),
          ('13', 'Email and Verify email'),
          ('14', 'Apply for residence?'),
          ('15', 'Disability or impairment?'),
        ],
      );
    }

    if (u.contains('contact') || u.contains('addr') || u.contains('phone')) {
      return (
        title: '📞 Address & Contact',
        steps: [
          ('1', 'Enter Street Address lines 1-4 and Postal Code'),
          ('2', 'Tick if Postal Address is different from Street'),
          ('3', 'Enter Email and Verify email'),
          ('4', 'Enter Home Telephone and Work Telephone'),
          ('5', 'Select Residence and Disability preferences'),
        ],
      );
    }

    if (u.contains('academic') || u.contains('subject') || u.contains('grade') || u.contains('qual') || u.contains('matric') || u.contains('result')) {
      return (
        title: '📚 Results Details',
        steps: [
          ('1', 'Enter Matric/Grade 12 Year'),
          ('2', 'Select Undergraduate or Postgraduate'),
          ('3', 'Select Upgrading and Matric type (SA/International)'),
          ('4', 'Enter Examination Number and School Leaving Certificate'),
          ('5', 'Add Subject: select subject, grade, result, symbol'),
          ('6', 'Click "Add Subject" for each additional subject'),
        ],
      );
    }

    if (u.contains('school') || u.contains('previous') || u.contains('institution') || u.contains('tertiary')) {
      return (
        title: '🏫 Previous Studies',
        steps: [
          ('1', 'Select which school you attended last'),
          ('2', 'Select what you are currently doing'),
          ('3', 'Select if you studied at another institution'),
        ],
      );
    }

    if (u.contains('doc') || u.contains('upload') || u.contains('file')) {
      return (
        title: '📎 Document Upload',
        steps: [
          ('1', 'Upload certified ID copy'),
          ('2', 'Upload matric results / academic record'),
          ('3', 'Upload proof of residence'),
          ('4', 'Upload any additional documents requested'),
          ('5', 'Make sure files are clear and under 2MB'),
        ],
      );
    }

    if (u.contains('review') || u.contains('confirm') || u.contains('submit')) {
      return (
        title: '✅ Review & Submit',
        steps: [
          ('1', 'Read through all your details carefully'),
          ('2', 'Check ID number and contact info'),
          ('3', 'Check subject choices and symbols'),
          ('4', 'Scroll to the bottom and click SUBMIT'),
          ('5', '⚠️ SAVE YOUR STUDENT NUMBER after submission!'),
        ],
      );
    }

    return (
      title: 'Application Guide',
      steps: [
        ('1', 'Fill Next of Kin & Account Contact details'),
        ('2', 'Enter Biographical details and ID'),
        ('3', 'Enter Address, Contact, Residence info'),
        ('4', 'Fill Matric/Results and Subject details'),
        ('5', 'Enter Previous School/Tertiary information'),
        ('6', 'Review all information carefully'),
        ('7', 'Submit & SAVE your student number!'),
      ],
    );
  }

  void _showGuidance() {
    final guidance = _guidanceForPage(_currentUrl);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            const StarAvatar(size: 28),
            const SizedBox(width: 8),
            Flexible(child: Text(guidance.title, style: const TextStyle(fontSize: 16))),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ...guidance.steps.map((s) => _GuideStep(s.$1, s.$2)),
            if (_profileJson != null) ...[
              const SizedBox(height: 12),
              const Text('You like me to try and auto fill this page?',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _injectAutofill(ctx),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.green),
                        foregroundColor: Colors.green,
                      ),
                      child: const Text('Yes'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(ctx),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.grey),
                        foregroundColor: Colors.grey,
                      ),
                      child: const Text('No'),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
          ElevatedButton.icon(
            onPressed: () { Navigator.pop(ctx); _openInChrome(); },
            icon: const Icon(Icons.open_in_browser, size: 16),
            label: const Text('Open in Chrome'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: Colors.blue.shade800,
        foregroundColor: Colors.white,
        actions: [
          GestureDetector(
            onTap: _showGuidance,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: StarAvatar(size: 30, pulse: true),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.open_in_browser),
            onPressed: _openInChrome,
            tooltip: 'Open in Chrome',
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
            const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}

class _GuideStep extends StatelessWidget {
  final String number;
  final String text;
  const _GuideStep(this.number, this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$number.', style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(width: 6),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 13))),
        ],
      ),
    );
  }
}
