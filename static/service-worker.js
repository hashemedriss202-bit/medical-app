// اسم النسخة - غيّره عند تحديث التطبيق
const CACHE_NAME = 'medical-ai-v1';

// الملفات التي سيتم تخزينها مؤقتاً
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/icon-72.png',
  '/static/icon-96.png',
  '/static/icon-128.png',
  '/static/icon-144.png',
  '/static/icon-152.png',
  '/static/icon-192.png',
  '/static/icon-384.png',
  '/static/icon-512.png',
  '/offline'
];

// تثبيت Service Worker وتخزين الملفات
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('تم فتح التخزين المؤقت');
        return cache.addAll(urlsToCache);
      })
      .catch(err => console.log('خطأ في التخزين:', err))
  );
});

// جلب الملفات من التخزين المؤقت أولاً (للتسريع)
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // إذا وجد الملف في التخزين المؤقت، أعده
        if (response) {
          return response;
        }
        // وإلا، اذهب إلى الشبكة
        return fetch(event.request)
          .then(response => {
            // لا تخزن الطلبات التي تفشل
            if (!response || response.status !== 200) {
              return response;
            }
            // خزن نسخة من الاستجابة للاستخدام المستقبلي
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            return response;
          });
      })
  );
});

// تحديث Service Worker وحذف النسخ القديمة
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});