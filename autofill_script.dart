String buildAutofillScript(String profileJson) {
  return _buildFullScript(profileJson, createStar: true);
}

String buildAutofillOnlyScript(String profileJson) {
  return _buildFullScript(profileJson, createStar: false);
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
    'oapfirstnames':         ['firstname','first name','fname','given name','givenname'],
    'oapsurname':          ['lastname','last name','lname','surname','family name','familyname'],
    'initials':          ['initials'],
    'gender':            ['gender','sex'],
    'oapidnumber':          ['idnumber','id number','identity number','national id','sa id','passport number','rsaid','rsaid'],
    'dateOfBirth':       ['dateofbirth','date of birth','dob','birthdate','birth date','birthday'],
    'oapemail':             ['email','e-mail','emailaddress','email address'],
    'oapcellno':             ['phone','telephone','tel','cell','cellphone','mobile','mobile number','contact no','phone number'],
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

  // ── Option helpers ──────────────────────────────────────────────────────
  function isPlaceholder(text) {
    var t = text.toLowerCase().trim();
    return t === '' || t === 'select' || t === 'choose' || t === 'please select'
      || t.indexOf('select') === 0 || t.indexOf('choose') === 0 || t.indexOf('--') !== -1;
  }

  function isYes(text) {
    var t = text.toLowerCase().trim();
    return t === 'yes' || t === 'y' || t === 'true' || t === '1'
      || t === 'sa citizen' || t === 'south african' || t === 'rsa';
  }

  function isNo(text) {
    var t = text.toLowerCase().trim();
    return t === 'no' || t === 'n' || t === 'false' || t === '0' || t === 'other';
  }

  function findOption(sel, rawVal) {
    if (!rawVal) return null;
    var vl = rawVal.toLowerCase().trim();
    var terms = [vl];
    if (vl === 'sa citizen' || vl === 'south african' || vl === 'south africa' || vl === 'sa' || vl === 'rsa') {
      terms = terms.concat(['south african','south africa','sa citizen','rsa']);
    }
    var bestOpt = null, bestScore = -1;
    for (var t = 0; t < terms.length; t++) {
      var tl = terms[t];
      var tWords = tl.split(/\\s+/);
      for (var k = 0; k < sel.options.length; k++) {
        var opt = sel.options[k];
        if (isPlaceholder(opt.text)) continue;
        var tt = opt.text.toLowerCase().trim();
        var vv = opt.value.toLowerCase().trim();
        var score = -1;
        if (tt === tl || vv === tl)                               score = 100;
        else if (tt.startsWith(tl) || vv.startsWith(tl))         score = 50;
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

  // ── THE CORE FIX: React/Angular/Vue aware value setter ──────────────────
  //
  // Plain el.value = x does NOT trigger React's synthetic event system.
  // React stores its own internal fiber/instance on the DOM node.
  // We must:
  //   1. Use the native HTMLInputElement descriptor's setter (bypasses React's override)
  //   2. Fire a real InputEvent (not just Event) so React's onChange fires
  //   3. Fire change + blur so Angular, Vue, and plain HTML forms also update
  //
  function setNativeValue(el, value) {
    // Get the prototype's own value setter (HTMLInputElement or HTMLTextAreaElement)
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
    // Focus first — some frameworks gate change events on focused elements
    el.dispatchEvent(new Event('focus', { bubbles: true }));

    // InputEvent is what React 16/17/18 actually listens for on text inputs
    try {
      el.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: el.value }));
    } catch(e) {
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // change — Angular, Vue, plain HTML
    el.dispatchEvent(new Event('change', { bubbles: true }));

    // blur — triggers validation in most frameworks
    el.dispatchEvent(new Event('blur', { bubbles: true }));

    // For good measure: propagate change up to the form (Angular reactive forms)
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
    // Also set selectedIndex for frameworks that watch that
    for (var i = 0; i < sel.options.length; i++) {
      if (sel.options[i].value === opt.value) { sel.selectedIndex = i; break; }
    }
    dispatchAll(sel);
    return sel.value.trim().length > 0;
  }

  // ── Field matching ──────────────────────────────────────────────────────
  function matchField(el) {
    // Normalise all identifying text for the element
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
      // Try finding label by wrapping element or aria-labelledby
      var lid = el.getAttribute('aria-labelledby');
      if (lid) {
        var labelEl = document.getElementById(lid);
        if (labelEl) labelText = labelEl.textContent.toLowerCase().replace(/[_\\-]/g, ' ').trim();
      }
      // Try nearest preceding label or parent label
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
          var score = alias.length * 2;                        // longer alias = more specific
          if (labelText.indexOf(alias) !== -1) score += 10;   // label match wins
          if (raw.indexOf(alias) !== -1) score += 5;          // attribute match
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

    var inputs = document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]):not([type=checkbox]):not([type=radio]), select, textarea');
    var filled = 0;
    var retries = [];

    for (var i = 0; i < inputs.length; i++) {
      var inp = inputs[i];
      if (inp.readOnly || inp.disabled) continue;
      // Skip already-filled fields (don't overwrite user edits)
      // Actually we DO want to fill — remove this guard if unwanted
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

    // Retry selects after a tick — some SPAs populate options asynchronously
    if (retries.length) {
      function doRetry() {
        for (var r = 0; r < retries.length; r++) {
          var item = retries[r];
          if (item.el.style.outline) continue; // already filled
          var ok = setSelectValue(item.el, vs[item.key]);
          if (ok) { filled++; item.el.style.outline = '3px solid #10B981'; item.el.style.outlineOffset = '1px'; }
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
