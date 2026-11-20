# Diccionario Sánscrito–Español (Ricardo Benadon)

Web: https://diccionariosanscrito.com/ (dominio propio desde el 15/11/2026; GitHub Pages, rama `main`, raíz del repo; el archivo `CNAME` conecta el dominio, no borrarlo). La dirección antigua pbo1976.github.io/diccionario-sanscrito redirige sola.

## Dónde está cada cosa
- `data/<letra>.json`: las entradas de cada letra. **Es la fuente de verdad del diccionario.** `data/index.json` es el índice de búsqueda y los recuentos por fuente.
- `img/`: ilustraciones de las entradas.
- `index.html`: la web (se edita directamente; no se ponen datos del diccionario aquí).
- App instalable (PWA): `manifest.webmanifest`, `sw.js` (funcionamiento sin conexión; pide primero a la red, así que las correcciones llegan solas) e `icons/`. Si se cambia la lógica de `sw.js`, subir la versión `V`.
- `tools/ebook/`: generador del EPUB (`epub.py`), tipografías y cubierta.
- `ERRATAS.md`: registro de correcciones hechas y pendientes.

## Regla: cada cambio en el diccionario actualiza también el ebook
1. Cualquier corrección, errata o entrada nueva se hace en `data/*.json` (y en `img/` si hace falta). Si cambia el número de entradas o las fuentes, regenerar `data/index.json`.
2. Anotar el cambio en `ERRATAS.md`.
3. Hacer commit con un mensaje claro en español (aparece en las notas de la versión del ebook) y `git push` a `main`.
4. El workflow `.github/workflows/ebook.yml` regenera el EPUB, lo valida con EPUBCheck y lo publica como una Release nueva. **No subir EPUB a mano.** Comprobar en Actions que la ejecución terminó bien.
5. Las versiones anteriores quedan en Releases; no borrarlas.

La web enlaza siempre a `releases/latest/download/Diccionario-Sanscrito-Espanol.epub` y a la página de Releases para versiones anteriores.

## Criterios editoriales
- No corregir el texto de Ricardo Benadon sin que Pato lo apruebe; las dudas se anotan como pendientes en `ERRATAS.md`.
- No publicar emails personales en la web. Contacto público: info@diccionariosanscrito.com (consultas) y el formulario de Google Forms en «Sobre la obra» (erratas).
- Edición sin fines de lucro; las definiciones pertenecen a las obras citadas.
