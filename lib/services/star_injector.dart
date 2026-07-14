import 'package:webview_flutter/webview_flutter.dart';

class StarInjector {
  static String getStarScript() {
    return '''
    (function() {
      if (window._starInjected) return;
      window._starInjected = true;
      
      console.log('⭐ INJECTING STAR');
      
      var star = document.createElement('div');
      star.id = 'star-button';
      star.innerHTML = '⭐';
      star.style.position = 'fixed';
      star.style.bottom = '20px';
      star.style.right = '20px';
      star.style.width = '60px';
      star.style.height = '60px';
      star.style.borderRadius = '50%';
      star.style.background = '#FFD700';
      star.style.display = 'flex';
      star.style.alignItems = 'center';
      star.style.justifyContent = 'center';
      star.style.fontSize = '30px';
      star.style.zIndex = '999999';
      star.style.cursor = 'pointer';
      star.style.border = '3px solid white';
      star.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
      
      star.onclick = function() {
        var panel = document.getElementById('guidance-panel');
        if (panel) { panel.remove(); return; }
        
        var p = document.createElement('div');
        p.id = 'guidance-panel';
        p.style.position = 'fixed';
        p.style.bottom = '90px';
        p.style.right = '20px';
        p.style.width = '280px';
        p.style.backgroundColor = 'white';
        p.style.padding = '15px';
        p.style.borderRadius = '12px';
        p.style.zIndex = '999999';
        p.style.boxShadow = '0 4px 20px rgba(0,0,0,0.4)';
        p.style.border = '2px solid #FFD700';
        
        p.innerHTML = 
          '<div style="font-weight:bold;font-size:16px;margin-bottom:10px;">📌 Application Guide</div>' +
          '<div style="padding:8px;background:#FFF3CD;margin-bottom:4px;border-radius:6px;">1. Click Apply Now</div>' +
          '<div style="padding:8px;background:#F0F8FF;margin-bottom:4px;border-radius:6px;">2. Enter ID number</div>' +
          '<div style="padding:8px;background:#E8F5E9;margin-bottom:4px;border-radius:6px;">3. Fill in details</div>' +
          '<div style="padding:8px;background:#F3E5F5;margin-bottom:4px;border-radius:6px;">4. Upload documents</div>' +
          '<div style="padding:8px;background:#FFF3E0;border-radius:6px;">5. Review & submit</div>' +
          '<div style="margin-top:10px;text-align:center;font-size:12px;color:#999;cursor:pointer;" onclick="this.parentElement.remove()">Close ✕</div>';
        
        document.body.appendChild(p);
      };
      
      document.body.appendChild(star);
      console.log('✅ STAR INJECTED!');
    })();
    ''';
  }
}
