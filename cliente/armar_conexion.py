# Arma actualizaciones/archivos/americarp/conexion.bin: la pantalla que tapa el juego mientras el SA-MP
# se conecta al server. Necesita Pillow. Uso: python cliente/armar_conexion.py [vista.png]
# Con vista.png deja ademas una imagen de como se ve en una pantalla de 1920x1080.
#
# Formato que lee carga_video.asi: "ACN1", cantidad de piezas y por cada pieza 11 enteros de 4 bytes
# (tipo, ancla, x, y, ancho, alto, brillo x, y, ancho, alto, largo) y la imagen (JPEG o PNG).
# Medidas en pixeles de una pantalla de 1920x1080; el juego las escala al alto de la pantalla.
# tipo: 0 fondo, 1 siempre, 2 conectando, 3 entrando al juego, 4 server reiniciando.
# ancla: 0 cubre toda la pantalla, 1 pegada a la izquierda, 2 pegada a la derecha.
# brillo: la linea donde el juego hace correr un tramo dorado para que se vea que sigue cargando.
# Desde el tipo 10 son las pantallas del server despues de conectar (ingreso y seleccion de
# personaje), que arma pantallas.py con ancla 3: estiradas a toda la pantalla como los TextDraws.
import io, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pantallas
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(raiz, "fuentes")
FONDO = os.path.join(raiz, "cliente", "conexion-fondo.jpg")
ESTRELLA = os.path.join(raiz, "fondo", "arranque-estrella.png")
destino = os.path.join(raiz, "actualizaciones", "archivos", "americarp", "conexion.bin")
DORADO = (242, 190, 80, 255)
BLANCO = (255, 255, 255, 255)


def fuente(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def fondo():
    img = Image.open(FONDO).convert("RGB")
    r = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    img = img.crop((x, y, x + W, y + H)).convert("RGBA")
    # Sombra a la izquierda y abajo para que el texto se lea sobre cualquier foto.
    sombra = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(sombra)
    for i in range(W):
        d.line([(i, 0), (i, H)], fill=(8, 10, 20, int(200 * max(0, 1 - i / 1100) ** 1.6)))
    abajo = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(abajo)
    for i in range(H):
        d.line([(0, i), (W, i)], fill=(8, 10, 20, int(230 * max(0, (i - 620) / 460) ** 1.4)))
    return Image.alpha_composite(Image.alpha_composite(img, sombra), abajo).convert("RGB")


def capa(dibujar):
    img = Image.new("RGBA", (W, H))
    dibujar(img, ImageDraw.Draw(img))
    return img


def logo(img, d):
    est = Image.open(ESTRELLA).convert("RGBA").resize((150, 150), Image.LANCZOS)
    img.alpha_composite(est, (92, 380))
    d.text((240, 398), "AMERICA", font=fuente("Inter-ExtraBold.ttf", 96), fill=BLANCO)
    d.text((244, 500), "ROLEPLAY", font=fuente("Inter-SemiBold.ttf", 34), fill=DORADO)


def consejo(img, d):
    texto = "Consejo: escribí /ayuda para ver los primeros pasos."
    f = fuente("Inter-Regular.ttf", 24)
    d.text((W - 120 - d.textlength(texto, font=f), 972), texto, font=f, fill=(215, 220, 230, 255))


LINEA = (120, 950, 520, 4)  # x, y, ancho, alto de la linea donde corre el reflejo


def estado(texto):
    def dibujar(img, d):
        d.text((120, 884), texto + "…", font=fuente("Inter-SemiBold.ttf", 34), fill=BLANCO)
        x, y, w, h = LINEA
        d.rounded_rectangle([x, y, x + w - 1, y + h - 1], radius=2, fill=(255, 255, 255, 60))
    return dibujar, LINEA


def png(img):
    caja = img.getbbox()
    b = io.BytesIO()
    img.crop(caja).save(b, "PNG", optimize=True)
    return caja, b.getvalue()


piezas = []
b = io.BytesIO()
fondo().save(b, "JPEG", quality=90)
piezas.append((0, 0, (0, 0, W, H), (0, 0, 0, 0), b.getvalue()))
for tipo, ancla, dibujar in ((1, 1, logo), (1, 2, consejo)):
    caja, datos = png(capa(dibujar))
    piezas.append((tipo, ancla, caja, (0, 0, 0, 0), datos))
for tipo, texto in ((2, "Conectando con el servidor"), (3, "Entrando al juego"), (4, "El servidor se está reiniciando")):
    dibujar, brillo = estado(texto)
    caja, datos = png(capa(dibujar))
    piezas.append((tipo, 1, caja, brillo, datos))

for tipo, caja, brillo, datos in pantallas.todas(FONDO):
    piezas.append((tipo, 3, caja, brillo, datos))

salida = b"ACN1" + struct.pack("<I", len(piezas))
for tipo, ancla, (x1, y1, x2, y2), brillo, datos in piezas:
    salida += struct.pack("<11i", tipo, ancla, x1, y1, x2 - x1, y2 - y1, *brillo, len(datos)) + datos

# Revisión: se vuelve a leer como lo hace la ASI.
n, pos = struct.unpack_from("<I", salida, 4)[0], 8
for _ in range(n):
    c = struct.unpack_from("<11i", salida, pos)
    pos += 44
    assert 0 <= c[0] <= 34 and 0 <= c[1] <= 3 and c[4] > 0 and c[5] > 0 and salida[pos:pos + 2] in (b"\xff\xd8", b"\x89P")
    pos += c[10]
assert pos == len(salida)

os.makedirs(os.path.dirname(destino), exist_ok=True)
open(destino, "wb").write(salida)
print("Listo: %s (%d piezas, %.2f MB)" % (destino, n, len(salida) / 1048576))

if len(sys.argv) > 1:
    vista = Image.open(io.BytesIO(piezas[0][4])).convert("RGBA")
    for tipo, ancla, (x1, y1, x2, y2), brillo, datos in piezas:
        if tipo in (1, 2):
            vista.alpha_composite(Image.open(io.BytesIO(datos)).convert("RGBA"), (x1, y1))
        if tipo == 2:  # el tramo dorado, como lo dibuja el juego en un momento cualquiera
            ImageDraw.Draw(vista).rectangle([brillo[0] + 140, brillo[1], brillo[0] + 140 + brillo[2] // 4, brillo[1] + brillo[3] - 1], fill=DORADO)
    vista.convert("RGB").save(sys.argv[1])
    # Y una vista de cada pantalla del server, con todo lo que puede dibujar la ASI encima.
    raiz_vista = os.path.splitext(sys.argv[1])[0]
    for nombre, fondo_tipo, extra in (("ingreso", 10, {11: 7, 12: 1, 13: 1}), ("seleccion", 20, {29: 0, 22: 1, 23: 2, 21: 0, 31: 0, 24: 0, 27: 0})):
        img = None
        for tipo, ancla, (x1, y1, x2, y2), brillo, datos in piezas:
            if tipo == fondo_tipo:
                img = Image.open(io.BytesIO(datos)).convert("RGBA")
        for t, n in extra.items():
            for tipo, ancla, (x1, y1, x2, y2), brillo, datos in piezas:
                if tipo != t:
                    continue
                pz = Image.open(io.BytesIO(datos)).convert("RGBA")
                veces = n if t in (11,) else 1
                for k in range(veces):
                    paso = brillo[0] * (k if t == 11 else n if t in (21, 22, 23, 29) else 7 if t == 12 else 0)
                    if t in (21, 22, 23, 29):
                        img.alpha_composite(pz, (x1, y1 + paso))
                    else:
                        img.alpha_composite(pz, (x1 + paso, y1))
                if t == 23:
                    img.alpha_composite(pz, (x1, y1 + brillo[0] * 3))
        img.convert("RGB").save(raiz_vista + "-" + nombre + ".png")
