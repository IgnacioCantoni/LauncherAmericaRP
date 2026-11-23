# Íconos del inventario para los objetos que no se venden en la tienda: la caña, lo que se encuentra
# trabajando, las armas y las balas. Mismo estilo que iconos.py (volumen, brillo y sombra, sin trazo).
# Las armas largas se dibujan acostadas y se giran en diagonal para llenar el cuadrado.
from PIL import Image, ImageDraw
from iconos import N, u, balas, cana, latas

MET = ((110, 114, 124), (38, 40, 46))       # metal pavonado
NEG = ((70, 70, 76), (18, 18, 22))          # plástico negro
MAD = ((185, 118, 62), (100, 58, 26))       # madera
CRO = ((235, 238, 244), (125, 130, 140))    # cromado
ORO = ((255, 225, 120), (185, 135, 40))


def _girar(p, ang):
    p.img = p.img.rotate(ang, resample=Image.BICUBIC, center=(N / 2, N / 2))


def _boca(p, x, y0, y1):
    """El agujero oscuro en la punta de un caño."""
    p.shape("rect", (x - 1.2, y0, x + 0.6, y1), (10, 10, 12), r=0.5, sombra=0)


# ---------- Hallazgos de los trabajos ----------

def botellas(p):
    for x, c in ((22, ((90, 170, 90), (25, 80, 35))), (50, ((175, 110, 50), (90, 45, 15)))):
        p.shape("rect", (x + 9, 8, x + 19, 30), *c, vertical=False, y0=x + 9, y1=x + 19, r=2)
        p.poly([(x + 9, 28), (x + 19, 28), (x + 28, 42), (x, 42)], *c, vertical=False, y0=x, y1=x + 28)
        p.shape("rect", (x, 40, x + 28, 94), *c, vertical=False, y0=x, y1=x + 28, r=5)
        p.shape("rect", (x + 2, 56, x + 26, 76), (240, 232, 210), (200, 188, 160), vertical=False, y0=x, y1=x + 28, sombra=0.2)
        p.brillo((x + 4, 14, x + 8, 90), 170, 1.0, ell=False)


def ropa(p):
    # remera doblada vista de frente, con el cuello y las mangas
    C = ((90, 150, 220), (35, 80, 150))
    p.poly([(30, 14), (42, 10), (58, 10), (70, 14), (92, 30), (82, 46), (72, 40), (72, 90), (28, 90), (28, 40), (18, 46), (8, 30)],
           *C, vertical=False, y0=10, y1=90)
    p.shape("ell", (40, 6, 60, 18), (25, 60, 120), (20, 45, 95), sombra=0.3)
    p.linea([(28, 62), (72, 62)], (60, 115, 190), 1.2, sombra=0)
    p.brillo((32, 18, 50, 50), 70, 4)


def radio_vieja(p):
    # radio de madera con dial y parlante
    p.linea([(70, 22), (88, 4)], (190, 192, 200), 1.6)
    p.shape("rect", (8, 22, 92, 88), *MAD, r=8)
    p.shape("rect", (14, 30, 52, 80), (60, 45, 35), (30, 22, 16), r=4, sombra=0.3)
    d = ImageDraw.Draw(p.img)
    for y in range(34, 78, 5):
        d.line([(u(17), u(y)), (u(49), u(y))], fill=(140, 110, 80, 255), width=int(u(1.2)))
    p.shape("rect", (58, 32, 86, 50), (240, 225, 170), (195, 170, 110), r=2, sombra=0.25)
    p.linea([(70, 34), (70, 48)], (200, 50, 40), 0.9, sombra=0)
    for x in (62, 76):
        p.shape("ell", (x, 58, x + 10, 68), *CRO, borde=3)
    p.brillo((12, 24, 88, 32), 90, 2)


def anteojos(p):
    m = p.mask(lambda d: (d.ellipse([u(6), u(34), u(46), u(70)], fill=255), d.ellipse([u(54), u(34), u(94), u(70)], fill=255)))
    p.linea([(42, 40), (50, 36), (58, 40)], (60, 60, 66), 2.5)
    p.linea([(8, 42), (2, 36)], (60, 60, 66), 2.5)
    p.linea([(92, 42), (98, 36)], (60, 60, 66), 2.5)
    p.fill(m, (70, 85, 110), (15, 18, 28), y0=34, y1=70, borde=4)
    p.brillo((12, 38, 26, 48), 170, 1.5)
    p.brillo((60, 38, 74, 48), 170, 1.5)


def bolso(p):
    # bolso de viaje con manijas y cierre
    m = p.mask(lambda d: d.arc([u(30), u(16), u(70), u(56)], 180, 360, fill=255, width=int(u(5))))
    p.fill(m, *NEG, borde=3)
    p.shape("rect", (8, 34, 92, 86), (70, 110, 70), (30, 60, 35), r=18)
    p.linea([(20, 44), (80, 44)], (190, 190, 195), 1.3, sombra=0)
    p.shape("rect", (40, 60, 60, 74), (40, 70, 45), (25, 45, 28), r=2, sombra=0.3)
    p.brillo((16, 37, 70, 50), 80, 3)


def maletin(p):
    p.shape("rect", (36, 18, 64, 30), *NEG, r=4)
    p.shape("rect", (41, 22, 59, 30), (0, 0, 0), sombra=0)
    p.img.paste((0, 0, 0, 0), [int(u(41)), int(u(23)), int(u(59)), int(u(30))])
    p.shape("rect", (6, 28, 94, 88), (55, 45, 40), (22, 17, 15), r=6)
    p.linea([(6, 46), (94, 46)], (30, 24, 20), 1.0, sombra=0)
    for x in (22, 70):
        p.shape("rect", (x, 40, x + 8, 52), *ORO, r=1.5, sombra=0.2)
    p.brillo((10, 31, 90, 38), 70, 2)


def reloj(p):
    p.shape("rect", (36, 2, 64, 30), (60, 40, 25), (30, 18, 10), vertical=False, y0=36, y1=64, r=4)
    p.shape("rect", (36, 70, 64, 98), (60, 40, 25), (30, 18, 10), vertical=False, y0=36, y1=64, r=4)
    p.shape("ell", (20, 20, 80, 80), *CRO, borde=5)
    p.shape("ell", (27, 27, 73, 73), (250, 250, 252), (205, 210, 220), sombra=0.35)
    d = ImageDraw.Draw(p.img)
    for i in range(12):
        import math
        a = math.radians(i * 30)
        x0, y0 = 50 + 19 * math.sin(a), 50 - 19 * math.cos(a)
        x1, y1 = 50 + 22 * math.sin(a), 50 - 22 * math.cos(a)
        d.line([(u(x0), u(y0)), (u(x1), u(y1))], fill=(40, 40, 45, 255), width=int(u(1.2)))
    d.line([(u(50), u(50)), (u(50), u(34))], fill=(25, 25, 30, 255), width=int(u(2)))
    d.line([(u(50), u(50)), (u(62), u(54))], fill=(25, 25, 30, 255), width=int(u(2)))
    p.shape("ell", (48, 48, 52, 52), (200, 40, 35), sombra=0)
    p.brillo((30, 28, 54, 42), 110, 2.5)


# ---------- Armas blancas ----------

def manopla(p):
    p.shape("rect", (14, 52, 86, 76), *CRO, r=10)
    m = p.mask(lambda d: [d.ellipse([u(x), u(24), u(x + 20), u(54)], fill=255) for x in (10, 30, 50, 70)])
    m2 = p.mask(lambda d: [d.ellipse([u(x + 5), u(30), u(x + 15), u(48)], fill=255) for x in (10, 30, 50, 70)])
    from PIL import ImageChops
    p.fill(ImageChops.subtract(m, m2), *CRO, y0=24, y1=54, borde=4)
    p.brillo((16, 54, 84, 60), 140, 1.5)


def palo_golf(p):
    p.linea([(14, 6), (72, 82)], (200, 202, 210), 2.6, c2=(120, 122, 130))
    p.linea([(14, 6), (24, 19)], *NEG[:1], w=5, c2=NEG[1])
    p.poly([(66, 76), (78, 80), (92, 86), (90, 94), (70, 92), (64, 84)], *CRO, y0=76, y1=94)
    p.brillo((70, 80, 88, 86), 120, 1)


def porra(p):
    p.linea([(14, 84), (84, 14)], *NEG[:1], w=8, c2=NEG[1])
    p.linea([(32, 66), (48, 82)], *NEG[:1], w=6, c2=NEG[1])
    p.brillo((40, 40, 70, 46), 60, 2)


def cuchillo(p):
    p.poly([(44, 56), (88, 10), (92, 14), (58, 70)], *CRO, vertical=False, y0=44, y1=92)
    p.poly([(44, 56), (88, 10), (66, 40)], (250, 252, 255), (200, 205, 215), sombra=0.15)
    p.linea([(38, 52), (60, 74)], (60, 60, 66), 4.5)
    p.linea([(14, 88), (46, 60)], *NEG[:1], w=10, c2=NEG[1])
    for t in (0.3, 0.6):
        x, y = 14 + 32 * t, 88 - 28 * t
        p.shape("ell", (x - 1.5, y - 1.5, x + 1.5, y + 1.5), *CRO, sombra=0)


def bate(p):
    m = p.mask(lambda d: (d.line([(u(16), u(86)), (u(48), u(54))], fill=255, width=int(u(6))),
                          d.polygon([(u(42), u(56)), (u(78), u(10)), (u(92), u(24)), (u(48), u(62))], fill=255),
                          d.ellipse([u(78), u(8), u(94), u(26)], fill=255),
                          d.ellipse([u(10), u(82), u(22), u(94)], fill=255)))
    p.fill(m, *MAD, vertical=False, y0=10, y1=94)
    p.linea([(16, 86), (30, 72)], *NEG[:1], w=6.5, c2=NEG[1])
    p.brillo((54, 30, 86, 40), 90, 2)


def pala(p):
    p.linea([(12, 10), (58, 62)], *MAD[:1], w=4.5, c2=MAD[1])
    p.linea([(8, 14), (18, 4)], *NEG[:1], w=4, c2=NEG[1])
    p.poly([(52, 60), (66, 46), (92, 76), (86, 92), (70, 88)], *MET, y0=46, y1=92)
    p.brillo((62, 52, 80, 70), 90, 2)


def taco(p):
    p.linea([(8, 92), (92, 8)], (235, 205, 150), 2.2, c2=(150, 100, 50))
    p.linea([(8, 92), (34, 66)], (40, 40, 45), 4.2)
    p.linea([(90, 10), (93, 7)], (90, 150, 220), 2.4, sombra=0)


def katana(p):
    m = p.mask(lambda d: d.polygon([(u(36), u(62)), (u(86), u(8)), (u(92), u(6)), (u(90), u(14)), (u(40), u(66))], fill=255))
    p.fill(m, *CRO, vertical=False, y0=36, y1=92)
    p.shape("ell", (30, 56, 46, 72), *ORO, borde=3)
    p.linea([(10, 92), (36, 66)], (40, 30, 30), 6)
    d = ImageDraw.Draw(p.img)
    for t in (0.2, 0.4, 0.6, 0.8):
        x, y = 10 + 26 * t, 92 - 26 * t
        d.line([(u(x - 2), u(y - 2)), (u(x + 2), u(y + 2))], fill=(200, 180, 140, 255), width=int(u(1.2)))


# ---------- Armas de fuego (acostadas, mirando a la derecha) ----------

def _pistola(p, largo=64, cuerpo=MET, alto=13):
    x0, y0 = 14, 34
    p.poly([(x0 + 10, y0 + alto - 1), (x0 + 26, y0 + alto - 1), (x0 + 22, y0 + alto + 34), (x0 + 6, y0 + alto + 32)], *NEG,
           vertical=False, y0=x0, y1=x0 + 26)
    p.linea([(x0 + 26, y0 + alto + 2), (x0 + 30, y0 + alto + 10), (x0 + 40, y0 + alto + 10), (x0 + 42, y0 + alto + 1)], *NEG[:1], w=2, c2=NEG[1])
    p.shape("rect", (x0, y0, x0 + largo, y0 + alto), *cuerpo, r=2)
    p.shape("rect", (x0 + 4, y0 + alto - 2, x0 + largo - 6, y0 + alto + 3), *NEG, r=1)
    d = ImageDraw.Draw(p.img)
    for k in range(4):
        x = x0 + 6 + k * 3
        d.line([(u(x), u(y0 + 2)), (u(x), u(y0 + alto - 3))], fill=(20, 20, 24, 255), width=int(u(0.8)))
    _boca(p, x0 + largo, y0 + 3, y0 + 7)
    p.brillo((x0 + 2, y0 + 1, x0 + largo - 2, y0 + 4), 130, 1.0, ell=False)
    return x0, y0


def pistola(p):
    _pistola(p)


def pistola_silenciador(p):
    x0, y0 = _pistola(p, largo=52)
    p.shape("rect", (x0 + 50, y0 + 1, x0 + 84, y0 + 10), *NEG, r=3)
    p.brillo((x0 + 52, y0 + 2, x0 + 82, y0 + 4), 90, 0.8, ell=False)


def desert_eagle(p):
    x0, y0 = _pistola(p, largo=70, cuerpo=CRO, alto=16)
    p.shape("rect", (x0 + 6, y0 - 3, x0 + 66, y0 + 1), *CRO, r=1)


def _largo(p, ang=-28):
    _girar(p, ang)


def escopeta(p):
    p.poly([(4, 46), (28, 44), (32, 58), (6, 70)], *MAD, y0=44, y1=70)             # culata
    p.shape("rect", (26, 42, 46, 56), *MET, r=2)                                    # cajón
    p.shape("rect", (44, 44, 96, 49), *MET, r=1)                                    # caño
    p.shape("rect", (48, 50, 86, 54), *NEG, r=1)                                    # tubo
    p.shape("rect", (56, 49, 74, 57), *MAD, r=2)                                    # corredera
    p.linea([(32, 56), (36, 62), (42, 62), (44, 56)], *NEG[:1], w=1.6, c2=NEG[1])
    _boca(p, 96, 44.5, 48.5)
    p.brillo((44, 44, 94, 46), 110, 0.8, ell=False)
    _largo(p)


def recortada(p):
    p.poly([(14, 52), (30, 48), (36, 60), (20, 80), (10, 76)], *MAD, y0=48, y1=80)
    p.shape("rect", (30, 44, 50, 58), *MET, r=2)
    p.shape("rect", (48, 44, 86, 50), *MET, r=1)
    p.shape("rect", (48, 50, 86, 56), *MET, r=1)
    p.shape("rect", (52, 56, 74, 60), *MAD, r=1.5)
    _boca(p, 86, 45, 49)
    _boca(p, 86, 51, 55)
    p.brillo((48, 44.5, 84, 46), 110, 0.8, ell=False)
    _girar(p, -18)


def escopeta_combate(p):
    p.poly([(4, 44), (26, 44), (26, 52), (8, 62)], *NEG, y0=44, y1=62)
    p.poly([(30, 54), (38, 54), (34, 72), (26, 70)], *NEG, vertical=False, y0=26, y1=38)
    p.shape("rect", (24, 40, 50, 55), *NEG, r=2)
    p.shape("rect", (48, 42, 96, 48), *MET, r=1)
    p.shape("rect", (50, 49, 88, 54), *NEG, r=1)
    p.shape("rect", (60, 48, 78, 57), (55, 55, 60), (20, 20, 24), r=2)
    _boca(p, 96, 43, 47)
    p.brillo((48, 42.5, 94, 44.5), 110, 0.8, ell=False)
    _largo(p)


def uzi(p):
    p.shape("rect", (18, 34, 76, 52), *MET, r=3)
    p.shape("rect", (74, 39, 88, 45), *MET, r=1)
    p.poly([(38, 50), (50, 50), (48, 90), (36, 90)], *NEG, vertical=False, y0=36, y1=50)
    p.linea([(50, 54), (54, 62), (62, 62), (62, 52)], *NEG[:1], w=1.8, c2=NEG[1])
    p.shape("rect", (22, 30, 40, 35), *NEG, r=1)
    _boca(p, 88, 40, 44)
    p.brillo((20, 35, 74, 38), 120, 0.9, ell=False)


def mp5(p):
    p.poly([(4, 40), (22, 42), (22, 52), (6, 58)], *NEG, y0=40, y1=58)
    p.shape("rect", (20, 38, 70, 52), *NEG, r=3)
    p.shape("rect", (68, 42, 92, 47), *MET, r=1)
    p.shape("rect", (60, 47, 76, 56), (55, 55, 60), (20, 20, 24), r=2)
    m = p.mask(lambda d: d.polygon([(u(44), u(50)), (u(52), u(50)), (u(58), u(80)), (u(50), u(82))], fill=255))
    p.fill(m, *MET, vertical=False, y0=44, y1=58)
    p.poly([(28, 50), (36, 50), (33, 68), (25, 66)], *NEG, vertical=False, y0=25, y1=36)
    _boca(p, 92, 43, 46)
    p.brillo((22, 39, 68, 42), 110, 0.8, ell=False)
    _girar(p, -12)


def tec9(p):
    p.shape("rect", (14, 36, 70, 52), *NEG, r=3)
    p.shape("rect", (68, 40, 90, 46), *MET, r=1)
    p.shape("rect", (70, 38, 88, 48), (60, 60, 64), (25, 25, 28), r=2, sombra=0.3)
    p.poly([(46, 50), (56, 50), (56, 86), (46, 86)], *MET, vertical=False, y0=46, y1=56)
    p.poly([(20, 50), (32, 50), (30, 76), (18, 74)], *NEG, vertical=False, y0=18, y1=32)
    _boca(p, 90, 41, 45)
    p.brillo((16, 37, 68, 40), 110, 0.8, ell=False)


def ak47(p):
    p.poly([(2, 42), (26, 44), (26, 52), (4, 62)], *MAD, y0=42, y1=62)
    p.shape("rect", (24, 40, 56, 52), *MET, r=2)
    p.shape("rect", (54, 42, 72, 50), *MAD, r=2)
    p.shape("rect", (70, 43, 97, 46.5), *MET, r=1)
    p.shape("rect", (72, 39, 84, 42.5), *MET, r=1)
    m = p.mask(lambda d: d.chord([u(30), u(36), u(64), u(86)], 20, 110, fill=255))
    m = p.mask(lambda d: d.polygon([(u(42), u(50)), (u(52), u(50)), (u(58), u(64)), (u(54), u(78)), (u(46), u(76)), (u(48), u(64))], fill=255))
    p.fill(m, *MET, y0=50, y1=78)
    p.poly([(28, 50), (36, 50), (32, 66), (24, 64)], *MAD, vertical=False, y0=24, y1=36)
    _boca(p, 97, 43.5, 46)
    p.brillo((26, 41, 54, 43), 110, 0.8, ell=False)
    _largo(p)


def m4(p):
    p.poly([(2, 42), (24, 42), (24, 52), (4, 58)], *NEG, y0=42, y1=58)
    p.shape("rect", (22, 40, 58, 52), *NEG, r=2)
    p.shape("rect", (30, 34, 50, 40), *NEG, r=1.5)
    p.shape("rect", (56, 41, 78, 50), (60, 62, 66), (25, 26, 30), r=2)
    p.shape("rect", (76, 43, 97, 46), *MET, r=1)
    p.poly([(42, 50), (50, 50), (52, 74), (44, 74)], *MET, vertical=False, y0=42, y1=52)
    p.poly([(28, 50), (35, 50), (31, 66), (24, 64)], *NEG, vertical=False, y0=24, y1=35)
    _boca(p, 97, 43.5, 45.5)
    p.brillo((24, 41, 56, 43), 100, 0.8, ell=False)
    _largo(p)


def rifle_caza(p):
    p.poly([(2, 44), (30, 44), (34, 54), (4, 64)], *MAD, y0=44, y1=64)
    p.shape("rect", (30, 42, 52, 52), *MET, r=2)
    p.shape("rect", (50, 44, 80, 51), *MAD, r=2)
    p.shape("rect", (50, 43, 98, 46.5), *MET, r=1)
    p.linea([(44, 41), (46, 36)], (180, 182, 190), 1.4)
    p.linea([(34, 52), (38, 58), (44, 58), (46, 52)], *NEG[:1], w=1.4, c2=NEG[1])
    _boca(p, 98, 43.5, 46)
    p.brillo((50, 43.5, 96, 45), 100, 0.7, ell=False)
    _largo(p)


def francotirador(p):
    p.poly([(2, 44), (28, 44), (32, 54), (4, 64)], *NEG, y0=44, y1=64)
    p.shape("rect", (28, 42, 54, 52), *NEG, r=2)
    p.shape("rect", (52, 44, 80, 50), *NEG, r=2)
    p.shape("rect", (52, 43.5, 98, 46.5), *MET, r=1)
    p.shape("rect", (30, 32, 60, 38), *MET, r=2.5)                                  # mira
    p.shape("rect", (26, 30, 32, 40), *MET, r=1.5)
    p.shape("rect", (58, 30, 64, 40), *MET, r=1.5)
    p.linea([(38, 38), (38, 42)], *NEG[:1], w=2)
    p.linea([(52, 38), (52, 42)], *NEG[:1], w=2)
    p.shape("ell", (60, 31, 64, 39), (120, 170, 230), (30, 60, 120), sombra=0)
    _boca(p, 98, 44, 46)
    p.brillo((30, 32.5, 58, 34), 120, 0.7, ell=False)
    _largo(p)


# ---------- Balas (una caja de munición por tipo) ----------

def _balas_color(p, punta, casquillo, largo):
    """Tres balas: punta y casquillo de colores distintos según el tipo; largo de 0 a 1."""
    alto = 30 + 40 * largo
    y = 92 - alto
    for x in (20, 42, 64):
        p.shape("rect", (x, y + alto * 0.42, x + 16, 90), *casquillo, vertical=False, y0=x, y1=x + 16, r=1.5)
        p.shape("rect", (x - 1, 84, x + 17, 91), casquillo[0], casquillo[1], vertical=False, y0=x, y1=x + 16, r=1.5)
        p.shape("ell", (x, y, x + 16, y + alto * 0.9), *punta, vertical=False, y0=x, y1=x + 16)
        p.img.paste((0, 0, 0, 0), [int(u(x - 1)), int(u(y + alto * 0.42)), int(u(x + 17)), int(u(y + alto * 0.42 + 2))])
        p.brillo((x + 3, y + 6, x + 6, 86), 150, 0.9, ell=False)


LATON = ((255, 215, 110), (170, 115, 30))
COBRE = ((215, 140, 90), (120, 60, 30))


def balas_pistola(p):
    _balas_color(p, COBRE, LATON, 0.15)


def cartuchos(p):
    # cartuchos de escopeta: cuerpo rojo de plástico y base de latón
    for x in (18, 41, 64):
        p.shape("rect", (x, 20, x + 18, 74), (230, 60, 50), (140, 25, 25), vertical=False, y0=x, y1=x + 18, r=3)
        p.shape("rect", (x - 1, 72, x + 19, 92), *LATON, vertical=False, y0=x, y1=x + 18, r=2)
        p.linea([(x + 1, 76), (x + 17, 76)], (150, 100, 25), 0.9, sombra=0)
        p.brillo((x + 3, 24, x + 6, 88), 140, 0.9, ell=False)


def balas_subfusil(p):
    _balas_color(p, ((200, 200, 205), (110, 110, 118)), LATON, 0.3)


def balas_asalto(p):
    _balas_color(p, COBRE, LATON, 0.7)


def balas_rifle(p):
    _balas_color(p, ((235, 235, 240), (140, 140, 150)), LATON, 1.0)


def _ajustado(fn, lado=90):
    """Agranda el dibujo hasta llenar el cuadrado (lado de 100), así todos los íconos se ven del mismo tamaño."""
    def f(p):
        fn(p)
        caja = p.img.getchannel("A").getbbox()
        if not caja:
            return
        recorte = p.img.crop(caja)
        k = u(lado) / max(recorte.size)
        recorte = recorte.resize((max(1, int(recorte.width * k)), max(1, int(recorte.height * k))), Image.LANCZOS)
        p.img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        p.img.alpha_composite(recorte, ((N - recorte.width) // 2, (N - recorte.height) // 2))
    f.__name__ = fn.__name__
    return f


# id del objeto (tabla objetos) -> ícono. La tienda usa los de iconos.POR_ID.
MAS_POR_ID = {
    11: cana, 12: latas, 13: botellas, 14: ropa, 15: radio_vieja, 16: anteojos, 17: bolso, 18: maletin, 19: reloj,
    20: manopla, 21: palo_golf, 22: porra, 23: cuchillo, 24: bate, 25: pala, 26: taco, 27: katana,
    28: pistola, 29: pistola_silenciador, 30: desert_eagle, 31: escopeta, 32: recortada, 33: escopeta_combate,
    34: uzi, 35: mp5, 36: tec9, 37: ak47, 38: m4, 39: rifle_caza, 40: francotirador,
    41: balas_pistola, 42: cartuchos, 43: balas_subfusil, 44: balas_asalto, 45: balas_rifle,
}
MAS_POR_ID = {k: _ajustado(f) for k, f in MAS_POR_ID.items()}
