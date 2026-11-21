# Piezas de las pantallas del server despues de conectar: el ingreso (contrasenia) y la seleccion de
# personaje, mas un fondo simple para el registro y la creacion de personaje. Las usa
# armar_conexion.py, que las agrega a conexion.bin. Lo que cambia (nombres, numeros, el personaje
# en 3D) lo dibuja el server con TextDraws encima; aca va solo lo fijo: el vidrio, los iconos,
# los rotulos y los botones. Medidas en una pantalla de 1920x1080; el juego las estira a la
# pantalla igual que los TextDraws (ancla 3), asi coinciden en cualquier resolucion.
# Las posiciones que usa el server estan en gamemode/cuentas/pantallas.inc de GABU-RP: si se
# mueve algo aca, se mueve alla tambien.
import io, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(raiz, "fuentes")
ESTRELLA = os.path.join(raiz, "fondo", "arranque-estrella.png")
DORADO = (242, 190, 80, 255)
ROSA = (255, 120, 170, 255)
BLANCO = (255, 255, 255, 255)
SUAVE = (214, 218, 232, 255)
TENUE = (205, 210, 226, 255)
VERDE = (110, 230, 160, 255)

# Tipos de pieza (los lee carga_video.asi).
FONDO_INGRESO, PUNTO, CURSOR, ENTRAR, SALIR = 10, 11, 12, 13, 14
FONDO_SELECCION, ELEGIDA, LIBRE, BLOQUEADA = 20, 21, 22, 23
JUGAR, CREAR, DESBLOQUEAR, CINE_SI, CINE_NO, CARA = 24, 25, 26, 27, 28, 29
FONDO_SIMPLE, PANEL_PERSONAJE, PANEL_LIBRE, PANEL_BLOQUEADA, SALIR_SELECCION = 30, 31, 32, 33, 34
ESTIRADA = 3

# Ingreso: la tarjeta centrada.
IX1, IY1, IX2, IY2 = 650, 150, 1270, 950
CAMPO_Y = 462                  # rotulo CONTRASENIA; la caja va de +24 a +92
PUNTO_X, PUNTO_PASO, PUNTOS = 754, 26, 17
BOTON_Y = CAMPO_Y + 116        # ENTRAR, 62 de alto
STATS_Y = BOTON_Y + 116
NOVEDAD_Y = STATS_Y + 128
PIE_Y = IY2 - 46

# Seleccion: ranuras a la izquierda, panel a la derecha.
CX1, CX2, RANURA_Y, RANURA_PASO, RANURA_ALTO = 96, 620, 300, 124, 108
PX1, PY1, PX2, PY2 = 1290, 96, 1824, 984
FILAS_Y = PY1 + 204            # primera fila del panel; cada una 88 mas abajo
CINE_Y = FILAS_Y + 5 * 88 + 6
JUGAR_Y = PY2 - 110


def fuente(peso, tam):
    return ImageFont.truetype(os.path.join(FUENTES, {"x": "Inter-ExtraBold.ttf", "s": "Inter-SemiBold.ttf", "r": "Inter-Regular.ttf"}[peso]), tam)


def playa(fondo_jpg):
    img = Image.open(fondo_jpg).convert("RGB")
    r = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H)).convert("RGBA")


class Lienzo:
    """Una imagen con una capa encima para dibujar con transparencia (PIL no mezcla al dibujar en RGBA)."""

    def __init__(self, img, borroso):
        self.img, self.borroso = img, borroso
        self.nueva()

    def nueva(self):
        self.capa = Image.new("RGBA", (W, H))
        self.d = ImageDraw.Draw(self.capa)

    def fijar(self):
        self.img = Image.alpha_composite(self.img, self.capa)
        self.nueva()
        return self.img

    def componer(self, capa):
        self.img = Image.alpha_composite(self.fijar(), capa)

    def sombra(self, x1, y1, x2, y2, r, a=90):
        s = Image.new("RGBA", (W, H))
        ImageDraw.Draw(s).rounded_rectangle([x1 - 6, y1 + 24, x2 + 6, y2 + 30], radius=r, fill=(0, 0, 10, a))
        self.componer(s.filter(ImageFilter.GaussianBlur(26)))

    def vidrio(self, x1, y1, x2, y2, r=24, tinte=100, sombra=True):
        """El fondo desenfocado y tenido dentro de la caja, con un brillo arriba y un borde fino."""
        if sombra:
            self.sombra(x1, y1, x2, y2, r)
        img = self.fijar()
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).rounded_rectangle([x1, y1, x2, y2], radius=r, fill=255)
        img.paste(Image.alpha_composite(self.borroso, Image.new("RGBA", (W, H), (14, 16, 34, tinte))), (0, 0), m)
        g = Image.new("RGBA", (W, H))
        gd = ImageDraw.Draw(g)
        for i in range(min(80, y2 - y1)):
            gd.line([(x1, y1 + i), (x2, y1 + i)], fill=(255, 255, 255, int(26 * (1 - i / 80))))
        img.paste(Image.alpha_composite(img, g), (0, 0), m)
        self.img = img
        self.d.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=(255, 255, 255, 14), outline=(255, 255, 255, 46), width=2)

    def borde(self, x1, y1, x2, y2, r, alfa=210):
        """Borde con degrade de dorado a rosa."""
        img = self.fijar()
        b = Image.new("RGBA", (W, H))
        bd = ImageDraw.Draw(b)
        for x in range(x1 - 2, x2 + 3):
            t = (x - x1) / max(1, x2 - x1)
            bd.line([(x, y1 - 2), (x, y2 + 2)], fill=(int(242 + 13 * t), int(190 - 70 * t), int(80 + 90 * t), alfa))
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).rounded_rectangle([x1 - 1, y1 - 1, x2 + 1, y2 + 1], radius=r + 1, outline=255, width=2)
        img.paste(b, (0, 0), m)

    def resplandor(self, x1, y1, x2, y2, color=(255, 130, 170, 150), r=30, desenfoque=18):
        g = Image.new("RGBA", (W, H))
        ImageDraw.Draw(g).rounded_rectangle([x1, y1, x2, y2], radius=r, fill=color)
        self.componer(g.filter(ImageFilter.GaussianBlur(desenfoque)))

    def pildora(self, x1, y1, x2, y2, texto, tam=26):
        """Boton principal: degrade de dorado a rosa con el texto oscuro."""
        img = self.fijar()
        c = Image.new("RGBA", (W, H))
        cd = ImageDraw.Draw(c)
        for x in range(x1, x2):
            t = (x - x1) / (x2 - x1)
            cd.line([(x, y1), (x, y2)], fill=(int(242 + 13 * t), int(190 - 70 * t), int(80 + 90 * t), 255))
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).rounded_rectangle([x1, y1, x2, y2], radius=(y2 - y1) // 2, fill=255)
        img.paste(c, (0, 0), m)
        f = fuente("x", tam)
        self.d.text(((x1 + x2 - self.d.textlength(texto, font=f)) / 2, (y1 + y2) / 2 - tam * 0.6), texto, font=f, fill=(30, 18, 40, 255))

    def logo(self, x, y, esc=1.0):
        img = self.fijar()
        est = Image.open(ESTRELLA).convert("RGBA").resize((int(96 * esc), int(96 * esc)), Image.LANCZOS)
        img.alpha_composite(est, (x, y))
        self.d.text((x + int(100 * esc), y + int(10 * esc)), "AMERICA", font=fuente("x", int(54 * esc)), fill=BLANCO)
        self.d.text((x + int(103 * esc), y + int(70 * esc)), "ROLEPLAY", font=fuente("s", int(20 * esc)), fill=DORADO)


def icono(d, x, y, tipo, col=SUAVE):
    if tipo == "gente":
        d.ellipse([x + 7, y, x + 19, y + 12], outline=col, width=3)
        d.arc([x, y + 12, x + 26, y + 36], 200, 340, fill=col, width=3)
    elif tipo == "onda":
        for i, h in enumerate([8, 14, 20, 26]):
            d.rounded_rectangle([x + i * 7, y + 26 - h, x + i * 7 + 4, y + 26], radius=2, fill=col)
    elif tipo == "trofeo":
        d.rounded_rectangle([x + 4, y, x + 22, y + 14], radius=6, outline=col, width=3)
        d.line([(x + 13, y + 14), (x + 13, y + 22)], fill=col, width=3)
        d.line([(x + 6, y + 24), (x + 20, y + 24)], fill=col, width=3)
    elif tipo == "billete":
        d.rounded_rectangle([x, y + 4, x + 28, y + 22], radius=4, outline=col, width=3)
        d.ellipse([x + 10, y + 9, x + 18, y + 17], outline=col, width=2)
    elif tipo == "banco":
        d.polygon([(x, y + 9), (x + 14, y), (x + 28, y + 9)], outline=col, width=3)
        for i in range(3):
            d.line([(x + 5 + i * 9, y + 12), (x + 5 + i * 9, y + 21)], fill=col, width=3)
        d.line([(x, y + 24), (x + 28, y + 24)], fill=col, width=3)
    elif tipo == "maletin":
        d.rounded_rectangle([x, y + 7, x + 28, y + 25], radius=4, outline=col, width=3)
        d.rectangle([x + 9, y + 2, x + 19, y + 7], outline=col, width=2)
    elif tipo == "escudo":
        d.polygon([(x + 14, y), (x + 27, y + 5), (x + 24, y + 19), (x + 14, y + 27), (x + 4, y + 19), (x + 1, y + 5)], outline=col, width=3)
    elif tipo == "pin":
        d.ellipse([x + 5, y, x + 23, y + 18], outline=col, width=3)
        d.polygon([(x + 8, y + 14), (x + 20, y + 14), (x + 14, y + 27)], fill=col)
    elif tipo == "candado":
        d.rounded_rectangle([x, y + 12, x + 24, y + 32], radius=4, fill=col)
        d.arc([x + 3, y - 2, x + 21, y + 22], 180, 360, fill=col, width=3)
    elif tipo == "candado_linea":
        d.rounded_rectangle([x, y + 14, x + 24, y + 34], radius=4, outline=col, width=3)
        d.arc([x + 3, y, x + 21, y + 22], 180, 360, fill=col, width=3)


def jpeg(img):
    b = io.BytesIO()
    img.convert("RGB").save(b, "JPEG", quality=90)
    return b.getvalue()


def recorte(capa):
    """La parte con algo dibujado de una capa transparente, como PNG: ((x1, y1, x2, y2), datos)."""
    caja = capa.getbbox()
    b = io.BytesIO()
    capa.crop(caja).save(b, "PNG", optimize=True)
    return caja, b.getvalue()


def pieza(tipo, c, brillo=(0, 0, 0, 0)):
    caja, datos = recorte(c)
    return (tipo, caja, brillo, datos)


def capa():
    c = Image.new("RGBA", (W, H))
    return c, ImageDraw.Draw(c)


def texto_der(d, x, y, t, f, col):
    d.text((x - d.textlength(t, font=f), y), t, font=f, fill=col)


def texto_centro(d, x, y, t, f, col):
    d.text((x - d.textlength(t, font=f) / 2, y), t, font=f, fill=col)


def base(fondo_jpg):
    pl = playa(fondo_jpg)
    return pl, Image.alpha_composite(pl, Image.new("RGBA", (W, H), (8, 8, 24, 50)))


# ---------------------------------------------------------------- ingreso
def ingreso(pl, fondo):
    piezas = []
    L = Lienzo(fondo.copy(), pl.filter(ImageFilter.GaussianBlur(12)))
    halo, hd = capa()
    hd.rounded_rectangle([IX1 - 10, IY1 + 40, IX2 + 10, IY2 + 50], radius=28, fill=(0, 0, 10, 90))
    L.componer(halo.filter(ImageFilter.GaussianBlur(40)))
    L.vidrio(IX1, IY1, IX2, IY2, 28, 100, sombra=False)
    L.logo(IX1 + 40, IY1 + 40, 0.82)
    d = L.d
    # pastilla de "en linea": el numero lo pone el server
    d.rounded_rectangle([IX2 - 40 - 170, IY1 + 34, IX2 - 40, IY1 + 66], radius=16, fill=(10, 10, 26, 150), outline=(255, 255, 255, 40))
    d.ellipse([IX2 - 40 - 156, IY1 + 45, IX2 - 40 - 146, IY1 + 55], fill=VERDE)
    d.text((IX1 + 40, IY1 + 204), "Hola de nuevo,", font=fuente("r", 20), fill=SUAVE)
    # campo de la contrasenia: los puntos y el cursor los dibuja la ASI
    d.text((IX1 + 40, CAMPO_Y), "CONTRASEÑA", font=fuente("s", 14), fill=TENUE)
    d.rounded_rectangle([IX1 + 40, CAMPO_Y + 24, IX2 - 40, CAMPO_Y + 92], radius=18, fill=(8, 8, 22, 150), outline=DORADO, width=2)
    icono(d, IX1 + 62, CAMPO_Y + 42, "candado", DORADO)
    L.resplandor(IX1 + 60, BOTON_Y + 18, IX2 - 60, BOTON_Y + 70)
    L.pildora(IX1 + 40, BOTON_Y, IX2 - 40, BOTON_Y + 62, "ENTRAR", 24)
    d = L.d
    # estadisticas: los numeros los pone el server
    d.line([(IX1 + 40, STATS_Y), (IX2 - 40, STATS_Y)], fill=(255, 255, 255, 40), width=1)
    cw = (IX2 - IX1 - 80) / 3
    for i, (ic, rotulo) in enumerate((("gente", "Personajes"), ("trofeo", "Récord de hoy"), ("onda", "Registrados hoy"))):
        x = IX1 + 40 + i * cw
        if i:
            d.line([(x, STATS_Y + 22), (x, STATS_Y + 86)], fill=(255, 255, 255, 35))
        icono(d, int(x + 24), STATS_Y + 30, ic, VERDE if ic == "onda" else DORADO)
        d.text((x + 66, STATS_Y + 58), rotulo, font=fuente("r", 14), fill=TENUE)
    d.line([(IX1 + 40, STATS_Y + 108), (IX2 - 40, STATS_Y + 108)], fill=(255, 255, 255, 40), width=1)
    d.rounded_rectangle([IX1 + 40, NOVEDAD_Y, IX1 + 108, NOVEDAD_Y + 26], radius=13, fill=ROSA)
    d.text((IX1 + 51, NOVEDAD_Y + 3), "NUEVO", font=fuente("x", 14), fill=(40, 10, 30, 255))
    d.text((IX1 + 40, PIE_Y), "¿Olvidaste tu clave? Pedila en el Discord.", font=fuente("r", 15), fill=TENUE)
    texto_der(d, IX2 - 40, PIE_Y, "Salir del servidor", fuente("s", 16), SUAVE)
    L.borde(IX1, IY1, IX2, IY2, 28)
    piezas.append((FONDO_INGRESO, (0, 0, W, H), (0, 0, 0, 0), jpeg(L.fijar())))

    # El primer punto y el cursor sin nada escrito; la ASI corre cada uno PUNTO_PASO por letra.
    c, d = capa()
    d.ellipse([PUNTO_X, CAMPO_Y + 51, PUNTO_X + 13, CAMPO_Y + 64], fill=BLANCO)
    piezas.append(pieza(PUNTO, c, (PUNTO_PASO, 0, PUNTOS, 0)))
    c, d = capa()
    d.rectangle([PUNTO_X - 6, CAMPO_Y + 41, PUNTO_X - 4, CAMPO_Y + 74], fill=DORADO)
    piezas.append(pieza(CURSOR, c, (PUNTO_PASO, 0, 0, 0)))
    # ENTRAR con el mouse encima: un brillo blanco sobre el boton. La pieza tambien es la zona del clic.
    c, d = capa()
    d.rounded_rectangle([IX1 + 40, BOTON_Y, IX2 - 40, BOTON_Y + 62], radius=31, fill=(255, 255, 255, 60))
    piezas.append(pieza(ENTRAR, c, (0, 0, 0, 0)))
    c, d = capa()
    f = fuente("s", 16)
    w = d.textlength("Salir del servidor", font=f)
    d.rounded_rectangle([IX2 - 52 - w, PIE_Y - 8, IX2 - 28, PIE_Y + 28], radius=18, fill=(255, 255, 255, 40))
    texto_der(d, IX2 - 40, PIE_Y, "Salir del servidor", f, BLANCO)
    piezas.append(pieza(SALIR, c, (0, 0, 0, 0)))
    return piezas


# ---------------------------------------------------------------- seleccion
def seleccion(pl, fondo):
    piezas = []
    L = Lienzo(fondo.copy(), pl.filter(ImageFilter.GaussianBlur(12)))
    d = L.d
    d.text((96, 96), "ELEGÍ TU", font=fuente("x", 60), fill=BLANCO)
    d.text((96, 160), "PERSONAJE", font=fuente("x", 60), fill=DORADO)
    d.text((100, 240), "Elegí uno y tocá JUGAR.", font=fuente("r", 20), fill=SUAVE)
    for k in range(4):
        y = RANURA_Y + k * RANURA_PASO
        L.vidrio(CX1, y, CX2, y + RANURA_ALTO, 22, 100)
    d = L.d
    d.text((CX1, RANURA_Y + 4 * RANURA_PASO + 6), "Salir del servidor", font=fuente("s", 17), fill=SUAVE)
    # plataforma del personaje y flechas para girarlo
    g, gd = capa()
    gd.ellipse([800, 860, 1120, 940], fill=(255, 150, 190, 120))
    L.componer(g.filter(ImageFilter.GaussianBlur(22)))
    d = L.d
    d.ellipse([840, 880, 1080, 920], outline=(255, 255, 255, 140), width=2)
    for x, flecha in ((790, "‹"), (1130, "›")):
        d.ellipse([x - 26, 874, x + 26, 926], fill=(255, 255, 255, 30), outline=(255, 255, 255, 80))
        texto_centro(d, x, 874, flecha, fuente("s", 34), BLANCO)
    # panel derecho: lo de adentro depende de la ranura elegida (piezas 31 a 33)
    L.vidrio(PX1, PY1, PX2, PY2, 28, 100)
    d = L.d
    d.rounded_rectangle([PX1 + 40, CINE_Y, PX2 - 40, CINE_Y + 62], radius=18, fill=(255, 255, 255, 14))
    d.text((PX1 + 60, CINE_Y + 10), "Cinemática al entrar", font=fuente("s", 18), fill=BLANCO)
    d.text((PX1 + 60, CINE_Y + 34), "La cámara baja del cielo hasta donde aparecés", font=fuente("r", 14), fill=TENUE)
    L.borde(PX1, PY1, PX2, PY2, 28)
    piezas.append((FONDO_SELECCION, (0, 0, W, H), (0, 0, 0, 0), jpeg(L.fijar())))

    # Lo que va en una ranura, dibujado en la primera; la ASI lo baja RANURA_PASO por cada ranura.
    ax, ay = CX1 + 20, RANURA_Y + 18
    c, d = capa()
    d.rounded_rectangle([ax, ay, ax + 72, ay + 72], radius=18, fill=(255, 255, 255, 34))
    piezas.append(pieza(CARA, c, (RANURA_PASO, 0, 0, 0)))
    c, d = capa()
    d.rounded_rectangle([ax, ay, ax + 72, ay + 72], radius=18, outline=(255, 255, 255, 120), width=2)
    texto_centro(d, ax + 36, ay + 10, "+", fuente("s", 40), BLANCO)
    d.text((ax + 92, RANURA_Y + 24), "Ranura libre", font=fuente("s", 26), fill=BLANCO)
    d.text((ax + 92, RANURA_Y + 62), "Crear un personaje nuevo", font=fuente("r", 17), fill=SUAVE)
    piezas.append(pieza(LIBRE, c, (RANURA_PASO, 0, 0, 0)))
    c, d = capa()
    d.rounded_rectangle([ax, ay, ax + 72, ay + 72], radius=18, fill=(255, 255, 255, 18))
    icono(d, ax + 24, ay + 20, "candado_linea", (190, 195, 210, 255))
    d.text((ax + 92, RANURA_Y + 24), "Ranura bloqueada", font=fuente("s", 26), fill=(200, 204, 218, 255))
    d.text((ax + 92, RANURA_Y + 62), "Se desbloquea con CASH", font=fuente("r", 17), fill=TENUE)
    d.rounded_rectangle([CX2 - 20 - 136, RANURA_Y + 64, CX2 - 20, RANURA_Y + 92], radius=14, fill=(242, 190, 80, 70), outline=(242, 190, 80, 160))
    piezas.append(pieza(BLOQUEADA, c, (RANURA_PASO, 0, 0, 0)))
    # Borde de la ranura elegida.
    L2 = Lienzo(Image.new("RGBA", (W, H)), None)
    L2.borde(CX1, RANURA_Y, CX2, RANURA_Y + RANURA_ALTO, 22)
    piezas.append(pieza(ELEGIDA, L2.fijar(), (RANURA_PASO, 0, 0, 0)))

    # Panel derecho con un personaje: pastillas, filas con iconos y rotulos (los valores, del server).
    c, d = capa()
    d.line([(PX1 + 40, PY1 + 184), (PX2 - 40, PY1 + 184)], fill=(255, 255, 255, 40))
    for x1, x2, fondo_p in ((PX1 + 40, PX1 + 160, (242, 190, 80, 70)), (PX1 + 172, PX1 + 320, (255, 255, 255, 30)), (PX1 + 332, PX1 + 494, (255, 120, 170, 60))):
        d.rounded_rectangle([x1, PY1 + 124, x2, PY1 + 156], radius=16, fill=fondo_p)
    for i, (ic, rotulo) in enumerate((("billete", "Efectivo"), ("banco", "Banco"), ("maletin", "Trabajo"), ("escudo", "Organización"), ("pin", "Aparece en"))):
        y = FILAS_Y + i * 88
        d.rounded_rectangle([PX1 + 40, y, PX2 - 40, y + 76], radius=18, fill=(255, 255, 255, 22), outline=(255, 255, 255, 30))
        d.rounded_rectangle([PX1 + 56, y + 16, PX1 + 100, y + 60], radius=12, fill=(242, 190, 80, 40))
        icono(d, PX1 + 64, y + 24, ic, DORADO)
        d.text((PX1 + 118, y + 14), rotulo, font=fuente("r", 15), fill=TENUE)
    piezas.append(pieza(PANEL_PERSONAJE, c, (0, 0, 0, 0)))
    for tipo, titulo, lineas, ic in (
        (PANEL_LIBRE, "Ranura libre", ["Creá un personaje nuevo: elegí su nombre,", "edad, origen y aspecto.", "", "Cada personaje tiene su propio dinero,", "trabajo y progreso."], None),
        (PANEL_BLOQUEADA, "Ranura bloqueada", ["Desbloqueala con CASH para tener", "otro personaje. Es para siempre,", "aunque después borres el personaje.", "", "No da dinero ni ventajas: cada personaje", "empieza de cero."], "candado_linea")):
        c, d = capa()
        d.text((PX1 + 40, PY1 + 40), titulo, font=fuente("x", 38), fill=BLANCO)
        d.line([(PX1 + 40, PY1 + 184), (PX2 - 40, PY1 + 184)], fill=(255, 255, 255, 40))
        for i, t in enumerate(lineas):
            d.text((PX1 + 40, PY1 + 214 + i * 30), t, font=fuente("r", 19), fill=SUAVE)
        piezas.append(pieza(tipo, c, (0, 0, 0, 0)))

    # Botones del panel segun la ranura elegida.
    for tipo, texto in ((JUGAR, "JUGAR"), (CREAR, "CREAR PERSONAJE"), (DESBLOQUEAR, "DESBLOQUEAR")):
        L2 = Lienzo(Image.new("RGBA", (W, H)), None)
        L2.resplandor(PX1 + 60, JUGAR_Y + 20, PX2 - 60, JUGAR_Y + 74)
        L2.pildora(PX1 + 40, JUGAR_Y, PX2 - 40, JUGAR_Y + 66, texto, 28 if len(texto) < 12 else 24)
        piezas.append(pieza(tipo, L2.fijar(), (0, 0, 0, 0)))
    for tipo, encendido in ((CINE_SI, True), (CINE_NO, False)):
        c, d = capa()
        d.rounded_rectangle([PX2 - 118, CINE_Y + 15, PX2 - 58, CINE_Y + 47], radius=16, fill=DORADO if encendido else (255, 255, 255, 50))
        kx = PX2 - 89 if encendido else PX2 - 115
        d.ellipse([kx, CINE_Y + 18, kx + 28, CINE_Y + 44], fill=BLANCO)
        piezas.append(pieza(tipo, c, (0, 0, 0, 0)))
    c, d = capa()
    f = fuente("s", 17)
    y = RANURA_Y + 4 * RANURA_PASO + 6
    d.rounded_rectangle([CX1 - 12, y - 8, CX1 + d.textlength("Salir del servidor", font=f) + 12, y + 30], radius=18, fill=(255, 255, 255, 40))
    d.text((CX1, y), "Salir del servidor", font=f, fill=BLANCO)
    piezas.append(pieza(SALIR_SELECCION, c, (0, 0, 0, 0)))
    return piezas


# ---------------------------------------------------------------- fondo simple
def simple(pl, fondo):
    L = Lienzo(Image.alpha_composite(fondo, Image.new("RGBA", (W, H), (8, 8, 24, 70))), None)
    L.logo(96, 80, 0.9)
    return [(FONDO_SIMPLE, (0, 0, W, H), (0, 0, 0, 0), jpeg(L.fijar()))]


def todas(fondo_jpg):
    pl, fondo = base(fondo_jpg)
    return ingreso(pl, fondo) + seleccion(pl, fondo) + simple(pl, fondo)
