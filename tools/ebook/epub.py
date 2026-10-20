"""Build an EPUB 3 of the dictionary from site/data (JSON per letter) and site/img."""
import json, os, re, sys, zipfile, uuid, html, datetime, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, "..")
SITE = os.environ.get("DIC_SITE", os.path.join(ROOT, "site"))          # carpeta con data/ e img/
ASSETS = os.environ.get("DIC_ASSETS", ROOT)                             # carpeta con fonts/ y cover.jpg
OUT = sys.argv[1]
WORK = os.environ.get("DIC_WORK", os.path.join(ROOT, "epub_build"))
VERSION = os.environ.get("DIC_VERSION", "")

# ---------- Harvard-Kyoto -> devanāgarī (same rules as the website) ----------
TOK = ["lRR","lR","RR","kh","gh","ch","jh","Th","Dh","th","dh","ph","bh","ai","au","a","A","i","I","u","U","R","e","o",
       "M","H","k","g","G","c","j","J","T","D","N","t","d","n","p","b","m","y","r","l","v","z","S","s","h","'"]
V_IND = {"a":"अ","A":"आ","i":"इ","I":"ई","u":"उ","U":"ऊ","R":"ऋ","RR":"ॠ","lR":"ऌ","lRR":"ॡ","e":"ए","ai":"ऐ","o":"ओ","au":"औ"}
V_SIGN = {"a":"","A":"ा","i":"ि","I":"ी","u":"ु","U":"ू","R":"ृ","RR":"ॄ","lR":"ॢ","lRR":"ॣ","e":"े","ai":"ै","o":"ो","au":"ौ"}
CONS = {"k":"क","kh":"ख","g":"ग","gh":"घ","G":"ङ","c":"च","ch":"छ","j":"ज","jh":"झ","J":"ञ","T":"ट","Th":"ठ","D":"ड","Dh":"ढ","N":"ण",
        "t":"त","th":"थ","d":"द","dh":"ध","n":"न","p":"प","ph":"फ","b":"ब","bh":"भ","m":"म","y":"य","r":"र","l":"ल","v":"व","z":"श","S":"ष","s":"स","h":"ह"}
def tokenize(s):
    out=[]; i=0
    while i<len(s):
        t=next((x for x in TOK if s.startswith(x,i)),None)
        if t: out.append(t); i+=len(t)
        else: out.append((s[i],)); i+=1
    return out
def to_deva(hk,w=""):
    hk=re.split(r"[(/]",hk)[0].strip().replace("-","")
    keepD=bool(re.match(r"[ḍḌ]",w.strip()))
    hk=re.sub(r"(^|\s)([BCDEFGLPVY])",lambda m:m.group(0) if (keepD and m.start()==0 and m.group(2)=="D") else m.group(1)+m.group(2).lower(),hk)
    toks=tokenize(hk); out=""; i=0
    while i<len(toks):
        t=toks[i]
        if isinstance(t,tuple):
            out+=t[0] if re.match(r"[\s,.;]",t[0]) else ""
        elif t in CONS:
            out+=CONS[t]; n=toks[i+1] if i+1<len(toks) else None
            if isinstance(n,str) and n in V_SIGN: out+=V_SIGN[n]; i+=1
            else: out+="्"
        elif t in V_IND: out+=V_IND[t]
        elif t=="M": out+="ं"
        elif t=="H": out+="ः"
        elif t=="'": out+="ऽ"
        i+=1
    return out.strip()
def fold(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD",s) if unicodedata.category(c)!="Mn").lower()

SRC = [
 ("huet","Hu","Gérard Huet","Lexique sanskrit-français (Héritage du Sanskrit)","#23752b"),
 ("grim","Gr","John Grimes","A Concise Dictionary of Indian Philosophy","#1f45c9"),
 ("schu","SW","Stephan Schuhmacher y Gert Woerner","Diccionario de la Sabiduría Oriental (Paidós)","#7a7210"),
 ("yap","Yap","Victor Yap","A Glossary of Sanskrit Words Gleaned from Sai Literature","#c75610"),
 ("warn","Wa","John Warne","Vedanta-Sanskrit Glossary","#5d5d92"),
 ("blav","Bl","Helena P. Blavatsky","Glosario Teosófico","#84287f"),
 ("prab","Pr","A. C. Bhaktivedanta Swami Prabhupāda","El Bhagavad-gītā tal como es","#8c1d1d"),
 ("iyen","Iy","B. K. S. Iyengar","Light on the Yoga Sūtras of Patañjali","#c0168a"),
 ("rama","RM","Ramana Maharshi","Collected Works, glosario","#0b7fa8"),
 ("auro","SA","Sri Aurobindo","Glossary of Sanskrit Terms in Integral Yoga Literature","#22307a"),
 ("fraw","Fr","David Frawley","Gods, Sages and Kings, glosario","#3f8a12"),
 ("coul","Co","Michael Coulson","Teach Yourself Sanskrit","#2a2b33"),
 ("otra","Var","Otras fuentes","Fuentes diversas, marcadas por el autor en gris","#5a5b63"),
]
SRCD = {k:(ab,n,w,c) for k,ab,n,w,c in SRC}
ABC = [("a","अ"),("ā","आ"),("i","इ"),("ī","ई"),("u","उ"),("ū","ऊ"),("ṛ","ऋ"),("e","ए"),("ai","ऐ"),("o","ओ"),("au","औ"),
       ("k","क"),("kh","ख"),("g","ग"),("gh","घ"),("c","च"),("ch","छ"),("j","ज"),("jh","झ"),("ṭ","ट"),("ṭh","ठ"),("ḍ","ड"),("ḍh","ढ"),
       ("t","त"),("th","थ"),("d","द"),("dh","ध"),("n","न"),("p","प"),("ph","फ"),("b","ब"),("bh","भ"),("m","म"),("y","य"),("r","र"),
       ("l","ल"),("v","व"),("ś","श"),("ṣ","ष"),("s","स"),("h","ह")]

meta=json.load(open(os.path.join(SITE,"data","index.json")))
key2slug={L["key"]:s for s,L in meta["letters"].items()}
letters=[(k,d,key2slug[k]) for k,d in ABC if k in key2slug]
data={slug:json.load(open(os.path.join(SITE,"data",slug+".json"))) for _,_,slug in letters}

PART=300
loc={}   # (slug,i) -> "file.xhtml#id"
files=[] # (filename, slug, start, end)
for key,dev,slug in letters:
    n=len(data[slug])
    for p,start in enumerate(range(0,n,PART)):
        fn=f"l-{slug}-{p+1}.xhtml"; files.append((fn,key,dev,slug,start,min(n,start+PART),p))
        for i in range(start,min(n,start+PART)): loc[(slug,i)]=f"{fn}#e{i}"
byword={}
for key,dev,slug in letters:
    for i,r in enumerate(data[slug]):
        k=re.sub(r"\d+$","",fold(r["w"]).replace(" ","").replace("-",""))
        byword.setdefault(k,(slug,i))

XREF=re.compile(r"((?<=\[)ver|(?<![A-Za-zÀ-ÿĀ-žḀ-ỿ])(?:Ver:?|Véase:?|→|cf\.))\s*([A-Za-zÀ-ÿĀ-žḀ-ỿ][A-Za-zÀ-ÿĀ-žḀ-ỿ-]+)")
def linkify(t, here):
    def rep(m):
        hit=byword.get(fold(m.group(2)).replace(" ","").replace("-",""))
        if not hit: return m.group(0)
        target=loc[hit]
        if target.split("#")[0]==here: target="#"+target.split("#")[1]
        return f'{m.group(1)} <a href="{target}">{m.group(2)}</a>'
    return XREF.sub(rep,t)

def page(title, body, cls=""):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="es" xml:lang="es">
<head><meta charset="utf-8"/><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body{f' class="{cls}"' if cls else ''}>
{body}
</body></html>'''

used_imgs=[]
def entry(slug,i,r,here):
    dev=(r.get("deva") or to_deva(r["hk"],r["w"]))
    if r.get("root"): dev="√ "+dev
    parts=[f'<div class="e" id="e{i}"><p class="hw"><b>{html.escape(r["w"])}</b> <span class="dv" lang="sa" xml:lang="sa">{dev}</span></p>']
    for d in r["d"]:
        ab,n,w,c=SRCD.get(d["s"],SRCD["otra"])
        parts.append(f'<p class="df">{linkify(html.escape(d["t"],quote=False),here)} <span class="ab s-{d["s"]}">[{ab}]</span></p>')
    for im in r.get("img",[]):
        used_imgs.append(im)
        parts.append(f'<div class="ill"><img src="{im}" alt="Ilustración de {html.escape(r["w"])}"/></div>')
    if r.get("cap"): parts.append(f'<p class="cap">{html.escape(" · ".join(r["cap"]))}</p>')
    parts.append("</div>")
    return "\n".join(parts)

CSS=f'''@font-face {{ font-family: "Gentium Book Plus"; src: url(fonts/GentiumBookPlus-Regular.ttf); }}
@font-face {{ font-family: "Gentium Book Plus"; font-weight: bold; src: url(fonts/GentiumBookPlus-Bold.ttf); }}
@font-face {{ font-family: "Gentium Book Plus"; font-style: italic; src: url(fonts/GentiumBookPlus-Italic.ttf); }}
@font-face {{ font-family: "Tiro Devanagari Sanskrit"; src: url(fonts/TiroDevanagariSanskrit-Regular.ttf); }}
body {{ font-family: "Gentium Book Plus", Georgia, serif; line-height: 1.4; margin: 0 4%; }}
h1, h2 {{ font-weight: normal; text-align: center; page-break-before: always; }}
h1.letter {{ font-size: 2.6em; margin: 1.2em 0 .6em; }}
h1.letter .dv {{ display: block; font-size: .9em; }}
.dv {{ font-family: "Tiro Devanagari Sanskrit", serif; }}
.e {{ margin: 0 0 .9em; }}
p {{ margin: 0; text-indent: 0; }}
p.hw {{ margin: 0 0 .15em; font-size: 1.08em; page-break-after: avoid; }}
p.hw .dv {{ font-size: 1.1em; margin-left: .3em; }}
p.df {{ margin: 0 0 .25em; text-align: left; }}
.ab {{ font-size: .78em; white-space: nowrap; }}
{chr(10).join(f'.s-{k} {{ color: {c}; }}' for k,ab,n,w,c in SRC)}
.ill {{ text-align: center; margin: .4em 0; }}
.ill img {{ max-width: 70%; max-height: 14em; }}
p.cap {{ font-size: .85em; font-style: italic; text-align: center; }}
.title {{ text-align: center; margin-top: 18%; }}
.title h1 {{ font-size: 2.2em; page-break-before: avoid; margin: .4em 0; }}
.title .dv {{ font-size: 1.8em; }}
.title .by {{ font-style: italic; margin-top: 2em; }}
.title .place {{ margin-top: 4em; letter-spacing: .1em; font-size: .9em; }}
.prose p {{ margin: 0 0 .8em; text-indent: 0; }}
table.src {{ border-collapse: collapse; width: 100%; font-size: .92em; }}
table.src td {{ padding: .35em .4em; border-bottom: 1px solid #ccc; vertical-align: top; }}
table.src td.k {{ white-space: nowrap; font-weight: bold; }}
ol.abc {{ list-style: none; padding: 0; text-align: center; line-height: 2; }}
ol.abc li {{ display: inline; margin: 0 .4em; }}
'''

def build():
    if os.path.exists(WORK): subprocess.run(["rm","-rf",WORK])
    os.makedirs(os.path.join(WORK,"OEBPS","img")); os.makedirs(os.path.join(WORK,"OEBPS","fonts")); os.makedirs(os.path.join(WORK,"META-INF"))
    O=lambda *p: os.path.join(WORK,"OEBPS",*p)
    total=sum(len(v) for v in data.values())
    open(O("style.css"),"w").write(CSS)
    # front matter
    open(O("titulo.xhtml"),"w").write(page("Portada interior",'''<div class="title">
<p class="dv" lang="sa" xml:lang="sa">संस्कृत–स्पेनी शब्दकोश</p>
<h1>Diccionario<br/>Sánscrito–Español</h1>
<p class="by">Compilación de Ricardo Benadon</p>
<p class="place">BUENOS AIRES · 2001–2014</p>
</div>'''))
    tot=f"{total:,}".replace(",",".")
    open(O("obra.xhtml"),"w").write(page("Sobre la obra",f'''<h2>Sobre la obra</h2><div class="prose">
<p>Este diccionario es una compilación realizada por Ricardo Benadon en Buenos Aires entre 2001 y 2014. Reúne, para cada término sánscrito, las definiciones de diccionarios y glosarios de distintas tradiciones, traducidas al español y ordenadas en una sola entrada.</p>
<p>Cada entrada presenta el término en transliteración académica (IAST) y en devanāgarī. En palabras del autor: «Se agregaron ilustraciones cuando el término se refiere a un lugar, un ṛṣi, un comentarista, un Rey, o un héroe», y «fue de gran ayuda el Cologne Digital Sanskrit Lexicon (from Monier-Williams' Sanskrit-English Dictionary), tanto en la red como en el volumen impreso».</p>
<p>Cada definición termina con la abreviatura de la obra de la que procede. La lista completa está en <a href="fuentes.xhtml">Fuentes y abreviaturas</a>.</p>
<p><b>Esta edición.</b> El texto se ha recuperado de los archivos originales del autor, que usaban tipografías antiguas para los signos diacríticos. El devanāgarī se reconstruye a partir de la convención Harvard-Kyoto de cada entrada. Las entradas siguen el orden en que el autor las dispuso dentro de cada letra.</p>
<p>Esta edición contiene {tot} entradas. La letra Bh no se ha encontrado entre los archivos conservados.{(" Versión del "+VERSION+".") if VERSION else ""}</p>
<p>Edición digital sin fines de lucro. Las definiciones pertenecen a las obras citadas. También disponible en línea, con buscador: pbo1976.github.io/diccionario-sanscrito</p>
<p>Consultas, comentarios o erratas: en la web, sección «Sobre la obra», hay un formulario de contacto.</p>
</div>'''))
    rows="\n".join(f'<tr><td class="k s-{k}">[{ab}]</td><td>{html.escape(n)}<br/><i>{html.escape(w)}</i></td></tr>' for k,ab,n,w,c in SRC)
    open(O("fuentes.xhtml"),"w").write(page("Fuentes y abreviaturas",f'<h2>Fuentes y abreviaturas</h2><table class="src">{rows}</table>'))
    abc_items="".join(f'<li><a href="l-{slug}-1.xhtml">{k}</a></li>' for k,d,slug in letters)
    open(O("alfabeto.xhtml"),"w").write(page("Índice de letras",f'<h2>Índice de letras</h2><ol class="abc">{abc_items}</ol>'))
    # letters
    for fn,key,dev,slug,start,end,p in files:
        body=[]
        if p==0: body.append(f'<h1 class="letter" id="top">{key[0].upper()+key[1:]}<span class="dv" lang="sa" xml:lang="sa">{dev}</span></h1>')
        for i in range(start,end): body.append(entry(slug,i,data[slug][i],fn))
        open(O(fn),"w").write(page(f"Letra {key}","\n".join(body)))
    # images
    for im in sorted(set(used_imgs)):
        subprocess.run(["cp",os.path.join(SITE,im),O(im)])
    # fonts: subset to the characters actually used
    text=open(O("style.css")).read()
    allchars=set()
    for f in os.listdir(O()):
        if f.endswith(".xhtml"): allchars|=set(open(O(f)).read())
    chars="".join(sorted(allchars))
    open(os.path.join(WORK,"chars.txt"),"w").write(chars)
    for f in ["GentiumBookPlus-Regular.ttf","GentiumBookPlus-Bold.ttf","GentiumBookPlus-Italic.ttf","TiroDevanagariSanskrit-Regular.ttf"]:
        subprocess.run(["pyftsubset",os.path.join(ASSETS,"fonts",f),f"--text-file={os.path.join(WORK,'chars.txt')}",
                        "--layout-features=*",f"--output-file={O('fonts',f)}"],check=True)
    # cover
    subprocess.run(["cp",os.path.join(ASSETS,"cover.jpg"),O("cover.jpg")],check=True)
    open(O("cover.xhtml"),"w").write(page("Cubierta",'<div style="text-align:center;margin:0;padding:0"><img src="cover.jpg" alt="Diccionario Sánscrito–Español" style="max-width:100%;max-height:100%"/></div>',"cover"))
    # nav
    nav_letters="\n".join(f'<li><a href="l-{slug}-1.xhtml">{key} {dev}</a></li>' for key,dev,slug in letters)
    open(O("nav.xhtml"),"w").write(f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="es" xml:lang="es">
<head><meta charset="utf-8"/><title>Índice</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
<nav epub:type="toc" id="toc"><h2>Índice</h2><ol>
<li><a href="titulo.xhtml">Portada interior</a></li>
<li><a href="obra.xhtml">Sobre la obra</a></li>
<li><a href="fuentes.xhtml">Fuentes y abreviaturas</a></li>
<li><a href="alfabeto.xhtml">Índice de letras</a></li>
{nav_letters}
</ol></nav>
<nav epub:type="landmarks" hidden=""><ol>
<li><a epub:type="cover" href="cover.xhtml">Cubierta</a></li>
<li><a epub:type="bodymatter" href="{files[0][0]}">Diccionario</a></li>
</ol></nav>
</body></html>''')
    # ncx (for older readers)
    np=[("titulo.xhtml","Portada interior"),("obra.xhtml","Sobre la obra"),("fuentes.xhtml","Fuentes y abreviaturas"),("alfabeto.xhtml","Índice de letras")]+[(f"l-{slug}-1.xhtml",f"{key} {dev}") for key,dev,slug in letters]
    bid="urn:uuid:"+str(uuid.uuid5(uuid.NAMESPACE_URL,"pbo1976.github.io/diccionario-sanscrito"))
    ncx="\n".join(f'<navPoint id="n{i}" playOrder="{i+1}"><navLabel><text>{html.escape(t)}</text></navLabel><content src="{s}"/></navPoint>' for i,(s,t) in enumerate(np))
    open(O("toc.ncx"),"w").write(f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{bid}"/></head>
<docTitle><text>Diccionario Sánscrito–Español</text></docTitle><navMap>{ncx}</navMap></ncx>''')
    # opf
    spine=["cover.xhtml","titulo.xhtml","obra.xhtml","fuentes.xhtml","alfabeto.xhtml"]+[f[0] for f in files]
    items=[]
    for i,f in enumerate(spine): items.append(f'<item id="x{i}" href="{f}" media-type="application/xhtml+xml"/>')
    items.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
    items.append('<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>')
    items.append('<item id="css" href="style.css" media-type="text/css"/>')
    items.append('<item id="cover-img" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>')
    for i,f in enumerate(sorted(os.listdir(O("fonts")))): items.append(f'<item id="f{i}" href="fonts/{f}" media-type="font/ttf"/>')
    for i,im in enumerate(sorted(set(used_imgs))): items.append(f'<item id="i{i}" href="{im}" media-type="image/jpeg"/>')
    now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    itemrefs="\n".join(f'<itemref idref="x{i}"{" linear=\"yes\""}/>' for i in range(len(spine)))
    open(O("content.opf"),"w").write(f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="es">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{bid}</dc:identifier>
<dc:title>Diccionario Sánscrito–Español</dc:title>
<dc:creator id="c1">Ricardo Benadon</dc:creator>
<meta refines="#c1" property="role" scheme="marc:relators">com</meta>
<dc:language>es</dc:language>
<dc:date>2014</dc:date>
<dc:description>Diccionario sánscrito–español compilado por Ricardo Benadon en Buenos Aires entre 2001 y 2014. {total} entradas.</dc:description>
<dc:rights>Edición digital sin fines de lucro. Las definiciones pertenecen a las obras citadas.</dc:rights>
<meta property="dcterms:modified">{now}</meta>
<meta name="cover" content="cover-img"/>
</metadata>
<manifest>
{chr(10).join(items)}
</manifest>
<spine toc="ncx">
{itemrefs}
</spine>
</package>''')
    open(os.path.join(WORK,"META-INF","container.xml"),"w").write('''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>''')
    with zipfile.ZipFile(OUT,"w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"),"application/epub+zip",compress_type=zipfile.ZIP_STORED)
        for d,_,fs in os.walk(WORK):
            for f in fs:
                p=os.path.join(d,f); a=os.path.relpath(p,WORK)
                if a in ("chars.txt",): continue
                z.write(p,a,compress_type=zipfile.ZIP_DEFLATED)
    print("entries",total,"files",len(files),"imgs",len(set(used_imgs)),"size",os.path.getsize(OUT))
build()
