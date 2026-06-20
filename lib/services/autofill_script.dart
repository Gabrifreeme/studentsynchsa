String buildAutofillScript(String profileJson) {
  return '''
(function() {
  var profile = $profileJson;

  // ── Field mapping ──────────────────────────────────────────────
  var fieldMap = {
    'title':          ['title', 'salutation'],
    'firstName':      ['firstname', 'first_name', 'fname'],
    'lastName':       ['lastname', 'last_name', 'lname', 'surname', 'family_name'],
    'initials':       ['initials'],
    'gender':         ['gender', 'sex'],
    'idNumber':       ['idnumber', 'id_number', 'identity_number', 'national_id', 'sa_id', 'passport_number', 'rsa_id'],
    'dateOfBirth':    ['dateofbirth', 'date_of_birth', 'dob', 'birthdate', 'birth_date', 'birthday'],
    'email':          ['email', 'e-mail', 'emailaddress', 'email_address'],
    'phone':          ['phone', 'telephone', 'tel', 'cell', 'cellphone', 'mobile', 'mobile_number', 'contact_no', 'phone_number'],
    'workPhone':      ['workphone', 'work_phone', 'telephone_work', 'tel_work'],
    'address':        ['address', 'street', 'physical_address', 'residential_address'],
    'addressLine2':   ['address2', 'address_line2', 'suburb', 'town', 'city'],
    'province':       ['province', 'state', 'region'],
    'postalCode':     ['postalcode', 'postal_code', 'postcode', 'zip', 'zipcode', 'code'],
    'nationality':    ['nationality', 'citizenship', 'citizen', 'country', 'sa citizen', 'south african'],
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

  function getVal(path) {
    var parts = path.split('.');
    var obj = profile;
    for (var i = 0; i < parts.length; i++) {
      if (!obj) return '';
      obj = obj[parts[i]];
    }
    return (obj != null ? String(obj) : '');
  }

  function fmtDate(iso) {
    if (!iso || iso.length < 10) return iso;
    var months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    var p = iso.split('T')[0].split('-');
    var m = parseInt(p[1], 10) - 1;
    return (m >= 0 && m < 12) ? p[2] + '-' + months[m] + '-' + p[0] : iso;
  }

  var valueSources = {
    'title':          getVal('personal.title'),
    'firstName':      getVal('personal.firstName'),
    'lastName':       getVal('personal.lastName'),
    'initials':       getVal('personal.initials'),
    'gender':         getVal('personal.gender'),
    'idNumber':       getVal('personal.idNumber'),
    'dateOfBirth':    fmtDate(getVal('personal.dateOfBirth')),
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

  function showToast(msg, color) {
    var t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'position:fixed;bottom:100px;right:24px;padding:12px 20px;background:' + (color || '#10B981') + ';color:#fff;border-radius:10px;z-index:9999999;font-family:Arial,sans-serif;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,0.3);transition:opacity 0.3s;';
    document.body.appendChild(t);
    setTimeout(function() { t.style.opacity = '0'; setTimeout(function() { t.remove(); }, 300); }, 2500);
  }

  function isPlaceholder(text) {
    var t = text.toLowerCase().trim();
    return t === '' || t === 'select' || t === 'choose' || t.indexOf('select...') === 0 || t.indexOf('choose...') === 0 || t.indexOf('--') !== -1 || t === 'please select';
  }

  function isYes(text) {
    var t = text.toLowerCase().trim();
    return t === 'yes' || t === 'y' || t === 'true' || t === '1' || t === 'sa citizen' || t === 'south african' || t === 'rsa';
  }

  function isNo(text) {
    var t = text.toLowerCase().trim();
    return t === 'no' || t === 'n' || t === 'false' || t === '0' || t === 'other';
  }

  function getSearchTerms(vl) {
    var terms = [vl];
    if (vl === 'sa citizen' || vl === 'south african' || vl === 'south africa' || vl === 'sa' || vl === 'rsa') {
      terms.push('south african', 'south africa', 'sa citizen', 'sa', 'rsa', 'other african countries');
    }
    if (vl.indexOf('male') !== -1 || vl.indexOf('female') !== -1) {
      terms.push('male', 'female');
    }
    return terms;
  }

  function findOption(sel, rawVal) {
    var vl = rawVal.toLowerCase().trim();
    var terms = getSearchTerms(vl);
    var bestOpt = null, bestScore = -1;
    for (var t = 0; t < terms.length; t++) {
      var term = terms[t];
      var tl = term.toLowerCase().trim();
      var tWords = tl.split(/\\s+/);
      for (var k = 0; k < sel.options.length; k++) {
        var opt = sel.options[k];
        if (isPlaceholder(opt.text)) continue;
        var tt = opt.text.toLowerCase().trim();
        var vv = opt.value.toLowerCase().trim();
        var score = -1;
        if (tt === tl || vv === tl) score = 100;
        else if (tt.startsWith(tl) || vv.startsWith(tl)) score = 50;
        else if (tt.indexOf(tl) !== -1 || vv.indexOf(tl) !== -1) score = 30;
        else if (tl.indexOf(tt) !== -1 || tl.indexOf(vv) !== -1) score = 20;
        else { for (var w = 0; w < tWords.length; w++) { if (tWords[w].length > 1 && (tt.indexOf(tWords[w]) !== -1 || vv.indexOf(tWords[w]) !== -1)) { score = 10; break; } } }
        if (score > bestScore) { bestScore = score; bestOpt = opt; }
      }
    }
    return bestOpt;
  }

  function dispatchAll(inp) {
    inp.dispatchEvent(new Event('input', {bubbles: true}));
    inp.dispatchEvent(new Event('change', {bubbles: true}));
    inp.dispatchEvent(new Event('select', {bubbles: true}));
    inp.dispatchEvent(new Event('blur', {bubbles: true}));
    if (inp.form) inp.form.dispatchEvent(new Event('change', {bubbles: true}));
  }

  function doAutofill() {
    var hasData = valueSources['firstName'] || valueSources['lastName'] || valueSources['email'];
    if (!hasData) {
      showToast('No profile data found. Go to Dashboard first.', '#EF4444');
      return;
    }
    var inputs = document.querySelectorAll('input, select, textarea');
    var filled = 0;
    var retrySelects = [];
    for (var i = 0; i < inputs.length; i++) {
      var inp = inputs[i];
      if (inp.readOnly || inp.disabled) continue;
      var elName = (inp.name + ' ' + inp.id + ' ' + (inp.placeholder || '') + ' ' + (inp.getAttribute('aria-label') || '') + ' ' + (inp.getAttribute('title') || '')).toLowerCase().replace(/[_-]/g, '').trim();
      var label = '';
      if (inp.labels && inp.labels.length) label = inp.labels[0].textContent.toLowerCase().trim();
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
            if (score > bestScore) { bestScore = score; bestKey = key; }
            break;
          }
        }
      }
      if (inp.tagName === 'SELECT' || inp.type === 'select-one') {
        inp.dispatchEvent(new Event('focus', {bubbles: true}));
        var hasYes = false, hasNo = false;
        for (var k = 0; k < inp.options.length; k++) {
          if (isPlaceholder(inp.options[k].text) && k === 0) continue;
          if (isYes(inp.options[k].text)) hasYes = true;
          if (isNo(inp.options[k].text)) hasNo = true;
        }
        if (hasYes && hasNo) {
          for (var k = 0; k < inp.options.length; k++) {
            if (isPlaceholder(inp.options[k].text)) continue;
            if (isYes(inp.options[k].text)) { inp.value = inp.options[k].value; filled++; dispatchAll(inp); inp.style.outline = '2px solid #10B981'; break; }
          }
          continue;
        }
      }
      if (bestKey && valueSources[bestKey]) {
        var val = valueSources[bestKey];
        var didFill = false;
        if (inp.tagName === 'SELECT' || inp.type === 'select-one') {
          var bestOpt = findOption(inp, val);
          if (bestOpt) { inp.value = bestOpt.value; didFill = true; }
          if (!didFill && inp.options.length <= 30) {
            retrySelects.push({el: inp, vl: val});
            for (var k = 1; k < inp.options.length; k++) {
              if (!isPlaceholder(inp.options[k].text) && inp.options[k].value) { inp.value = inp.options[k].value; didFill = true; break; }
            }
          }
        } else {
          inp.value = val;
          didFill = true;
        }
        if (didFill) { filled++; dispatchAll(inp); inp.style.outline = '2px solid #10B981'; }
      }
    }
    if (retrySelects.length) {
      var doRetry = function() {
        for (var r = 0; r < retrySelects.length; r++) {
          var rs = retrySelects[r];
          var inp = rs.el, vl = rs.vl;
          inp.dispatchEvent(new Event('focus', {bubbles: true}));
          var bestOpt = findOption(inp, vl);
          if (bestOpt) { inp.value = bestOpt.value; filled++; dispatchAll(inp); inp.style.outline = '2px solid #10B981'; }
        }
        // Re-scan for dynamically-added elements
        var newInputs = document.querySelectorAll('input, select, textarea');
        for (var n = 0; n < newInputs.length; n++) {
          var ni = newInputs[n];
          if (ni.readOnly || ni.disabled || ni.style.outline) continue;
          var elName = (ni.name + ' ' + ni.id + ' ' + (ni.placeholder || '') + ' ' + (ni.getAttribute('aria-label') || '') + ' ' + (ni.getAttribute('title') || '')).toLowerCase().replace(/[_-]/g, '').trim();
          var label = '';
          if (ni.labels && ni.labels.length) label = ni.labels[0].textContent.toLowerCase().trim();
          var allText = elName + ' ' + label;
          var bestKey = null, bestScore = 0;
          for (var key in fieldMap) {
            var aliases = fieldMap[key];
            for (var j = 0; j < aliases.length; j++) {
              var alias = aliases[j];
              if (allText.indexOf(alias) !== -1) {
                var score = alias.length;
                if (label.indexOf(alias) !== -1) score += 5;
                if (elName.indexOf(alias) !== -1) score += 3;
                if (score > bestScore) { bestScore = score; bestKey = key; }
                break;
              }
            }
          }
          if (bestKey && valueSources[bestKey]) {
            var v = valueSources[bestKey];
            if (ni.tagName === 'SELECT' || ni.type === 'select-one') {
              ni.dispatchEvent(new Event('focus', {bubbles: true}));
              var bo = findOption(ni, v);
              if (bo) { ni.value = bo.value; filled++; dispatchAll(ni); ni.style.outline = '2px solid #10B981'; }
            } else {
              ni.value = v; filled++; dispatchAll(ni); ni.style.outline = '2px solid #10B981';
            }
          }
        }
      };
      setTimeout(doRetry, 800);
      setTimeout(doRetry, 2500);
    }
    showToast(filled > 0 ? '✅ Filled ' + filled + ' field' + (filled > 1 ? 's' : '') + '!' : 'No fields matched.', filled > 0 ? '#10B981' : '#EF4444');
  }

  // Create floating Star as a convenience
  function createStar() {
    var old = document.getElementById('ssa-star');
    if (old) return old;
    var star = document.createElement('div');
    star.id = 'ssa-star';
    star.innerHTML = '★';
    star.style.cssText = 'position:fixed;bottom:24px;right:24px;width:60px;height:60px;background:#0F1624;border-radius:50%;z-index:999999;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(124,58,237,0.5);border:2px solid #7C3AED;color:#FFD700;font-size:40px;font-family:Arial,sans-serif;transition:transform 0.2s;';
    star.onclick = doAutofill;
    document.body.appendChild(star);
    return star;
  }
  function tryCreate() { if (document.body) { createStar(); } else { setTimeout(tryCreate, 500); } }
  tryCreate();
})();
''';
}

String buildAutofillOnlyScript(String profileJson) {
  return '''
(function() {
  try {
  (function(){var d=document.createElement('div');d.textContent='+';d.style.cssText='position:fixed;top:4px;left:4px;padding:4px 8px;background:#10B981;color:#fff;z-index:9999999;font-family:Arial;font-size:12px;border-radius:4px;';document.body.appendChild(d);setTimeout(function(){d.remove();},999999);})();
  var profile = $profileJson;
  var fieldMap = {
    'title':['title','salutation'],    'firstName':['firstname','first_name','fname'],
    'lastName':['lastname','last_name','lname','surname','family_name'],'initials':['initials'],
    'gender':['gender','sex'],'idNumber':['idnumber','id_number','identity_number','national_id','sa_id','passport_number','rsa_id'],
    'dateOfBirth':['dateofbirth','date_of_birth','dob','birthdate','birth_date','birthday'],
    'email':['email','e-mail','emailaddress','email_address'],'phone':['phone','telephone','tel','cell','cellphone','mobile','mobile_number','contact_no','phone_number'],
    'workPhone':['workphone','work_phone','telephone_work','tel_work'],'address':['address','street','physical_address','residential_address'],
    'addressLine2':['address2','address_line2','suburb','town','city'],'province':['province','state','region'],
    'postalCode':['postalcode','postal_code','postcode','zip','zipcode','code'],'nationality':['nationality','citizenship','citizen','country','sa citizen','south african'],
    'homeLanguage':['homelanguage','home_language','language','first_language'],'populationGroup':['populationgroup','population_group','race','ethnicity'],
    'maritalStatus':['maritalstatus','marital_status'],'schoolName':['school','schoolname','school_name','highschool','high_school','institution'],
    'currentGrade':['grade','current_grade','grade12','matric'],'matricYear':['matricyear','year_of_matric','year','examination_year'],
    'matricType':['matrictype','matric_type','exam_type','examination_type'],'examinationNumber':['examinationnumber','exam_number','candidate_number'],
    'applicationLevel':['applicationlevel','level_of_study','study_level','application_type'],'faculty':['faculty','faculty_choice'],
    'programme':['programme','course','program','qualification','course_choice','study_programme'],'academicYear':['academicyear','academic_year','year_of_study','study_year'],
    'studyMode':['studymode','study_mode','mode_of_study','attendance_mode','fulltime_parttime'],'nextOfKinName':['nextofkin_name','nextofkin','guardian_name','parent_name','parentguardian'],
    'nextOfKinPhone':['nextofkin_phone','guardian_phone','parent_phone','emergency_contact'],'nextOfKinEmail':['nextofkin_email','guardian_email','parent_email']
  };
  function g(p){var o=profile;for(var i=0;i<p.split('.').length;i++){if(!o)return'';o=o[p.split('.')[i]];}return o!=null?String(o):'';}
  function d(i){if(!i||i.length<10)return i;var m=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];var p=i.split('T')[0].split('-');var n=parseInt(p[1],10)-1;return(n>=0&&n<12)?p[2]+'-'+m[n]+'-'+p[0]:i;}
  var vs={'title':g('personal.title'),'firstName':g('personal.firstName'),'lastName':g('personal.lastName'),'initials':g('personal.initials'),'gender':g('personal.gender'),'idNumber':g('personal.idNumber'),'dateOfBirth':d(g('personal.dateOfBirth')),'email':g('contact.email'),'phone':g('contact.phone'),'workPhone':g('contact.workPhone'),'address':g('address.address'),'addressLine2':g('address.addressLine2'),'province':g('address.province'),'postalCode':g('address.postalCode'),'nationality':g('demographic.nationality'),'homeLanguage':g('demographic.homeLanguage'),'populationGroup':g('demographic.populationGroup'),'maritalStatus':g('demographic.maritalStatus'),'schoolName':g('school.schoolName'),'currentGrade':g('school.currentGrade'),'matricYear':g('results.matricYear'),'matricType':g('results.matricType'),'examinationNumber':g('results.examinationNumber'),'applicationLevel':g('results.applicationLevel'),'faculty':g('qualification.choices[0].faculty'),'programme':g('qualification.choices[0].programme'),'academicYear':g('qualification.academicYear'),'studyMode':g('qualification.studyMode'),'nextOfKinName':g('nextOfKin.name'),'nextOfKinPhone':g('nextOfKin.mobilePhone'),'nextOfKinEmail':g('nextOfKin.email')};
  function t(m,c){var e=document.createElement('div');e.textContent=m;e.style.cssText='position:fixed;bottom:100px;right:24px;padding:12px 20px;background:'+(c||'#10B981')+';color:#fff;border-radius:10px;z-index:9999999;font-family:Arial,sans-serif;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,0.3);';document.body.appendChild(e);setTimeout(function(){e.style.opacity='0';setTimeout(function(){e.remove();},300);},2500);}
  function ip(t){var s=t.toLowerCase().trim();return s===''||s==='select'||s==='choose'||s.indexOf('select...')===0||s.indexOf('choose...')===0||s.indexOf('--')!==-1||s==='please select';}
  function iy(t){var s=t.toLowerCase().trim();return s==='yes'||s==='y'||s==='true'||s==='1'||s==='sa citizen'||s==='south african'||s==='rsa';}
  function i_n(t){var s=t.toLowerCase().trim();return s==='no'||s==='n'||s==='false'||s==='0'||s==='other';}
  function gs(v){var r=[v];if(v==='sa citizen'||v==='south african'||v==='south africa'||v==='sa'||v==='rsa'){r.push('south african','south africa','sa citizen','sa','rsa','other african countries');}if(v.indexOf('male')!==-1||v.indexOf('female')!==-1){r.push('male','female');}return r;}
  function fo(sel,rv){var vl=rv.toLowerCase().trim(),terms=gs(vl),bo=null,bs=-1;for(var t=0;t<terms.length;t++){var tl=terms[t].toLowerCase().trim(),tw=tl.split(/\\s+/);for(var z=0;z<sel.options.length;z++){var o=sel.options[z];if(ip(o.text))continue;var tt=o.text.toLowerCase().trim(),vv=o.value.toLowerCase().trim(),sc=-1;if(tt===tl||vv===tl)sc=100;else if(tt.startsWith(tl)||vv.startsWith(tl))sc=50;else if(tt.indexOf(tl)!==-1||vv.indexOf(tl)!==-1)sc=30;else if(tl.indexOf(tt)!==-1||tl.indexOf(vv)!==-1)sc=20;else{for(var w=0;w<tw.length;w++){if(tw[w].length>1&&(tt.indexOf(tw[w])!==-1||vv.indexOf(tw[w])!==-1)){sc=10;break;}}}if(sc>bs){bs=sc;bo=o;}}}return bo;}
  function da(e){e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));e.dispatchEvent(new Event('select',{bubbles:true}));e.dispatchEvent(new Event('blur',{bubbles:true}));if(e.form)e.form.dispatchEvent(new Event('change',{bubbles:true}));}
  var h=vs['firstName']||vs['lastName']||vs['email'];if(!h){t('No profile found. Go to Dashboard first.','#EF4444');return;}
  var inputs=document.querySelectorAll('input,select,textarea'),filled=0,rx=[];
  for(var i=0;i<inputs.length;i++){var inp=inputs[i];if(inp.readOnly||inp.disabled)continue;
    var el=(inp.name+' '+inp.id+' '+(inp.placeholder||'')+' '+(inp.getAttribute('aria-label')||'')+' '+(inp.getAttribute('title')||'')).toLowerCase().replace(/[_-]/g,'').trim();
    var lb='';if(inp.labels&&inp.labels.length)lb=inp.labels[0].textContent.toLowerCase().trim();var all=el+' '+lb;
    var bk=null,bs=0;for(var k in fieldMap){var a=fieldMap[k];for(var j=0;j<a.length;j++){var al=a[j];if(all.indexOf(al)!==-1){var s=al.length;if(lb.indexOf(al)!==-1)s+=5;if(el.indexOf(al)!==-1)s+=3;if(s>bs){bs=s;bk=k;}break;}}}
    if(inp.tagName==='SELECT'||inp.type==='select-one'){inp.dispatchEvent(new Event('focus',{bubbles:true}));var hy=0,hn2=0;for(var z=0;z<inp.options.length;z++){if(ip(inp.options[z].text)&&z===0)continue;if(iy(inp.options[z].text))hy=1;if(i_n(inp.options[z].text))hn2=1;}if(hy&&hn2){for(var z=0;z<inp.options.length;z++){if(ip(inp.options[z].text))continue;if(iy(inp.options[z].text)){inp.value=inp.options[z].value;filled++;da(inp);inp.style.outline='2px solid #10B981';break;}}continue;}}
    if(bk&&vs[bk]){var v=vs[bk],mt=0;if(inp.tagName==='SELECT'||inp.type==='select-one'){var bo=fo(inp,v);if(bo){inp.value=bo.value;mt=1;}if(!mt&&inp.options.length<=30){rx.push({e:inp,vl:v});for(var z=1;z<inp.options.length;z++){if(!ip(inp.options[z].text)&&inp.options[z].value){inp.value=inp.options[z].value;break;}}}}else{inp.value=v;mt=1;}
      if(mt){filled++;da(inp);inp.style.outline='2px solid #10B981';}}
  if(rx.length){var dr=function(){for(var r=0;r<rx.length;r++){var rs=rx[r],e=rs.e,vl=rs.vl;e.dispatchEvent(new Event('focus',{bubbles:true}));var bo=fo(e,vl);if(bo){e.value=bo.value;filled++;da(e);e.style.outline='2px solid #10B981';}}var ni=document.querySelectorAll('input,select,textarea');for(var n=0;n<ni.length;n++){var x=ni[n];if(x.readOnly||x.disabled||x.style.outline)continue;var el2=(x.name+' '+x.id+' '+(x.placeholder||'')+' '+(x.getAttribute('aria-label')||'')+' '+(x.getAttribute('title')||'')).toLowerCase().replace(/[_-]/g,'').trim();var lb='';if(x.labels&&x.labels.length)lb=x.labels[0].textContent.toLowerCase().trim();var al2=el2+' '+lb,bk2=null,bs2=0;for(var k in fieldMap){var a=fieldMap[k];for(var j=0;j<a.length;j++){var al=a[j];if(al2.indexOf(al)!==-1){var s=al.length;if(lb.indexOf(al)!==-1)s+=5;if(el2.indexOf(al)!==-1)s+=3;if(s>bs2){bs2=s;bk2=k;}break;}}}if(bk2&&vs[bk2]){var v2=vs[bk2];if(x.tagName==='SELECT'||x.type==='select-one'){x.dispatchEvent(new Event('focus',{bubbles:true}));var bo2=fo(x,v2);if(bo2){x.value=bo2.value;filled++;da(x);x.style.outline='2px solid #10B981';}}else{x.value=v2;filled++;da(x);x.style.outline='2px solid #10B981';}}}};setTimeout(dr,800);setTimeout(dr,2500);}
  t(filled>0?'✅ Filled '+filled+' field'+(filled>1?'s':'')+'!':'No fields matched.',filled>0?'#10B981':'#EF4444');
  }catch(e){var d=document.createElement('div');d.textContent='⚠️ JS Error: '+e.message;d.style.cssText='position:fixed;top:10px;left:10px;padding:8px 16px;background:#EF4444;color:#fff;z-index:9999999;font-family:Arial;font-size:14px;border-radius:6px;';document.body.appendChild(d);}
})();
''';
}
