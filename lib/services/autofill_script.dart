// ─────────────────────────────────────────────────────────────────────────────
// autofill_script.dart  –  LipSyncStudent Star Auto-Fill
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
    genderCode:        (function() {
                          var g = gv('personal.gender').toLowerCase();
                          if (g.indexOf('female') !== -1 || g === 'f') return 'F';
                          if (g.indexOf('male') !== -1 || g === 'm') return 'M';
                          return 'M'; // default: 'Other', 'Prefer not to say' → M
                        })(),
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
    heardAboutUs:      gv('demographic.heardAboutUs'),
    nationality:       gv('demographic.nationality'),
    isSACitizen:       (function() {
                         var nat = (gv('demographic.nationality') || '').toLowerCase();
                         var idn = (gv('personal.idNumber') || '').trim();
                         if (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) return 'Yes';
                         if (idn.length >= 13) return 'Yes';
                         return 'No';
                       })(),
    citizenshipCodeValue: (function() {
                            var nat = (gv('demographic.nationality') || '').toLowerCase();
                            var idn = (gv('personal.idNumber') || '').trim();
                            var sa = (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) || idn.length >= 13;
                            return sa ? 'OTHER AFRICAN COUNTRIES' : (gv('demographic.citizenshipCode') || '');
                          })(),
    citizenshipShortCode: (function() {
                            var nat = (gv('demographic.nationality') || '').toLowerCase();
                            var idn = (gv('personal.idNumber') || '').trim();
                            var sa = (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) || idn.length >= 13;
                            return sa ? 'OTHER AFRICAN COUNTRIES' : (gv('demographic.citizenshipCode') || '');
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
    firstName:         ['firstname','first name','fname','given name','name','first names'],
    lastName:          ['lastname','last name','surname','lname','family name','maiden name'],
    initials:          ['initials'],
    title:             ['title','salutation'],
    gender:            ['gender','sex'],
    idNumber:          ['id number','idnumber','identity number','national id','id no','passport'],
    dateOfBirth:       ['date of birth','dateofbirth','dob','birth date','birthdate','birthday'],
    email:             ['email','e-mail','email address'],
    phone:             ['cell','cellphone','mobile','phone','telephone','contact number','cellphone number','cell number'],
    workPhone:         ['work phone','work tel','telephone work'],
    address:           ['address','street','physical address'],
    addressLine2:      ['address 2','suburb','town','city'],
    province:          ['province','state','region','select province'],
    postalCode:        ['postal code','postalcode','post code','postcode','zip'],
    nationality:       ['nationality','citizenship','citizen'],
    isSACitizen:       ['sa citizen','possession of','valid sa','sa id'],
    homeLanguage:      ['home language','homelanguage','language','correspondence language'],
    populationGroup:   ['population group','ethnicity'],
    raceValue:         ['race','population group'],
    maritalStatus:     ['marital status','maritalstatus'],
    maritalYesNo:      ['married','are you married','marital status'],
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
    var wlWords = wl.split(/s+/);
    var best = null, bestScore = -1;
    for (var i = 0; i < sel.options.length; i++) {
      var opt = sel.options[i];
      if (isPlaceholder(opt.text)) continue;
      var tl = opt.text.toLowerCase().trim();
      var vl = opt.value.toLowerCase().trim();
      var tlWords = tl.split(/s+/);
      var vlWords = vl.split(/s+/);
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
    // Scan closest visible label for generic portals
    if (el.labels && el.labels.length) {
      for (var li = 0; li < el.labels.length; li++) {
        parts.push(el.labels[li].textContent || '');
      }
    } else {
      // Scan closest visible label via 'for' attribute (label -> input link)
      var inputId = el.id || '';
      if (!inputId && el.name) inputId = el.name;
      if (inputId) {
        var inputLabels = document.querySelectorAll('label[for="' + inputId + '"]');
        for (var lblIdx = 0; lblIdx < inputLabels.length; lblIdx++) {
          parts.push(inputLabels[lblIdx].textContent || '');
        }
      }
      // Also scan via aria-labelledby
      var ariaLblIds = el.getAttribute('aria-labelledby');
      if (ariaLblIds) {
        var ids = ariaLblIds.split(/s+/);
        for (var a = 0; a < ids.length; a++) {
          var lbl = document.getElementById(ids[a]);
          if (lbl) parts.push(lbl.textContent || '');
        }
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
    // For email: only match when label explicitly contains 'email'
    // Prevents 'email' from winning on unrelated labels via partial match.
    var bestKey = null, bestScore = 0;
    for (var key in fieldMap) {
      var aliases = fieldMap[key];
      for (var j = 0; j < aliases.length; j++) {
        var alias = aliases[j];
        // Email guard: require the word 'email' be present in label for email key
        if (key === 'email' && text.indexOf('email') === -1 && text.indexOf('e-mail') === -1 && text.indexOf('mail') === -1) continue;
        if (text.indexOf(alias) !== -1) {
          var score = alias.length * 2;
          if (score > bestScore) { bestScore = score; bestKey = key; }
        }
      }
    }
    // If best match is weak (< 4 chars alias * 2 = 8), leave blank rather than guessing
    if (bestScore < 8) return null;
    return bestKey;
  }

  // ── 5. Hardcoded NWU page-specific sequence ────────────────────────────
  // Visible debug div so we can confirm the script is running.
  (function createDebugDiv() {
    var d = document.getElementById('ssa-debug-div');
    if (!d) {
      d = document.createElement('div');
      d.id = 'ssa-debug-div';
      d.style.position = 'fixed';
      d.style.top = '0';
      d.style.left = '0';
      d.style.zIndex = '9999';
      d.style.background = 'black';
      d.style.color = 'lime';
      d.style.padding = '10px';
      d.style.fontFamily = 'monospace';
      d.style.fontSize = '14px';
      d.innerHTML = '<b>[SSA] Autofill running...</b>';
      document.body.appendChild(d);
    }
  })();

  function _fillNwuByPosition() {
    var html = document.body.innerHTML.toLowerCase();
    if (html.indexOf('nwu') === -1 && html.indexOf('nwu.ac.za') === -1) return false;

    var selects = document.querySelectorAll(
      'select:not([disabled])',
    );
    // Collect all visible controls in document order
    var ns = [];
    var allInputs = document.querySelectorAll('input:not([type=submit]):not([type=button]):not([type=reset]):not([type=image]), select:not([disabled]), textarea');
    for (var i = 0; i < allInputs.length; i++) {
      var c = allInputs[i];
      // NEVER interact with CAPTCHA/reCAPTCHA elements — student solves manually
      var parent = c.parentNode;
      var skipCap = false;
      // Check if element or any parent has recaptcha-related class/id
      while (parent && parent !== document.body) {
        var cls = (parent.className || '').toString().toLowerCase();
        var id = (parent.id || '').toString().toLowerCase();
        if (cls.indexOf('g-recaptcha') !== -1 || cls.indexOf('recaptcha') !== -1 || id.indexOf('recaptcha') !== -1 || (parent.getAttribute && parent.getAttribute('data-sitekey'))) { skipCap = true; break; }
        parent = parent.parentNode;
      }
      if (skipCap) continue;
      if (c.disabled || c.getAttribute('hidden') !== null || (c.getAttribute('type') || '').toLowerCase() === 'hidden') continue;
      ns.push(c);
    }

    // Stop if there are fewer than 4 visible controls — most pages are not this.
    if (ns.length < 4) return false;

    // ── Ordered mapping (12 fields ── NWU): ────────────────────────────
    //   0  Nationality (dropdown)     -> nationality (South Africa)
    //   1  Identity Number            -> idNumber
    //   2  Surname                    -> lastName
    //   3  Initials                   -> initials
    //   4  First Names                -> firstName
    //   5  Date Of Birth              -> dateOfBirth
    //   6  Title                      -> title
    //   7  Maiden Name                -> lastName
    //   8  Email Address              -> email
    //   9  Home Language (dropdown)   -> homeLanguage
    //  10  Correspondence Language    -> homeLanguage
    //  11  Cellphone Number           -> phone
    var vsi = {
      'nationality':       (vs.nationality && vs.nationality.trim()) ? vs.nationality : 'South Africa',
      'idNumber':          vs.idNumber,
      'lastName':          vs.lastName,
      'initials':          vs.initials,
      'firstName':         vs.firstName,
      'dateOfBirth':       vs.dateOfBirth,
      'title':             vs.title,
      'email':             vs.email,
      'homeLanguage':      vs.homeLanguage,
      'phone':             vs.phone,
    };

    function visible(el) {
      var t = (el.type || '');
      return t !== 'submit' && t !== 'button' && t !== 'reset' && t !== 'image';
    }
    function tryFill(el, key) {
      if (!el) return false;
      // Nationality dropdown: default to first real option when profile empty
      if (key === 'nationality' && (!vsi[key] || vsi[key] === '')) {
        if (el.tagName === 'SELECT' && el.options && el.options.length > 0) {
          for (var ni = 0; ni < el.options.length; ni++) {
            var txt = (el.options[ni].textContent || '').toLowerCase().trim();
            if (txt && txt.indexOf('--') === -1 && txt.indexOf('please') === -1) {
              el.value = el.options[ni].value;
              el.dispatchEvent(new Event('change', { bubbles: true }));
              return true;
            }
          }
        }
        return false;
      }
      if (!vsi[key] || vsi[key] === '') return false;
      var value = vsi[key];
      var tag = el.tagName;
      if (tag === 'SELECT') {
        var opt = null;
        // Try exact match first for 'South Africa' on Nationality dropdown
        for (var i = 0; i < el.options.length; i++) {
          var optTextRaw = (el.options[i].textContent || '').trim();
          if (optTextRaw.toLowerCase() === 'south africa') { opt = el.options[i]; break; }
        }
        // Then try partial/text match
        if (!opt) {
          for (var i = 0; i < el.options.length; i++) {
            var optText = (el.options[i].textContent || '').toLowerCase().trim();
            if (optText.indexOf(value.toLowerCase()) !== -1 || value.toLowerCase().indexOf(optText) !== -1) { opt = el.options[i]; break; }
          }
        }
        if (!opt) opt = el.options[0];
        if (opt) {
          el.value = opt.value;
          // Simulate a real user interaction (click + events) for custom dropdowns
          try { opt.click(); } catch (e2) {}
          el.dispatchEvent(new Event('focus', { bubbles: true }));
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          el.dispatchEvent(new Event('blur', { bubbles: true }));
          return true;
        }
        return false;
      }
      try {
        if (el.removeAttribute) el.removeAttribute('readonly');
        if (el.removeAttribute) el.removeAttribute('disabled');
      } catch (e) {}
      el.style.display = 'block';
      el.style.visibility = 'visible';
      try {
        if (el.removeAttribute) el.removeAttribute('readonly');
        if (el.removeAttribute) el.removeAttribute('disabled');
      } catch (e) {}
      el.style.display = 'block';
      el.style.visibility = 'visible';
      el.value = value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
      return true;
    }

    var filled = 0;
    for (var k = 0; k < ns.length && k < 12; k++) {
      var key = '';
      if (k === 0) key = 'nationality';
      else if (k === 1) key = 'idNumber';
      else if (k === 2) key = 'lastName';
      else if (k === 3) key = 'initials';
      else if (k === 4) key = 'firstName';
      else if (k === 5) key = 'dateOfBirth';
      else if (k === 6) key = 'title';
      else if (k === 7) key = 'lastName';
      else if (k === 8) key = 'email';
      else if (k === 9) key = 'homeLanguage';
      else if (k === 10) key = 'homeLanguage';
      else if (k === 11) key = 'phone';
      if (!vsi[key] || vsi[key] === '' || (vsi[key] + '').toLowerCase().indexOf('http') !== -1 || (vsi[key] + '').toLowerCase().indexOf('.ac.za') !== -1) continue;
      var el = ns[k];
      console.log('[autofill] field', k, 'key=', key, 'tag=', el.tagName, 'value=', vsi[key], 'hasSetter=', !!(Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set));
      if (el.tagName === 'SELECT') {
        for (var i = 0; i < el.options.length; i++) {
          if ((el.options[i].text || '').toLowerCase().indexOf((vsi[key] || '').toLowerCase()) !== -1) { el.value = el.options[i].value; break; }
        }
      } else {
        el.value = vsi[key];
      }
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      var label = key === 'idNumber' ? 'Identity' : key === 'lastName' ? 'Surname/Maiden' : key === 'initials' ? 'Initials' : key === 'firstName' ? 'First Names' : key === 'dateOfBirth' ? 'DOB' : key === 'title' ? 'Title' : key === 'email' ? 'Email' : key === 'homeLanguage' ? 'Language' : key === 'phone' ? 'Cell' : key === 'nationality' ? 'Nationality' : key;
      var dd = document.getElementById('ssa-debug-div');
      if (dd) dd.innerHTML += '<br>Filled ' + label;
      filled++;
    }
    return filled > 0;
  }
  if (_fillNwuByPosition()) return; // NWU: use the hardcoded sequence.

  // ── 5b. Main autofill ─────────────────────────────────────────────────
  function doAutofill() {
    if (!firstName && !lastName && !email) {
      showToast('No profile data. Please complete your profile first.', '#EF4444');
      return;
    }

    var inputs = document.querySelectorAll(
      'input:not([type=submit]):not([type=button])'
      + ':not([type=reset]):not([type=image]),'
      + 'select, textarea'
    );

    var filled = 0;
    var alreadyHandled = {};

    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      if (el.disabled) continue;
      var isHidden = (el.type === 'hidden');

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

      // Skip LOV description/display helper fields (e.g. oapCitzCode_desc).
      // The portal auto-populates these from the real value field; filling both
      // creates a duplicate visible row.  Exact itsExact entries above can
      // still target _desc fields that need explicit filling.
      if (elName.indexOf('_DESC') !== -1 || elName.indexOf('_DISPLAY') !== -1 || elName.indexOf('_LOV') !== -1) continue;

      // Hidden fields: only fill via exact itsExact match above — never fuzzy,
      // to avoid clobbering CSRF/token/state inputs.
      if (isHidden) continue;

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

    // Fallback: generic position-based fill when IDs missing (e.g. UWC portals)
    if (filled === 0) {
      var allInputs2 = document.querySelectorAll('input:not([type=submit]):not([type=button]):not([type=reset]):not([type=image]), select:not([disabled]), textarea');
      for (var p = 0; p < allInputs2.length && p < 8; p++) {
        var el2 = allInputs2[p];
        if (el2.disabled || el2.getAttribute('hidden') !== null || (el2.getAttribute('type') || '').toLowerCase() === 'hidden') continue;
        var mapVals = [vs.lastName, vs.firstName, vs.email, vs.dateOfBirth, vs.phone, vs.idNumber, vs.initials, vs.title];
        if (!mapVals[p] || mapVals[p] === '') continue;
        var value2 = mapVals[p];
        if (el2.tagName === 'SELECT') {
          for (var i = 0; i < el2.options.length; i++) {
            if ((el2.options[i].text || '').toLowerCase().indexOf((value2 || '').toLowerCase()) !== -1) { el2.value = el2.options[i].value; break; }
          }
        } else {
          el2.value = value2;
        }
        el2.dispatchEvent(new Event('input', { bubbles: true }));
        el2.dispatchEvent(new Event('change', { bubbles: true }));
        filled++;
      }
    }
    function setSelect2Ajax(selector, valueText) {
      if (!valueText) return false;
      var el = document.querySelector(selector);
      if (!el) return false;

      function triggerEvents(element) {
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.dispatchEvent(new Event('input', { bubbles: true }));
        if (typeof jQuery !== 'undefined') {
          try { jQuery(element).trigger('change.select2'); } catch(e) {}
          try { jQuery(element).trigger('select2:select'); } catch(e) {}
          try { if (jQuery(element).data('select2')) jQuery(element).val(element.value).trigger('change'); } catch(e) {}
        }
      }

      if (typeof jQuery !== 'undefined' && jQuery(el).data('select2')) {
        var jqEl = jQuery(el);

        jqEl.select2('open');

        setTimeout(function() {
          var results = document.querySelectorAll('.select2-results__option');
          var matched = false;
          for (var i = 0; i < results.length; i++) {
            if (results[i].textContent.trim().toLowerCase() === valueText.toLowerCase()) {
              results[i].click();
              matched = true;
              break;
            }
          }

          if (!matched) {
            var newOption = new Option(valueText, valueText, true, true);
            jqEl.append(newOption).trigger('change');
          }

          jqEl.select2('close');
          el.style.outline = '3px solid #10B981';
          filled++;
        }, 500);

        return true;
      }

      function tryStandard() {
        if (el.options.length === 0) return false;
        var opt = findOption(el, valueText);
        if (!opt) return false;
        el.value = opt.value;
        triggerEvents(el);
        el.style.outline = '3px solid #10B981';
        filled++;
        return true;
      }

      if (tryStandard()) return true;

      var retries = 0;
      var interval = setInterval(function() {
        retries++;
        if (tryStandard() || retries >= 10) {
          clearInterval(interval);
        }
      }, 600);

      return true;
    }

    setSelect2Ajax('select[name="race"]', vs.raceValue);
    setSelect2Ajax('select[name="address"]', vs.province);

    // Race fallback: if AJAX gave us nothing, populate manually
    (function() {
      var s = document.querySelector('select[name="race"]');
      if (s && s.options.length === 0) {
        ['African','Asian','Coloured','Indian','Other','White'].forEach(function(t) {
          s.add(new Option(t, t));
        });
        s.value = vs.raceValue || 'African';
        s.dispatchEvent(new Event('change', { bubbles: true }));
        if (typeof \$ !== 'undefined' && \$('select[name="race"]').data('select2')) \$('select[name="race"]').trigger('change');
      }
    })();

    // Province fallback: if AJAX gave us nothing, populate manually
    (function() {
      var s = document.querySelector('select[name="address"]');
      if (s && s.options.length === 0) {
        ['Eastern Cape','Free State','Gauteng','Kwazulu/Natal','Limpopo','Mpumalanga','North West','Northern Cape','Western Cape'].forEach(function(t) {
          s.add(new Option(t, t));
        });
        s.value = vs.province || 'Gauteng';
        s.dispatchEvent(new Event('change', { bubbles: true }));
        if (typeof \$ !== 'undefined' && \$('select[name="address"]').data('select2')) \$('select[name="address"]').trigger('change');
      }
    })();

    // Postal code override: directly set oapStreetAddrPCodeRq to postal code value
    (function() {
      var v = vs.postalCode;
      if (!v) return;
      ['oapStreetAddrPCodeRq', 'oapStreetAddrPCodeRq_desc'].forEach(function(name) {
        var el = document.querySelector('input[name="' + name + '"]');
        if (!el) return;
        try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch(e) {}
        el.value = v;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
      });
    })();

    // Heard about us override
    (function() {
      var v = vs.heardAboutUs;
      if (!v) return;
      ['oapHeard', 'oapHeard_desc'].forEach(function(name) {
        var el = document.querySelector('input[name="' + name + '"]');
        if (!el) el = document.getElementById(name);
        if (!el) return;
        try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch(e) {}
        el.value = v;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
      });
    })();

    // Residence required override
    (function() {
      var el = document.getElementById('oapResReq') || document.querySelector('select[name="oapResReq"]');
      if (!el) {
        el = document.getElementById('oapTVETResReq') || document.querySelector('select[name="oapTVETResReq"]');
      }
      if (!el) return;
      var v = vs.residenceRequired || 'Y';
      if (el.options.length === 0) {
        ['--- Please select ---', 'Yes', 'No'].forEach(function(t) {
          el.add(new Option(t, t));
        });
      }
      el.value = v;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      if (typeof \$ !== 'undefined' && \$('#' + el.id).data('select2')) \$('#' + el.id).trigger('change');
    })();

    // Citizenship code override (oapCitCode / oapCitzCode = OTHER AFRICAN COUNTRIES)
    (function() {
      var v = vs.citizenshipShortCode || 'OTHER AFRICAN COUNTRIES';
      ['oapCitCode', 'oapCitCode_desc', 'oapCitzCode', 'oapCitzCode_desc'].forEach(function(name) {
        var el = document.getElementById(name) || document.querySelector('input[name="' + name + '"]');
        if (!el) return;
        try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch(e) {}
        el.value = v;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
      });
    })();

    // Gender: direct DOM manipulation (confirmed working in Edge)
    (function() {
      var v = vs.genderCode || 'F';
      var nativeSelect = document.getElementById('oapGender');
      if (!nativeSelect) return;
      nativeSelect.removeAttribute('readonly');
      nativeSelect.removeAttribute('disabled');
      nativeSelect.value = v;
      nativeSelect.setCustomValidity('');
      nativeSelect.checkValidity();
      ['input', 'change', 'blur', 'apexchange'].forEach(function(eventType) {
        nativeSelect.dispatchEvent(new Event(eventType, { bubbles: true }));
      });
      nativeSelect.setAttribute('data-apex-changed', 'true');
      var wrapper = nativeSelect.closest('.t-Form-fieldContainer');
      if (wrapper) {
        wrapper.classList.remove('has-error', 'is-error');
        var err = wrapper.querySelector('[id\$="_error_placeholder"]');
        if (err) { err.textContent = ''; err.style.display = 'none'; }
      }
      var nextBtn = document.querySelector('button[data-id="NEXT"]') ||
                    document.querySelector('#B_NEXT') ||
                    document.querySelector('input[value="Next"]') ||
                    document.querySelector('button[type="submit"]') ||
                    document.querySelector('.t-Button--next');
      if (nextBtn) {
        nextBtn.removeAttribute('disabled');
        nextBtn.classList.remove('is-disabled', 't-Button--disabled');
        nextBtn.style.pointerEvents = 'auto';
        nextBtn.style.opacity = '1';
      }
      console.log('Gender set to ' + v);
    })();

    showToast(
      filled > 0
        ? '✅ Filled ' + filled + ' field' + (filled !== 1 ? 's' : '') + '!'
        : 'No fields matched. Try scrolling to the next section.',
      filled > 0 ? '#10B981' : '#EF4444'
    );

    var visibleFields = Array.from(document.querySelectorAll('input:not([type="hidden"]), select, textarea')).filter(function(el) { return el.offsetParent !== null; });
    var filledCount = visibleFields.filter(function(el) { return el.value; }).length;
    console.log('Total visible:', visibleFields.length, 'Filled:', filledCount);

    try { AutofillResult.postMessage(JSON.stringify({ filled: filled, total: visibleFields.length })); } catch (e) {}
  }

  window.requestFlutterAutofill = doAutofill;

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


})();
''';
}

/// Returns JS that hooks the portal's Apply/Submit/Next button and resolves
/// relative URLs against the page's own base URI. Re-injection safe: it
/// de-dups listeners via a per-element data attribute and never bails out
/// early so sub-page navigations keep working.
String buildNavigationFixScript() {
  return '${'''
(function() {
  var SELECTOR = 'button[type="submit"], input[type="submit"], button[data-id="NEXT"], #B_NEXT, button[data-id="APPLY"], button[data-id="SUBMIT"], input[value="Apply"], input[value="Submit"], input[value="Next"], button[class*="t-Button"], a[class*="t-Button"], button[class*="button"]';

  function resolveUrl(url) {
    try {
      // Relative URLs (common on ITS portals: "gw1view", "../oap", "?p=1")
      // must be resolved against the page's own base URI, not the app's.
      return new URL(url, document.baseURI).href;
    } catch (e) {
      return url;
    }
  }

  function hook(el) {
    if (!el) return;
    // De-dup: never attach twice to the same element, even across re-injections.
    if (el.getAttribute('data-ssa-nav-hooked') === '1') return;
    el.setAttribute('data-ssa-nav-hooked', '1');

    el.addEventListener('click', function(e) {
      var href = el.getAttribute('href');
      if (!href) return;   // no href -> let the native submit happen
      var resolved = resolveUrl(href);
      console.log('[ssa-nav] ' + (el.textContent || '').trim() +
                   ' -> ' + href + ' (resolved: ' + resolved + ')');
      window.location.assign(resolved);
    }, true);   // capture: true -> runs before other scripts / preventDefault
  }

  function scan() {
    var nodes = document.querySelectorAll(SELECTOR);
    for (var i = 0; i < nodes.length; i++) {
      hook(nodes[i]);
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
  if (!window.__ssaNavTimer) {
    var _t = setInterval(scan, 1500);
    window.__ssaNavTimer = true;
    setTimeout(function() {
      try { clearInterval(_t); window.__ssaNavTimer = false; } catch (e) {}
    }, 15000);
  }

  console.log('[ssa-nav] navigation fix installed: ' + SELECTOR);
})();
'''
  .trim()}\n';
}

/// Returns JS that removes the old/stale postal-code picker markup from the
/// page so the new one can take its place without duplicate rows.
String buildRemoveOldPostalPickerScript() {
  return '${'''
(function() {
  // Remove any previously injected postal-code picker UI (old styling /
  // duplicate rows) before the new one is added.
  var old = document.getElementById('ssa-postal-picker');
  if (old) {
    old.remove();
    console.log('[ssa-postal] removed old picker');
  }
  var legacy = document.querySelector('[data-ssa-postal-picker]');
  if (legacy) {
    legacy.remove();
    console.log('[ssa-postal] removed legacy picker');
  }
})();
'''
  .trim()}\n';
}

/// Returns JS that injects the new postal-code picker into the page.
/// The picker is a small dropdown populated from the profile's postal code;
/// selecting a value writes it back into the portal's postal fields.
String buildPostalCodePickerScript(String profileJson) {
  return '${'''
(function() {
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

  var postalCode = gv('address.postalCode');

  if (document.getElementById('ssa-postal-picker')) return; // already injected

  var sel = document.createElement('select');
  sel.id = 'ssa-postal-picker';
  sel.title = 'Postal code';
  sel.style.cssText = 'font-size:13px;padding:4px 6px;border:1px solid #999;border-radius:4px;';

  var placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = '-- Select postal code --';
  sel.appendChild(placeholder);

  if (postalCode) {
    var opt = document.createElement('option');
    opt.value = postalCode;
    opt.textContent = postalCode;
    opt.selected = true;
    sel.appendChild(opt);
  }

  sel.addEventListener('change', function() {
    var val = sel.value;
    if (!val) return;
    // Write the selected postal code into the portal's postal fields.
    var targets = [
      'input[name="oapStreetAddrPCodeRq"]',
      'input[name="oapStreetAddrPCodeRq_desc"]',
      'input[name="oapPostalAddrPCodeRq"]',
      'input[name="oapPostalAddrPCodeRq_desc"]',
      'input[name="P_POSTAL_CODE"]',
      'input[name="P_POST_CODE"]',
      'input[name="P_POSTAL"]',
      'input[name="postal_code"]',
      'input[name="postalcode"]',
      'input[name="post_code"]',
      'input[name="postcode"]'
    ];
    for (var i = 0; i < targets.length; i++) {
      var el = document.querySelector(targets[i]);
      if (!el) continue;
      try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch (e) {}
      el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
    }
    console.log('[ssa-postal] postal code set to ' + val);
  });

  // Attach to the postal-code row if one exists, otherwise float it.
  var anchor =
    document.querySelector('input[name="oapStreetAddrPCodeRq"]') ||
    document.querySelector('input[name="P_POSTAL_CODE"]') ||
    document.querySelector('input[name="postalcode"]');
  if (anchor && anchor.parentElement) {
    anchor.parentElement.appendChild(sel);
  } else if (document.body) {
    sel.style.cssText += 'position:fixed;top:80px;right:20px;z-index:2147483646;';
    document.body.appendChild(sel);
  }

  console.log('[ssa-postal] picker injected (code: ' + (postalCode || 'none') + ')');
})();
'''
  .trim()}\n';
}
