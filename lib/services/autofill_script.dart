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

  var firstName   = gv('personal.firstName');
  var lastName    = gv('personal.lastName');
  var email       = gv('contact.email');
  var dobIso      = gv('personal.dateOfBirth');

  var vs = {
    firstName:         firstName,
    lastName:          lastName,
    initials:          gv('personal.initials'),
    title:             gv('personal.title'),
    gender:            gv('personal.gender'),
    idNumber:          gv('personal.idNumber'),
    dateOfBirth:       fmtDate(dobIso),
    dateOfBirthSlash:  fmtDateSlash(dobIso),
    email:             email,
    phone:             gv('contact.phone'),
    workPhone:         gv('contact.workPhone'),
    address:           gv('address.address'),
    addressLine2:      gv('address.addressLine2'),
    province:          gv('address.province'),
    postalCode:        gv('address.postalCode'),
    nationality:       gv('demographic.nationality'),
    homeLanguage:      gv('demographic.homeLanguage'),
    populationGroup:   gv('demographic.populationGroup'),
    maritalStatus:     gv('demographic.maritalStatus'),
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
    // Personal
    'P_SURNAME':           vs.lastName,
    'P_NAME':              vs.firstName,
    'P_INITIALS':          vs.initials,
    'P_TITLE':             vs.title,
    'P_GENDER':            vs.gender,
    'P_ID_NO':             vs.idNumber,
    'P_PASSPORT_NO':       vs.idNumber,
    'P_DATE_OF_BIRTH':     vs.dateOfBirth,
    'P_DOB':               vs.dateOfBirth,
    'P_BIRTH_DATE':        vs.dateOfBirth,
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
    province:          ['province','state','region'],
    postalCode:        ['postal code','postalcode','post code','postcode','zip'],
    nationality:       ['nationality','citizenship','citizen'],
    homeLanguage:      ['home language','homelanguage','language'],
    populationGroup:   ['population group','race','ethnicity'],
    maritalStatus:     ['marital status','maritalstatus'],
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

  function findOption(sel, want) {
    if (!want) return null;
    var wl = want.toLowerCase().trim();
    var best = null, bestScore = -1;
    for (var i = 0; i < sel.options.length; i++) {
      var opt = sel.options[i];
      if (isPlaceholder(opt.text)) continue;
      var tl = opt.text.toLowerCase().trim();
      var vl = opt.value.toLowerCase().trim();
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

  // ÔöÇÔöÇ 5. Main autofill ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
  function doAutofill() {
    if (!firstName && !lastName && !email) {
      showToast('No profile data. Please complete your profile first.', '#EF4444');
      return;
    }

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
    }

    showToast(
      filled > 0
        ? 'Ô£à Filled ' + filled + ' field' + (filled !== 1 ? 's' : '') + '!'
        : 'No fields matched. Try scrolling to the next section.',
      filled > 0 ? '#10B981' : '#EF4444'
    );
  }

  ${addFloatingStar ? '''
  // Floating star button injected into the page
  (function() {
    if (document.getElementById('ssa-star')) return;
    var star = document.createElement('div');
    star.id = 'ssa-star';
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

  doAutofill();
})();
''';
}
