// Minimal service worker: caches static assets (CSS/icons) for offline use
// and installability. Page content (orders, dashboard, etc.) is always
// fetched fresh from the network since it's personal/live business data.

const CACHE_NAME = "tailoring-shell-v1";
const SHELL_ASSETS = [
  "/static/css/style.css",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;

  // Only cache-first for our own static assets. Everything else (pages,
  // form posts, API-ish calls) goes straight to the network so customers
  // and admins always see live data.
  if (req.method === "GET" && req.url.includes("/static/")) {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req))
    );
  }
});
