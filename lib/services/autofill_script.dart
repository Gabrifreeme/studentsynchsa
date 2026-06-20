// ─────────────────────────────────────────────────────────────────────────────
// autofill_script.dart  –  StudentSyncSA Star Auto-Fill
//
// Built specifically for ITS (Oracle PL/SQL) university portals used by
// UNIVEN, UL, TUT, NWU and others. These portals use P_* field names and
// plain HTML — no React, no Angular, no framework events needed.
// Falls back to generic matching for other university sites.
// ─────────────────────────────────────────────────────────────────────────────

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

  // ── 2. ITS portal exact-name map (P_* Oracle fields) ──────────────────
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

  // ── 5. Main autofill ───────────────────────────────────────────────────
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
        ? '✅ Filled ' + filled + ' field' + (filled !== 1 ? 's' : '') + '!'
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
    star.innerHTML = '⭐';
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
