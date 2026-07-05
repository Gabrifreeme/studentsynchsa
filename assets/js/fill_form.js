// ── Star ──
(function() {
    if (document.getElementById('ssa-star')) return;
    var s = document.createElement('div');
    s.id = 'ssa-star';
    s.textContent = '\u2605';
    var css = {
        position: 'fixed', bottom: '90px', right: '16px',
        width: '48px', height: '48px', borderRadius: '50%',
        background: '#7C3AED', color: '#fff',
        fontSize: '28px', lineHeight: '48px', textAlign: 'center',
        cursor: 'pointer', zIndex: '999999',
        boxShadow: '0 2px 12px rgba(124,58,237,0.5)',
        border: 'none', userSelect: 'none'
    };
    for (var k in css) s.style[k] = css[k];
    s.onclick = function() {
        if (window._ssaData) fillForm(window._ssaData);
    };
    document.body.appendChild(s);
})();

// ── fillForm ──
function fillForm(p) {
    var inputs = document.querySelectorAll('input, select, textarea');
    var n = 0;
    function fire(el) {
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('blur', { bubbles: true }));
    }
    for (var i = 0; i < inputs.length; i++) {
        var inp = inputs[i];
        var attrs = (inp.name + inp.id + inp.placeholder).toLowerCase();
        for (var key in p) {
            if (!p.hasOwnProperty(key)) continue;
            var v = p[key];
            if (!v || attrs.indexOf(key.toLowerCase()) === -1) continue;
            if (inp.tagName === 'SELECT') {
                for (var j = 0; j < inp.options.length; j++) {
                    var opt = inp.options[j];
                    if (opt.value.toLowerCase() === String(v).toLowerCase() ||
                        opt.text.toLowerCase().indexOf(String(v).toLowerCase()) > -1) {
                        inp.value = opt.value; fire(inp); n++;
                        break;
                    }
                }
            } else if (inp.type === 'radio' || inp.type === 'checkbox') {
                var radios = document.querySelectorAll('input[name="' + inp.name + '"]');
                for (var j = 0; j < radios.length; j++) {
                    var r = radios[j];
                    if (r.value.toLowerCase() === String(v).toLowerCase() ||
                        r.id.toLowerCase().indexOf(String(v).toLowerCase()) > -1) {
                        r.checked = true; fire(r); n++;
                        break;
                    }
                }
            } else {
                inp.value = v; fire(inp); n++;
            }
            break;
        }
    }
    console.log('Star filled ' + n + ' fields');
}

// ── setProfileData ──
function setProfileData(data) {
    window._ssaData = data;
}
