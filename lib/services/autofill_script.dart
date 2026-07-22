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
    'OAPGENDER':              vs.genderCode,
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
    province:          ['province','state','region','select province'],
    postalCode:        ['postal code','postalcode','post code','postcode','zip'],
    nationality:       ['nationality','citizenship','citizen'],
    isSACitizen:       ['sa citizen','possession of','valid sa','sa id'],
    homeLanguage:      ['home language','homelanguage','language'],
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
    var wlWords = wl.split(/\s+/);
    var best = null, bestScore = -1;
    for (var i = 0; i < sel.options.length; i++) {
      var opt = sel.options[i];
      if (isPlaceholder(opt.text)) continue;
      var tl = opt.text.toLowerCase().trim();
      var vl = opt.value.toLowerCase().trim();
      var tlWords = tl.split(/\s+/);
      var vlWords = vl.split(/\s+/);
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

    // ── Handle Select2 AJAX dropdowns (Race, Province) ─────────────────────
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

    showToast(
      filled > 0
        ? '✅ Filled ' + filled + ' field' + (filled !== 1 ? 's' : '') + '!'
        : 'No fields matched. Try scrolling to the next section.',
      filled > 0 ? '#10B981' : '#EF4444'
    );

    var visibleTotal = 0;
    for (var ti = 0; ti < inputs.length; ti++) {
      if (inputs[ti].offsetParent !== null) visibleTotal++;
    }

    try { AutofillResult.postMessage(JSON.stringify({ filled: filled, total: visibleTotal })); } catch (e) {}
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
