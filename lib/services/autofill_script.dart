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

String buildAutofillScript(String profileJson) {
  return _script(profileJson, addFloatingStar: true);
}

String buildAutofillOnlyScript(String profileJson) {
  return _script(profileJson, addFloatingStar: false);
}

String _script(String profileJson, {required bool addFloatingStar}) {
  return '''
(function() {
  // ── 1. Profile data ────────────────────────────────────────────────────
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

  // ── 2. ITS portal exact-name map (P_* Oracle fields) ──────────────────
  // These are the actual INPUT NAME attributes used by ITS/Univen/UL/TUT etc.
  var itsExact = {
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

  // ── 3. Generic fuzzy fieldMap (fallback for non-ITS sites) ────────────
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
    isSACitizen:       ['sa citizen','possession of','valid sa','sa id'],
    homeLanguage:      ['home language','homelanguage','language'],
    populationGroup:   ['population group','ethnicity'],
    raceValue:         ['race'],
    maritalStatus:     ['marital status','maritalstatus'],
    maritalYesNo:      ['married','are you married'],
    disabilityValue:   ['disabled','disability','are you disabled'],
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

  // ── 4. Helpers ─────────────────────────────────────────────────────────
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
    var wlWords = wl.split(/\\s+/);
    var best = null, bestScore = -1;
    for (var i = 0; i < sel.options.length; i++) {
      var opt = sel.options[i];
      if (isPlaceholder(opt.text)) continue;
      var tl = opt.text.toLowerCase().trim();
      var vl = opt.value.toLowerCase().trim();
      var tlWords = tl.split(/\\s+/);
      var vlWords = vl.split(/\\s+/);
      var score = -1;
      // 100: exact text/value equals want
      if (tl === wl || vl === wl) score = 100;
      // 60: whole-word match (want word == option word) — avoids "female" matching "male"
      if (score < 60) {
        for (var w = 0; w < wlWords.length; w++) {
          var word = wlWords[w];
          if (word.length < 2) continue;
          var hit = false;
          for (var o = 0; o < tlWords.length; o++) { if (tlWords[o] === word) { hit = true; break; } }
          if (!hit) for (var v = 0; v < vlWords.length; v++) { if (vlWords[v] === word) { hit = true; break; } }
          if (hit) { score = 60; break; }
        }
      }
      // 60: prefix match (handles "africa" <-> "african", value prefix)
      if (score < 60) {
        if (tl.indexOf(wl) === 0 || vl.indexOf(wl) === 0 || wl.indexOf(tl) === 0 || wl.indexOf(vl) === 0) score = 60;
      }
      // 30: substring containment (lowest priority, avoids female/male false tie)
      if (score < 30) {
        if (tl.indexOf(wl) !== -1 || vl.indexOf(wl) !== -1) score = 30;
      }
      if (score > bestScore) { bestScore = score; best = opt; }
    }
    return bestScore >= 10 ? best : null;
  }

  // Plain value setter + minimal events — ITS is plain HTML, no framework needed.
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
        try { jQuery(el).trigger('select2:select'); } catch(e) {}
        try { if (jQuery(el).data('select2')) jQuery(el).val(opt.value).trigger('change'); } catch(e) {}
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
    // Some fields (e.g. oapCitzCode) are read-only by default — clear that.
    try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch (e) {}
    // Only force visibility for non-hidden fields. Hidden backing/value fields
    // (common on LOV-style forms) must stay hidden, otherwise a duplicate
    // visible row appears next to the visible display field.
    if (el.type !== 'hidden') {
      try { el.style.display = 'block'; el.style.visibility = 'visible'; } catch (e) {}
    }
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
      for (var d = 0; d < 6 && p; d++) {
        if (p.tagName === 'TD' || p.tagName === 'TH' || p.tagName === 'LABEL') {
          parts.push(p.textContent);
        }
        if (p.tagName === 'TR') {
          var cells = p.cells;
          if (cells && cells.length >= 2) parts.push(cells[0].textContent);
          // Radio/checkbox questions often sit in the PREVIOUS row, not an ancestor.
          if (el.type === 'radio' || el.type === 'checkbox') {
            var prev = p.previousElementSibling;
            for (var pr = 0; pr < 2 && prev; pr++) {
              if (prev.textContent) parts.push(prev.textContent);
              prev = prev.previousElementSibling;
            }
          }
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

  // ── 5. Main autofill ───────────────────────────────────────────────────
  function doAutofill() {
    console.log('🔍 Autofill started');
    var fields = {
      oapFirstNames: profile.personal.firstName,
      oapSurname: profile.personal.lastName,
      oapBirthdate: profile.personal.dateOfBirth,
      itsEmail: profile.contact.email,
      verifyEmail: profile.contact.email,
      oapWorkPhone: profile.contact.workPhone,
      oapHomePhone: profile.contact.phone,
      oapIntCell: profile.contact.phone,
      oapStreetAddr1: profile.address.address,
      oapStreetAddr4: profile.address.province,
      oapStreetAddrPCodeRq: profile.address.postalCode,
      oapPostalAddrPCodeRq: profile.address.postalCode,
    };

    var filled = 0;
    for (var name in fields) {
      var value = fields[name];
      var el = document.getElementById(name);
      if (el && value) {
        el.value = value;
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('input', { bubbles: true }));
        filled++;
        console.log('✅ Filled ' + name + ': ' + value);
      }
    }

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
    }
    if (idEl && idEl.value) {
      idEl.dispatchEvent(new Event('blur', { bubbles: true }));
      console.log('✅ Blur fired on ID number field');
    }

    // Auto-set citizenship code to R.S.A when a valid SA ID is present.
    ssaAutoCitizenship();

    var msg = filled > 0 ? '✅ Filled ' + filled + ' fields' : 'No fields found';
    console.log(msg);

    showToast(
      filled > 0
        ? '✅ Filled ' + filled + ' field' + (filled !== 1 ? 's' : '') + '!'
        : 'No fields matched. Try scrolling to the next section.',
      filled > 0 ? '#10B981' : '#EF4444'
    );

    try { AutofillResult.postMessage(JSON.stringify({ filled: filled, total: filled })); } catch (e) {}
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
    };
    document.body.appendChild(star);
    console.log('✅ Star injected and connected to doAutofill');
  })();
  ''' : ''}


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
    return u.replace(/(gen\.gw1pkg\.gw1)view([^a-zA-Z0-9]|\$)/g, '\$1proc\$2');
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
        redirect: 'follow',
        credentials: 'same-origin'
      }).then(function(res) {
        return res.text().then(function(html) {
          console.log('[navfix] fetch POST done: HTTP ' + res.status + ' len ' + html.length);
          diag('POST back HTTP ' + res.status + ' (' + html.length + ' chars)');
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
        try { origSubmit.call(f); } catch (e2) {}
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
      if (!submitViaFetch(f)) { try { origSubmit.call(f); } catch (err) {} }
    }
  }, true);

  // Direct form.submit() calls fire NO 'submit' event — patch the prototype
  // so the POST is hijacked (and the action corrected) before it goes out.
  var origSubmit = HTMLFormElement.prototype.submit;
  if (origSubmit && !origSubmit.__ssaPatched) {
    var submitWrapper = function() {
      var f = this;
      fixAction(f, true);
      if (isItsPostForm(f) && submitViaFetch(f)) return;
      return origSubmit.apply(this, arguments);
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
    w.style.cssText = 'position:relative;display:block;margin:8px 0;font-family:Arial,sans-serif;';

    // Search input
    var input = document.createElement('input');
    input.type = 'text';
    input.placeholder = '🔍 Type code or area (e.g. 0001 or Arcadia)...';
    input.autocomplete = 'off';
    input.inputMode = 'numeric';
    input.style.cssText = 'width:100%;padding:12px 16px;font-size:16px;'
      + 'border:2px solid #7C3AED;border-radius:8px;box-sizing:border-box;'
      + 'outline:none;background:#fff;color:#0F1624;';
    w.appendChild(input);

    // Dropdown
    var drop = document.createElement('div');
    drop.style.cssText = 'position:absolute;top:100%;left:0;right:0;'
      + 'max-height:280px;overflow-y:auto;background:#fff;'
      + 'border:2px solid #7C3AED;border-top:none;'
      + 'border-radius:0 0 8px 8px;box-shadow:0 4px 14px rgba(0,0,0,0.15);'
      + 'z-index:9999;display:none;';
    w.appendChild(drop);

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
    }

    function pick(code, loc) {
      input.value = code + ' — ' + loc;
      v.value = code;
      v.removeAttribute('readonly'); v.removeAttribute('disabled');

      if (d) {
        d.value = code + ' — ' + loc;
        d.removeAttribute('readonly'); d.removeAttribute('disabled');
      }

      // ITS / APEX expects all of these events to fire validation
      ['input','change','blur','focus'].forEach(function(evt) {
        v.dispatchEvent(new Event(evt, { bubbles: true }));
        if (d) d.dispatchEvent(new Event(evt, { bubbles: true }));
      });

      // jQuery / Select2 glue
      if (typeof jQuery !== 'undefined') {
        try {
          jQuery(v).trigger('change');
          if (d) jQuery(d).trigger('change');
          jQuery(v).trigger('select2:select');
          if (d) jQuery(d).trigger('select2:select');
        } catch (e) {}
      }

      drop.style.display = 'none';
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
    input.addEventListener('blur',   function() { setTimeout(function() { drop.style.display = 'none'; }, 200); });
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        var first = drop.querySelector('div[style*="cursor:pointer"]');
        if (first) first.click();
      } else if (e.key === 'Escape') {
        drop.style.display = 'none';
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

