import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Check what navfix actually loaded
expr = """(function(){
  var keys = Object.keys(window).filter(function(k){ return k.indexOf('ssa') === 0 || k.indexOf('navfix') !== -1; });
  return JSON.stringify({
    ssaKeys: keys.slice(0, 20),
    hasSubmitViaFetch: typeof submitViaFetch !== 'undefined',
    navfixSource: typeof __ssaNavfix !== 'undefined' ? __ssaNavfix.toString().substring(0, 500) : 'missing'
  });
})()"""
print("Navfix details:", d.evaluate_js(expr))
