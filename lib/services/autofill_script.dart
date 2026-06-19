String buildAutofillScript(String profileJson) {
  return '''
(function() {
  var profile = $profileJson;

  // ── Field mapping ──────────────────────────────────────────────
  var fieldMap = {
    'title':          ['title', 'salutation'],
    'firstName':      ['firstname', 'first_name', 'fname', 'name', 'initials', 'names'],
    'lastName':       ['lastname', 'last_name', 'lname', 'surname', 'family_name'],
    'initials':       ['initials'],
    'gender':         ['gender', 'sex'],
    'idNumber':       ['idnumber', 'id_number', 'id', 'identity_number', 'national_id', 'sa_id', 'passport_number', 'rsa_id'],
    'dateOfBirth':    ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday'],
    'email':          ['email', 'e-mail', 'emailaddress', 'email_address'],
    'phone':          ['phone', 'telephone', 'tel', 'cell', 'cellphone', 'mobile', 'mobile_number', 'contact_no', 'phone_number'],
    'workPhone':      ['workphone', 'work_phone', 'telephone_work', 'tel_work'],
    'address':        ['address', 'street', 'physical_address', 'residential_address'],
    'addressLine2':   ['address2', 'address_line2', 'suburb', 'town', 'city'],
    'province':       ['province', 'state', 'region'],
    'postalCode':     ['postalcode', 'postal_code', 'postcode', 'zip', 'zipcode', 'code'],
    'nationality':    ['nationality', 'citizenship', 'citizen', 'country'],
    'homeLanguage':   ['homelanguage', 'home_language', 'language', 'first_language'],
    'populationGroup':['populationgroup', 'population_group', 'race', 'ethnicity'],
    'maritalStatus':  ['maritalstatus', 'marital_status'],
    'schoolName':     ['school', 'schoolname', 'school_name', 'highschool', 'high_school', 'institution'],
    'currentGrade':   ['grade', 'current_grade', 'grade12', 'matric'],
    'matricYear':     ['matricyear', 'year_of_matric', 'year', 'examination_year'],
    'matricType':     ['matrictype', 'matric_type', 'exam_type', 'examination_type'],
    'examinationNumber':['examinationnumber', 'exam_number', 'candidate_number'],
    'applicationLevel':['applicationlevel', 'level_of_study', 'study_level', 'application_type'],
    'faculty':        ['faculty', 'faculty_choice'],
    'programme':      ['programme', 'course', 'program', 'qualification', 'course_choice', 'study_programme'],
    'academicYear':   ['academicyear', 'academic_year', 'year_of_study', 'study_year'],
    'studyMode':      ['studymode', 'study_mode', 'mode_of_study', 'attendance_mode', 'fulltime_parttime'],
    'nextOfKinName':  ['nextofkin_name', 'nextofkin', 'guardian_name', 'parent_name', 'parentguardian'],
    'nextOfKinPhone': ['nextofkin_phone', 'guardian_phone', 'parent_phone', 'emergency_contact'],
    'nextOfKinEmail': ['nextofkin_email', 'guardian_email', 'parent_email'],
  };

  // ── Helper: get a value from nested profile ────────────────────
  function getVal(path) {
    var parts = path.split('.');
    var obj = profile;
    for (var i = 0; i < parts.length; i++) {
      if (!obj) return '';
      obj = obj[parts[i]];
    }
    return (obj != null ? String(obj) : '');
  }

  var valueSources = {
    'title':          getVal('personal.title'),
    'firstName':      getVal('personal.firstName'),
    'lastName':       getVal('personal.lastName'),
    'initials':       getVal('personal.initials'),
    'gender':         getVal('personal.gender'),
    'idNumber':       getVal('personal.idNumber'),
    'dateOfBirth':    getVal('personal.dateOfBirth'),
    'email':          getVal('contact.email'),
    'phone':          getVal('contact.phone'),
    'workPhone':      getVal('contact.workPhone'),
    'address':        getVal('address.address'),
    'addressLine2':   getVal('address.addressLine2'),
    'province':       getVal('address.province'),
    'postalCode':     getVal('address.postalCode'),
    'nationality':    getVal('demographic.nationality'),
    'homeLanguage':   getVal('demographic.homeLanguage'),
    'populationGroup':getVal('demographic.populationGroup'),
    'maritalStatus':  getVal('demographic.maritalStatus'),
    'schoolName':     getVal('school.schoolName'),
    'currentGrade':   getVal('school.currentGrade'),
    'matricYear':     getVal('results.matricYear'),
    'matricType':     getVal('results.matricType'),
    'examinationNumber': getVal('results.examinationNumber'),
    'applicationLevel': getVal('results.applicationLevel'),
    'faculty':        getVal('qualification.choices[0].faculty'),
    'programme':      getVal('qualification.choices[0].programme'),
    'academicYear':   getVal('qualification.academicYear'),
    'studyMode':      getVal('qualification.studyMode'),
    'nextOfKinName':  getVal('nextOfKin.name'),
    'nextOfKinPhone': getVal('nextOfKin.mobilePhone'),
    'nextOfKinEmail': getVal('nextOfKin.email'),
  };

  // ── Create the Star ────────────────────────────────────────────
  var old = document.getElementById('ssa-star');
  if (old) old.remove();

  var star = document.createElement('div');
  star.id = 'ssa-star';
  star.innerHTML = '★';
  star.style.cssText = 'position:fixed;bottom:24px;right:24px;width:60px;height:60px;background:#0F1624;border-radius:50%;z-index:999999;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(124,58,237,0.5);border:2px solid #7C3AED;color:#FFD700;font-size:40px;font-family:Arial,sans-serif;transition:transform 0.2s;';
  star.onmouseenter = function() { star.style.transform = 'scale(1.1)'; };
  star.onmouseleave  = function() { star.style.transform = 'scale(1)'; };

  // ── Toast helper ───────────────────────────────────────────────
  function showToast(msg, color) {
    var t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:100px;right:24px;padding:12px 20px;background:' + (color || '#10B981') + ';color:#fff;border-radius:10px;z-index:9999999;font-family:Arial,sans-serif;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,0.3);transition:opacity 0.3s;';
    document.body.appendChild(t);
    setTimeout(function() { t.style.opacity = '0'; setTimeout(function() { t.remove(); }, 300); }, 2500);
  }

  star.onclick = function() {
    // ── Attempt autofill ────────────────────────────────────────
    var inputs = document.querySelectorAll('input, select, textarea');
    var filled = 0;
    var suggestions = [];

    for (var i = 0; i < inputs.length; i++) {
      var inp = inputs[i];
      if (inp.readOnly || inp.disabled) continue;
      var elName = (inp.name + ' ' + inp.id + ' ' + (inp.placeholder || '') + ' ' + (inp.getAttribute('aria-label') || '')).toLowerCase().replace(/[_\-]/g, '');

      // Find label text
      var label = '';
      if (inp.labels && inp.labels.length) {
        label = inp.labels[0].textContent.toLowerCase();
      }
      var allText = elName + ' ' + label;
      var bestKey = null;
      var bestScore = 0;

      for (var key in fieldMap) {
        var aliases = fieldMap[key];
        for (var j = 0; j < aliases.length; j++) {
          var alias = aliases[j];
          if (allText.indexOf(alias) !== -1) {
            var score = alias.length;
            if (label.indexOf(alias) !== -1) score += 5;
            if (elName.indexOf(alias) !== -1) score += 3;
            if (score > bestScore) {
              bestScore = score;
              bestKey = key;
            }
            break;
          }
        }
      }

      if (bestKey && valueSources[bestKey]) {
        var val = valueSources[bestKey];
        if (inp.tagName === 'SELECT') {
          // Try matching option text first, then value
          var matched = false;
          for (var k = 0; k < inp.options.length; k++) {
            var opt = inp.options[k];
            if (opt.text.toLowerCase().indexOf(val.toLowerCase()) !== -1 || opt.value.toLowerCase().indexOf(val.toLowerCase()) !== -1) {
              inp.value = opt.value;
              matched = true;
              break;
            }
          }
          if (matched) filled++;
        } else {
          inp.value = val;
          filled++;
        }
        inp.dispatchEvent(new Event('input', {bubbles: true}));
        inp.dispatchEvent(new Event('change', {bubbles: true}));
        inp.dispatchEvent(new Event('blur', {bubbles: true}));
        inp.style.borderColor = '#10B981';
        inp.style.outline = '2px solid #10B981';
      }
    }

    showToast(filled > 0 ? '✅ Filled ' + filled + ' field' + (filled > 1 ? 's' : '') + '!' : 'No fields matched. Tap ★ to try again after entering text.', filled > 0 ? '#10B981' : '#EF4444');
  };

  document.body.appendChild(star);
})();
''';
}
