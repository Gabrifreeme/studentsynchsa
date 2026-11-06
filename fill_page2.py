import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Fill page-2 form with profile data
fill_script = """
(function() {
  function setVal(id, val) {
    var el = document.getElementById(id);
    if (!el) return 'missing';
    if (el.value !== undefined) {
      el.value = val;
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return 'ok';
    }
    return 'no value prop';
  }

  var results = [];
  results.push('homeLang=' + setVal('oapHomeLang', 'English'));
  results.push('ethnic=' + setVal('oapEthnic', 'Black'));
  results.push('cellInd=' + setVal('oapCellInd', 'Y'));
  results.push('email=' + setVal('itsEmail', 'test.user@example.com'));
  results.push('verifyEmail=' + setVal('verifyEmail', 'test.user@example.com'));
  results.push('street1=' + setVal('oapStreetAddr1', '28 Virginia Road'));
  results.push('street2=' + setVal('oapStreetAddr2', 'Nzhelele'));
  results.push('street3=' + setVal('oapStreetAddr3', 'Thohoyandou'));
  results.push('street4=' + setVal('oapStreetAddr4', 'Limpopo'));
  results.push('postal=' + setVal('oapStreetAddrPCodeRq', '0950'));
  results.push('resReq=' + setVal('oapResReq', 'Y'));
  return results.join(', ');
})()
"""

result = d.evaluate_js(fill_script)
print("Fill result:", result)
