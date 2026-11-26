if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  });
}

window.acePushSupported = function () {
  return 'serviceWorker' in navigator && 'PushManager' in window &&
    typeof Notification !== 'undefined';
};

function aceUrlBase64ToUint8Array(base64String) {
  var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  var base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
  var raw = atob(base64);
  var output = new Uint8Array(raw.length);
  for (var i = 0; i < raw.length; ++i) output[i] = raw.charCodeAt(i);
  return output;
}

window.acePushRegister = async function (vapidPublicKey) {
  try {
    if (!window.acePushSupported()) {
      return JSON.stringify({
        ok: false,
        error: 'Push unavailable: secure=' + window.isSecureContext +
          ', sw=' + ('serviceWorker' in navigator) +
          ', push=' + ('PushManager' in window) +
          ', notify=' + (typeof Notification !== 'undefined'),
      });
    }
    var permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      return JSON.stringify({ ok: false, error: 'Permission denied' });
    }
    var reg = await navigator.serviceWorker.register('sw.js');
    await navigator.serviceWorker.ready;
    var sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: aceUrlBase64ToUint8Array(vapidPublicKey),
    });
    var json = sub.toJSON();
    return JSON.stringify({
      ok: true,
      endpoint: json.endpoint,
      p256dh: json.keys.p256dh,
      auth: json.keys.auth,
    });
  } catch (e) {
    return JSON.stringify({ ok: false, error: String(e) });
  }
};
