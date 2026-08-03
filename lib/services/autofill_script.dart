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
    var monthMap = {
      'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
      'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
      'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
    };
    var monthAbbr = monthNames[parseInt(monthNum) - 1] || monthNum;

    // Remove any existing custom date picker
    var existing = document.getElementById('ssa-date-picker');
    if (existing) {
      // navfix calendar picker is already injected — fill the hidden field and
      // let it keep control of the UI.
      var t = document.getElementById('oapBirthdate')
        || document.querySelector('input[name="OAPBIRTHDATE"]')
        || document.querySelector('input[name="oapBirthdate"]');
      if (t) {
        t.value = parseInt(day) + '-' + monthAbbr + '-' + year;
        t.dispatchEvent(new Event('input', { bubbles: true }));
        t.dispatchEvent(new Event('change', { bubbles: true }));
      }
      return;
    }

    // Find the original date field
    var target = document.getElementById('oapBirthdate')
      || document.querySelector('input[name="OAPBIRTHDATE"]')
      || document.querySelector('input[name="oapBirthdate"]')
      || document.querySelector('input[id*="birth" i], input[id*="Birth" i]');

    if (!target) {
      console.log('No target date field found for custom picker');
      return;
    }

    target.style.display = 'none';

    var wrapper = document.createElement('div');
    wrapper.id = 'ssa-date-picker';
    wrapper.style.cssText = 'display:inline-flex;gap:8px;align-items:flex-end;margin:8px 0;';

    function makeSelect(label, options, selected, widthPx) {
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
      placeholder.selected = !selected;
      sel.appendChild(placeholder);
      options.forEach(function(opt) {
        var o = document.createElement('option');
        o.value = opt;
        o.textContent = opt;
        if (opt === selected) o.selected = true;
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

    var dayPart = makeSelect('DD', days, String(day), 60);
    var monthPart = makeSelect('MON', monthNames, monthAbbr, 80);
    var yearPart = makeSelect('YYYY', years, year, 100);

    function updateDob() {
      var d = dayPart.select.value;
      var m = monthPart.select.value;
      var y = yearPart.select.value;
      if (d && m && y && monthMap[m]) {
        var formatted = parseInt(d) + '-' + m + '-' + y;
        target.value = formatted;
        target.dispatchEvent(new Event('input', { bubbles: true }));
        target.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('Date set to:', formatted);
      }
    }

    dayPart.select.addEventListener('change', updateDob);
    monthPart.select.addEventListener('change', updateDob);
    yearPart.select.addEventListener('change', updateDob);

    wrapper.appendChild(dayPart.div);
    wrapper.appendChild(monthPart.div);
    wrapper.appendChild(yearPart.div);

    var insertAfter = target;
    var customWrapper = document.getElementById('custom-date-wrapper');
    if (customWrapper) insertAfter = customWrapper;
    insertAfter.parentNode.insertBefore(wrapper, insertAfter.nextSibling);

    target.value = parseInt(day) + '-' + monthAbbr + '-' + year;
    target.dispatchEvent(new Event('input', { bubbles: true }));
    target.dispatchEvent(new Event('change', { bubbles: true }));

    console.log('Date picker injected: ' + parseInt(day) + '-' + monthAbbr + '-' + year);
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
    //    citizenshipShortCode → the 2-letter LOV *code* (short code) when known,
    //      falling back to the description when no short code is mapped.
    citizenshipCodeValue: (function() {
                            var nat = (gv('demographic.nationality') || '').toLowerCase();
                            var idn = (gv('personal.idNumber') || '').trim();
                            var sa = (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) || idn.length >= 13;
                            // Long LOV description
                            return sa ? 'OTHER AFRICAN COUNTRIES' : (gv('demographic.citizenshipDescription') || gv('demographic.nationality') || '');
                          })(),
    citizenshipShortCode: (function() {
                            var nat = (gv('demographic.nationality') || '').toLowerCase();
                            var idn = (gv('personal.idNumber') || '').trim();
                            var sa = (nat.indexOf('south') !== -1 && nat.indexOf('african') !== -1) || idn.length >= 13;
                            // Short 2-letter code for SA; fall back to whichever is set
                            if (sa) return 'OA';
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
    var idEl = document.getElementById('oapIdNumber')
      || document.querySelector('input[name="OAPIDNUMBER"]')
      || document.querySelector('input[name="oapIdNumber"]')
      || document.querySelector('input[id*="id" i]');
    if (idEl && idEl.value) {
      idEl.dispatchEvent(new Event('blur', { bubbles: true }));
      console.log('✅ Blur fired on ID number field');
    }

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

  // Expand a truncated ITS procedure name: gw1v -> gw1view, gw1p -> gw1proc.
  function expandProc(u) {
    if (typeof u !== 'string') return u;
    var marker = 'gen.gw1pkg.gw1';
    var i = u.indexOf(marker);
    if (i === -1) return u;
    var restStart = i + marker.length;
    var rest = u.substring(restStart);
    var q = rest.indexOf('?');
    var sl = rest.indexOf('/');
    var cut = -1;
    if (q === -1 && sl === -1) { cut = rest.length; }
    else if (q !== -1 && (sl === -1 || q < sl)) { cut = q; }
    else { cut = sl; }
    var proc = rest.substring(0, cut);
    var tail = rest.substring(cut);
    if (proc === 'v') return u.substring(0, restStart) + 'view' + tail;
    if (proc === 'p') return u.substring(0, restStart) + 'proc' + tail;
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
  function fixAction(form, log) {
    if (!form || form.tagName !== 'FORM') return;
    var before = form.getAttribute('action') || '';
    var after = fixUrl(before);
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
      'OTHER AFRICAN COUNTRIES','R.S.A.','RWANDA','SENEGAL','SEYCHELLES','SIERRA LEONE',
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

  // Full calendar date picker replacing the ITS calendar-button field.
  function ssaDatePicker() {
    if (document.getElementById('ssa-date-picker') || document.getElementById('custom-date-wrapper')) return;
    var dob = document.getElementById('oapBirthdate')
      || document.querySelector('input[name="oapBirthdate"]')
      || document.querySelector('input[name="OAPBIRTHDATE"]')
      || document.querySelector('input[name="P_DATE_OF_BIRTH"]')
      || document.querySelector('input[id*="birth" i], input[id*="Birth" i]');
    if (!dob) return;

    var MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

    function parseDob(v) {
      var t = (v || '').trim();
      if (!t) return { d: null, mo: null, y: null };
      var m = /^(\\d{1,2})\\s*[-/]\\s*([A-Za-z]{3,9})\\s*[-/]\\s*(\\d{4})\$/.exec(t);
      if (m) {
        var mo = MONTHS.indexOf(m[2].toUpperCase());
        return { d: parseInt(m[1]), mo: mo >= 0 ? mo : 0, y: parseInt(m[3]) };
      }
      var n = /^(\\d{1,2})\\s*[-/]\\s*(\\d{1,2})\\s*[-/]\\s*(\\d{4})\$/.exec(t);
      if (n) return { d: parseInt(n[1]), mo: parseInt(n[2]) - 1, y: parseInt(n[3]) };
      var s = /^(\\d{4})\\s*[-/]\\s*(\\d{1,2})\\s*[-/]\\s*(\\d{1,2})\$/.exec(t);
      if (s) return { d: parseInt(s[3]), mo: parseInt(s[2]) - 1, y: parseInt(s[1]) };
      return { d: null, mo: null, y: null };
    }

    var cur = parseDob(dob.value);
    var view = { y: cur.y || 1990, mo: cur.mo || 0 };

    dob.style.display = 'none';
    var row = dob.closest('div') || dob.parentElement;
    if (row) {
      var calBtns = row.querySelectorAll('a[onclick*="cal"], img[src*="cal"], button, input[type="image"]');
      for (var i = 0; i < calBtns.length; i++) {
        var el = calBtns[i];
        if (!el.contains(dob) && el !== dob) el.style.display = 'none';
      }
    }

    var wrap = document.createElement('div');
    wrap.id = 'ssa-date-picker';
    wrap.style.cssText = 'display:inline-flex;gap:6px;align-items:center;font-family:Arial,sans-serif;';

    var show = document.createElement('input');
    show.type = 'text';
    show.readOnly = true;
    show.placeholder = 'DD-MON-YYYY';
    show.style.cssText = 'width:150px;padding:10px;font-size:17px;border:1px solid #7C3AED;border-radius:6px;text-align:center;font-family:monospace;background:#fff;color:#0F1624;';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = '📅';
    btn.style.cssText = 'padding:8px 12px;font-size:17px;border:1px solid #7C3AED;border-radius:6px;background:#fff;cursor:pointer;';

    wrap.appendChild(show);
    wrap.appendChild(btn);

    var cal = document.createElement('div');
    cal.style.cssText = 'position:fixed;z-index:2147483647;background:#fff;border:1px solid #bbb;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,0.28);padding:12px;width:286px;font-family:Arial,sans-serif;display:none;';

    var head = document.createElement('div');
    head.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;';
    var prev = document.createElement('button');
    prev.type = 'button'; prev.textContent = '‹'; prev.style.cssText = 'padding:4px 10px;font-size:16px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;';
    var title = document.createElement('div');
    title.style.cssText = 'font-weight:bold;font-size:15px;';
    var next = document.createElement('button');
    next.type = 'button'; next.textContent = '›'; next.style.cssText = 'padding:4px 10px;font-size:16px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;';
    head.appendChild(prev); head.appendChild(title); head.appendChild(next);
    cal.appendChild(head);

    var grid = document.createElement('div');
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(7,1fr);gap:2px;text-align:center;font-size:13px;';
    cal.appendChild(grid);

    var foot = document.createElement('div');
    foot.style.cssText = 'display:flex;justify-content:space-between;margin-top:8px;';
    var todayBtn = document.createElement('button');
    todayBtn.type = 'button'; todayBtn.textContent = 'Today';
    todayBtn.style.cssText = 'padding:6px 12px;font-size:13px;border:1px solid #7C3AED;border-radius:4px;background:#7C3AED;color:#fff;cursor:pointer;';
    var closeBtn = document.createElement('button');
    closeBtn.type = 'button'; closeBtn.textContent = 'Close';
    closeBtn.style.cssText = 'padding:6px 12px;font-size:13px;border:1px solid #ccc;border-radius:4px;background:#fff;cursor:pointer;';
    foot.appendChild(todayBtn); foot.appendChild(closeBtn);
    cal.appendChild(foot);

    document.body.appendChild(cal);

    function fmt() {
      return cur.d ? cur.d + '-' + MONTHS[cur.mo] + '-' + cur.y : '';
    }

    function apply() {
      var val = fmt();
      dob.value = val;
      dob.removeAttribute('readonly');
      dob.removeAttribute('disabled');
      ['input','change','blur'].forEach(function(ev) {
        dob.dispatchEvent(new Event(ev, { bubbles: true }));
      });
      show.value = val;
      console.log('Date set to: ' + val);
    }

    function render() {
      var first = new Date(view.y, view.mo, 1).getDay();
      var daysIn = new Date(view.y, view.mo + 1, 0).getDate();
      title.textContent = MONTHS[view.mo] + ' ' + view.y;
      grid.innerHTML = '';
      ['S','M','T','W','T','F','S'].forEach(function(d) {
        var h = document.createElement('div');
        h.textContent = d;
        h.style.cssText = 'font-weight:bold;color:#7C3AED;padding:4px 0;font-size:12px;';
        grid.appendChild(h);
      });
      for (var i = 0; i < first; i++) grid.appendChild(document.createElement('div'));
      for (var d = 1; d <= daysIn; d++) {
        var cell = document.createElement('div');
        cell.textContent = d;
        cell.style.cssText = 'padding:7px 0;border-radius:6px;cursor:pointer;color:#0F1624;';
        if (d === cur.d && view.mo === cur.mo && view.y === cur.y) {
          cell.style.background = '#7C3AED'; cell.style.color = '#fff';
        }
        cell.onclick = (function(dd) {
          return function() {
            cur = { d: dd, mo: view.mo, y: view.y };
            apply();
            cal.style.display = 'none';
          };
        })(d);
        grid.appendChild(cell);
      }
    }

    function open() {
      view = { y: cur.y || 1990, mo: cur.mo || 0 };
      render();
      var r = btn.getBoundingClientRect();
      var left = Math.max(8, Math.min(window.innerWidth - 300, r.left));
      var top = r.bottom + 8;
      if (top + 340 > window.innerHeight) top = Math.max(8, r.top - 340);
      cal.style.left = left + 'px';
      cal.style.top = top + 'px';
      cal.style.display = 'block';
    }

    btn.onclick = function(e) {
      e.stopPropagation();
      if (cal.style.display === 'none') open(); else cal.style.display = 'none';
    };
    prev.onclick = function() { view.mo--; if (view.mo < 0) { view.mo = 11; view.y--; } render(); };
    next.onclick = function() { view.mo++; if (view.mo > 11) { view.mo = 0; view.y++; } render(); };
    todayBtn.onclick = function() {
      var n = new Date();
      cur = { d: n.getDate(), mo: n.getMonth(), y: n.getFullYear() };
      apply();
      cal.style.display = 'none';
    };
    closeBtn.onclick = function() { cal.style.display = 'none'; };
    document.addEventListener('click', function(e) {
      if (cal.style.display !== 'none' && e.target !== btn && !cal.contains(e.target)) {
        cal.style.display = 'none';
      }
    });

    // Keep the picker display in sync if the field value changes elsewhere
    // (e.g. the star autofill writing the hidden field).
    dob.addEventListener('change', function() {
      var p = parseDob(dob.value);
      if (p) { cur = p; show.value = fmt(); }
    });

    show.value = fmt();
    dob.parentNode.insertBefore(wrap, dob.nextSibling);
    console.log('Custom date picker injected');
  }

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
    ssaDatePicker();
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

  diag('Page: ' + window.location.href);
  diag('NavFix injected');

  ssaEnhance();
  setTimeout(ssaEnhance, 800);
  setTimeout(ssaEnhance, 2500);
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

