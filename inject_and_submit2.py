import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Read the navfix script from the Dart file
with open(r'C:\Users\chris\StudentSyncSA\lib\services\autofill_script.dart', 'r', encoding='utf-8') as f:
    autofill_code = f.read()

# Extract ssaDatePickerJs
start_dp = autofill_code.index("const String ssaDatePickerJs = r'''") + len("const String ssaDatePickerJs = r'''")
end_dp = autofill_code.index("'''", start_dp)
datepicker_script = autofill_code[start_dp:end_dp]

# Extract the buildNavigationFixScript function body
start_idx = autofill_code.index("String buildNavigationFixScript()")
start_func = autofill_code.index("'''", start_idx) + 3
end_func = autofill_code.index("'''", start_func)
navfix_script = autofill_code[start_func:end_func]

# Combine both scripts
full_script = datepicker_script + "\n" + navfix_script

# Inject the combined script
inject_expr = f"""(function(){{
  var script = document.createElement('script');
  script.textContent = {repr(full_script)};
  document.head.appendChild(script);
  return 'injected'
}})()"""

result = d.evaluate_js(inject_expr)
print("Inject result:", result)

# Now run navfix and submit
submit_expr = """(function(){
  if(typeof __ssaNavfix!=='undefined'){
    __ssaNavfix();
    var f=document.forms[0];
    if(!f) return 'no form';
    if(typeof submitViaFetch==='function'){
      submitViaFetch(f);
      return 'submitted via fetch'
    }
    return 'navfix loaded but submitViaFetch not found'
  }
  return 'navfix not loaded'
})()"""

result = d.evaluate_js(submit_expr)
print("Submit result:", result)
