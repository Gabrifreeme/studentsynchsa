// A fetch handler makes the site installable as a PWA on Android Chrome.
self.addEventListener('fetch', function () {});

self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', function (event) {
  var data = { title: 'New email', body: '' };
  try {
    if (event.data) data = event.data.json();
  } catch (e) {
    if (event.data) data.body = event.data.text();
  }
  event.waitUntil(
    self.registration.showNotification(data.title || 'New email', {
      body: data.body || '',
      icon: 'icons/Icon-192.png',
      tag: 'acesi-email',
      data: { url: data.url || '/' },
    })
  );
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(function (list) {
        for (var i = 0; i < list.length; i++) {
          if ('focus' in list[i]) return list[i].focus();
        }
        return self.clients.openWindow(event.notification.data.url || '/');
      })
  );
});
