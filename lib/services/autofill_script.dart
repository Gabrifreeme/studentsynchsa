<<<<<<< Updated upstream
// ─────────────────────────────────────────────────────────────────────────────
// autofill_script.dart  –  StudentSyncSA Star Auto-Fill
//
// Built specifically for ITS (Oracle PL/SQL) university portals used by
// UNIVEN, UL, TUT, NWU and others. These portals use P_* field names and
// plain HTML — no React, no Angular, no framework events needed.
// Falls back to generic matching for other university sites.
// ─────────────────────────────────────────────────────────────────────────────

/// Self-contained DOM date picker used by both the webview screen and the
/// autofill script. Pure in-flow calendar (no native `<input type="date">`,
/// no `<select>` year list, no fixed popup) so it fits the phone WebView.
///
/// Design goals (v2, "reconsidered UI"):
///   * Always-visible day grid — no empty state, no toggle, no popup.
///   * Iframe-aware: the Venda/ITS form can live in a same-origin iframe, so
///     the picker scans the top document AND every accessible frame and builds
///     against whichever one hosts the DOB field. Retries until APEX renders it.
///   * Suppresses the portal's own (broken in WebView) calendar: the real field
///     is hidden + made read-only, inline onfocus/onclick handlers removed, and
///     focus/click capture-listeners stop the ITS calendar from opening.
///   * Re-attached on every page/frame by buildNavigationFixScript so a form
///     POST (fetch + document.write) can't leave the portal calendar behind.
///   * Autofill-safe: `ssaDatePickerSet` on the top window forwards to whatever
///     frame hosts the picker, so fillDateFields() always lands in the real field.
const String ssaDatePickerJs = r'''
(function() {
  if (window.__ssaDatePickerLoaded) return;
  window.__ssaDatePickerLoaded = true;

  var MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  var MONTHS_FULL = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var WD = ['Su','Mo','Tu','We','Th','Fr','Sa'];

  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  function findDobIn(doc) {
    try {
      return doc.getElementById('oapBirthdate')
        || doc.querySelector('input[name="oapBirthdate"]')
        || doc.querySelector('input[name="OAPBIRTHDATE"]')
        || doc.querySelector('input[name="P_DATE_OF_BIRTH"]')
        || doc.querySelector('input[id*="birth" i], input[id*="Birth" i], input[name*="birth" i], input[name*="Birth" i]');
    } catch (e) {
      try {
        return doc.getElementById('oapBirthdate')
          || doc.querySelector('input[name="oapBirthdate"]')
          || doc.querySelector('input[name="OAPBIRTHDATE"]')
          || doc.querySelector('input[name="P_DATE_OF_BIRTH"]')
          || doc.querySelector('input[id*="birth"], input[name*="birth"]');
      } catch (e2) { return null; }
    }
  }

  // Top document + every same-origin frame (recursively). The Venda/ITS form
  // can be rendered inside an iframe; the top document alone often has no field.
  function allWindows() {
    var out = [];
    (function walk(win) {
      try { out.push(win); } catch (e) { return; }
      try {
        for (var i = 0; i < win.frames.length; i++) {
          var f = win.frames[i];
          try { if (f.document) walk(f); } catch (e) {}
        }
      } catch (e) {}
    })(window);
    return out;
  }

  // Stop the portal's own (broken in WebView) calendar from ever opening.
  function suppressPortalCalendar(doc, dob) {
    try {
      dob.removeAttribute('onfocus');
      dob.removeAttribute('onclick');
      dob.removeAttribute('onchange');
    } catch (e) {}
    if (dob.__ssaSuppressed) return;
    dob.__ssaSuppressed = true;
    var stop = function(e) {
      if (e && e.preventDefault) e.preventDefault();
      if (e && e.stopPropagation) e.stopPropagation();
    };
    dob.addEventListener('focus', stop, true);
    dob.addEventListener('click', stop, true);
    dob.addEventListener('mousedown', stop, true);
    dob.addEventListener('keydown', function(e) {
      if (e.key && e.key !== 'Tab') { e.preventDefault(); e.stopPropagation(); }
    }, true);
  }

  // Wherever a picker actually got built: { win, set } — the set() writes the
  // real field in the right frame and fires the events APEX listens for.
  var built = null;

  function buildIn(win, doc) {
    var dob = findDobIn(doc);
    if (!dob) return false;

    var existing = doc.getElementById('ssa-date-picker-wrap');
    if (existing && existing.__ssaDob === dob) return true; // already built here

    suppressPortalCalendar(doc, dob);

    var oldWrap = doc.getElementById('ssa-date-picker-wrap');
    if (oldWrap) oldWrap.remove();
    var oldNative = doc.getElementById('custom-date-wrapper');
    if (oldNative) oldNative.remove();

    dob.removeAttribute('onfocus');
    dob.removeAttribute('onclick');
    dob.readOnly = true;
    dob.setAttribute('readonly', '');
    dob.style.display = 'none';
    dob.style.visibility = 'hidden';

    var row = dob.closest ? (dob.closest('div') || dob.parentElement) : dob.parentElement;
    if (row) {
      var trigs = row.querySelectorAll ? row.querySelectorAll('a, img, button, input[type="image"], span[class*="cal" i]') : [];
      for (var i = 0; i < trigs.length; i++) {
        var t = trigs[i];
        if (!t.contains(dob) && t !== dob) t.style.display = 'none';
      }
    }

    var E = function(tag) { return doc.createElement(tag); };

    var wrap = E('div');
    wrap.id = 'ssa-date-picker-wrap';
    wrap.__ssaDob = dob;
    wrap.style.cssText = 'width:100%;max-width:360px;box-sizing:border-box;margin:10px 0;font-family:Arial,Helvetica,sans-serif;';

    var lbl = E('div');
    lbl.textContent = 'Date of Birth';
    lbl.style.cssText = 'font-size:11px;color:#6B7280;font-weight:bold;text-transform:uppercase;margin-bottom:6px;letter-spacing:0.6px;';

    var displayEl = E('input');
    displayEl.type = 'text';
    displayEl.id = 'ssa-date-display';
    displayEl.readOnly = true;
    displayEl.placeholder = 'DD-MON-YYYY';
    displayEl.style.cssText = 'width:100%;box-sizing:border-box;padding:14px;font-size:18px;font-weight:bold;border:2px solid #7C3AED;border-radius:10px;background:#fff;color:#0F1624;text-align:center;';

    // Calendar card — always visible, no toggle, no popup, no empty state.
    var card = E('div');
    card.style.cssText = 'box-sizing:border-box;width:100%;margin-top:8px;border:1px solid #E5E7EB;border-radius:12px;background:#fff;padding:10px;';

    var head = E('div');
    head.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;';

    var prev = E('button');
    prev.type = 'button';
    prev.setAttribute('aria-label', 'Previous month');
    prev.textContent = '◀';
    prev.style.cssText = 'min-width:44px;min-height:44px;font-size:16px;border:1px solid #D1D5DB;border-radius:10px;background:#F9FAFB;cursor:pointer;color:#0F1624;';

    var title = E('div');
    title.textContent = '';
    title.style.cssText = 'flex:1;text-align:center;font-weight:bold;font-size:16px;color:#0F1624;padding:0 4px;cursor:pointer;';

    var next = E('button');
    next.type = 'button';
    next.setAttribute('aria-label', 'Next month');
    next.textContent = '▶';
    next.style.cssText = 'min-width:44px;min-height:44px;font-size:16px;border:1px solid #D1D5DB;border-radius:10px;background:#F9FAFB;cursor:pointer;color:#0F1624;';

    head.appendChild(prev);
    head.appendChild(title);
    head.appendChild(next);
    card.appendChild(head);

    var week = E('div');
    week.style.cssText = 'display:grid;grid-template-columns:repeat(7,1fr);gap:2px;margin-bottom:2px;';
    for (var w = 0; w < WD.length; w++) {
      var h = E('div');
      h.textContent = WD[w];
      h.style.cssText = 'text-align:center;font-size:12px;color:#6B7280;font-weight:bold;padding:4px 0;';
      week.appendChild(h);
    }
    card.appendChild(week);

    var grid = E('div');
    grid.id = 'ssa-date-grid';
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(7,1fr);gap:3px;';
    card.appendChild(grid);

    var foot = E('div');
    foot.style.cssText = 'display:flex;gap:6px;margin-top:8px;';

    var todayBtn = E('button');
    todayBtn.type = 'button';
    todayBtn.textContent = 'Today';
    todayBtn.style.cssText = 'flex:1;min-height:44px;font-size:15px;font-weight:bold;border:1px solid #7C3AED;border-radius:10px;background:#fff;color:#7C3AED;cursor:pointer;';

    var yearBtn = E('button');
    yearBtn.type = 'button';
    yearBtn.textContent = 'Year';
    yearBtn.style.cssText = 'flex:1;min-height:44px;font-size:15px;font-weight:bold;border:1px solid #7C3AED;border-radius:10px;background:#fff;color:#7C3AED;cursor:pointer;';

    var clearBtn = E('button');
    clearBtn.type = 'button';
    clearBtn.textContent = 'Clear';
    clearBtn.style.cssText = 'flex:1;min-height:44px;font-size:15px;font-weight:bold;border:1px solid #D1D5DB;border-radius:10px;background:#F9FAFB;color:#4B5563;cursor:pointer;';

    foot.appendChild(todayBtn);
    foot.appendChild(yearBtn);
    foot.appendChild(clearBtn);
    card.appendChild(foot);

    wrap.appendChild(lbl);
    wrap.appendChild(displayEl);
    wrap.appendChild(card);
    dob.parentNode.insertBefore(wrap, dob);

    var selected = null;
    var view = { y: 2000, mo: 0 };
    var touched = false;
    var yearMode = false;
    var viewYearWindow = null;

    function parseDob(v) {
      var t = (v || '').trim();
      if (!t) return null;
      var m = /^(\d{1,2})\s*[-/]\s*([A-Za-z]{3,9})\s*[-/]\s*(\d{4})$/.exec(t);
      if (m) {
        var mo = MONTHS.indexOf(m[2].toUpperCase());
        if (mo >= 0) return { d: parseInt(m[1],10), mo: mo, y: parseInt(m[3],10) };
      }
      var n = /^(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{4})$/.exec(t);
      if (n) return { d: parseInt(n[1],10), mo: parseInt(n[2],10) - 1, y: parseInt(n[3],10) };
      var s = /^(\d{4})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})$/.exec(t);
      if (s) return { d: parseInt(s[3],10), mo: parseInt(s[2],10) - 1, y: parseInt(s[1],10) };
      return null;
    }

    function fmt(dt) {
      if (!dt) return '';
      return pad2(dt.d) + '-' + MONTHS[dt.mo] + '-' + dt.y;
    }

    function fire(evName) {
      var ev;
      try { ev = new (win.Event || Event)(evName, { bubbles: true }); } catch (e) { ev = null; }
      if (ev) { try { dob.dispatchEvent(ev); } catch (e) {} }
      if (win.jQuery) {
        try { win.jQuery(dob).trigger(evName); } catch (e) {}
      }
    }

    function renderYears() {
      yearMode = true;
      if (viewYearWindow === null) {
        var start = selected ? selected.y : view.y;
        viewYearWindow = start - (start % 20);
      }
      var startYear = viewYearWindow;
      title.textContent = startYear + ' - ' + (startYear + 19);
      grid.innerHTML = '';
      for (var y = startYear; y < startYear + 20; y++) {
        var cell = E('button');
        cell.type = 'button';
        cell.textContent = y;
        cell.style.cssText = 'min-height:40px;font-size:15px;border:1px solid #E5E7EB;border-radius:8px;background:#fff;color:#0F1624;cursor:pointer;';
        if (selected && selected.y === y) {
          cell.style.background = '#7C3AED';
          cell.style.color = '#fff';
          cell.style.fontWeight = 'bold';
        }
        cell.onclick = (function(yy) {
          return function() {
            view.y = yy;
            viewYearWindow = null;
            touched = true;
            renderGrid();
          };
        })(y);
        grid.appendChild(cell);
      }
    }

    function renderGrid() {
      yearMode = false;
      title.textContent = MONTHS_FULL[view.mo] + ' ' + view.y;
      grid.innerHTML = '';
      var first = new Date(view.y, view.mo, 1).getDay();
      var daysIn = new Date(view.y, view.mo + 1, 0).getDate();
      var now = new Date();
      var tod = { d: now.getDate(), mo: now.getMonth(), y: now.getFullYear() };
      for (var i = 0; i < first; i++) grid.appendChild(E('div'));
      for (var d = 1; d <= daysIn; d++) {
        var cell = E('button');
        cell.type = 'button';
        cell.textContent = d;
        var isSel = selected && selected.d === d && selected.mo === view.mo && selected.y === view.y;
        var isTod = tod.d === d && tod.mo === view.mo && tod.y === view.y;
        var st = 'min-height:44px;font-size:17px;font-weight:600;border-radius:10px;background:#fff;color:#0F1624;cursor:pointer;border:1px solid #E5E7EB;';
        if (isSel) st += 'background:#7C3AED;color:#fff;border-color:#7C3AED;font-weight:bold;';
        else if (isTod) st += 'border:2px solid #7C3AED;background:#F3F0FF;color:#7C3AED;';
        cell.style.cssText = st;
        cell.onclick = (function(day) {
          return function() { commit({ d: day, mo: view.mo, y: view.y }); };
        })(d);
        grid.appendChild(cell);
      }
    }

    function render() {
      if (yearMode) renderYears(); else renderGrid();
    }

    function syncDisplay() {
      var cur = parseDob(dob.value);
      if (cur) {
        displayEl.value = fmt(cur);
        selected = cur;
        if (!touched) view = { y: cur.y, mo: cur.mo };
      } else {
        if (!touched && displayEl.value !== '') displayEl.value = '';
        if (!touched) selected = null;
      }
    }

    function commit(dt) {
      var val = fmt(dt);
      dob.removeAttribute('readonly');
      dob.removeAttribute('disabled');
      dob.value = val;
      displayEl.value = val;
      selected = dt;
      touched = true;
      view = { y: dt.y, mo: dt.mo };
      ['input','change','blur'].forEach(fire);
      if (win.apex && win.apex.event && win.apex.event.trigger) {
        try { win.apex.event.trigger(dob, 'change'); } catch (e) {}
      }
      render();
    }

    function clearVal() {
      dob.removeAttribute('readonly');
      dob.removeAttribute('disabled');
      dob.value = '';
      displayEl.value = '';
      selected = null;
      touched = false;
      ['input','change','blur'].forEach(fire);
      render();
    }

    prev.onclick = function() {
      touched = true;
      if (yearMode) {
        viewYearWindow = (viewYearWindow || (view.y - (view.y % 20))) - 20;
        renderYears();
      } else {
        view.mo--;
        if (view.mo < 0) { view.mo = 11; view.y--; }
        renderGrid();
      }
    };
    next.onclick = function() {
      touched = true;
      if (yearMode) {
        viewYearWindow = (viewYearWindow || (view.y - (view.y % 20))) + 20;
        renderYears();
      } else {
        view.mo++;
        if (view.mo > 11) { view.mo = 0; view.y++; }
        renderGrid();
      }
    };
    title.onclick = function() {
      touched = true;
      if (yearMode) { renderGrid(); } else { viewYearWindow = null; renderYears(); }
    };
    todayBtn.onclick = function() {
      var n = new Date();
      commit({ d: n.getDate(), mo: n.getMonth(), y: n.getFullYear() });
    };
    yearBtn.onclick = function() { touched = true; viewYearWindow = null; renderYears(); };
    clearBtn.onclick = clearVal;

    var localSet = function(value) {
      dob.removeAttribute('readonly');
      dob.removeAttribute('disabled');
      dob.value = value;
      var p = parseDob(value);
      if (p) {
        selected = p;
        view = { y: p.y, mo: p.mo };
        displayEl.value = fmt(p);
      } else {
        displayEl.value = value || '';
      }
      touched = true;
      ['input','change','blur'].forEach(fire);
      render();
    };
    localSet.__ssaLocal = true;
    win.ssaDatePickerSet = localSet;

    syncDisplay();
    if (selected) view = { y: selected.y, mo: selected.mo };
    render();

    try { win.setInterval(function() { syncDisplay(); }, 500); } catch (e) {}
    try {
      var MO = win.MutationObserver || win.__ssaMutationObserver;
      if (typeof MO !== 'undefined' && MO) {
        var obs = new MO(function() { syncDisplay(); });
        obs.observe(dob, { attributes: true, attributeFilter: ['value'] });
      }
    } catch (e) {}

    if (!built) built = { win: win, set: localSet, dob: dob };

    console.log('SSA date picker built (' + (win === window.top ? 'top' : 'iframe') + ')');
    return true;
  }

  function tryBuildAll() {
    var ws = allWindows();
    for (var i = 0; i < ws.length; i++) {
      try { if (buildIn(ws[i], ws[i].document)) return true; } catch (e) {}
    }
    return false;
  }

  // Continuously re-check: APEX renders the form (and any iframe it lives in)
  // asynchronously, and form POSTs (fetch + document.write) replace the DOM, so
  // we keep watching and rebuild the moment a birthdate field exists.
  function builtAlive() {
    if (!built) return false;
    try { return !(built.dob && built.dob.isConnected === false); } catch (e) { return false; }
  }
  (function poll() {
    if (!builtAlive()) built = null;
    tryBuildAll();
    setTimeout(poll, 700);
  })();

  // Top-window dispatcher: the autofill script runs in the top frame but the
  // real field may live in an iframe. Forward to whichever frame has the picker.
  if (window.top === window) {
    window.ssaDatePickerInit = function() { tryBuildAll(); };
    window.ssaDatePickerSet = function(value) {
      if (builtAlive()) { built.set(value); return; }
      built = null;
      tryBuildAll();
      if (builtAlive()) { built.set(value); return; }
      var ws = allWindows();
      for (var i = 0; i < ws.length; i++) {
        try {
          var s = ws[i].ssaDatePickerSet;
          if (s && s.__ssaLocal) { s(value); return; }
        } catch (e) {}
      }
      for (var j = 0; j < ws.length; j++) {
        try {
          var el = findDobIn(ws[j].document);
          if (el) {
            el.value = value;
            el.removeAttribute('readonly');
            el.removeAttribute('disabled');
            ['input','change','blur'].forEach(function(ev) {
              try { el.dispatchEvent(new Event(ev, { bubbles: true })); } catch (e) {}
            });
            return;
          }
        } catch (e) {}
      }
    };
  }
})();
''';

String buildDatePickerScript() => ssaDatePickerJs;

=======
>>>>>>> Stashed changes
String buildAutofillScript(String profileJson) {
  return _script(profileJson, addFloatingStar: true);
}

String buildAutofillOnlyScript(String profileJson) {
  return _script(profileJson, addFloatingStar: false);
}

String buildGuidanceScript(String profileJson, String guidanceJson) {
  return _script(profileJson, addFloatingStar: true, guidanceJson: guidanceJson);
}

String buildNavigationFixScript() {
  return '''
(function() {
  if (window.__ssaNavFix) return;
  window.__ssaNavFix = true;

  var _open = window.open;
  window.open = function(url, name, specs) {
    if (url) {
      window.location.href = url;
      return window;
    }
    return _open.apply(window, arguments);
  };

  document.addEventListener('click', function(e) {
    var a = e.target.closest('a[target="_blank"], a[target="_new"]');
    if (a && a.href) {
      e.preventDefault();
      e.stopPropagation();
      window.location.href = a.href;
    }
  }, true);
})();
''';
}

String buildViewportPatch() {
  return '''
(function() {
  var meta = document.querySelector('meta[name="viewport"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.name = 'viewport';
    document.head.appendChild(meta);
  }
  meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
})();
''';
}

String buildBlanketAutofillSuppressScript() {
  return '''
(function() {
  var inputs = document.querySelectorAll('input');
  for (var i = 0; i < inputs.length; i++) {
    var el = inputs[i];
    if (!el.getAttribute('autocomplete')) {
      el.setAttribute('autocomplete', 'off');
    }
    el.removeAttribute('autocorrect');
    el.removeAttribute('autocapitalize');
    el.removeAttribute('spellcheck');
  }
})();
''';
}

String buildSecurityPatch() {
  return '''
(function() {
  window.__defineGetter__('top', function() { return window; });
  window.__defineGetter__('parent', function() { return window; });
  window.__defineGetter__('owner', function() { return window; });
  try { delete window.top; } catch(e) {}
  try { delete window.parent; } catch(e) {}
  try { delete window.owner; } catch(e) {}
  window.top = window;
  window.parent = window;
})();
''';
}

String buildLabelPatch() {
  return '''
(function() {
  var inputs = document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button])');
  for (var i = 0; i < inputs.length; i++) {
    var el = inputs[i];
    if (el.labels && el.labels.length > 0) continue;
    var label = document.querySelector('label[for="' + el.id + '"]');
    if (label) continue;
    var parent = el.parentElement;
    for (var d = 0; d < 5 && parent; d++) {
      var lbl = parent.querySelector('label');
      if (lbl) break;
      var text = parent.textContent.trim();
      if (text && text.length < 80 && (parent.tagName === 'TD' || parent.tagName === 'TH' || parent.tagName === 'LABEL')) {
        el.setAttribute('aria-label', text.replace(/\\s+/g, ' ').replace(/[:\\*]/g, '').trim());
        break;
      }
      parent = parent.parentElement;
    }
  }
})();
''';
}

String buildAutocompletePatch() {
  return '''
(function() {
  var map = {
    'input[name*="name" i], input[name*="姓名" i]': 'name',
    'input[name*="email" i], input[type="email"]': 'email',
    'input[name*="phone" i], input[name*="cell" i], input[name*="tel" i]': 'tel',
    'input[name*="address" i], input[name*="street" i]': 'street-address',
    'input[name*="city" i], input[name*="town" i]': 'address-level2',
    'input[name*="province" i], input[name*="state" i]': 'address-level1',
    'input[name*="postal" i], input[name*="zip" i]': 'postal-code',
    'input[name*="country" i]': 'country',
    'input[name*="company" i], input[name*="organisation" i]': 'organization',
    'input[name*="id" i], input[name*="passport" i]': 'off',
  };
  for (var sel in map) {
    var els = document.querySelectorAll(sel);
    for (var i = 0; i < els.length; i++) {
      els[i].setAttribute('autocomplete', map[sel]);
    }
  }
})();
''';
}

String buildSelectAutocompletePatch() {
  return '''
(function() {
  var selects = document.querySelectorAll('select');
  for (var i = 0; i < selects.length; i++) {
    var sel = selects[i];
    var name = (sel.name || '').toLowerCase();
    var opts = [];
    for (var j = 0; j < sel.options.length; j++) {
      opts.push({ text: sel.options[j].text.trim().toLowerCase(), value: sel.options[j].value });
    }
    sel._ssaOpts = opts;
  }
})();
''';
}

String buildProvinceDisambiguationPatch() {
  return '''
(function() {
  var selects = document.querySelectorAll('select');
  for (var i = 0; i < selects.length; i++) {
    var sel = selects[i];
    var name = (sel.name || '').toUpperCase();
    if (name.indexOf('PROVINCE') === -1 && name.indexOf('P_PROVINCE') === -1) continue;
    var provMap = {
      'gauteng': 'GP', 'kwazulu-natal': 'KZN', 'kwa-zulu natal': 'KZN',
      'western cape': 'WC', 'eastern cape': 'EC', 'free state': 'FS',
      'limpopo': 'LP', 'mpumalanga': 'MP', 'north west': 'NW',
      'northern cape': 'NC',
    };
    for (var j = 0; j < sel.options.length; j++) {
      var ot = sel.options[j].text.trim().toLowerCase();
      var ov = sel.options[j].value.trim().toUpperCase();
      if (provMap[ot]) {
        sel.options[j].setAttribute('data-ssa-prov', provMap[ot]);
      }
    }
  }
})();
''';
}

String buildFocusPatch() {
  return '''
(function() {
  var inputs = document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset])');
  for (var i = 0; i < inputs.length; i++) {
    inputs[i].setAttribute('inputmode', 'text');
  }
  var phones = document.querySelectorAll('input[name*="phone" i], input[name*="cell" i], input[name*="tel" i]');
  for (var i = 0; i < phones.length; i++) {
    phones[i].setAttribute('inputmode', 'tel');
  }
  var emails = document.querySelectorAll('input[name*="email" i], input[type="email"]');
  for (var i = 0; i < emails.length; i++) {
    emails[i].setAttribute('inputmode', 'email');
  }
  var nums = document.querySelectorAll('input[name*="id" i], input[name*="passport" i], input[name*="postal" i]');
  for (var i = 0; i < nums.length; i++) {
    nums[i].setAttribute('inputmode', 'numeric');
  }
})();
''';
}

String buildInputmodePatch() {
  return '''
(function() {
  var style = document.createElement('style');
  style.textContent = 'input, select, textarea { font-size: 16px !important; min-height: 44px !important; }';
  document.head.appendChild(style);
})();
''';
}

String buildFormLabelPatch() {
  return '''
(function() {
  var forms = document.querySelectorAll('form');
  for (var f = 0; f < forms.length; f++) {
    forms[f].setAttribute('autocomplete', 'off');
  }
  var submitBtns = document.querySelectorAll('input[type="submit"], button[type="submit"]');
  for (var i = 0; i < submitBtns.length; i++) {
    submitBtns[i].style.minHeight = '44px';
    submitBtns[i].style.minWidth = '44px';
  }
})();
''';
}

// ============================================
// GOLD STAR GUIDANCE
// ============================================

String buildStarScript(String profileJson) {
  return '''
(function() {
  if (window.__ssaStarActive) return;
  window.__ssaStarActive = true;

  var profile = $profileJson;

  // ── Guidance steps ────────────────────────
  var steps = [
    { icon: '\\uD83C\\uDFAF', title: 'Start Application',
      text: 'Click "Apply Now" or the red APPLY pill to go to the ITS portal.' },
    { icon: '\\uD83D\\uDC64', title: 'Register as New Applicant',
      text: 'On the ITS login page, click "New applicant" to start a new application.' },
    { icon: '\\uD83D\\uDCDD', title: 'Personal Details',
      text: 'Fill in your name, ID number, date of birth, gender, and nationality.' },
    { icon: '\\uD83D\\uDCF1', title: 'Contact Information',
      text: 'Enter your cell number, email, and physical & postal address.' },
    { icon: '\\uD83C\\uDFEB', title: 'School & Matric Details',
      text: 'Provide school name, matric year, and exam number.' },
    { icon: '\\uD83C\\uDF93', title: 'Faculty & Programme',
      text: 'Choose your faculty and programme of study.' },
    { icon: '\\u2705', title: 'Review & Submit',
      text: 'Review everything and submit — you will receive a reference number by SMS/email.' },
    { icon: '\\uD83D\\uDCCE', title: 'Upload Documents',
      text: 'Upload your ID, matric certificate, and proof of residence when prompted.' }
  ];

  var ga = function() {};
  if (typeof doAutofill === 'function') ga = doAutofill;

  // ── Log helper ────────────────────────────
  function log(msg) {
    try { window.FlutterLog && FlutterLog.postMessage('[STAR] ' + msg); } catch(e) {}
  }

  // ── Inject the star ───────────────────────
  function placeStar() {
    if (document.getElementById('ssa-star')) return;

    var s = document.createElement('div');
    s.id = 'ssa-star';
    s.textContent = '\\u2B50';
    s.style.cssText = 'position:fixed;bottom:20px;right:20px;width:60px;height:60px;'
      + 'border-radius:50%;z-index:2147483647;cursor:pointer;font-size:32px;'
      + 'display:flex;align-items:center;justify-content:center;'
      + 'background:radial-gradient(circle at 30% 30%, #FFD700, #FFA500);'
      + 'box-shadow:0 4px 20px rgba(0,0,0,0.4);'
      + 'border:3px solid #FFF;'
      + 'user-select:none;transition:transform 0.2s;';
    s.onmouseover = function() { s.style.transform = 'scale(1.1)'; };
    s.onmouseout  = function() { s.style.transform = 'scale(1)'; };
    s.onclick = showGuide;
    s.setAttribute('aria-label', 'Application guide');

    (document.body || document.documentElement).appendChild(s);
    log('injected on ' + window.location.href);
  }

  // ── Guidance panel ────────────────────────
  function showGuide() {
    var old = document.getElementById('ssa-guide');
    if (old) { old.remove(); return; }

    var ov = document.createElement('div');
    ov.id = 'ssa-guide';
    ov.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:2147483646;'
      + 'background:rgba(0,0,0,0.5);display:flex;align-items:flex-end;'
      + 'justify-content:center;padding:16px;box-sizing:border-box;';

    var card = document.createElement('div');
    card.style.cssText = 'background:#fff;border-radius:20px 20px 0 0;'
      + 'max-width:400px;width:100%;max-height:85vh;overflow-y:auto;'
      + 'padding:20px 16px 24px;box-shadow:0 -4px 30px rgba(0,0,0,0.25);'
      + 'font:16px/1.5 Arial,sans-serif;color:#1F2937;';

    // Header
    card.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">'
      + '<span style="font-size:20px;font-weight:700;">\\u2B50 How to Apply</span>'
      + '<span id="ssa-guide-close" style="font-size:24px;cursor:pointer;color:#9CA3AF;">\\u00D7</span>'
      + '</div>';

    // Steps
    var ol = document.createElement('ol');
    ol.style.cssText = 'margin:0;padding:0 0 0 20px;';
    for (var i = 0; i < steps.length; i++) {
      var li = document.createElement('li');
      li.style.cssText = 'margin-bottom:12px;';
      li.innerHTML = '<div><strong>' + steps[i].icon + ' ' + steps[i].title + '</strong></div>'
        + '<div style="font-size:14px;color:#4B5563;">' + steps[i].text + '</div>';
      ol.appendChild(li);
    }
    card.appendChild(ol);

    // Auto-fill button
    var btnRow = document.createElement('div');
    btnRow.style.cssText = 'display:flex;gap:10px;margin-top:16px;';
    var fillBtn = document.createElement('button');
    fillBtn.textContent = '\\u26A1 Run Auto-Fill';
    fillBtn.style.cssText = 'flex:1;padding:12px;border:none;border-radius:12px;'
      + 'background:#065F46;color:#fff;font-size:15px;font-weight:600;cursor:pointer;'
      + 'min-height:48px;';
    fillBtn.onclick = function() {
      ov.remove();
      if (typeof doAutofill === 'function') doAutofill();
    };
    var closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.style.cssText = 'flex:1;padding:12px;border:1px solid #D1D5DB;border-radius:12px;'
      + 'background:#fff;color:#374151;font-size:15px;cursor:pointer;min-height:48px;';
    closeBtn.onclick = function() { ov.remove(); };
    btnRow.appendChild(fillBtn);
    btnRow.appendChild(closeBtn);
    card.appendChild(btnRow);

    ov.appendChild(card);
    document.body.appendChild(ov);

    // Close handlers
    document.getElementById('ssa-guide-close').onclick = function() { ov.remove(); };
    ov.onclick = function(e) { if (e.target === ov) ov.remove(); };
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { ov.remove(); document.removeEventListener('keydown', esc); }
    });
  }

  // ── Self-heal via MutationObserver ────────
  var _reTimer = null;
  function scheduleReinject() {
    if (_reTimer) return;
    _reTimer = setTimeout(function() {
      _reTimer = null;
      if (!document.getElementById('ssa-star')) {
        placeStar();
        log('re-injected (DOM mutation)');
      }
    }, 300);
  }

  if (window.MutationObserver) {
    try {
      var obs = new MutationObserver(function() { scheduleReinject(); });
      if (document.body) {
        obs.observe(document.body, { childList: true, subtree: true });
      } else {
        document.addEventListener('DOMContentLoaded', function() {
          obs.observe(document.body, { childList: true, subtree: true });
        });
      }
    } catch(e) {}
  }

  // ── Re-inject on SPA navigation ──────────
  window.addEventListener('popstate', function() { scheduleReinject(); });
  window.addEventListener('hashchange', function() { scheduleReinject(); });
  setTimeout(function() { scheduleReinject(); }, 1500);

  // ── Kick off ──────────────────────────────
  function boot() {
    placeStar();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
''';
}

String _script(String profileJson, {required bool addFloatingStar, String guidanceJson = ''}) {  return '''
(function() {
  // ÔöÇÔöÇ 1. Profile data ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  var profile = $profileJson;

  // ── 1b. Shared custom date picker (also injected separately by the
  //      university webview). Idempotent — `__ssaDatePickerLoaded` guard
  //      makes a second injection a no-op.
  $ssaDatePickerJs

  function gv(path) {
    var parts = path.split('.');
    var o = profile;
    for (var i = 0; i < parts.length; i++) {
      if (o == null || typeof o !== 'object') return '';
      o = o[parts[i]];
    }
    return (o !== null && o !== undefined) ? String(o) : '';
  }

  function fmtDate(iso) {
    if (!iso || iso.length < 10) return iso || '';
    var months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    var p = iso.split('T')[0].split('-');
    var m = parseInt(p[1], 10) - 1;
    return (m >= 0 && m < 12) ? p[2] + '-' + months[m] + '-' + p[0] : iso;
  }

  // date also as DD/MM/YYYY for ITS portals
  function fmtDateSlash(iso) {
    if (!iso || iso.length < 10) return iso || '';
    var p = iso.split('T')[0].split('-');
    return p[2] + '/' + p[1] + '/' + p[0];
  }

  // date as DD-MM-YYYY for ITS portals (e.g. 16-03-1963)
  function fmtDateDash(iso) {
    if (!iso || iso.length < 10) return iso || '';
    var p = iso.split('T')[0].split('-');
    return p[2] + '-' + p[1] + '-' + p[0];
  }

  // Individual date parts for split fields
  function fmtDateDay(iso) {
    if (!iso || iso.length < 10) return '';
    var p = iso.split('T')[0].split('-');
    return p[2];
  }
  function fmtDateMonth(iso) {
    if (!iso || iso.length < 10) return '';
    var p = iso.split('T')[0].split('-');
    return p[1];
  }
  function fmtDateYear(iso) {
    if (!iso || iso.length < 10) return '';
    var p = iso.split('T')[0].split('-');
    return p[0];
  }

  // date as DD-M-YYYY for ITS portals (e.g. 13-4-1964)
  function fmtDateShort(iso) {
    if (!iso || iso.length < 10) return iso || '';
    var p = iso.split('T')[0].split('-');
    return parseInt(p[2]) + '-' + parseInt(p[1]) + '-' + p[0];
  }

  // Fill date as separate day/month/year fields (DD-MON-YYYY)
  function fillDateFields(dobIso) {
    if (!dobIso || dobIso.length < 10) return;
    var p = dobIso.split('T')[0].split('-'); // [YYYY, MM, DD]
    var day = parseInt(p[2]);
    var monthNum = p[1];
    var year = p[0];

    var monthNames = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    var monthAbbr = monthNames[parseInt(monthNum) - 1] || monthNum;
    var portalVal = parseInt(day) + '-' + monthAbbr + '-' + year;

    // Prefer the shared custom picker (idempotent; builds on demand). Its
    // commit() writes the DD-MON-YYYY value into the real portal field and
    // fires input/change/blur, then its sync loop keeps the display in step.
    if (typeof window.ssaDatePickerSet === 'function') {
      window.ssaDatePickerSet(portalVal);
      return;
    }

    // Fallback: write the real field directly — across the top document AND
    // every same-origin iframe (the ITS form can live inside one).
    var wins = [];
    (function walk(w2) {
      try { wins.push(w2); } catch (e) { return; }
      try {
        for (var fi = 0; fi < w2.frames.length; fi++) {
          try { if (w2.frames[fi].document) walk(w2.frames[fi]); } catch (e) {}
        }
      } catch (e) {}
    })(window);

    var target = null;
    for (var wi = 0; wi < wins.length && !target; wi++) {
      try {
        target = wins[wi].document.getElementById('oapBirthdate')
          || wins[wi].document.querySelector('input[name="OAPBIRTHDATE"]')
          || wins[wi].document.querySelector('input[name="oapBirthdate"]')
          || wins[wi].document.querySelector('input[id*="birth" i], input[id*="Birth" i]');
      } catch (e) {}
    }

    if (!target) {
      console.log('No target date field found');
      return;
    }
    target.value = portalVal;
    target.dispatchEvent(new Event('input', { bubbles: true }));
    target.dispatchEvent(new Event('change', { bubbles: true }));
    console.log('Date filled (fallback): ' + portalVal);
  }

  var firstName   = gv('personal.firstName');
  var lastName    = gv('personal.lastName');
  var email       = gv('contact.email');
  var dobIso      = gv('personal.dateOfBirth');
  console.log('🔍 DEBUG dobIso:', dobIso, '→ dash:', fmtDateDash(dobIso));

  var vs = {
    firstName:         firstName,
    lastName:          lastName,
    initials:          gv('personal.initials'),
    title:             gv('personal.title'),
    gender:            gv('personal.gender'),
    genderCode:        (function() {
                          var g = gv('personal.gender').toLowerCase();
                          if (g.indexOf('female') !== -1 || g === 'f') return 'F';
                          if (g.indexOf('male') !== -1 || g === 'm') return 'M';
                          return 'M'; // default: 'Other', 'Prefer not to say' → M
                        })(),
    idNumber:          gv('personal.idNumber'),
    dateOfBirth:       fmtDate(dobIso),
    dateOfBirthSlash:  fmtDateSlash(dobIso),
    dateOfBirthDash:   fmtDateDash(dobIso),
    dateOfBirthDay:    fmtDateDay(dobIso),
    dateOfBirthMonth:  fmtDateMonth(dobIso),
    dateOfBirthYear:   fmtDateYear(dobIso),
    email:             email,
    phone:             gv('contact.phone'),
    workPhone:         gv('contact.workPhone'),
    address:           gv('address.address'),
    addressLine2:      gv('address.addressLine2'),
    addressLine3:      gv('address.addressLine3'),
    province:          gv('address.province'),
    postalCode:        gv('address.postalCode'),
    heardAboutUs:      gv('demographic.heardAboutUs'),
    nationality:       gv('demographic.nationality'),
<<<<<<< Updated upstream
    isSACitizen:       (function() {
                         var nat = (gv('demographic.nationality') || '').toLowerCase();
                         var idn = (gv('personal.idNumber') || '').trim();
                         if (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) return 'Yes';
                         if (idn.length >= 13) return 'Yes';
                         return 'No';
                       })(),
    // FIX #5: citizenshipCodeValue → the LOV *description* (long label) for SA citizens.
    //    citizenshipShortCode → the LOV *code* (short code) when known,
    //      falling back to the description when no short code is mapped.
    citizenshipCodeValue: (function() {
                            var nat = (gv('demographic.nationality') || '').toLowerCase();
                            var idn = (gv('personal.idNumber') || '').trim();
                            var sa = (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) || idn.length >= 13;
                            // Long LOV description
                            return sa ? 'R.S.A' : (gv('demographic.citizenshipDescription') || gv('demographic.nationality') || '');
                          })(),
    citizenshipShortCode: (function() {
                            var nat = (gv('demographic.nationality') || '').toLowerCase();
                            var idn = (gv('personal.idNumber') || '').trim();
                            var sa = (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) || idn.length >= 13;
                            // ITS citizenship code for SA (used by the oapCitzCode / oapCitCode LOV fields);
                            // fall back to whichever profile value is set for non-SA applicants.
                            if (sa) return 'R.S.A';
                            return gv('demographic.citizenshipCode') || gv('demographic.citizenshipShortCode') || '';
                          })(),
    homeLanguage:      gv('demographic.homeLanguage'),
    ethnicValue:       (function() {
                          var pg = (gv('demographic.populationGroup') || '').toLowerCase();
                          if (pg.indexOf('afric') !== -1 || pg.indexOf('black') !== -1) return 'BLACK';
                          if (pg.indexOf('colour') !== -1 || pg.indexOf('colored') !== -1) return 'COLOURED';
                          if (pg.indexOf('indian') !== -1 || pg.indexOf('asian') !== -1) return 'INDIAN';
                          if (pg.indexOf('white') !== -1) return 'WHITE';
                          return '';
                        })(),
    employedValue:     (function() {
                          var es = (gv('status.employmentStatus') || '').toLowerCase();
                          return es.indexOf('employed') !== -1 ? 'Yes' : 'No';
                        })(),
    bursaryValue:      (function() {
                          var br = (gv('status.bursaryRequired') || '').toLowerCase();
                          return br.indexOf('y') !== -1 ? 'Y' : 'N';
                        })(),
    residenceRequired: (function() {
                          var wr = (gv('status.wantsResidence') || '').toLowerCase();
                          return wr.indexOf('y') !== -1 ? 'Y' : 'N';
                        })(),
=======
    homeLanguage:      gv('demographic.homeLanguage'),
>>>>>>> Stashed changes
    populationGroup:   gv('demographic.populationGroup'),
    maritalStatus:     gv('demographic.maritalStatus'),
    maritalYesNo:      (function() {
                            var m = (gv('demographic.maritalStatus') || '').toLowerCase();
                            return m.indexOf('married') !== -1 ? 'Yes' : 'No';
                          })(),
    disabilityValue:   (function() {
                            var d = (gv('status.disabilityStatus') || '').toLowerCase();
                            return d.indexOf('y') !== -1 || d.indexOf('disable') !== -1 ? 'Yes' : 'No';
                          })(),
    raceValue:         (function() {
                            var pg = (gv('demographic.populationGroup') || '').toLowerCase();
                            if (pg.indexOf('afric') !== -1 || pg.indexOf('black') !== -1) return 'African';
                            if (pg.indexOf('colour') !== -1 || pg.indexOf('colored') !== -1) return 'Coloured';
                            if (pg.indexOf('asian') !== -1) return 'Asian';
                            if (pg.indexOf('indian') !== -1) return 'Indian';
                            if (pg.indexOf('white') !== -1) return 'White';
                            return pg || '';
                          })(),
    schoolName:        gv('school.schoolName'),
    currentGrade:      gv('school.currentGrade'),
    matricYear:        gv('results.matricYear'),
    matricType:        gv('results.matricType'),
    examinationNumber: gv('results.examinationNumber'),
    applicationLevel:  gv('results.applicationLevel'),
    faculty:           gv('qualification.choices.0.faculty'),
    programme:         gv('qualification.choices.0.programme'),
    academicYear:      gv('qualification.academicYear'),
    studyMode:         gv('qualification.studyMode'),
    nextOfKinName:     gv('nextOfKin.name'),
    nextOfKinPhone:    gv('nextOfKin.mobilePhone'),
    nextOfKinEmail:    gv('nextOfKin.email'),
  };

  // ÔöÇÔöÇ 2. ITS portal exact-name map (P_* Oracle fields) ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  // These are the actual INPUT NAME attributes used by ITS/Univen/UL/TUT etc.
  var itsExact = {
<<<<<<< Updated upstream
    // UNIVEN / Venda OAP exact-name maps
    'OAPCITIZENTYPE':     vs.isSACitizen,
    'OAPCITZCODE':        vs.citizenshipShortCode,
    'OAPCITCODE':         vs.citizenshipShortCode,
    'OAPCITCODE_DESC':    vs.citizenshipCodeValue,
    'OAPHOMELANG':        vs.homeLanguage,
    'OAPETHNIC':          vs.ethnicValue,
    'OAPEMPLOYED':        vs.employedValue,
    'OAPBURSARYREQ':      vs.bursaryValue,
    'OAPRESREQ':          vs.residenceRequired,
    // Address
    'OAPSTREETADDR1':           vs.address,
    'OAPSTREETADDR2':           vs.addressLine2,
    'OAPSTREETADDR3':           vs.addressLine3,
    'OAPSTREETADDR4':           vs.province,
    'OAPSTREETADDRPCODEREQ':      vs.postalCode,
    'OAPSTREETADDRPCODEREQ_DESC': vs.postalCode,
    'OAPPOSTALADDRPCODEREQ':      vs.postalCode,
    'OAPPOSTALADDRPCODEREQ_DESC': vs.postalCode,
    // Date of birth
    'OAPBIRTHDATE':           vs.dateOfBirth,
    'OAPBIRTHDAY':            vs.dateOfBirthDay,
    'OAPBIRTHMONTH':          vs.dateOfBirthMonth,
    'OAPBIRTHYEAR':           vs.dateOfBirthYear,
    // Heard about us
    'OAPHEARD':               vs.heardAboutUs,
    'OAPHEARD_DESC':          vs.heardAboutUs,
    'oapGender':              vs.genderCode,
=======
>>>>>>> Stashed changes
    // Personal
    'P_SURNAME':           vs.lastName,
    'P_NAME':              vs.firstName,
    'P_INITIALS':          vs.initials,
    'P_TITLE':             vs.title,
    'P_GENDER':            vs.gender,
    'P_ID_NO':             vs.idNumber,
    'P_PASSPORT_NO':       vs.idNumber,
    'P_DATE_OF_BIRTH':     vs.dateOfBirthDash,
    'P_DOB':               vs.dateOfBirthDash,
    'P_BIRTH_DATE':        vs.dateOfBirthDash,
    // Contact
    'P_EMAIL':             vs.email,
    'P_EMAIL_ADDRESS':     vs.email,
    'P_CONFIRM_EMAIL':     vs.email,
    'P_EMAIL2':            vs.email,
    'P_CELL_NO':           vs.phone,
    'P_CELL':              vs.phone,
    'P_CELLPHONE':         vs.phone,
    'P_PHONE':             vs.phone,
    'P_TEL_NO':            vs.phone,
    'P_WORK_TEL':          vs.workPhone,
    // Address
    'P_ADDRESS_1':         vs.address,
    'P_ADDRESS_2':         vs.addressLine2,
    'P_ADDRESS1':          vs.address,
    'P_ADDRESS2':          vs.addressLine2,
    'P_PHYSICAL_ADDRESS':  vs.address,
    'P_SUBURB':            vs.addressLine2,
    'P_CITY':              vs.addressLine2,
    'P_PROVINCE':          vs.province,
    'P_POSTAL_CODE':       vs.postalCode,
    'P_POST_CODE':         vs.postalCode,
    'P_POSTAL':            vs.postalCode,
    // Demographic
    'P_NATIONALITY':       vs.nationality,
    'P_CITIZEN':           vs.nationality,
    'P_CITIZENSHIP':       vs.nationality,
    'P_HOME_LANGUAGE':     vs.homeLanguage,
    'P_LANGUAGE':          vs.homeLanguage,
    'P_POPULATION_GROUP':  vs.populationGroup,
    'P_RACE':              vs.populationGroup,
    'P_MARITAL_STATUS':    vs.maritalStatus,
    // School
    'P_SCHOOL_NAME':       vs.schoolName,
    'P_SCHOOL':            vs.schoolName,
    'P_GRADE':             vs.currentGrade,
    // Results
    'P_MATRIC_YEAR':       vs.matricYear,
    'P_EXAM_YEAR':         vs.matricYear,
    'P_EXAM_TYPE':         vs.matricType,
    'P_EXAM_NO':           vs.examinationNumber,
    'P_CANDIDATE_NO':      vs.examinationNumber,
    // Application
    'P_FACULTY':           vs.faculty,
    'P_PROGRAMME':         vs.programme,
    'P_COURSE':            vs.programme,
    'P_QUALIFICATION':     vs.programme,
    'P_STUDY_MODE':        vs.studyMode,
    'P_YEAR_OF_STUDY':     vs.academicYear,
    // Next of kin
    'P_PARENT_NAME':       vs.nextOfKinName,
    'P_GUARDIAN_NAME':     vs.nextOfKinName,
    'P_NOK_NAME':          vs.nextOfKinName,
    'P_PARENT_CELL':       vs.nextOfKinPhone,
    'P_GUARDIAN_CELL':     vs.nextOfKinPhone,
    'P_NOK_CELL':          vs.nextOfKinPhone,
    'P_PARENT_EMAIL':      vs.nextOfKinEmail,
    'P_GUARDIAN_EMAIL':    vs.nextOfKinEmail,
    'P_NOK_EMAIL':         vs.nextOfKinEmail,
  };

  // ÔöÇÔöÇ 3. Generic fuzzy fieldMap (fallback for non-ITS sites) ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  var fieldMap = {
    firstName:         ['firstname','first name','fname','given name','name'],
    lastName:          ['lastname','last name','surname','lname','family name'],
    initials:          ['initials'],
    title:             ['title','salutation'],
    gender:            ['gender','sex'],
    idNumber:          ['id number','idnumber','identity number','national id','id no','passport'],
    dateOfBirth:       ['date of birth','dateofbirth','dob','birth date','birthdate','birthday'],
    email:             ['email','e-mail','email address'],
    phone:             ['cell','cellphone','mobile','phone','telephone','contact number'],
    workPhone:         ['work phone','work tel','telephone work'],
    address:           ['address','street','physical address'],
    addressLine2:      ['address 2','suburb','town','city'],
    province:          ['province','state','region','select province'],
    postalCode:        ['postal code','postalcode','post code','postcode','zip'],
    nationality:       ['nationality','citizenship','citizen'],
    homeLanguage:      ['home language','homelanguage','language'],
    populationGroup:   ['population group','ethnicity'],
<<<<<<< Updated upstream
    raceValue:         ['race'],
    maritalStatus:     ['marital status','maritalstatus'],
    maritalYesNo:      ['married','are you married'],
    disabilityValue:   ['disabled','disability','are you disabled'],
=======
    raceValue:         ['race','population group'],
    maritalStatus:     ['marital status','maritalstatus'],
    maritalYesNo:      ['married','are you married','marital status'],
    disabilityValue:   ['disabled','disability','are you disabled'],
    raceValue:         ['race','population group'],
>>>>>>> Stashed changes
    schoolName:        ['school','high school','institution'],
    currentGrade:      ['grade','current grade'],
    matricYear:        ['matric year','exam year','year of matric'],
    matricType:        ['matric type','exam type'],
    examinationNumber: ['exam number','candidate number','examination number'],
    faculty:           ['faculty'],
    programme:         ['programme','course','program','qualification'],
    academicYear:      ['academic year','year of study'],
    studyMode:         ['study mode','mode of study','attendance'],
    nextOfKinName:     ['next of kin','guardian','parent name','emergency contact name'],
    heardAboutUs:      ['hear about us','heard about us','how did you hear','how did you find'],
    nextOfKinPhone:    ['guardian phone','parent phone','emergency contact number'],
    nextOfKinEmail:    ['guardian email','parent email'],
  };

  // ÔöÇÔöÇ 4. Helpers ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  function showToast(msg, color) {
    var old = document.getElementById('ssa-toast');
    if (old) old.remove();
    var t = document.createElement('div');
    t.id = 'ssa-toast';
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:90px;right:20px;padding:12px 18px;'
      + 'background:' + (color||'#10B981') + ';color:#fff;border-radius:10px;'
      + 'z-index:2147483647;font:14px Arial,sans-serif;'
      + 'box-shadow:0 4px 14px rgba(0,0,0,0.35);transition:opacity 0.4s;';
    document.body.appendChild(t);
    setTimeout(function() {
      t.style.opacity = '0';
      setTimeout(function() { if (t.parentNode) t.remove(); }, 400);
    }, 3000);
  }

  function isPlaceholder(text) {
    var t = (text || '').toLowerCase().trim();
    return !t || t === 'select' || t === 'choose' || t === 'please select'
      || t === 'none' || t.indexOf('--') !== -1
      || t.indexOf('select ') === 0 || t.indexOf('choose ') === 0;
  }

  function findOption(sel, want) {    if (!want) return null;
    var wl = want.toLowerCase().trim();
<<<<<<< Updated upstream
    var wlWords = wl.split(/\\s+/);
=======
>>>>>>> Stashed changes
    var best = null, bestScore = -1;
    for (var i = 0; i < sel.options.length; i++) {
      var opt = sel.options[i];
      if (isPlaceholder(opt.text)) continue;
      var tl = opt.text.toLowerCase().trim();
      var vl = opt.value.toLowerCase().trim();
<<<<<<< Updated upstream
      var tlWords = tl.split(/\\s+/);
      var vlWords = vl.split(/\\s+/);
=======
>>>>>>> Stashed changes
      var score = -1;
      if (tl === wl || vl === wl)                               score = 100;
      else if (tl.indexOf(wl) !== -1 || vl.indexOf(wl) !== -1) score = 50;
      else if (wl.indexOf(tl) !== -1 && tl.length > 2)         score = 30;
      else {
        var words = wl.split(/\\s+/);
        for (var w = 0; w < words.length; w++) {
          if (words[w].length > 2 && (tl.indexOf(words[w]) !== -1 || vl.indexOf(words[w]) !== -1)) {
            score = 10; break;
          }
        }
      }
      if (score > bestScore) { bestScore = score; best = opt; }
    }
    return bestScore >= 10 ? best : null;
  }

  // Plain value setter + minimal events ÔÇö ITS is plain HTML, no framework needed.
  // We still dispatch input+change for any JS validation the portal has.
  function fill(el, value) {
    if (!value && value !== 0) return false;
    var v = String(value);
    if (el.tagName === 'SELECT') {
      var opt = findOption(el, v);
      if (!opt) return false;
      el.value = opt.value;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      if (typeof jQuery !== 'undefined') {
        try { jQuery(el).trigger('change.select2'); } catch(e) {}
<<<<<<< Updated upstream
        try { jQuery(el).trigger('select2:select'); } catch(e) {}
        try { if (jQuery(el).data('select2')) jQuery(el).val(opt.value).trigger('change'); } catch(e) {}
=======
>>>>>>> Stashed changes
      }
      return true;
    }
    if (el.type === 'radio') {
      var radios = document.querySelectorAll('input[type=radio][name="' + el.name + '"]');
      var vl = v.toLowerCase().trim();
      for (var r = 0; r < radios.length; r++) {
        var rv = (radios[r].value || '').toLowerCase().trim();
        var rl = (radios[r].nextSibling ? radios[r].nextSibling.textContent || '' : '').toLowerCase().trim();
        if (rv === vl || rl.indexOf(vl) !== -1 || vl.indexOf(rv) !== -1) {
          radios[r].checked = true;
          radios[r].dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
      return false;
    }
    if (el.type === 'checkbox') return false;
    el.value = v;
    el.dispatchEvent(new Event('input',  { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur',   { bubbles: true }));
    return el.value.trim().length > 0;
  }

  function elText(el) {
    var parts = [
      el.name || '',
      el.id   || '',
      el.placeholder || '',
      el.getAttribute('aria-label') || '',
      el.getAttribute('title') || '',
      el.getAttribute('data-field') || '',
    ];
    if (el.labels && el.labels.length) {
      parts.push(el.labels[0].textContent);
    } else {
      var lid = el.getAttribute('for') || el.getAttribute('aria-labelledby');
      if (lid) {
        var lel = document.getElementById(lid);
        if (lel) parts.push(lel.textContent);
      }
      var p = el.parentElement;
      for (var d = 0; d < 3 && p; d++) {
        if (p.tagName === 'TD' || p.tagName === 'TH' || p.tagName === 'LABEL') {
          parts.push(p.textContent);
          break;
        }
        if (p.tagName === 'TR') {
          var cells = p.cells;
          if (cells && cells.length >= 2) parts.push(cells[0].textContent);
          break;
        }
        p = p.parentElement;
      }
    }
    return parts.join(' ').toLowerCase().replace(/[_\\-]/g, ' ').replace(/\\s+/g, ' ').trim();
  }

  function fuzzyMatch(el) {
    var text = elText(el);
    var bestKey = null, bestScore = 0;
    for (var key in fieldMap) {
      var aliases = fieldMap[key];
      for (var j = 0; j < aliases.length; j++) {
        if (text.indexOf(aliases[j]) !== -1) {
          var score = aliases[j].length * 2;
          if (score > bestScore) { bestScore = score; bestKey = key; }
          break;
        }
      }
    }
    return bestKey;
  }

<<<<<<< Updated upstream
  // ── 4b. Citizenship auto-fill ──────────────────────────────────────────
  // When a 13-digit SA ID is present (typed into the portal or from the
  // profile), auto-set the citizenship code field(s) to R.S.A. The portal's
  // own APEX eventRun sometimes fails to fire in the WebView, so we do it
  // ourselves — matching how this worked before the autofill refactor.
  function isSaidNumber(v) {
    return /^\\d{13}\$/.test((v || '').trim());
  }

  // Search all same-origin frames (recursively) — the ITS form often lives in an iframe.
  function allWindowsForCitizenship() {
    var out = [];
    (function walk(win) {
      try { out.push(win); } catch (e) { return; }
      try {
        for (var i = 0; i < win.frames.length; i++) {
          var f = win.frames[i];
          try { if (f.document) walk(f); } catch (e) {}
        }
      } catch (e) {}
    })(window);
    return out;
  }

  function findIdFieldIn(doc) {
    return doc.getElementById('oapIDnumber')
      || doc.querySelector('input[name="OAPIDNUMBER"]')
      || doc.querySelector('input[name="oapIDnumber"]')
      || doc.querySelector('input[id*="idNumber" i]')
      || doc.querySelector('input[name*="IDNUMBER" i]');
  }

  function ssaAutoCitizenship() {
    var idn = '';
    var wins = allWindowsForCitizenship();
    for (var w = 0; w < wins.length; w++) {
      var idEl = findIdFieldIn(wins[w].document);
      if (idEl && (idEl.value || '').trim()) {
        idn = (idEl.value || '').trim();
        break;
      }
    }
    // If the user typed something in the ID field, trust it — a passport
    // number must NOT be overridden. Only fall back to the profile ID when
    // the field is empty (e.g. the star autofill ran first).
    if (!idn) idn = (profile.personal && profile.personal.idNumber || '').trim();
    if (!isSaidNumber(idn)) return;

    // Portal field names for citizenship (from ITS exact-name map)
    var citizenshipFields = [
      'OAPCITZCODE',      // Primary citizenship code field
      'OAPCITCODE',       // Alternative citizenship code field
      'OAPCITCODE_DESC',  // Citizenship code description (LOV display)
      'OAPCITIZENTYPE',   // Citizen type (Yes/No)
      'OAPCITZCODE_DESC', // Alternative description field
    ];

    var wrote = 0;
    for (var w = 0; w < wins.length; w++) {
      var doc = wins[w].document;
      for (var n = 0; n < citizenshipFields.length; n++) {
        var fieldName = citizenshipFields[n];
        var el = doc.getElementById(fieldName)
          || doc.querySelector('input[name="' + fieldName + '"]')
          || doc.querySelector('select[name="' + fieldName + '"]');
        if (!el) continue;
        try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch (e) {}
        var value = (fieldName === 'OAPCITIZENTYPE') ? 'Yes' : 'R.S.A';
        el.value = value;
        el.dispatchEvent(new Event('input',  { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur',   { bubbles: true }));
        wrote++;
        console.log('✅ Citizenship field auto-set: ' + fieldName + ' = ' + value + ' (frame: ' + (w === 0 ? 'top' : 'iframe') + ')');
      }
    }
    // Also check for custom dropdown
    for (var w = 0; w < wins.length; w++) {
      var sel = wins[w].document.getElementById('custom-citz-code');
      if (sel && sel.value !== 'R.S.A') {
        sel.value = 'R.S.A';
        sel.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
    if (wrote > 0) showToast('Citizenship Code → R.S.A', '#10B981');
  }

  function isIdField(el) {
    if (!el || !el.tagName) return false;
    var n = (el.name || '').toUpperCase().replace(/[_-\\s]/g, '');
    var i = (el.id || '').toUpperCase().replace(/[_-\\s]/g, '');
    return n.indexOf('IDNUMBER') !== -1 || n.indexOf('IDNO') !== -1
      || n.indexOf('PASSPORT') !== -1 || n.indexOf('OAPIDNUMBER') !== -1
      || i.indexOf('OAPIDNUMBER') !== -1;
  }

  document.addEventListener('input',  function(e) { if (isIdField(e.target)) ssaAutoCitizenship(); }, true);
  document.addEventListener('change', function(e) { if (isIdField(e.target)) ssaAutoCitizenship(); }, true);
  document.addEventListener('blur',   function(e) { if (isIdField(e.target)) ssaAutoCitizenship(); }, true);

=======
  // ÔöÇÔöÇ 5. Main autofill ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
>>>>>>> Stashed changes
  function doAutofill() {
    console.log('🔍 Autofill started');

    // Check page code - only autofill from Biographical page (ITS_OAP02) onwards
    // NOT on Start page (ITS_OAP_START) which has student-responsibility fields
    var pageCode = document.getElementById('page_code')?.value || '';
    var validPages = ['ITS_OAP02', 'ITS_OAP02_1', 'ITS_OAP03', 'ITS_OAP04', 'ITS_OAP05', 'ITS_OAP06', 'ITS_OAP07', 'ITS_OAP08'];
    var isValidPage = validPages.some(function(p) { return pageCode.indexOf(p) !== -1; });

    if (!isValidPage) {
      console.log('🔍 Autofill skipped - not a valid page for autofill: ' + pageCode);
      showToast('Auto-fill skipped: This page requires your input', '#EF4444');
      try { AutofillResult.postMessage(JSON.stringify({ filled: 0, total: 0, skipped: true })); } catch (e) {}
      return;
    }

<<<<<<< Updated upstream
    console.log('🔍 Autofill started on page: ' + pageCode);

    // Trigger blur on ID number field so APEX eventRun() fires
    // and populates citizenship + other dependent fields
    var wins = allWindowsForCitizenship();
    var idEl = null;
    for (var w = 0; w < wins.length; w++) {
      var doc = wins[w].document;
      idEl = doc.getElementById('oapIDnumber')
        || doc.querySelector('input[name="OAPIDNUMBER"]')
        || doc.querySelector('input[name="oapIDnumber"]')
        || doc.querySelector('input[id*="id" i]');
      if (idEl) break;
=======
    var inputs = document.querySelectorAll(
      'input:not([type=hidden]):not([type=submit]):not([type=button])'
      + ':not([type=reset]):not([type=image]),'
      + 'select, textarea'
    );

    var filled = 0;
    var alreadyHandled = {};

    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      if (el.readOnly || el.disabled) continue;

      var elName = (el.name || '').toUpperCase().trim();

      // Pass 1: ITS exact name match (highest confidence)
      if (elName && itsExact[elName] !== undefined) {
        if (itsExact[elName] && fill(el, itsExact[elName])) {
          el.style.outline = '3px solid #10B981';
          filled++;
          alreadyHandled[i] = true;
          continue;
        }
      }

      // Pass 2: ITS partial/case-insensitive name match
      if (elName) {
        for (var itk in itsExact) {
          if (elName.indexOf(itk) !== -1 || itk.indexOf(elName) !== -1) {
            if (itsExact[itk] && fill(el, itsExact[itk])) {
              el.style.outline = '3px solid #10B981';
              filled++;
              alreadyHandled[i] = true;
              break;
            }
          }
        }
        if (alreadyHandled[i]) continue;
      }

      // Pass 3: Generic fuzzy match on label/placeholder text
      var key = fuzzyMatch(el);
      if (key && vs[key]) {
        if (fill(el, vs[key])) {
          el.style.outline = '3px solid #10B981';
          filled++;
        }
      }
>>>>>>> Stashed changes
    }
    if (idEl && idEl.value) {
      idEl.dispatchEvent(new Event('blur', { bubbles: true }));
      console.log('✅ Blur fired on ID number field');
    }

    // Auto-set citizenship code to R.S.A when a valid SA ID is present.
    ssaAutoCitizenship();

    var msg = filled > 0 ? '✅ Filled ' + filled + ' fields' : 'No fields found';
    console.log(msg);

    // ── Retry dynamic Select2 selects ──────────────────────────
    var fallbackOpts = {
      'select[name="race"]':    ['African','Asian','Coloured','Indian','Other','White'],
      'select[name="address"]': ['Eastern Cape','Free State','Gauteng','Kwazulu/Natal','Limpopo','Mpumalanga','North West','Northern Cape','Western Cape'],
    };

    function tryFillSelect(sel, val) {
      var el = document.querySelector(sel);
      if (!el || !val) return false;
      if (el.options.length === 0) return false;
      el.removeAttribute('readonly');
      var opt = findOption(el, val);
      if (!opt) return false;
      el.value = opt.value;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      if (typeof jQuery !== 'undefined') {
        try { jQuery(el).trigger('change.select2'); } catch(e) {}
        try { jQuery(el).trigger('select2:select'); } catch(e) {}
        try { if (jQuery(el).data('select2')) jQuery(el).val(opt.value).trigger('change'); } catch(e) {}
      }
      el.style.outline = '3px solid #10B981';
      filled++;
      return true;
    }

    function injectFallback(sel, val) {
      var el = document.querySelector(sel);
      if (!el || !val) return false;
      if (el.options.length > 0) return false;
      var opts = fallbackOpts[sel];
      if (!opts) return false;
      opts.forEach(function(text) {
        var opt = document.createElement('option');
        opt.value = text;
        opt.text = text;
        el.add(opt);
      });
      el.value = val;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      if (typeof jQuery !== 'undefined') {
        try { jQuery(el).trigger('change.select2'); } catch(e) {}
        try { jQuery(el).trigger('select2:select'); } catch(e) {}
        try { if (jQuery(el).data('select2')) jQuery(el).val(val).trigger('change'); } catch(e) {}
      }
      el.style.outline = '3px solid #10B981';
      filled++;
      return true;
    }

    var pending = dynamicSelects.filter(function(d) { return !tryFillSelect(d.sel, d.val); });
    if (pending.length > 0) {
      var retries = 0;
      var retryInterval = setInterval(function() {
        retries++;
        pending = pending.filter(function(d) { return !tryFillSelect(d.sel, d.val); });
        if (pending.length === 0 || retries >= 30) {
          clearInterval(retryInterval);
          // Fallback: inject options if API never loaded
          pending.forEach(function(d) { injectFallback(d.sel, d.val); });
        }
      }, 500);
    }

    showToast(
      filled > 0
        ? 'Ô£à Filled ' + filled + ' field' + (filled !== 1 ? 's' : '') + '!'
        : 'No fields matched. Try scrolling to the next section.',
      filled > 0 ? '#10B981' : '#EF4444'
    );
<<<<<<< Updated upstream

    try { AutofillResult.postMessage(JSON.stringify({ filled: filled, total: filled })); } catch (e) {}
=======
>>>>>>> Stashed changes
  }

  window.requestFlutterAutofill = doAutofill;

  // Auto-inject date picker after APEX initializes
  (function() {
    var profile = $profileJson;
    var dobIso = (profile.personal && profile.personal.dateOfBirth) || '';
    if (!dobIso || dobIso.length < 10) return;

    function tryInject() {
      // Check if APEX is ready (apex object exists and page is initialized)
      if (window.apex && window.apex.page && window.apex.page.isInitialized) {
        fillDateFields(dobIso);
        return;
      }
      // Or wait for apexafterrefresh event
      if (window.apex && window.apex.event) {
        window.apex.event.trigger(document, 'apexafterrefresh');
        setTimeout(tryInject, 500);
        return;
      }
      // Fallback: retry after delay
      setTimeout(tryInject, 500);
    }

    // Start after a short delay to let APEX initialize
    setTimeout(tryInject, 1000);
  })();

  ${addFloatingStar ? '''
  // Floating Star button
  (function() {
    if (document.getElementById('ssa-star')) return;
    const star = document.createElement('div');
    star.id = 'ssa-star';
<<<<<<< Updated upstream
    star.textContent = '⭐';
    star.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: #0F1624;
      color: #FFD700;
      font-size: 32px;
      border: 2px solid #7C3AED;
      box-shadow: 0 4px 20px rgba(124,58,237,0.5);
      z-index: 2147483646;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      user-select: none;
    `
    star.onclick = function() {
      console.log('⭐ Star clicked — running doAutofill');
      if (typeof doAutofill === 'function') {
        doAutofill();
      } else {
        console.log('❌ doAutofill not found');
}
        }
        document.body.appendChild(star);
        console.log('✅ Star injected and connected to doAutofill');
      });
    }''' : ''}

  ${!addFloatingStar ? 'doAutofill();' : ''}
=======
    star.innerHTML = 'Ô¡É';
    star.title = 'Star Auto-Fill';
    star.style.cssText = 'position:fixed;bottom:24px;right:24px;width:56px;height:56px;'
      + 'background:#0F1624;border-radius:50%;z-index:2147483646;cursor:pointer;'
      + 'display:flex;align-items:center;justify-content:center;'
      + 'box-shadow:0 4px 20px rgba(124,58,237,0.5);border:2px solid #7C3AED;'
      + 'color:#FFD700;font-size:32px;user-select:none;';
    star.onclick = doAutofill;
    function tryAppend() {
      if (document.body) document.body.appendChild(star);
      else setTimeout(tryAppend, 300);
    }
    tryAppend();
  })();
  ''' : ''}
>>>>>>> Stashed changes

})();
''';
}

// ── Portal patches ──────────────────────────────────────────────────────────
// Stub implementations for build*Patch functions referenced by webview_impl.dart
// and university_portal_screen.dart. These fix APEX portal rendering and
// navigation inside a Flutter WebView.

String buildNavigationFixScript() {
  return '''
var __ssaNavfix = function() {
  // ── ITS URL helpers ─────────────────────────────────────────────────
  // ITS portal navigation uses RELATIVE URLs everywhere
  // (location.replace('gen.gw1pkg.gw1view'), dynamic form action
  // 'gen.gw1pkg.gw1proc', ...). The Android WebView sometimes truncates
  // these to '.../gen.gw1pkg.gw1v' / '.../gen.gw1pkg.gw1p' when resolving
  // or requesting them, which 404s. We expand truncated procedure names
  // and resolve relative URLs to absolute BEFORE they leave the page.

  // Expand a truncated ITS procedure name. Handles full-marker truncation
  // (gen.gw1pkg.gw1v -> gen.gw1pkg.gw1view, gen.gw1pkg.gw1p -> gw1proc) plus
  // aggressive truncation where the marker itself is partially eaten by a
  // 64-char URL limit (gwa/gwas/gwav/gwavs -> gw1view, gw1p/gw1pr/gw1pro ->
  // gw1proc, and short-marker 'gen.gw1pkg.gw' remainders like 'a'/'p').
  function _expandFromMarker(u, pos, markerLen, fullMarker) {
    var restStart = pos + markerLen;
    var rest = u.substring(restStart);
    var q = rest.indexOf('?');
    var sl = rest.indexOf('/');
    var hs = rest.indexOf('#');
    var cut;
    if (q === -1 && sl === -1 && hs === -1) { cut = rest.length; }
    else {
      cut = rest.length;
      if (q !== -1 && q < cut) cut = q;
      if (sl !== -1 && sl < cut) cut = sl;
      if (hs !== -1 && hs < cut) cut = hs;
    }
    var proc = rest.substring(0, cut);
    var tail = rest.substring(cut);
    if (fullMarker) {
      if (proc === 'view' || proc === 'v' || proc === 'vi' || proc === 'vie' ||
          proc === 'gwa' || proc === 'gwas' || proc === 'gwav' || proc === 'gwavs' ||
          proc === 'gw1v' || proc === 'gw1vi' || proc === 'gw1vie' ||
          proc === 'a' || proc === 'as' || proc === 'av' || proc === 'avs') {
        return u.substring(0, restStart) + 'view' + tail;
      }
      if (proc === 'proc' || proc === 'p' || proc === 'pr' || proc === 'pro' ||
          proc === 'gw1p' || proc === 'gw1pr' || proc === 'gw1pro') {
        return u.substring(0, restStart) + 'proc' + tail;
      }
      return u.substring(0, restStart) + proc + tail;
    }
    if (proc === '' || proc === '1' || proc.indexOf('1v') === 0 ||
        proc.indexOf('1gwa') === 0 || proc.indexOf('1gwav') === 0 ||
        proc.indexOf('1gwas') === 0) {
      return u.substring(0, restStart) + '1view' + tail;
    }
    if (proc === '1' || proc.indexOf('1p') === 0) {
      return u.substring(0, restStart) + '1proc' + tail;
    }
    if (proc === 'a' || proc === 'as' || proc === 'av' || proc === 'avs') {
      return u.substring(0, restStart) + '1view' + tail;
    }
    if (proc === 'p' || proc === 'pr' || proc === 'pro') {
      return u.substring(0, restStart) + '1proc' + tail;
    }
    return u.substring(0, restStart) + proc + tail;
  }

  function expandProc(u) {
    if (typeof u !== 'string') return u;
    var fullMarker = 'gen.gw1pkg.gw1';
    var shortMarker = 'gen.gw1pkg.gw';
    var i = u.indexOf(fullMarker);
    if (i !== -1) return _expandFromMarker(u, i, fullMarker.length, true);
    var j = u.indexOf(shortMarker);
    if (j !== -1) return _expandFromMarker(u, j, shortMarker.length, false);
    return u;
  }

  // Resolve a possibly-relative URL against the current page URL.
  function resolveUrl(u) {
    if (typeof u !== 'string' || !u) return u;
    if (u.indexOf('http://') === 0 || u.indexOf('https://') === 0 ||
        u.indexOf('javascript:') === 0 || u.indexOf('data:') === 0 ||
        u.indexOf('mailto:') === 0 || u.indexOf('#') === 0) return u;
    var base = window.location.href;
    var hash = base.indexOf('#'); if (hash !== -1) base = base.substring(0, hash);
    var query = base.indexOf('?'); if (query !== -1) base = base.substring(0, query);
    if (u.charAt(0) === '/') {
      var scheme = base.indexOf('//');
      var originSlash = base.indexOf('/', scheme + 2);
      var origin = originSlash === -1 ? base : base.substring(0, originSlash);
      return origin + u;
    }
    var lastSlash = base.lastIndexOf('/');
    var dir = lastSlash === -1 ? base + '/' : base.substring(0, lastSlash + 1);
    return dir + u;
  }

  function fixUrl(u) { return resolveUrl(expandProc(u)).replace('unlven', 'univen'); }

  // Report to the Flutter layer for on-device visibility.
  function diag(msg) {
    console.log('[navfix] ' + msg);
    try { AutofillResult.postMessage(JSON.stringify({ diag: msg })); } catch (e) {}
  }

  // ── Form actions ────────────────────────────────────────────────────
  // A POST form whose action points at a gw1view page must POST to gw1proc —
  // the ITS server only accepts POSTs at the proc handler and answers a POST
  // to gw1view with a 404. wizard.js sometimes (re)sets the Next form action
  // to gw1view, so rewrite it here and again right before submit.
  function rewriteViewToProc(u) {
    if (typeof u !== 'string' || u.indexOf('gen.gw1pkg.gw1') === -1) return u;
    return u.replace(/(gen.gw1pkg.gw1)view([^a-zA-Z0-9]|\$)/g, '\$1proc\$2');
  }

  function fixAction(form, log) {
    if (!form || form.tagName !== 'FORM') return;
    var before = form.getAttribute('action') || '';
    var after = fixUrl(before);
    // Only rewrite view->proc for explicit POST forms; a form with no method
    // attribute GETs and must keep its gw1view target.
    var method = (form.getAttribute('method') || '').toUpperCase();
    if (method === 'POST') after = rewriteViewToProc(after);
    if (after !== before) {
      form.setAttribute('action', after);
      console.log('[navfix] form action: ' + before + ' -> ' + after);
      if (log) diag('Form action: ' + before + ' -> ' + after);
    }
  }

  // A form is an ITS wizard POST target when its action resolves to
  // .../gen.gw1pkg.gw1proc (or its truncated .../gw1p form).
  function isItsPostForm(f) {
    if (!f || f.tagName !== 'FORM') return false;
    var a = (f.getAttribute('action') || f.action || '').toString();
    return a.indexOf('gen.gw1pkg.gw1') !== -1 && /gw1(proc|p)([^a-z]|\$)/.test(a);
  }

  // ROOT CAUSE: wizard.js always builds a fresh form whose action is the
  // correct relative 'gen.gw1pkg.gw1proc' and calls xForm.submit(). But the
  // Android WebView mangles the native form POST, truncating 'gw1proc' to
  // 'gw1p' / 'gw1view' to 'gw1v' when the request goes out, so the server 404s.
  // JS cannot see that mangling (it happens below the page), so we never let
  // the native POST run: we POST the same body via fetch to the full absolute
  // URL and write the returned page back into the document.
  function submitViaFetch(f) {
    var target = (f.getAttribute('action') || f.action || '').toString();
    if (target.indexOf('gen.gw1pkg.gw1') === -1) return false;
    try {
      var body = new URLSearchParams(new FormData(f)).toString();
      console.log('[navfix] fetch POST -> ' + target);
      diag('POST via fetch -> ' + target);
      fetch(target, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
        body: body,
        redirect: 'manual',
        credentials: 'same-origin'
      }).then(function(res) {
        // ITS uses Post/Redirect/Get: a 3xx means "next page", which the
        // WebView must follow NATIVELY — a fetch-followed GET of the redirect
        // target loses the POST context and renders a blank white page.
        if (res.type === 'opaqueredirect' || (res.status >= 300 && res.status < 400)) {
          var loc = null;
          try { loc = res.headers.get('Location'); } catch (e) {}
          if (loc) {
            console.log('[navfix] fetch POST redirect -> ' + loc);
            window.location.assign(resolveUrl(loc));
          } else {
            try { realSubmit.call(f); } catch (e2) {}
          }
          return;
        }
        return res.text().then(function(html) {
          console.log('[navfix] fetch POST done: HTTP ' + res.status + ' len ' + html.length);
          diag('POST back HTTP ' + res.status + ' (' + html.length + ' chars)');
          // A blank/empty body would document.write into a white page —
          // navigate natively so the real ITS response shows instead.
          if (!html || html.replace(/s+/g, '').length === 0) {
            console.log('[navfix] blank POST response, navigating natively to ' + target);
            window.location.assign(target);
            return;
          }
          document.open();
          document.write(html);
          document.close();
          // The new document has no listeners (they were attached to the old
          // one) — re-run navfix so the next page's form submits are hijacked.
          setTimeout(function() {
            try { __ssaNavfix(); } catch (e) {}
          }, 30);
        });
      }).catch(function(err) {
        console.log('[navfix] fetch POST failed, falling back to native submit: ' + err);
        try { realSubmit.call(f); } catch (e2) {}
      });
      return true;
    } catch (e) {
      console.log('[navfix] fetch POST exception, falling back: ' + e);
      return false;
    }
  }

  document.addEventListener('submit', function(e) {
    var f = e.target;
    fixAction(f, true);
    if (isItsPostForm(f)) {
      e.preventDefault();
      if (!submitViaFetch(f)) { try { realSubmit.call(f); } catch (err) {} }
    }
  }, true);

  // Direct form.submit() calls fire NO 'submit' event — patch the prototype
  // so the POST is hijacked (and the action corrected) before it goes out.
  // Use a window-level copy of the TRUE original so a re-run (after a
  // document.write-rendered page) never captures the already-wrapped submit —
  // that would recurse forever in the fetch-failure fallback.
  var realSubmit = window.__ssaRealSubmit || HTMLFormElement.prototype.submit;
  window.__ssaRealSubmit = realSubmit;
  if (realSubmit && !realSubmit.__ssaPatched) {
    var submitWrapper = function() {
      var f = this;
      fixAction(f, true);
      if (isItsPostForm(f) && submitViaFetch(f)) return;
      return realSubmit.apply(this, arguments);
    };
    submitWrapper.__ssaPatched = true;
    HTMLFormElement.prototype.submit = submitWrapper;
  }

  var forms = document.querySelectorAll('form');
  for (var i = 0; i < forms.length; i++) fixAction(forms[i]);

  var observer = new MutationObserver(function(mutations) {
    for (var m = 0; m < mutations.length; m++) {
      var nodes = mutations[m].addedNodes;
      for (var n = 0; n < nodes.length; n++) {
        var node = nodes[n];
        if (node.tagName === 'FORM') {
          fixAction(node);
        } else if (node.querySelectorAll) {
          var dyn = node.querySelectorAll('form');
          for (var d = 0; d < dyn.length; d++) fixAction(dyn[d]);
        }
      }
    }
  });
  if (document.body) observer.observe(document.body, { childList: true, subtree: true });

  // ── Page enhancements (run on every page, incl. fetch-written ones) ──

  // Replace the ITS citizenship LOV with a plain dropdown.
  function ssaCitizenship() {
    if (document.getElementById('custom-citz-code')) return;
    var citz = document.getElementById('oapCitzCode');
    if (!citz) return;
    var countryList = [
      'AFGHANISTAN','ALBANIA','ALGERIA','ANDORRA','ANGOLA','ANTIGUA AND BARBUDA',
      'ARGENTINA','ARMENIA','AUSTRALIA','AUSTRIA','AZERBAIJAN','BAHAMAS','BAHRAIN',
      'BANGLADESH','BARBADOS','BELARUS','BELGIUM','BELIZE','BENIN','BHUTAN','BOLIVIA',
      'BOSNIA AND HERZEGOVINA','BOTSWANA','BRAZIL','BURKINA FASO','BURUNDI','CAMEROON',
      'CAPE VERDE','CENTRAL AFRICAN REPUBLIC','CHAD','CORTE de VOIRE','DJIBOUTI','EGYPT',
      'EQUATORIAL GUINEA','ERITREA','ETHIOPIA','FRANCE','GABON','GAMBIA','GERMANY','GHANA',
      'GUINEA BISAU','INDIA','ITALY','KENYA','LESOTHO','LIBERIA','LIBYA','MADAGASCAR','MALAWI',
      'MALI','MAURITANIA','MAURITIUS','MOROCCO','MOZAMBIQUE','NAMIBIA','NIGER','NIGERIA',
      'OTHER AFRICAN COUNTRIES','R.S.A','RWANDA','SENEGAL','SEYCHELLES','SIERRA LEONE',
      'SUDAN','SWAZILAND','TANZANIA','TOGO','TUNISIA','UGANDA','UNITED ARAB EMIRATES',
      'ZAMBIA','ZIMBABWE'
    ];
    var wrapper = citz.closest('div');
    if (!wrapper) return;
    var lovBtn = wrapper.querySelector('a[onclick*="lov"], img[src*="lov.gif"]');
    if (lovBtn) lovBtn.remove();
    var select = document.createElement('select');
    select.id = 'custom-citz-code';
    select.style.cssText = 'width:100%;padding:8px;font-size:16px;border:1px solid #ccc;border-radius:4px;';
    var emptyOption = document.createElement('option');
    emptyOption.value = ''; emptyOption.textContent = '';
    select.appendChild(emptyOption);
    countryList.forEach(function(country) {
      var opt = document.createElement('option');
      opt.value = country; opt.textContent = country;
      select.appendChild(opt);
    });
    select.addEventListener('change', function() {
      citz.value = this.value;
      citz.dispatchEvent(new Event('change', { bubbles: true }));
      citz.dispatchEvent(new Event('input', { bubbles: true }));
      console.log('Citizenship Code set to: ' + this.value);
    });
    var observer = new MutationObserver(function() {
      if (citz.value !== select.value) select.value = citz.value;
    });
    observer.observe(citz, { attributes: true, attributeFilter: ['value'] });
    citz.addEventListener('change', function() { select.value = citz.value; });
    citz.addEventListener('input', function() { select.value = citz.value; });
    wrapper.insertBefore(select, citz);
    console.log('Custom citizenship dropdown injected');
  }

  // The shared DOM date picker (ssaDatePickerJs) is embedded at the end of this
  // script so it re-attaches on every page/frame — the old inline calendar that
  // collided with it ('ssa-date-picker' id) was removed entirely.

  // Replace the ITS "Where did you hear about us" LOV with a plain select.
  function ssaHeardDropdown() {
    if (document.getElementById('ssa-heard-select')) return;
    var field = document.getElementById('oapHeard')
      || document.querySelector('input[name="oapHeard"]')
      || document.querySelector('input[name="OAPHEARD"]');
    if (!field) return;

    var OPTIONS = ["FRIEND/FAMILY", "NEWSPAPER", "PERSONAL", "PUBLIC RELATION'S OFFICER",
      "RADIO", "SOCIAL MEDIA", "SCHOOL TEACHER", "TELEVISION", "UNIVEN WEB SITE"];

    var cell = field.closest('td, div, fieldset');
    if (cell) {
      var lovs = cell.querySelectorAll('a[onclick*="lov"], img[src*="lov"], button, input[type="image"]');
      for (var i = 0; i < lovs.length; i++) lovs[i].style.display = 'none';
    }

    var desc = document.getElementById('oapHeard_desc')
      || document.querySelector('input[name="oapHeard_desc"]')
      || document.querySelector('input[name="OAPHEARD_DESC"]');
    if (desc) desc.style.display = 'none';
    field.style.display = 'none';

    var sel = document.createElement('select');
    sel.id = 'ssa-heard-select';
    sel.style.cssText = 'width:100%;min-width:220px;padding:11px 10px;font-size:16px;border:1px solid #7C3AED;border-radius:6px;background:#fff;color:#0F1624;position:relative;z-index:10000;';

    var ph = document.createElement('option');
    ph.value = ''; ph.textContent = '-- Select --'; ph.disabled = true; ph.selected = true;
    sel.appendChild(ph);

    OPTIONS.forEach(function(o) {
      var op = document.createElement('option');
      op.value = o; op.textContent = o;
      if (o === field.value) op.selected = true;
      sel.appendChild(op);
    });

    sel.addEventListener('change', function() {
      field.value = this.value;
      if (desc) { desc.value = this.value; desc.dispatchEvent(new Event('change', { bubbles: true })); }
      field.dispatchEvent(new Event('change', { bubbles: true }));
      field.dispatchEvent(new Event('input', { bubbles: true }));
      field.dispatchEvent(new Event('blur', { bubbles: true }));
      console.log('Heard about us set to: ' + this.value);
    });

    field.parentNode.insertBefore(sel, field.nextSibling);
    console.log('Heard-about-us dropdown injected');
  }

  function ssaEnhance() {
    ssaCitizenship();
    ssaHeardDropdown();
  }

  // ── JS navigations (location.replace / assign) ──────────────────────
  var originalReplace = window.location.replace;
  if (originalReplace && !originalReplace.__ssaPatched) {
    var rp = function(u) {
      var fixed = fixUrl(u);
      if (typeof u === 'string' && fixed !== u) {
        console.log('[navfix] nav: ' + u + ' -> ' + fixed);
        diag('Nav: ' + u + ' -> ' + fixed);
      }
      return originalReplace.call(this, fixed);
    };
    rp.__ssaPatched = true;
    window.location.replace = rp;
  }
  var originalAssign = window.location.assign;
  if (originalAssign && !originalAssign.__ssaPatched) {
    var as = function(u) {
      var fixed = fixUrl(u);
      if (typeof u === 'string' && fixed !== u) {
        console.log('[navfix] nav: ' + u + ' -> ' + fixed);
        diag('Nav: ' + u + ' -> ' + fixed);
      }
      return originalAssign.call(this, fixed);
    };
    as.__ssaPatched = true;
    window.location.assign = as;
  }

  // location.href = '...' / window.location = '...' bypass both replace and
  // assign. Patch the Location href setter so those get expanded too.
  try {
    var loc = window.location;
    var locProto = Object.getPrototypeOf(loc);
    var hrefDesc = Object.getOwnPropertyDescriptor(locProto, 'href');
    if (hrefDesc && hrefDesc.set && !hrefDesc.set.__ssaPatched) {
      var origHrefGet = hrefDesc.get;
      var origHrefSet = hrefDesc.set;
      var hrefSetWrapper = function(v) {
        var fixed = fixUrl(v);
        if (typeof v === 'string' && fixed !== v) {
          console.log('[navfix] location.href: ' + v + ' -> ' + fixed);
          diag('location.href: ' + v + ' -> ' + fixed);
        }
        return origHrefSet.call(this, fixed);
      };
      hrefSetWrapper.__ssaPatched = true;
      Object.defineProperty(locProto, 'href', {
        configurable: true,
        enumerable: true,
        get: function() { return origHrefGet.call(this); },
        set: hrefSetWrapper
      });
    }
  } catch (e) {}

  // Plain <a href="gen.gw1pkg.gw1..."> links fire no submit event and don't go
  // through replace/assign. Expand + absolutize their href at click time so a
  // truncated relative link can't 404. Capture phase so it runs before the
  // default navigation.
  document.addEventListener('click', function(e) {
    var el = e.target;
    while (el && el.tagName !== 'A') { el = el.parentElement; }
    if (!el || !el.href) return;
    var h = el.getAttribute('href');
    if (!h || h.indexOf('gen.gw1pkg.gw1') === -1) return;
    var fixed = fixUrl(h);
    if (fixed !== h) {
      el.setAttribute('href', fixed);
      console.log('[navfix] link href: ' + h + ' -> ' + fixed);
    }
  }, true);

  // ── fetch/XHR redirects ─────────────────────────────────────────────
  var originalFetch = window.fetch;
  if (originalFetch && !originalFetch.__ssaPatched) {
    var fetcher = function(input, init) {
      var u = typeof input === 'string' ? input : (input && input.url ? input.url : '');
      var fixed = fixUrl(u);
      if (fixed !== u) {
        if (typeof input === 'string') { input = fixed; }
        else if (input && input.url) { input.url = fixed; }
      }
      return originalFetch.call(this, input, init);
    };
    fetcher.__ssaPatched = true;
    window.fetch = fetcher;
  }

  // ── Dynamic relative resources (JSONP / script srcs) ────────────────
  // its_scripts.js callDynBGproc() injects JSONP <script> tags with a RELATIVE
  // src ('web.w01pkg.w01_setHeader?x_stmp=...&x_call=...'). Like form actions,
  // a relative ITS URL can be mangled by the WebView and 404. Replace it with
  // an equivalent that uses the resolved absolute src so the request can't be
  // mangled. (This mirrors how the page's other relative navigations are fixed.)
  if (typeof window.callDynBGproc === 'function' && !window.callDynBGproc.__ssaPatched) {
    window.callDynBGproc = function(DBProcedure, DBParameters, DBTagName) {
      var dynamicScriptAreaTagName = 'dynScriptArea';
      var d = new Date();
      var v_param = DBParameters;
      if (v_param === undefined) { v_param = '&'; }
      var v_new_param = v_param.replace(/&/gi, '*').replace(/\\+/g, '~');
      if (DBTagName && DBTagName !== '') { dynamicScriptAreaTagName = DBTagName; }
      var xx = document.getElementById(dynamicScriptAreaTagName);
      if (xx != null && xx.parentNode) { xx.parentNode.removeChild(xx); }
      var xscript = document.createElement('script');
      xscript.setAttribute('language', 'Javascript');
      xscript.setAttribute('type', 'text/javascript');
      xscript.setAttribute('id', dynamicScriptAreaTagName);
      var src = 'web.w01pkg.w01_setHeader?x_stmp=' + escape(d.getTime()) +
                '&x_call=' + DBProcedure + '&x_parms=' + escape(v_new_param);
      xscript.setAttribute('src', fixUrl(src));
      document.getElementsByTagName('head').item(0).appendChild(xscript);
      window.status = 'Done';
      return true;
    };
    window.callDynBGproc.__ssaPatched = true;
  }

  // Absolutize any other relative ITS resource URL (script/iframe/img/link)
  // that the page adds after load (document.write pages, AJAX, LOV popups).
  function absolutizeResourceEl(el) {
    if (!el || !el.getAttribute) return;
    var attr = null;
    if (el.tagName === 'SCRIPT' || el.tagName === 'IFRAME' || el.tagName === 'IMG') attr = 'src';
    else if (el.tagName === 'LINK' || el.tagName === 'A') attr = 'href';
    if (!attr) return;
    var v = el.getAttribute(attr);
    if (!v || typeof v !== 'string') return;
    if (v.indexOf('http://') === 0 || v.indexOf('https://') === 0 || v.indexOf('data:') === 0 ||
        v.indexOf('javascript:') === 0 || v.indexOf('mailto:') === 0 || v.indexOf('//') === 0 ||
        v.charAt(0) === '/' || v.charAt(0) === '#') return;
    var fixed = fixUrl(v);
    if (fixed !== v) {
      el.setAttribute(attr, fixed);
      console.log('[navfix] resource src: ' + v + ' -> ' + fixed);
    }
  }

  var resObserver = new MutationObserver(function(muts) {
    for (var m = 0; m < muts.length; m++) {
      var nodes = muts[m].addedNodes;
      for (var n = 0; n < nodes.length; n++) {
        var node = nodes[n];
        if (node.nodeType !== 1) continue;
        absolutizeResourceEl(node);
        if (node.querySelectorAll) {
          var subs = node.querySelectorAll('script[src], iframe[src], img[src], link[href]');
          for (var s = 0; s < subs.length; s++) absolutizeResourceEl(subs[s]);
        }
      }
    }
  });
  resObserver.observe(document.documentElement, { childList: true, subtree: true });

  diag('Page: ' + window.location.href);
  diag('NavFix injected');

  ssaEnhance();
  setTimeout(ssaEnhance, 800);
  setTimeout(ssaEnhance, 2500);

  // Shared DOM date picker — idempotent and frame-aware. Re-attached here on
  // every page/frame (incl. fetch + document.write POST navigations) so the
  // portal's own broken calendar never gets a chance to surface.
  $ssaDatePickerJs
};
__ssaNavfix();

// ITS can render the application form inside a same-origin iframe, which the
// top-frame script cannot reach directly. Re-apply the fix inside every
// same-origin iframe so their form actions / navigations are corrected too.
function __ssaApplyToFrames() {
  try {
    var frames = document.querySelectorAll('iframe');
    for (var i = 0; i < frames.length; i++) {
      try {
        var doc = frames[i].contentDocument;
        if (doc && doc !== document) {
          var s = doc.createElement('script');
          s.textContent = '(' + __ssaNavfix.toString() + ')();';
          doc.documentElement.appendChild(s);
        }
      } catch (e) {}
    }
  } catch (e) {}
}
__ssaApplyToFrames();
setTimeout(__ssaApplyToFrames, 1200);
setTimeout(__ssaApplyToFrames, 3000);
setTimeout(__ssaApplyToFrames, 6000);
setTimeout(__ssaApplyToFrames, 12000);
''';
}

String buildViewportPatch() {
  return '''
(function() {
  var vp = document.querySelector('meta[name="viewport"]');
  if (!vp) {
    vp = document.createElement('meta');
    vp.name = 'viewport';
    document.head.appendChild(vp);
  }
  vp.content = 'width=device-width, initial-scale=1.0, maximum-scale=3.0, user-scalable=yes';
  console.log('Viewport patch applied');
})();
''';
}

/// Injects the My Profile dark theme (matches React ITSProfile component,
/// mirrored from server.py `_UI_CSS`) into the portal page as an idempotent
/// `<style id="ssa-theme">`. Purely cosmetic — structural widgets (app bar,
/// progress bar, Material fields, bottom bar) are added by the ACEsi server's
/// ui_fix script when it is running; this keeps pages themed when it is not.
String buildThemeCssScript() {
  return r'''
(function() {
  if (window.__ssaThemeActive) return;
  window.__ssaThemeActive = true;

  var CSS = 'html,body{background:#0F172A!important;color:#F8FAFC!important}'
    + 'input{background:#1E2635!important;color:#F8FAFC!important;border:none!important;border-radius:8px!important;padding:10px 12px!important;font-size:14px!important}'
    + 'select{background:#1E2635!important;color:#F8FAFC!important;border:none!important;border-radius:8px!important;padding:10px 12px!important;font-size:14px!important}'
    + 'textarea{background:#1E2635!important;color:#F8FAFC!important;border:none!important;border-radius:8px!important;padding:10px 12px!important;font-size:14px!important}'
    + 'input[type=submit]{background:#7C3AED!important}'
    + 'input[type=button]{background:transparent!important}'
    + 'td{color:#9CA3AF!important;background:transparent!important}'
    + 'font{color:#9CA3AF!important}'
    + 'b,strong{color:#F8FAFC!important}'
    + 'label{color:#9CA3AF!important}'
    + 'h1,h2,h3{color:#F8FAFC!important}'
    + 'a{color:#7C3AED!important}'
    + 'option{background:#1E2635!important;color:#F8FAFC!important}'
    + '#ssa-appbar{position:fixed;top:0;left:0;right:0;z-index:2147483000;height:56px;display:flex;align-items:center;justify-content:center;background:#0F172A}'
    + '#ssa-appbar span{color:#F8FAFC;font-size:18px;font-weight:500}'
    + '#ssa-prog{position:fixed;top:56px;left:0;right:0;z-index:2147483000;background:#0F172A;padding:16px 24px 6px 24px}'
    + '#ssa-prog .bar{display:flex;margin-bottom:8px}'
    + '#ssa-prog .seg{height:4px;border-radius:2px;flex:1;margin:0 2px;background:#1E2635}'
    + '#ssa-prog .seg.on{background:#7C3AED}'
    + '#ssa-prog .step{text-align:right;color:#6B7280;font-size:12px;padding-bottom:6px}'
    + '#ssa-star{position:fixed;right:16px;bottom:110px;z-index:2147482999;width:48px;height:48px;border-radius:50%;background:#1E2635;border:1px solid #2A3447;display:flex;align-items:center;justify-content:center;font-size:22px;color:#FFC107;box-shadow:0 0 12px rgba(255,193,7,.4)}';

  function inject() {
    var s = document.getElementById('ssa-theme');
    if (!s) {
      s = document.createElement('style');
      s.id = 'ssa-theme';
      document.head.appendChild(s);
    }
    if (s.textContent !== CSS) s.textContent = CSS;
  }

  inject();

  var observer = new MutationObserver(function() {
    if (!document.getElementById('ssa-theme')) inject();
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  setInterval(function() {
    if (!document.getElementById('ssa-theme')) inject();
  }, 500);

  console.log('[SSA] theme CSS injected (resilient)');
})();
''';
}

String buildBlanketAutofillSuppressScript() {
  return '''
(function() {
  var inputs = document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image])');
  for (var i = 0; i < inputs.length; i++) {
    inputs[i].setAttribute('autocomplete', 'off');
    inputs[i].setAttribute('autocorrect', 'off');
    inputs[i].setAttribute('autocapitalize', 'off');
    inputs[i].setAttribute('spellcheck', 'false');
  }
  console.log('Autofill suppressed on ' + inputs.length + ' fields');
})();
''';
}

String buildSecurityPatch() {
  return '''
(function() {
  // APEX security: ensure hidden CSRF/token fields are preserved
  // and not accidentally removed or modified by our other patches.
  var forms = document.querySelectorAll('form');
  for (var i = 0; i < forms.length; i++) {
    var f = forms[i];
    var hiddens = f.querySelectorAll('input[type="hidden"]');
    for (var j = 0; j < hiddens.length; j++) {
      // Ensure hidden fields stay hidden but are NOT disabled
      hiddens[j].style.display = 'none';
      hiddens[j].removeAttribute('disabled');
    }
  }

  // Do NOT override apex.page.submit — doing so silently swallows errors
  // and prevents the form from submitting if the original throws.

  console.log('Security patch applied');
})();
''';
}

String buildLabelPatch() {
  return '''
(function() {
  // Fix label-for associations for APEX form fields
  var labels = document.querySelectorAll('label');
  for (var i = 0; i < labels.length; i++) {
    var lbl = labels[i];
    var forId = lbl.getAttribute('for');
    if (forId) {
      var target = document.getElementById(forId);
      if (!target) {
        // Try matching by name
        var name = forId.replace(/_display\$/, '').replace(/_value\$/, '');
        var field = document.querySelector('[name="' + name + '"]');
        if (field) {
          lbl.setAttribute('for', field.id || field.name);
        }
      }
    }
  }
  console.log('Label patch applied');
})();
''';
}

String buildAutocompletePatch() {
  return '''
(function() {
  // Disable autocomplete on APEX LOV fields and text inputs
  var fields = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"]');
  for (var i = 0; i < fields.length; i++) {
    var f = fields[i];
    f.setAttribute('autocomplete', 'off');
    // Remove APEX-generated readonly from LOV fields if they block typing
    if (f.readOnly && f.name && f.name.indexOf('lov') === -1) {
      // keep readonly for non-LOV fields
    }
  }
  console.log('Autocomplete patch applied');
})();
''';
}

String buildSelectAutocompletePatch() {
  return '''
(function() {
  // Fix Select2/APEX LOV dropdowns — make them usable in WebView
  var selects = document.querySelectorAll('select');
  for (var i = 0; i < selects.length; i++) {
    var s = selects[i];
    s.removeAttribute('disabled');
    s.removeAttribute('readonly');
    s.setAttribute('autocomplete', 'off');
  }

  // Ensure LOV popups open in-page (not popup windows)
  if (window.open) {
    var origOpen = window.open;
    window.open = function(url, name, features) {
      if (url && url.indexOf('lov') !== -1) {
        // Try to load LOV in current page instead of popup
        console.log('LOV popup blocked, URL: ' + url);
        return null;
      }
      return origOpen.call(window, url, name, features);
    };
  }

  console.log('Select autocomplete patch applied');
})();
''';
}

String buildProvinceDisambiguationPatch() {
  return '''
(function() {
  // ITS portals have two province fields — street address vs postal address
  // Ensure the correct one gets filled by auto-fill
  var streetProv = document.querySelector('select[name="OAPSTREETADDR4"]');
  var postalProv = document.querySelector('select[name="OAPPOSTALADDR4"]');
  // Remove ambiguity — mark them clearly
  if (streetProv) streetProv.setAttribute('data-province-type', 'street');
  if (postalProv) postalProv.setAttribute('data-province-type', 'postal');
  console.log('Province disambiguation patch applied');
})();
''';
}

String buildFocusPatch() {
  return '''
(function() {
  // Fix focus issues on Android WebView — ensure keyboard appears on tap
  var inputs = document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image])');
  for (var i = 0; i < inputs.length; i++) {
    var f = inputs[i];
    f.removeAttribute('readonly');
    // Add touch handler to force focus
    f.addEventListener('touchstart', function() {
      this.focus();
    }, { passive: true });
  }

  // Also fix select elements — ensure they respond to touch
  var selects = document.querySelectorAll('select');
  for (var i = 0; i < selects.length; i++) {
    selects[i].removeAttribute('disabled');
  }

  console.log('Focus patch applied to ' + inputs.length + ' fields');
})();
''';
}

String buildInputmodePatch() {
  return '''
(function() {
  // Set correct inputmode for mobile keyboards
  var inputs = document.querySelectorAll('input');
  for (var i = 0; i < inputs.length; i++) {
    var f = inputs[i];
    var name = (f.name || '').toLowerCase();
    // Phone fields
    if (name.indexOf('phone') !== -1 || name.indexOf('tel') !== -1 || name.indexOf('cell') !== -1) {
      f.setAttribute('inputmode', 'tel');
    }
    // Numeric fields (ID number, postal code)
    if (name.indexOf('id') !== -1 || name.indexOf('pcode') !== -1 || name.indexOf('code') !== -1) {
      f.setAttribute('inputmode', 'numeric');
    }
    // Email fields
    if (name.indexOf('email') !== -1) {
      f.setAttribute('inputmode', 'email');
    }
  }
  console.log('Inputmode patch applied');
})();
''';
}

String buildFormLabelPatch() {
  return '''
(function() {
  // Additional form label fixes — ensure labels are visible and correctly positioned
  var containers = document.querySelectorAll('.t-Form-fieldContainer, .t-Form-inputContainer');
  for (var i = 0; i < containers.length; i++) {
    var c = containers[i];
    var lbl = c.querySelector('label');
    var input = c.querySelector('input, select, textarea');
    if (lbl && input && !lbl.getAttribute('for')) {
      lbl.setAttribute('for', input.id || input.name);
    }
  }

  // Ensure required-field markers are visible
  var requireds = document.querySelectorAll('.u-TF-item--required, [required]');
  for (var i = 0; i < requireds.length; i++) {
    requireds[i].style.display = '';
  }

  console.log('Form label patch applied');
})();
''';
}

String buildPostalCodePickerScript(String profileJson) {
  return '''
(function() {
  var profile = $profileJson;
  var profilePostal = (profile.address && profile.address.postalCode) || '';

  // South African postal codes → location (extend as needed)
  var db = {
    // ── Pretoria / Tshwane ──
    '0001': 'Arcadia, Pretoria', '0002': 'Arcadia, Pretoria',
    '0006': 'Groenkloof, Pretoria', '0007': 'Arcadia, Pretoria',
    '0008': 'Hatfield, Pretoria', '0011': 'Hatfield, Pretoria',
    '0014': 'Menlyn, Pretoria', '0017': 'Centurion',
    '0018': 'Wierda Park, Centurion', '0028': 'Lynnwood, Pretoria',
    '0030': 'Menlyn, Pretoria', '0035': 'Lynnwood Manor, Pretoria',
    '0037': 'Waterkloof, Pretoria', '0044': 'Brooklyn, Pretoria',
    '0066': 'Atteridgeville', '0072': 'Mamelodi, Pretoria',
    '0081': 'Hatfield, Pretoria', '0084': 'Hatfield, Pretoria',
    '0086': 'Menlo Park, Pretoria', '0157': 'Wierda Park, Centurion',
    '0169': 'Clubview, Centurion', '0170': 'Lyttelton, Centurion',
    '0181': 'Wierda Park, Centurion', '0200': 'Pretoria',
    '0204': 'Pretoria West', '0229': 'Silverton, Pretoria',
    '0232': 'Silverton, Pretoria', '0257': 'Akasia, Pretoria',
    '0258': 'Akasia, Pretoria', '0294': 'Sunnyside, Pretoria',
    // ── Johannesburg / Gauteng ──
    '2000': 'Johannesburg', '2001': 'Johannesburg',
    '2007': 'Auckland Park, JHB', '2016': 'Crosby, JHB',
    '2017': 'Marshalltown, JHB', '2021': 'Bez Valley, JHB',
    '2024': 'Observatory, JHB', '2031': 'Illovo, JHB',
    '2036': 'Bryanston, JHB', '2041': 'Constantia, JHB',
    '2049': 'Alexandra, JHB', '2060': 'Craighall Park, JHB',
    '2061': 'Linden, JHB', '2062': 'Emmarentia, JHB',
    '2065': 'Westdene, JHB', '2067': 'Greymont, JHB',
    '2068': 'Blairgowrie, JHB', '2069': 'Ferndale, JHB',
    '2070': 'Ferndale, Randburg', '2072': 'Cresta, JHB',
    '2074': 'Blackheath, JHB', '2076': 'Northcliff, JHB',
    '2077': 'Constantia Kloof, JHB', '2078': 'Weltevredenpark',
    '2090': 'Norwood, JHB', '2094': 'Parktown, JHB',
    '2121': 'Auckland Park, JHB', '2148': 'Booysens, JHB',
    '2191': 'Linden, JHB', '2196': 'Linden, JHB',
    // ── Cape Town / Western Cape ──
    '7000': 'Cape Town', '7005': 'Maitland, Cape Town',
    '7100': 'Eerste River', '7130': 'Somerset West',
    '7140': 'Strand', '7200': 'Goodwood, Cape Town',
    '7400': 'Epping, Cape Town', '7441': 'Milnerton, Cape Town',
    '7449': 'Sunningdale, Cape Town', '7450': 'Pinelands',
    '7460': 'Elsies River', '7500': 'Parow, Cape Town',
    '7505': 'Bellville', '7535': 'Bellville',
    '7540': 'Bellville', '7545': 'Durbanville',
    '7560': 'Brackenfell', '7570': 'Kraaifontein',
    '7600': 'Stellenbosch', '7646': 'Paarl',
    '7655': 'Worcester', '7700': 'Claremont, Cape Town',
    '7725': 'Claremont, Cape Town', '7735': 'Constantia, Cape Town',
    '7764': 'Khayelitsha', '7779': 'Philippi',
    '7785': 'Mitchells Plain', '7790': 'Mitchells Plain',
    '7800': 'Constantia, Cape Town', '7806': 'Bergvliet',
    '7809': 'Plumstead', '7813': 'Tokai',
    '7925': 'Cape Town', '7945': 'Tokai, Cape Town',
    '7975': 'Fish Hoek', '7980': 'Simons Town',
    // ── Durban / KZN ──
    '3000': 'Durban', '3001': 'Durban',
    '3010': 'Berea, Durban', '3025': 'Overport, Durban',
    '3039': 'Durban North', '3040': 'Durban North',
    '3070': 'Queensburgh', '3079': 'Westville',
    '3100': 'Pietermaritzburg', '3201': 'Pietermaritzburg',
    '3245': 'Howick', '3300': 'Ladysmith',
    '3400': 'Newcastle', '3500': 'Empangeni',
    '3610': 'Mtubatuba', '3650': 'Richards Bay',
    '3800': 'Greytown', '3860': 'Eshowe',
    '3920': 'Richards Bay', '3940': 'Richards Bay',
    // ── Eastern Cape ──
    '5200': 'East London', '5201': 'East London',
    '5500': 'Umtata', '6001': 'Port Elizabeth',
    '6045': 'Newton Park, PE', '6055': 'Newton Park, PE',
    '6059': 'Walmer, PE', '6139': 'Jeffreys Bay',
    '6170': 'Uitenhage', '6229': 'Despatch',
    '6300': 'Humansdorp', '6335': 'Jeffreys Bay',
    '6470': 'Oudtshoorn', '6500': 'George',
    '6529': 'George', '6570': 'Knysna', '6600': 'Plettenberg Bay',
    // ── Free State ──
    '9300': 'Bloemfontein', '9301': 'Bloemfontein',
    '9310': 'Bloemfontein', '9350': 'Bloemfontein',
    '9700': 'Bethlehem', '9800': 'Welkom',
    '9900': 'Kroonstad',
    // ── Limpopo (UNIVEN) ──
    '0699': 'Polokwane', '0700': 'Polokwane',
    '0710': 'Polokwane', '0727': 'Sovenga',
    '0880': 'Phalaborwa', '0900': 'Musina',
    '0950': 'Thohoyandou', '0951': 'Thohoyandou',
    '0952': 'Thohoyandou', '0953': 'Thohoyandou',
    '0954': 'Thohoyandou', '0955': 'Thohoyandou',
    '0956': 'Thohoyandou', '0957': 'Thohoyandou',
    '0958': 'Thohoyandou', '0959': 'Thohoyandou',
    '0960': 'Sibasa', '0961': 'Sibasa',
    '0962': 'Sibasa', '0963': 'Sibasa',
    '0970': 'Mutale', '0971': 'Mutale',
    // ── Mpumalanga ──
    '1200': 'Nelspruit', '1201': 'Nelspruit',
    '1240': 'White River', '1245': 'Hazyview',
    '1270': 'Ermelo', '1300': 'Standerton',
    '1350': 'Secunda', '1370': 'Middelburg',
    '1400': 'Witbank', '1500': 'KwaMhlanga',
    // ── North West ──
    '2500': 'Rustenburg', '2520': 'Rustenburg',
    '2531': 'Potchefstroom', '2550': 'Stilfontein',
    '2560': 'Klerksdorp', '2600': 'Vereeniging',
    '2614': 'Vanderbijlpark', '2700': 'Brits',
    '2800': 'Mafikeng', '2900': 'Vryburg',
    // ── Northern Cape ──
    '8300': 'Kimberley', '8500': 'Upington',
    '8600': 'Springbok', '8700': 'Calvinia',
    '8800': 'Kuruman'
  };

  // Sorted list for fast lookup
  var list = [];
  for (var k in db) list.push({ c: k, l: db[k] });
  list.sort(function(a, b) { return a.c.localeCompare(b.c); });

  function inject(targetId) {
    var v = document.getElementById(targetId);
    if (!v) return false;
    if (document.getElementById('ssa-pc-' + targetId)) return true; // already injected

    // Hide original (and APEX _display sibling if present)
    v.style.display = 'none';
    v.removeAttribute('readonly'); v.removeAttribute('disabled');
    var d = document.getElementById(targetId + '_display');
    if (d) { d.style.display = 'none'; d.removeAttribute('readonly'); d.removeAttribute('disabled'); }

    // Wrapper
    var w = document.createElement('div');
    w.id = 'ssa-pc-' + targetId;
    w.style.cssText = 'position:relative;display:block;margin:8px 0;'
      + 'font-family:Arial,sans-serif;z-index:2147483647;';

    // Search input
    var input = document.createElement('input');
    input.type = 'text';
    input.placeholder = '🔍 Type code or area (e.g. 0001 or Arcadia)...';
    input.autocomplete = 'off';
    input.inputMode = 'numeric';
    input.style.cssText = 'width:100%;padding:12px 16px;font-size:16px;'
      + 'border:2px solid #7C3AED;border-radius:8px;box-sizing:border-box;'
      + 'outline:none;background:#fff;color:#0F1624;';

    var row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;gap:6px;';

    var closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.textContent = '✕';
    closeBtn.title = 'Close postal picker';
    closeBtn.style.cssText = 'background:none;border:none;font-size:18px;'
      + 'color:#888;cursor:pointer;padding:6px 10px;flex:0 0 auto;';
    closeBtn.addEventListener('click', function() {
      closeDrop();
      input.blur();
    });
    row.appendChild(input);
    row.appendChild(closeBtn);
    w.appendChild(row);

    // Dropdown
    var drop = document.createElement('div');
    drop.style.cssText = 'position:absolute;top:100%;left:0;right:0;'
      + 'max-height:280px;overflow-y:auto;background:#fff;'
      + 'border:2px solid #7C3AED;border-top:none;'
      + 'border-radius:0 0 8px 8px;box-shadow:0 4px 14px rgba(0,0,0,0.15);'
      + 'z-index:2147483647;display:none;';
    w.appendChild(drop);

    // Full-screen transparent backdrop: tapping anywhere outside the picker
    // closes the dropdown — a reliable "exit" on touch devices.
    var backdrop = document.createElement('div');
    backdrop.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;'
      + 'z-index:2147483646;display:none;background:transparent;';
    backdrop.addEventListener('click', function() { closeDrop(); input.blur(); });
    document.body.appendChild(backdrop);

    function closeDrop() {
      drop.style.display = 'none';
      backdrop.style.display = 'none';
    }

    document.addEventListener('click', function(e) {
      if (w.contains(e.target)) return;
      closeDrop();
    });

    function show(q) {
      q = (q || '').toLowerCase().trim();
      drop.innerHTML = '';
      var matches = [];
      for (var i = 0; i < list.length && matches.length < 50; i++) {
        var item = list[i];
        if (!q || item.c.indexOf(q) === 0 || item.l.toLowerCase().indexOf(q) !== -1) {
          matches.push(item);
        }
      }
      if (matches.length === 0) {
        var e = document.createElement('div');
        e.textContent = q ? 'No postal codes match "' + q + '"' : 'Start typing to search...';
        e.style.cssText = 'padding:14px 16px;color:#888;font-style:italic;';
        drop.appendChild(e);
      } else {
        matches.forEach(function(item) {
          var row = document.createElement('div');
          row.style.cssText = 'padding:10px 14px;cursor:pointer;'
            + 'border-bottom:1px solid #f0f0f0;'
            + 'display:flex;align-items:center;gap:12px;';
          row.onmouseenter = function() { this.style.background = '#F3F0FF'; };
          row.onmouseleave = function() { this.style.background = '#fff'; };

          var badge = document.createElement('span');
          badge.textContent = item.c;
          badge.style.cssText = 'font-family:monospace;font-size:14px;'
            + 'font-weight:bold;color:#0F1624;background:#F3F0FF;'
            + 'padding:4px 10px;border-radius:4px;min-width:64px;text-align:center;';
          row.appendChild(badge);

          var loc = document.createElement('span');
          loc.textContent = item.l;
          loc.style.cssText = 'font-size:14px;color:#555;flex:1;';
          row.appendChild(loc);

          row.onclick = function() { pick(item.c, item.l); };
          drop.appendChild(row);
        });
      }
      drop.style.display = 'block';
      backdrop.style.display = 'block';
    }

    function pick(code, loc) {
      var desc = document.getElementById(targetId + '_desc');
      input.value = code + ' — ' + loc;
      v.value = code;
      v.removeAttribute('readonly'); v.removeAttribute('disabled');

      if (d) {
        d.value = code + ' — ' + loc;
        d.removeAttribute('readonly'); d.removeAttribute('disabled');
      }

      // ITS stores the LOV code in the main field and its description in the
      // *_desc sibling; leaving *_desc empty makes ITS reject the code.
      if (desc) {
        desc.value = code;
        desc.removeAttribute('readonly'); desc.removeAttribute('disabled');
      }

      // ITS / APEX expects all of these events to fire validation
      ['input','change','blur','focus'].forEach(function(evt) {
        v.dispatchEvent(new Event(evt, { bubbles: true }));
        if (d) d.dispatchEvent(new Event(evt, { bubbles: true }));
        if (desc) desc.dispatchEvent(new Event(evt, { bubbles: true }));
      });

      // jQuery / Select2 glue
      if (typeof jQuery !== 'undefined') {
        try {
          jQuery(v).trigger('change');
          if (d) jQuery(d).trigger('change');
          if (desc) jQuery(desc).trigger('change');
          jQuery(v).trigger('select2:select');
          if (d) jQuery(d).trigger('select2:select');
        } catch (e) {}
      }

      closeDrop();
      input.blur();
      console.log('✅ Postal code selected:', code, '→', loc);

      // Trigger APEX event chain if available
      if (window.apex && window.apex.event) {
        try { window.apex.event.trigger(v, 'change'); } catch (e) {}
      }

      // Visual feedback
      input.style.borderColor = '#10B981';
      setTimeout(function() { input.style.borderColor = '#7C3AED'; }, 1200);
    }

    input.addEventListener('focus', function() { show(input.value); });
    input.addEventListener('input',  function() { show(input.value); });
    input.addEventListener('blur',   function() { setTimeout(function() { closeDrop(); }, 200); });
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        var first = drop.querySelector('div[style*="cursor:pointer"]');
        if (first) first.click();
      } else if (e.key === 'Escape') {
        closeDrop();
        input.blur();
      }
    });

    v.parentNode.insertBefore(w, v.nextSibling);

    // Pre-fill from profile
    if (profilePostal) {
      input.value = profilePostal;
      var hit = null;
      for (var i = 0; i < list.length; i++) if (list[i].c === profilePostal) { hit = list[i]; break; }
      if (hit) pick(hit.c, hit.l);
    }
    return true;
  }

  function tryAll() {
    var ids = [
      'oapStreetAddrPCodeRq', 'oapPostalAddrPCodeRq',
      'OAPSTREETADDRPCODEREQ', 'OAPPOSTALADDRPCODEREQ',
      'OAPSTREETADDRPCODEREQ_DESC', 'OAPPOSTALADDRPCODEREQ_DESC'
    ];
    var n = 0;
    for (var i = 0; i < ids.length; i++) if (inject(ids[i])) n++;
    if (n === 0) setTimeout(tryAll, 600);
    else console.log('✅ Postal code picker injected on ' + n + ' field(s)');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { setTimeout(tryAll, 600); });
  } else {
    setTimeout(tryAll, 600);
  }
})();
''';
}

String buildRemoveOldPostalPickerScript() {
  return r'''
(function() {
  ['oapStreetAddrPCodeRqFld', 'oapPostalAddrPCodeRqFld'].forEach(function(fldId) {
    var fld = document.getElementById(fldId);
    if (!fld || !fld.parentNode) return;
    var parent = fld.parentNode;

    var codeId = fldId.replace('Fld', '');
    var input = document.getElementById(codeId);
    if (input) {
      // Move the hidden value input outside the container so the
      // postal picker script can still find it.
      parent.insertBefore(input, fld.nextSibling);
    }

    parent.removeChild(fld);
    console.log('Removed old picker:', fldId);
  });
})();
''';
}
