// ─────────────────────────────────────────────────────────────────────────────
// autofill_script.dart  –  StudentSyncSA Star Auto-Fill
//
// Built specifically for ITS (Oracle PL/SQL) university portals used by
// UNIVEN, UL, TUT, NWU and others. These portals use P_* field names and
// plain HTML — no React, no Angular, no framework events needed.
// Falls back to generic matching for other university sites.
// ─────────────────────────────────────────────────────────────────────────────

String buildAutofillScript(String profileJson) {
  return _buildFullScript(profileJson, createStar: true);
}

String buildAutofillOnlyScript(String profileJson) {
  return _buildFullScript(profileJson, createStar: false);
}

String buildCompleteAutofillScript(String profileJson, {bool createStar = true}) {
  return buildAutofillScript(profileJson);
}

String _buildFullScript(String profileJson, {required bool createStar}) {
  final starBlock = createStar ? r'''
  function createStar() {
    if (document.getElementById('ssa-star')) return;
    var star = document.createElement('div');
    star.id = 'ssa-star';
    star.innerHTML = '★';
    star.style.cssText = 'position:fixed;bottom:24px;right:24px;width:60px;height:60px;background:#0F1624;border-radius:50%;z-index:999999;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(124,58,237,0.5);border:2px solid #7C3AED;color:#FFD700;font-size:40px;font-family:Arial,sans-serif;transition:transform 0.2s;';
    star.onclick = doAutofill;
    document.body.appendChild(star);
  }
  function tryCreate() { if (document.body) { createStar(); } else { setTimeout(tryCreate, 500); } }
  tryCreate();
''' : '';

  return '''
(function() {
  var profile = $profileJson;

  var fieldMap = {
    'title':             ['title','salutation'],
    'firstName':         ['firstname','first name','fname','given name','givenname'],
    'lastName':          ['lastname','last name','lname','surname','family name','familyname'],
    'initials':          ['initials'],
    'gender':            ['gender','sex'],
    'idNumber':          ['idnumber','id number','identity number','national id','sa id','passport number','rsaid'],
    'dateOfBirth':       ['dateofbirth','date of birth','dob','birthdate','birth date','birthday'],
    'email':             ['email','e-mail','emailaddress','email address'],
    'phone':             ['phone','telephone','tel','cell','cellphone','mobile','mobile number','contact no','phone number'],
    'workPhone':         ['workphone','work phone','telephone work','tel work'],
    'address':           ['address','street','physical address','residential address'],
    'addressLine2':      ['address2','address line2','suburb','town','city'],
    'province':          ['province','state','region'],
    'postalCode':        ['postalcode','postal code','postcode','zip','zipcode','code'],
    'nationality':       ['nationality','citizenship','citizen','country','sa citizen','south african'],
    'homeLanguage':      ['homelanguage','home language','language','first language'],
    'populationGroup':   ['populationgroup','population group','race','ethnicity'],
    'maritalStatus':     ['maritalstatus','marital status'],
    'schoolName':        ['school','schoolname','school name','highschool','high school','institution'],
    'currentGrade':      ['grade','current grade','grade12','matric'],
    'matricYear':        ['matricyear','year of matric','examination year'],
    'matricType':        ['matrictype','matric type','exam type','examination type'],
    'examinationNumber': ['examinationnumber','exam number','candidate number'],
    'applicationLevel':  ['applicationlevel','level of study','study level','application type'],
    'faculty':           ['faculty','faculty choice'],
    'programme':         ['programme','course','program','qualification','course choice','study programme'],
    'academicYear':      ['academicyear','academic year','year of study','study year'],
    'studyMode':         ['studymode','study mode','mode of study','attendance mode'],
    'nextOfKinName':     ['nextofkin name','nextofkin','guardian name','parent name','parentguardian'],
    'nextOfKinPhone':    ['nextofkin phone','guardian phone','parent phone','emergency contact'],
    'nextOfKinEmail':    ['nextofkin email','guardian email','parent email'],
  };

  function getVal(path) {
    var parts = path.split('.');
    var obj = profile;
    for (var i = 0; i < parts.length; i++) {
      if (obj == null || typeof obj !== 'object') return '';
      obj = obj[parts[i]];
    }
    return (obj != null && obj !== undefined) ? String(obj) : '';
  }

  function fmtDate(iso) {
    if (!iso || iso.length < 10) return iso;
    var months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    var p = iso.split('T')[0].split('-');
    var m = parseInt(p[1], 10) - 1;
    return (m >= 0 && m < 12) ? p[2] + '-' + months[m] + '-' + p[0] : iso;
  }

  var vs = {
    'title':             getVal('personal.title'),
    'firstName':         getVal('personal.firstName'),
    'lastName':          getVal('personal.lastName'),
    'initials':          getVal('personal.initials'),
    'gender':            getVal('personal.gender'),
    'idNumber':          getVal('personal.idNumber'),
    'dateOfBirth':       fmtDate(getVal('personal.dateOfBirth')),
    'email':             getVal('contact.email'),
    'phone':             getVal('contact.phone'),
    'workPhone':         getVal('contact.workPhone'),
    'address':           getVal('address.address'),
    'addressLine2':      getVal('address.addressLine2'),
    'province':          getVal('address.province'),
    'postalCode':        getVal('address.postalCode'),
    'nationality':       getVal('demographic.nationality'),
    'homeLanguage':      getVal('demographic.homeLanguage'),
    'populationGroup':   getVal('demographic.populationGroup'),
    'maritalStatus':     getVal('demographic.maritalStatus'),
    'schoolName':        getVal('school.schoolName'),
    'currentGrade':      getVal('school.currentGrade'),
    'matricYear':        getVal('results.matricYear'),
    'matricType':        getVal('results.matricType'),
    'examinationNumber': getVal('results.examinationNumber'),
    'applicationLevel':  getVal('results.applicationLevel'),
    'faculty':           getVal('qualification.choices.0.faculty'),
    'programme':         getVal('qualification.choices.0.programme'),
    'academicYear':      getVal('qualification.academicYear'),
    'studyMode':         getVal('qualification.studyMode'),
    'nextOfKinName':     getVal('nextOfKin.name'),
    'nextOfKinPhone':    getVal('nextOfKin.mobilePhone'),
    'nextOfKinEmail':    getVal('nextOfKin.email'),
  };

  // ── Toast ───────────────────────────────────────────────────────────────
  function showToast(msg, color) {
    var old = document.getElementById('ssa-toast');
    if (old) old.remove();
    var t = document.createElement('div');
    t.id = 'ssa-toast';
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:100px;right:24px;padding:12px 20px;background:' + (color||'#10B981') + ';color:#fff;border-radius:10px;z-index:9999999;font-family:Arial,sans-serif;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,0.3);transition:opacity 0.4s;';
    document.body.appendChild(t);
    setTimeout(function() { t.style.opacity = '0'; setTimeout(function() { if(t.parentNode) t.remove(); }, 400); }, 2800);
  }

  // ── Helper functions for uniform matching ──────────────────────────────
  function cleanText(text) {
    if (!text) return '';
    return text.toString()
               .replace(/\\u00a0/g, ' ') // replace non-breaking spaces
               .replace(/\\s+/g, ' ')    // collapse duplicate spaces
               .toLowerCase()
               .trim();
  }

  function isPlaceholder(text) {
    var t = cleanText(text);
    return t === '' || t === 'select' || t === 'choose' || t === 'please select'
      || t.indexOf('select') === 0 || t.indexOf('choose') === 0 || t.indexOf('--') !== -1;
  }

  function isYes(text) {
    var t = cleanText(text);
    return t === 'yes' || t === 'y' || t === 'true' || t === '1'
      || t === 'sa citizen' || t === 'south african' || t === 'rsa';
  }

  function isNo(text) {
    var t = cleanText(text);
    return t === 'no' || t === 'n' || t === 'false' || t === '0' || t === 'other';
  }

  // Recursive search to penetrate any IFRAMEs / FRAMEs in University portals
  function getElementsFromAllFrames(selector) {
    var elements = [];
    function search(doc) {
      if (!doc) return;
      try {
        var found = doc.querySelectorAll(selector);
        for (var i = 0; i < found.length; i++) {
          elements.push(found[i]);
        }
      } catch (e) {}
      try {
        var frames = doc.querySelectorAll('iframe, frame');
        for (var j = 0; j < frames.length; j++) {
          try {
            var fDoc = frames[j].contentDocument || frames[j].contentWindow.document;
            search(fDoc);
          } catch (e) {}
        }
      } catch (e) {}
    }
    search(document);
    return elements;
  }

  // ── Option matcher for dropdowns ─────────────────────────────────────────
  function findOption(sel, rawVal) {
    if (!rawVal) return null;
    var vl = cleanText(rawVal);
    var terms = [vl];
    if (vl === 'sa citizen' || vl === 'south african' || vl === 'south africa' || vl === 'sa' || vl === 'rsa') {
      terms = terms.concat(['south african','south africa','sa citizen','rsa']);
    }
    var bestOpt = null, bestScore = -1;
    for (var t = 0; t < terms.length; t++) {
      var tl = terms[t];
      var tWords = tl.split(' ');
      for (var k = 0; k < sel.options.length; k++) {
        var opt = sel.options[k];
        if (isPlaceholder(opt.text)) continue;
        var tt = cleanText(opt.text);
        var vv = cleanText(opt.value);
        var score = -1;
        if (tt === tl || vv === tl)                               score = 100;
        else if (tt.indexOf(tl) === 0 || vv.indexOf(tl) === 0)   score = 50;
        else if (tt.indexOf(tl) !== -1 || vv.indexOf(tl) !== -1) score = 30;
        else if (tl.indexOf(tt) !== -1 && tt.length > 2)         score = 20;
        else {
          for (var w = 0; w < tWords.length; w++) {
            if (tWords[w].length > 2 && (tt.indexOf(tWords[w]) !== -1 || vv.indexOf(tWords[w]) !== -1)) {
              score = 10; break;
            }
          }
        }
        if (score > bestScore) { bestScore = score; bestOpt = opt; }
      }
    }
    return bestScore >= 10 ? bestOpt : null;
  }

  // ── Value setters + Event trigger chain (React, Angular & Legacy aware) ──
  function setNativeValue(el, value) {
    var nativeProto = el.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    var descriptor = Object.getOwnPropertyDescriptor(nativeProto, 'value');
    if (descriptor && descriptor.set) {
      descriptor.set.call(el, value);
    } else {
      el.value = value;
    }
  }

  function dispatchAll(el) {
    el.dispatchEvent(new Event('focus', { bubbles: true }));

    try {
      el.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: el.value }));
    } catch(e) {
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // Standard modern events
    el.dispatchEvent(new Event('change', { bubbles: true }));

    // Legacy inline event trigger (CRITICAL for old university web portals)
    if (typeof el.onchange === 'function') {
      try { el.onchange(); } catch(e) {}
    }
    if (typeof el.oninput === 'function') {
      try { el.oninput(); } catch(e) {}
    }

    el.dispatchEvent(new Event('blur', { bubbles: true }));
    if (el.form) el.form.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function setInputValue(el, value) {
    if (!value && value !== 0) return false;
    var before = el.value;
    setNativeValue(el, String(value));
    dispatchAll(el);
    var after = el.value;
    return after.trim().length > 0 && after !== before;
  }

  function setSelectValue(sel, value) {
    var opt = findOption(sel, value);
    if (!opt) return false;
    sel.dispatchEvent(new Event('focus', { bubbles: true }));
    sel.value = opt.value;
    for (var i = 0; i < sel.options.length; i++) {
      if (sel.options[i].value === opt.value) { sel.selectedIndex = i; break; }
    }
    dispatchAll(sel);
    return sel.value.trim().length > 0;
  }

  // ── New radio button matcher function ────────────────────────────────────
  function setRadioValue(radioGroup, value) {
    if (!value) return false;
    var targetVal = cleanText(value);
    var isTargetYes = isYes(targetVal);
    var isTargetNo = isNo(targetVal);
    var matchedRadio = null;
    var bestScore = -1;

    for (var i = 0; i < radioGroup.length; i++) {
      var radio = radioGroup[i];
      var rVal = cleanText(radio.value);
      var rText = '';

      // Locate labels matching the radio button ID
      if (radio.id) {
        var labelEl = document.querySelector('label[for="' + radio.id + '"]');
        if (labelEl) rText = cleanText(labelEl.textContent);
      }
      if (!rText) {
        var parent = radio.parentElement;
        if (parent && parent.tagName === 'LABEL') {
          rText = cleanText(parent.textContent);
        } else {
          var nextNode = radio.nextSibling;
          if (nextNode && nextNode.nodeType === 3) {
            rText = cleanText(nextNode.textContent);
          }
        }
      }

      var score = -1;
      if (rVal === targetVal || rText === targetVal) {
        score = 100;
      } else if (isTargetYes && (isYes(rVal) || isYes(rText))) {
        score = 90;
      } else if (isTargetNo && (isNo(rVal) || isNo(rText))) {
        score = 90;
      } else if (rText.indexOf(targetVal) !== -1 || rVal.indexOf(targetVal) !== -1) {
        score = 50;
      }

      if (score > bestScore) {
        bestScore = score;
        matchedRadio = radio;
      }
    }

    if (matchedRadio && bestScore >= 50) {
      matchedRadio.checked = true;
      matchedRadio.dispatchEvent(new Event('focus', { bubbles: true }));
      matchedRadio.dispatchEvent(new Event('click', { bubbles: true }));
      if (typeof matchedRadio.onclick === 'function') {
        try { matchedRadio.onclick(); } catch(e) {}
      }
      matchedRadio.dispatchEvent(new Event('change', { bubbles: true }));
      if (typeof matchedRadio.onchange === 'function') {
        try { matchedRadio.onchange(); } catch(e) {}
      }
      matchedRadio.dispatchEvent(new Event('blur', { bubbles: true }));
      return true;
    }
    return false;
  }

  // ── Field matching ──────────────────────────────────────────────────────
  function matchField(el) {
    var raw = [
      el.name || '',
      el.id || '',
      el.placeholder || '',
      el.getAttribute('aria-label') || '',
      el.getAttribute('aria-labelledby') || '',
      el.getAttribute('title') || '',
      el.getAttribute('data-field') || '',
      el.getAttribute('data-name') || '',
    ].join(' ').toLowerCase().replace(/[_\\-]/g, ' ').trim();

    var labelText = '';
    if (el.labels && el.labels.length) {
      labelText = el.labels[0].textContent.toLowerCase().replace(/[_\\-]/g, ' ').trim();
    } else {
      var lid = el.getAttribute('aria-labelledby');
      if (lid) {
        var labelEl = document.getElementById(lid);
        if (labelEl) labelText = labelEl.textContent.toLowerCase().replace(/[_\\-]/g, ' ').trim();
      }
      var parent = el.parentElement;
      for (var d = 0; d < 4 && parent; d++) {
        var lbl = parent.querySelector('label');
        if (lbl && !lbl.htmlFor) { labelText = lbl.textContent.toLowerCase().replace(/[_\\-]/g, ' ').trim(); break; }
        parent = parent.parentElement;
      }
    }

    var allText = raw + ' ' + labelText;
    var bestKey = null, bestScore = 0;

    for (var key in fieldMap) {
      var aliases = fieldMap[key];
      for (var j = 0; j < aliases.length; j++) {
        var alias = aliases[j];
        if (allText.indexOf(alias) !== -1) {
          var score = alias.length * 2;
          if (labelText.indexOf(alias) !== -1) score += 10;
          if (raw.indexOf(alias) !== -1) score += 5;
          if (score > bestScore) { bestScore = score; bestKey = key; }
          break;
        }
      }
    }
    return bestKey;
  }

  // ── Main fill loop ──────────────────────────────────────────────────────
  function doAutofill() {
    if (!vs['firstName'] && !vs['lastName'] && !vs['email']) {
      showToast('No profile data. Go to Dashboard first.', '#EF4444');
      return;
    }

    // 1. Fill standard inputs, textareas, and dropdowns (select elements) across ALL nested frames
    var normalSelector = 'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]):not([type=checkbox]):not([type=radio]), select, textarea';
    var inputs = getElementsFromAllFrames(normalSelector);
    var filled = 0;
    var retries = [];

    for (var i = 0; i < inputs.length; i++) {
      var inp = inputs[i];
      if (inp.readOnly || inp.disabled) continue;

      var key = matchField(inp);
      if (!key || !vs[key]) continue;

      var ok = false;
      if (inp.tagName === 'SELECT') {
        ok = setSelectValue(inp, vs[key]);
        if (!ok) retries.push({ el: inp, key: key });
      } else {
        ok = setInputValue(inp, vs[key]);
      }

      if (ok) {
        filled++;
        inp.style.outline = '3px solid #10B981';
        inp.style.outlineOffset = '1px';
      }
    }

    // 2. Fill radio buttons across ALL nested frames
    var radios = getElementsFromAllFrames('input[type=radio]');
    var radioGroups = {};
    for (var j = 0; j < radios.length; j++) {
      var rad = radios[j];
      if (rad.disabled) continue;
      var name = rad.name;
      if (!name) continue;
      
      // Grouping by frame origin to avoid mixing elements with same name in separate frame documents
      var frameKey = (rad.ownerDocument === document) ? 'main' : 'iframe_' + j;
      var groupKey = frameKey + '_' + name;
      
      if (!radioGroups[groupKey]) {
        radioGroups[groupKey] = [];
      }
      radioGroups[groupKey].push(rad);
    }

    for (var gKey in radioGroups) {
      var group = radioGroups[gKey];
      var representative = group[0];
      var key = matchField(representative);
      if (key && vs[key]) {
        var ok = setRadioValue(group, vs[key]);
        if (ok) {
          filled++;
          group.forEach(function(r) {
            if (r.parentElement) {
              r.parentElement.style.outline = '2px solid #10B981';
              r.parentElement.style.borderRadius = '4px';
            }
          });
        }
      }
    }

    // 3. Fill checkboxes across ALL nested frames
    var checkboxes = getElementsFromAllFrames('input[type=checkbox]');
    for (var c = 0; c < checkboxes.length; c++) {
      var chk = checkboxes[c];
      if (chk.disabled || chk.readOnly) continue;
      var key = matchField(chk);
      if (key && vs[key]) {
        var val = vs[key].toLowerCase().trim();
        var shouldCheck = isYes(val);
        if (chk.checked !== shouldCheck) {
          chk.checked = shouldCheck;
          chk.dispatchEvent(new Event('focus', { bubbles: true }));
          chk.dispatchEvent(new Event('click', { bubbles: true }));
          if (typeof chk.onclick === 'function') { try { chk.onclick(); } catch(e) {} }
          chk.dispatchEvent(new Event('change', { bubbles: true }));
          if (typeof chk.onchange === 'function') { try { chk.onchange(); } catch(e) {} }
          chk.dispatchEvent(new Event('blur', { bubbles: true }));
          filled++;
          if (chk.parentElement) {
            chk.parentElement.style.outline = '2px solid #10B981';
          }
        }
      }
    }

    // Retry select elements asynchronously for cascade loading dropdowns
    if (retries.length) {
      function doRetry() {
        for (var r = 0; r < retries.length; r++) {
          var item = retries[r];
          if (item.el.style.outline) continue;
          var ok = setSelectValue(item.el, vs[item.key]);
          if (ok) { 
            filled++; 
            item.el.style.outline = '3px solid #10B981'; 
            item.el.style.outlineOffset = '1px'; 
          }
        }
      }
      setTimeout(doRetry, 600);
      setTimeout(doRetry, 2000);
      setTimeout(doRetry, 5000);
    }

    showToast(
      filled > 0 ? '✅ Filled ' + filled + ' field' + (filled > 1 ? 's' : '') + '!' : 'No fields matched.',
      filled > 0 ? '#10B981' : '#EF4444'
    );
  }

  $starBlock

  doAutofill();
})();
''';
}

// ── iEnabler portal patches (run in onPageFinished, before autofill) ─────

// Security patch: C1 (PIN credential block), C2 (ID masking), C3 (OTP audit),
//                 A1 (PIN autocomplete/credential suppress), A3 (extension suppress)
String buildSecurityPatch() => '''
(function() {
  var pin = document.querySelector('input[type="password"], input[name="P_PIN"]');
  if (pin) {
    pin.setAttribute('autocomplete', 'off');
    pin.setAttribute('data-lpignore', 'true');
    pin.setAttribute('data-1p-ignore', 'true');
    pin.setAttribute('data-bwignore', 'true');
    pin.setAttribute('data-dashlane-rid', 'ignore');
    var num = document.querySelector('input[name="P_STUDENT_NO"], input[name="P_NUMB"]');
    if (num) num.setAttribute('autocomplete', 'off');
    var form = document.querySelector('form');
    if (form) form.setAttribute('autocomplete', 'off');
    document.addEventListener('visibilitychange', function() {
      if (document.hidden && pin.value) pin.value = '';
    });
  }
  var idField = document.querySelector('[name="P_ID_NO"]');
  if (idField) {
    idField.setAttribute('autocomplete', 'off');
    idField.addEventListener('paste', function(e) { e.stopPropagation(); }, true);
    idField.addEventListener('blur', function() {
      if (idField.value.length === 13) idField.setAttribute('type', 'password');
    });
    idField.addEventListener('focus', function() {
      idField.setAttribute('type', 'text');
    });
  }
  document.querySelectorAll('input').forEach(function(el) {
    var ac = el.getAttribute('autocomplete') || '';
    if (ac.includes('one-time-code')) el.setAttribute('autocomplete', 'off');
  });
})();
''';

// Label patch: B1 — aria-label injection for autofill heuristics + screen readers
String buildLabelPatch() => '''
(function() {
  var map = {
    'P_SURNAME':      'Surname',
    'P_INITIALS':     'First names / Initials',
    'P_ID_NO':        'South African ID number',
    'P_PASSPORT_NO':  'Passport number',
    'P_EMAIL':        'Email address',
    'P_CELL_NO':      'Cell phone number',
    'P_DATE_OF_BIRTH':'Date of birth',
    'P_STUDENT_NO':   'Student number',
    'P_PIN':          'PIN',
    'P_GENDER':       'Gender',
    'P_HOME_LANG':    'Home language',
    'P_RACE':         'Population group',
    'P_NATIONALITY':  'Nationality',
    'P_ADDRESS_1':    'Street address line 1',
    'P_POSTAL_CODE':  'Postal code',
  };
  Object.keys(map).forEach(function(name) {
    var el = document.querySelector('[name="' + name + '"]');
    if (!el) return;
    el.setAttribute('aria-label', map[name]);
    if (!el.id) el.id = 'ss_' + name.toLowerCase();
  });
})();
''';

// Autocomplete patch: B2 + A2 — WHATWG autocomplete tokens + suppress address fields
String buildAutocompletePatch() => '''
(function() {
  var dangerousNames = ['P_ADDRESS_1','P_ADDRESS_2','P_POSTAL_CODE',
                        'P_CITY','P_PROVINCE','P_COUNTRY'];
  dangerousNames.forEach(function(n) {
    var el = document.querySelector('[name="' + n + '"]');
    if (el) el.setAttribute('autocomplete', 'off');
  });
  var tokens = {
    'P_SURNAME':      'family-name',
    'P_INITIALS':     'given-name',
    'P_EMAIL':        'email',
    'P_CELL_NO':      'tel-national',
    'P_DATE_OF_BIRTH':'bday',
    'P_GENDER':       'sex',
    'P_STUDENT_NO':   'username',
    'P_PIN':          'off',
    'P_ID_NO':        'off',
    'P_PASSPORT_NO':  'off',
    'P_ADDRESS_1':    'off',
    'P_POSTAL_CODE':  'off',
  };
  Object.keys(tokens).forEach(function(name) {
    var el = document.querySelector('[name="' + name + '"]');
    if (el) el.setAttribute('autocomplete', tokens[name]);
  });
})();
''';

// Focus patch: B3 — move autofocus from PIN to student number
String buildFocusPatch() => '''
(function() {
  var pin = document.querySelector('[name="P_PIN"]');
  if (pin) pin.removeAttribute('autofocus');
  var num = document.querySelector('[name="P_STUDENT_NO"], [name="P_NUMB"]');
  if (num) num.focus();
})();
''';

// Inputmode patch: B4 — numeric inputmode for ID, phone, postal code, student no
String buildInputmodePatch() => '''
(function() {
  var numericFields = ['P_ID_NO','P_CELL_NO','P_POSTAL_CODE',
                       'P_STUDENT_NO','P_NUMB'];
  numericFields.forEach(function(name) {
    var el = document.querySelector('[name="' + name + '"]');
    if (el) {
      el.setAttribute('inputmode', 'numeric');
      el.setAttribute('pattern', '[0-9]*');
    }
  });
  var dob = document.querySelector('[name="P_DATE_OF_BIRTH"]');
  if (dob) dob.setAttribute('inputmode', 'numeric');
})();
''';

// Form label patch: B5 — name the <form> so Chrome doesn't merge across steps
String buildFormLabelPatch() => '''
(function() {
  var forms = document.querySelectorAll('form');
  if (forms.length === 1) {
    forms[0].setAttribute('aria-label', document.title || 'University application form');
    if (!forms[0].id) forms[0].id = 'ss_main_form';
  }
})();
''';

String buildInjectScript(String oapName, String normalizedValue) {
  final v = normalizedValue.replaceAll("'", "\\'");
  return '''
(function() {
  var target = '$v';
  if (!target) return 'false';
  var names = ['$oapName', '${oapName.startsWith('oap') ? 'P_${oapName.substring(3).toUpperCase()}' : oapName}', '${oapName.toLowerCase()}'];
  for (var ni = 0; ni < names.length; ni++) {
    var name = names[ni];
    var radios = document.querySelectorAll('input[type="radio"][name="' + name + '"]');
    if (radios.length > 0) {
      for (var ri = 0; ri < radios.length; ri++) {
        if (radios[ri].value === target || radios[ri].value.toLowerCase() === target.toLowerCase()) {
          radios[ri].checked = true;
          radios[ri].dispatchEvent(new Event('change', { bubbles: true }));
          return 'true';
        }
      }
    }
    var el = document.querySelector('input[name="' + name + '"], textarea[name="' + name + '"]');
    if (el) {
      el.value = target;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return 'true';
    }
    var sel = document.querySelector('select[name="' + name + '"]');
    if (sel) {
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === target || sel.options[i].value.toLowerCase() === target.toLowerCase()) {
          sel.selectedIndex = i;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          return 'true';
        }
      }
      for (var i = 0; i < sel.options.length; i++) {
        var txt = sel.options[i].text.trim().toLowerCase();
        if (txt === target.toLowerCase() || txt.indexOf(target.toLowerCase()) === 0) {
          sel.selectedIndex = i;
          sel.dispatchEvent(new Event('change', { bubbles: true }));
          return 'true';
        }
      }
    }
  }
  return 'false';
})();
''';
}

String buildFieldScanScript() => '''
(function() {
  var result = [];

  function scan(container) {
    var els = container.querySelectorAll('input, select, textarea');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var name = el.getAttribute('name') || '(no name)';
      var id = el.getAttribute('id') || '';
      var type = el.tagName.toLowerCase();
      if (el.type) type += '[' + el.type + ']';
      var info = name + '|' + type;
      if (id) info += '|id=' + id;
      var ph = el.getAttribute('placeholder');
      if (ph) info += '|placeholder=' + ph.substring(0, 40);
      var aria = el.getAttribute('aria-label');
      if (aria) info += '|aria=' + aria.substring(0, 40);
      if (result.indexOf(info) === -1) result.push(info);
    }
  }

  // Scan main document
  scan(document);

  // Scan iframes
  var frames = document.querySelectorAll('iframe');
  for (var fi = 0; fi < frames.length; fi++) {
    try {
      var doc = frames[fi].contentDocument || frames[fi].contentWindow.document;
      if (doc) scan(doc);
    } catch(e) {}
  }

  return result.join('\\\\n');
})();
''';

String buildBlanketAutofillSuppressScript() => '''
(function() {
  var inputs = document.querySelectorAll(
    'input[type="text"], input[type="email"], input[type="tel"], input[type="password"]'
  );
  inputs.forEach(function(el) {
    el.setAttribute('autocomplete', 'off');
    el.setAttribute('data-lpignore', 'true');
    el.setAttribute('data-1p-ignore', 'true');
  });
})();
''';

String buildSelectAutocompletePatch() => '''
(function() {
  var selectTokens = {
    'P_GENDER':         'sex',
    'P_NATIONALITY':    'country-name',
    'P_PROVINCE':       'address-level1',
    'P_MARITAL_STATUS': 'off',
    'P_HOME_LANG':      'off',
    'P_RACE':           'off',
    'P_DISABILITY':     'off',
    'P_QUAL_TYPE':      'off',
    'P_FACULTY':        'off',
    'P_PREV_TERTIARY':  'off',
  };
  Object.keys(selectTokens).forEach(function(name) {
    var el = document.querySelector('select[name="' + name + '"]');
    if (el) el.setAttribute('autocomplete', selectTokens[name]);
  });
})();
''';

String buildProvinceDisambiguationPatch() => '''
(function() {
  var province = document.querySelector('select[name="P_PROVINCE"]');
  if (!province) return;
  var pageText = (document.title + ' ' + (document.body ? document.body.innerText : '')).toLowerCase();
  var isPostal = pageText.indexOf('postal') !== -1;
  province.id = isPostal ? 'P_PROVINCE_POSTAL' : 'P_PROVINCE_RESIDENTIAL';
  province.setAttribute('autocomplete', 'address-level1');
  if (isPostal) {
    var form = province.closest('form');
    if (form) form.setAttribute('autocomplete', 'postal-address');
  }
})();
''';

/// Oracle ITS portals use <select> elements alongside hidden <input> fields
/// that mirror the selected value.  After the second autofill pass those
/// hidden mirrors can still hold stale data; this patch force-syncs them
/// by reading the visible <select>'s current value.
/// Scrolls to the field and attaches a change listener so the tick turns
/// green automatically when the student fills it in.
/// Searches by: name (case-insensitive), id, name-suffix, and label text.
String buildScrollToFieldScript(String oapName, String label) {
  final bare = oapName.startsWith('oap') ? oapName.substring(3) : oapName;
  final names = [
    oapName,
    'P_${bare.toUpperCase()}',
    oapName.toLowerCase(),
    bare.toUpperCase(),
    bare.toLowerCase(),
  ];
  final quoted = names.map((n) => "'$n'").join(', ');
  return '''
(function() {
  var names = [$quoted];
  var lowers = names.map(function(t){ return t.toLowerCase(); });

  function find() {
    var f;
    for (var i = 0; i < lowers.length; i++) {
      f = document.getElementById(lowers[i]) ||
          document.querySelector('[id="' + lowers[i] + '"]') ||
          document.querySelector('[name="' + lowers[i] + '"]');
      if (f) return f;
    }
    return null;
  }

  var field = find();
  if (!field) return false;
  field.scrollIntoView({ behavior: 'smooth', block: 'center' });
  field.classList.add('fix-highlight');
  field.focus();
  if (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA') field.select();
  setTimeout(function(){ field.classList.remove('fix-highlight'); }, 3000);
  if (!field._fieldWatchAdded) {
    field._fieldWatchAdded = true;
    field.addEventListener('change', function() { FieldChangeChannel.postMessage('$oapName'); });
    field.addEventListener('input', function() { FieldChangeChannel.postMessage('$oapName'); });
  }
  return true;
})();
''';
}

String buildWizardResyncPatch() => '''
(function() {
  var selects = document.querySelectorAll('select');
  for (var i = 0; i < selects.length; i++) {
    var sel = selects[i];
    var name = sel.getAttribute('name');
    if (!name) continue;
    var hidden = document.querySelector('input[type="hidden"][name="' + name + '"]');
    if (hidden) {
      hidden.value = sel.value;
      hidden.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }
})();
''';


