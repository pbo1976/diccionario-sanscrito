# Diccionario Sánscrito–Español (Ricardo Benadon)

Web: https://pbo1976.github.io/diccionario-sanscrito/ (GitHub Pages, rama `main`, raíz del repo).

## Dónde está cada cosa
- `data/<letra>.json`: las entradas de cada letra. **Es la fuente de verdad del diccionario.** `data/index.json` es el índice de búsqueda y los recuentos por fuente.
- `img/`: ilustraciones de las entradas.
- `index.html`: la web, generada a partir de una plantilla; no se editan datos aquí.
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
- No publicar emails personales en la web; el contacto es un formulario de Google Forms en «Sobre la obra».
- Edición sin fines de lucro; las definiciones pertenecen a las obras citadas.
