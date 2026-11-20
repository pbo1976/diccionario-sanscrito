// Diccionario Sánscrito–Español: funcionamiento sin conexión.
// La página y los datos se piden primero a la red (para que las correcciones lleguen enseguida)
// y, si no hay conexión, se sirven desde la copia guardada. Ilustraciones y tipografías: copia guardada primero.
const V = "dic-v2";
const SHELL = ["/", "/manifest.webmanifest", "/data/index.json", "/icons/icon-192.png", "/icons/apple-touch-icon.png"];

self.addEventListener("install", e => {
  // Se guarda todo el diccionario al instalar (~7 MB), para que funcione sin conexión desde el principio.
  e.waitUntil((async () => {
    const c = await caches.open(V);
    await c.addAll(SHELL);
    try {
      const idx = await (await fetch("/data/index.json", {cache: "no-cache"})).json();
      await c.addAll(Object.keys(idx.letters || {}).map(s => "/data/" + s + ".json"));
    } catch (_) {}
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== V) await caches.delete(k);
    await self.clients.claim();
    // Guardar todas las letras en segundo plano para poder consultar sin conexión (~7 MB).
    try {
      const idx = await (await fetch("/data/index.json")).json();
      const c = await caches.open(V);
      for (const slug of Object.keys(idx.letters || {})) {
        const url = "/data/" + slug + ".json";
        if (!(await c.match(url))) { try { await c.add(url); } catch (_) {} }
      }
    } catch (_) {}
  })());
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const same = url.origin === location.origin;
  const isFont = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (!same && !isFont) return;                       // formulario, contador, GitHub: sin tocar
  if (isFont || url.pathname.startsWith("/img/") || url.pathname.startsWith("/icons/")) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok || res.type === "opaque") { const cp = res.clone(); caches.open(V).then(c => c.put(req, cp)); }
      return res;
    })));
    return;
  }
  const key = req.mode === "navigate" ? "/" : req;
  e.respondWith(fetch(req).then(res => {
    if (res.ok) { const cp = res.clone(); caches.open(V).then(c => c.put(key, cp)); }
    return res;
  }).catch(() => caches.match(key, {ignoreSearch: true})));
});
