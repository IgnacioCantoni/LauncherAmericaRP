# Íconos con volumen: degradés, sombra interna en los bordes, brillos y sombra en el piso. Sin trazo negro.
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math

N = 640
K = N / 100.0


def u(v):
    return v * K


class R:
    def __init__(self):
        self.img = Image.new("RGBA", (N, N), (0, 0, 0, 0))

    def mask(self, fn):
        m = Image.new("L", (N, N), 0)
        fn(ImageDraw.Draw(m))
        return m

    def grad(self, c1, c2, vertical=True, y0=0, y1=100):
        """Degradé lineal de c1 a c2 entre y0 e y1 (o x0..x1 si no es vertical)."""
        tira = Image.new("RGBA", (1, N))
        a, b = u(y0), u(y1)
        for i in range(N):
            t = min(1, max(0, (i - a) / max(1, b - a)))
            tira.putpixel((0, i), tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)) + (255,))
        g = tira.resize((N, N), Image.NEAREST)
        if not vertical:
            g = g.transpose(Image.TRANSPOSE)
        return g

    def fill(self, m, c1, c2=None, vertical=True, y0=0, y1=100, sombra=0.55, borde=6):
        c2 = c2 or c1
        g = self.grad(c1, c2, vertical, y0, y1)
        lay = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        lay.paste(g, (0, 0), m)
        if sombra:
            # oscurece el contorno por dentro: da volumen
            bl = m.filter(ImageFilter.GaussianBlur(u(borde) / 2))
            edge = ImageChops.subtract(m, bl).point(lambda v: min(255, int(v * 2.2 * sombra)))
            dark = Image.new("RGBA", (N, N), (0, 0, 0, 255))
            dark.putalpha(edge)
            lay.alpha_composite(dark)
            lay.putalpha(ImageChops.multiply(lay.getchannel("A"), m))
        self.img.alpha_composite(lay)

    def shape(self, kind, box, c1, c2=None, r=0, **kw):
        b = [u(v) for v in box]
        if kind == "rect":
            m = self.mask(lambda d: d.rounded_rectangle(b, radius=u(r), fill=255))
        elif kind == "ell":
            m = self.mask(lambda d: d.ellipse(b, fill=255))
        self.fill(m, c1, c2, y0=kw.pop("y0", box[1]), y1=kw.pop("y1", box[3]), **kw)
        return m

    def poly(self, pts, c1, c2=None, y0=None, y1=None, **kw):
        q = [(u(x), u(y)) for x, y in pts]
        m = self.mask(lambda d: d.polygon(q, fill=255))
        ys = [p[1] for p in pts]
        self.fill(m, c1, c2, y0=min(ys) if y0 is None else y0, y1=max(ys) if y1 is None else y1, **kw)
        return m

    def linea(self, pts, color, w, c2=None, **kw):
        q = [(u(x), u(y)) for x, y in pts]

        def f(d):
            d.line(q, fill=255, width=int(u(w)), joint="curve")
            for x, y in (q[0], q[-1]):
                rr = u(w) / 2
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
        m = self.mask(f)
        self.fill(m, color, c2 or color, vertical=False, y0=min(p[0] for p in pts) - w, y1=max(p[0] for p in pts) + w, borde=w, **kw)

    def brillo(self, box, a=150, blur=2.0, ell=True, color=(255, 255, 255)):
        lay = Image.new("RGBA", (N, N), color + (0,))
        m = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(m)
        (d.ellipse if ell else d.rectangle)([u(v) for v in box], fill=a)
        lay.putalpha(ImageChops.multiply(m.filter(ImageFilter.GaussianBlur(u(blur))), self.img.getchannel("A")))
        self.img.alpha_composite(lay)

    def puntos(self, lista, color, r):
        d = ImageDraw.Draw(self.img)
        for x, y in lista:
            d.ellipse([u(x - r), u(y - r * 0.6), u(x + r), u(y + r * 0.6)], fill=color)

    def done(self, px, piso=True):
        out = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        if piso:
            a = self.img.getchannel("A")
            sh = Image.new("RGBA", (N, N), (0, 0, 0, 0))
            sh.putalpha(a.point(lambda v: v * 0.55).filter(ImageFilter.GaussianBlur(u(2.2))))
            out.alpha_composite(sh, (int(u(1.2)), int(u(2.4))))
        out.alpha_composite(self.img)
        return out.resize((px, px), Image.LANCZOS)


PAN = ((246, 214, 160), (196, 140, 72))


def sandwich(p):
    p.poly([(12, 56), (52, 18), (90, 56)], (250, 228, 185), (222, 180, 120))
    p.poly([(16, 52), (52, 22), (86, 52)], (255, 240, 210), (240, 210, 160), sombra=0.2)
    p.poly([(9, 55), (18, 51), (28, 56), (38, 51), (48, 56), (58, 51), (68, 56), (78, 51), (91, 55), (91, 62), (9, 62)], (120, 200, 70), (60, 140, 40))
    p.shape("rect", (11, 60, 89, 67), (235, 80, 60), (170, 40, 35), r=3)
    p.shape("rect", (10, 66, 90, 72), (255, 215, 80), (225, 165, 40), r=2)
    p.shape("rect", (11, 71, 89, 85), (240, 205, 150), (190, 135, 70), r=4)
    p.brillo((30, 30, 52, 40), 90, 3)


def hamburguesa(p):
    p.shape("ell", (12, 18, 88, 70), (245, 175, 85), (190, 110, 40), y0=18, y1=48)
    p.img.paste((0, 0, 0, 0), [0, int(u(46)), N, N])
    p.puntos([(32, 30), (46, 25), (60, 30), (40, 37), (54, 36), (68, 38), (26, 39)], (255, 240, 200, 255), 1.8)
    p.brillo((26, 22, 54, 32), 120, 3)
    p.poly([(10, 47), (90, 47), (86, 56), (76, 52), (66, 57), (56, 52), (46, 57), (36, 52), (26, 57), (14, 53)], (140, 215, 80), (60, 140, 40))
    p.poly([(14, 50), (86, 50), (80, 58), (20, 58)], (255, 205, 60), (230, 160, 30))
    p.shape("rect", (12, 54, 88, 65), (140, 70, 45), (80, 35, 20), r=5)
    p.shape("rect", (14, 64, 86, 80), (235, 165, 80), (170, 100, 40), r=7)


def pizza(p):
    p.poly([(50, 90), (14, 24), (86, 24)], (255, 215, 90), (240, 170, 50))
    p.shape("rect", (10, 15, 90, 28), (230, 165, 85), (170, 100, 40), r=7)
    p.brillo((20, 16, 60, 20), 100, 2)
    for x, y in ((36, 36), (57, 34), (47, 53), (44, 70), (60, 49)):
        p.shape("ell", (x, y, x + 11, y + 10), (225, 70, 55), (150, 30, 25), borde=4)
        p.brillo((x + 2, y + 1, x + 6, y + 4), 140, 0.8)


def agua(p):
    p.shape("rect", (40, 6, 60, 17), (70, 140, 240), (20, 70, 170), r=2)
    p.poly([(41, 17), (59, 17), (61, 25), (39, 25)], (215, 235, 250), (170, 205, 235), sombra=0.3)
    p.poly([(39, 25), (61, 25), (72, 38), (72, 88), (68, 93), (32, 93), (28, 88), (28, 38)], (200, 230, 252), (120, 180, 230), vertical=False, y0=28, y1=72, sombra=0.4)
    p.shape("rect", (28, 50, 72, 70), (60, 130, 230), (25, 80, 180), vertical=False, y0=28, y1=72, sombra=0.3)
    p.brillo((32, 30, 38, 88), 200, 1.2, ell=False)
    p.brillo((62, 34, 66, 86), 80, 1.5, ell=False)


def gaseosa(p):
    p.shape("rect", (26, 14, 74, 90), (240, 60, 55), (150, 20, 20), vertical=False, y0=26, y1=74, r=8)
    p.shape("rect", (29, 9, 71, 17), (235, 235, 240), (150, 150, 160), vertical=False, y0=29, y1=71, r=3)
    p.shape("rect", (29, 87, 71, 94), (220, 220, 228), (140, 140, 150), vertical=False, y0=29, y1=71, r=3)
    lay = R()
    m = lay.mask(lambda d: (d.ellipse([u(20), u(40), u(80), u(62)], fill=255), d.ellipse([u(20), u(47), u(80), u(69)], fill=0)))
    m = ImageChops.multiply(m, p.mask(lambda d: d.rectangle([u(26), 0, u(74), N], fill=255)))
    p.fill(m, (255, 255, 255), (220, 220, 225), sombra=0.15)
    p.brillo((33, 20, 39, 84), 170, 1.5, ell=False)


def energizante(p):
    p.shape("rect", (28, 12, 72, 92), (60, 62, 70), (15, 15, 20), vertical=False, y0=28, y1=72, r=7)
    p.shape("rect", (31, 7, 69, 15), (235, 235, 240), (140, 140, 150), vertical=False, y0=31, y1=69, r=3)
    p.poly([(57, 22), (38, 56), (50, 56), (43, 82), (65, 45), (53, 45), (61, 22)], (215, 255, 80), (120, 200, 20), sombra=0.3)
    p.brillo((33, 18, 38, 86), 120, 1.5, ell=False)


def celular(p):
    p.shape("rect", (27, 5, 73, 95), (80, 82, 90), (25, 25, 30), vertical=False, y0=27, y1=73, r=10)
    p.shape("rect", (31, 10, 69, 90), (20, 20, 24), r=7, sombra=0)
    p.shape("rect", (33, 13, 67, 87), (110, 170, 255), (110, 60, 200), r=5, sombra=0.2)
    for i in range(3):
        for j in range(3):
            x, y = 37 + i * 10, 34 + j * 12
            p.shape("rect", (x, y, x + 7, y + 7), (255, 255, 255), (210, 220, 240), r=2, sombra=0.2)
    p.shape("rect", (43, 15, 57, 18), (10, 10, 12), r=1.5, sombra=0)
    lay = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).polygon([(u(33), u(13)), (u(55), u(13)), (u(33), u(50))], fill=55)
    lay.putalpha(m)
    p.img.alpha_composite(lay)


def tarjeta(p):
    p.shape("rect", (7, 23, 93, 79), (70, 120, 210), (20, 50, 120), vertical=False, y0=7, y1=93, r=7)
    p.brillo((-20, 10, 60, 50), 60, 6)
    p.shape("rect", (16, 48, 32, 61), (250, 215, 110), (190, 140, 40), r=2.5, sombra=0.4)
    for x in range(40, 86, 12):
        p.shape("rect", (x, 66, x + 9, 70), (220, 230, 250), r=1.5, sombra=0)
    p.shape("rect", (68, 30, 86, 40), (235, 160, 40), (200, 60, 40), vertical=False, y0=68, y1=86, r=5, sombra=0.2)


def radio(p):
    p.linea([(64, 32), (76, 5)], (60, 60, 64), 4.5)
    p.shape("rect", (23, 27, 77, 95), (85, 92, 100), (30, 32, 36), vertical=False, y0=23, y1=77, r=9)
    p.shape("rect", (31, 34, 69, 52), (170, 240, 160), (80, 170, 80), r=3, sombra=0.6)
    for j in range(4):
        p.shape("rect", (31, 59 + j * 8, 69, 63 + j * 8), (25, 25, 28), r=2, sombra=0)
    p.shape("ell", (64, 20, 72, 28), (230, 60, 50), (140, 20, 20), borde=3)
    p.brillo((26, 30, 31, 90), 90, 1.2, ell=False)


def mochila(p):
    p.linea([(37, 24), (37, 12), (63, 12), (63, 24)], (120, 70, 35), 5)
    p.shape("rect", (19, 19, 81, 93), (195, 125, 65), (120, 65, 30), vertical=False, y0=19, y1=81, r=17)
    p.shape("rect", (19, 19, 81, 50), (205, 135, 75), (150, 85, 40), r=17, sombra=0.5)
    p.shape("rect", (29, 55, 71, 86), (165, 100, 50), (105, 55, 25), r=7)
    p.shape("rect", (29, 54, 71, 62), (130, 75, 35), (95, 50, 20), r=3, sombra=0.3)
    p.shape("rect", (45, 51, 55, 66), (250, 215, 110), (180, 130, 40), r=2, sombra=0.4)
    p.brillo((26, 24, 40, 46), 70, 3)


def botiquin(p):
    p.shape("rect", (37, 12, 63, 26), (210, 210, 215), (130, 130, 140), r=5)
    p.img.paste((0, 0, 0, 0), [int(u(42)), int(u(17)), int(u(58)), int(u(23))])
    p.shape("rect", (9, 23, 91, 89), (250, 250, 252), (195, 195, 205), r=9)
    p.shape("rect", (44, 35, 57, 78), (240, 70, 65), (170, 25, 25), r=1.5, sombra=0.3)
    p.shape("rect", (29, 50, 72, 63), (240, 70, 65), (170, 25, 25), r=1.5, sombra=0.3)
    p.brillo((14, 26, 86, 34), 120, 2)


def balas(p):
    for x in (20, 42, 64):
        p.shape("rect", (x, 44, x + 16, 90), (255, 215, 110), (170, 115, 30), vertical=False, y0=x, y1=x + 16, r=1.5)
        p.shape("rect", (x - 1, 84, x + 17, 91), (220, 170, 70), (140, 90, 20), vertical=False, y0=x, y1=x + 16, r=1.5)
        p.shape("ell", (x, 18, x + 16, 62), (215, 140, 90), (120, 60, 30), vertical=False, y0=x, y1=x + 16)
        p.img.paste((0, 0, 0, 0), [int(u(x - 1)), int(u(44)), int(u(x + 17)), int(u(46))])
        p.brillo((x + 3, 24, x + 6, 86), 150, 0.9, ell=False)


def latas(p):
    p.poly([(14, 42), (58, 30), (66, 72), (22, 86)], (200, 205, 215), (120, 125, 135), vertical=False, y0=14, y1=66)
    p.poly([(26, 46), (56, 38), (58, 48), (28, 56)], (230, 70, 60), (160, 30, 30), sombra=0.2)
    p.shape("rect", (50, 34, 86, 92), (230, 232, 238), (130, 135, 145), vertical=False, y0=50, y1=86, r=6)
    p.shape("rect", (50, 50, 86, 70), (60, 120, 210), (30, 60, 140), vertical=False, y0=50, y1=86, sombra=0.2)
    p.brillo((54, 38, 58, 88), 160, 1.0, ell=False)


def cana(p):
    p.linea([(16, 90), (84, 8)], (180, 120, 60), 3.5, c2=(110, 65, 25))
    p.linea([(16, 90), (32, 71)], (40, 40, 44), 6)
    ImageDraw.Draw(p.img).line([(u(84), u(8)), (u(86), u(62))], fill=(235, 235, 240, 220), width=int(u(0.8)))
    p.shape("ell", (24, 64, 42, 82), (180, 185, 195), (80, 85, 95), borde=4)
    p.shape("ell", (30, 70, 36, 76), (60, 60, 65), sombra=0)
    p.linea([(86, 62), (86, 69), (82, 71)], (200, 200, 205), 1.6)


def llaves(p):
    ORO = ((255, 225, 120), (190, 140, 40))
    p.linea([(42, 42), (86, 86)], *ORO[:1], w=8, c2=ORO[1])
    for a, b in (((70, 70), (79, 61)), ((80, 80), (89, 71))):
        p.linea([a, b], ORO[0], 7, c2=ORO[1])
    m = p.mask(lambda d: (d.ellipse([u(10), u(10), u(50), u(50)], fill=255), d.ellipse([u(22), u(22), u(34), u(34)], fill=0)))
    p.fill(m, ORO[0], ORO[1], y0=10, y1=50)
    p.brillo((16, 14, 30, 24), 160, 1.5)


def insumos(p):
    p.shape("rect", (9, 33, 91, 67), (255, 255, 255), (190, 195, 205), r=17)
    m = p.mask(lambda d: d.rounded_rectangle([u(9), u(33), u(91), u(67)], radius=u(17), fill=255))
    m = ImageChops.multiply(m, p.mask(lambda d: d.rectangle([0, 0, u(50), N], fill=255)))
    p.fill(m, (90, 175, 245), (30, 90, 180), y0=33, y1=67)
    p.brillo((16, 37, 82, 44), 170, 1.5)


def venda(p):
    # caja de insumos (gasas) en perspectiva: tapa, frente azul y blanco, cruz azul
    p.poly([(14, 30), (64, 30), (86, 16), (36, 16)], (250, 252, 255), (215, 222, 235))
    p.poly([(64, 30), (86, 16), (86, 70), (64, 88)], (185, 195, 212), (140, 150, 170), vertical=False, y0=64, y1=86)
    p.shape("rect", (14, 30, 64, 88), (255, 255, 255), (205, 212, 225), r=1)
    p.shape("rect", (14, 30, 64, 42), (60, 130, 220), (30, 80, 170), r=1, sombra=0.3)
    p.shape("rect", (34, 50, 44, 80), (60, 130, 220), (30, 80, 170), r=1, sombra=0.2)
    p.shape("rect", (24, 60, 54, 70), (60, 130, 220), (30, 80, 170), r=1, sombra=0.2)
    p.poly([(64, 30), (86, 16), (86, 26), (64, 42)], (45, 105, 195), (25, 70, 150), sombra=0.2)


def frasco(p):
    # frasco de remedio naranja con tapa blanca y etiqueta
    p.shape("rect", (26, 8, 74, 26), (255, 255, 255), (190, 195, 205), vertical=False, y0=26, y1=74, r=4)
    for x in range(30, 72, 5):
        ImageDraw.Draw(p.img).line([(u(x), u(10)), (u(x), u(24))], fill=(180, 185, 195, 255), width=int(u(0.7)))
    p.shape("rect", (29, 25, 71, 94), (245, 160, 50), (175, 85, 15), vertical=False, y0=29, y1=71, r=6)
    p.shape("rect", (29, 44, 71, 78), (250, 250, 252), (215, 218, 225), vertical=False, y0=29, y1=71, sombra=0.25)
    p.shape("rect", (35, 50, 50, 54), (220, 60, 50), r=1, sombra=0)
    for j in range(3):
        p.shape("rect", (35, 58 + j * 6, 64 - j * 6, 61 + j * 6), (150, 155, 165), r=1, sombra=0)
    p.brillo((32, 28, 37, 90), 150, 1.2, ell=False)


# ---------- Íconos del HUD sin CEF (van chicos, dentro de los círculos oscuros: formas simples y llenas) ----------

def hud_hambre(p):
    # tenedor y cuchillo plateados
    PL = ((250, 252, 255), (140, 148, 160))
    for x in (17, 27, 37):
        p.shape("rect", (x, 6, x + 6, 36), *PL, vertical=False, y0=x, y1=x + 6, r=3, borde=3)
    p.shape("rect", (15, 30, 45, 44), *PL, vertical=False, y0=15, y1=45, r=6, borde=3)
    p.shape("rect", (25, 40, 35, 94), *PL, vertical=False, y0=25, y1=35, r=5, borde=3)
    m = p.mask(lambda d: (d.pieslice([u(56), u(6), u(88), u(76)], 90, 270, fill=255), d.rectangle([u(71), u(6), u(80), u(50)], fill=255)))
    p.fill(m, *PL, vertical=False, y0=56, y1=80, borde=3)
    p.shape("rect", (67, 48, 79, 94), *PL, vertical=False, y0=67, y1=79, r=5, borde=3)
    p.brillo((19, 8, 21, 34), 200, 0.6, ell=False)
    p.brillo((60, 12, 64, 60), 170, 0.8, ell=False)


def hud_sed(p):
    m = p.mask(lambda d: (d.polygon([(u(50), u(4)), (u(20), u(56)), (u(80), u(56))], fill=255), d.ellipse([u(18), u(36), u(82), u(96)], fill=255)))
    p.fill(m, (140, 215, 255), (20, 100, 220), y0=10, y1=96, borde=8)
    p.brillo((30, 50, 42, 80), 210, 1.5)
    p.brillo((56, 74, 70, 86), 90, 2)


def hud_cansancio(p):
    m = p.mask(lambda d: (d.ellipse([u(8), u(8), u(92), u(92)], fill=255), d.ellipse([u(32), u(-6), u(108), u(70)], fill=0)))
    p.fill(m, (255, 248, 200), (225, 180, 70), vertical=False, y0=8, y1=70, borde=8)
    p.brillo((14, 34, 26, 70), 150, 2)
    for x, y, r in ((30, 70, 4), (48, 80, 3), (22, 52, 2.5)):
        p.shape("ell", (x - r, y - r, x + r, y + r), (215, 170, 70), (180, 135, 50), borde=2, sombra=0.4)


def hud_auto(p):
    p.poly([(24, 26), (70, 26), (84, 48), (12, 48)], (235, 60, 55), (170, 25, 25))
    p.poly([(29, 31), (47, 31), (47, 46), (19, 46)], (190, 225, 250), (90, 140, 190), sombra=0.3)
    p.poly([(51, 31), (67, 31), (77, 46), (51, 46)], (190, 225, 250), (90, 140, 190), sombra=0.3)
    p.shape("rect", (4, 44, 96, 72), (240, 70, 60), (150, 20, 20), r=9)
    p.brillo((10, 47, 90, 52), 150, 1.2)
    p.shape("rect", (4, 56, 14, 62), (255, 230, 120), (220, 170, 50), r=2, sombra=0)
    for x in (14, 64):
        p.shape("ell", (x, 58, x + 24, 82), (70, 70, 76), (15, 15, 18), borde=6)
        p.shape("ell", (x + 7, 65, x + 17, 75), (220, 222, 228), (140, 145, 155), borde=3)


def hud_nafta(p):
    p.linea([(58, 34), (76, 34), (84, 46), (84, 74), (90, 80), (90, 86)], (60, 60, 64), 6)
    p.shape("rect", (78, 12, 92, 32), (70, 70, 75), (25, 25, 28), r=3)
    p.shape("rect", (10, 8, 60, 92), (240, 70, 60), (150, 20, 20), vertical=False, y0=10, y1=60, r=7)
    p.shape("rect", (18, 16, 52, 40), (210, 245, 220), (110, 180, 130), r=3, sombra=0.6)
    p.shape("rect", (4, 86, 66, 96), (90, 92, 98), (40, 40, 44), r=2)
    p.brillo((14, 44, 19, 84), 120, 1.0, ell=False)


def hud_vida(p):
    m = p.mask(lambda d: (d.ellipse([u(6), u(10), u(52), u(56)], fill=255), d.ellipse([u(48), u(10), u(94), u(56)], fill=255),
                          d.polygon([(u(9), u(42)), (u(91), u(42)), (u(50), u(92))], fill=255)))
    p.fill(m, (255, 110, 100), (175, 20, 30), y0=10, y1=92, borde=8)
    p.brillo((16, 18, 34, 34), 200, 2)


def hud_chaleco(p):
    # chaleco antibalas visto de frente: cuerpo con cuello en V y placas
    m = p.mask(lambda d: d.polygon([(u(26), u(6)), (u(40), u(6)), (u(50), u(26)), (u(60), u(6)), (u(74), u(6)), (u(88), u(22)),
                                     (u(88), u(90)), (u(12), u(90)), (u(12), u(22))], fill=255))
    p.fill(m, (150, 175, 205), (55, 75, 105), vertical=False, y0=12, y1=88, borde=8)
    p.shape("rect", (20, 40, 46, 62), (110, 135, 165), (60, 80, 110), r=3, sombra=0.4)
    p.shape("rect", (54, 40, 80, 62), (110, 135, 165), (60, 80, 110), r=3, sombra=0.4)
    p.shape("rect", (12, 70, 88, 78), (45, 60, 85), (30, 40, 60), sombra=0.2)
    p.brillo((16, 24, 24, 84), 120, 1.2, ell=False)


HUD = {"hud_hambre": hud_hambre, "hud_sed": hud_sed, "hud_cansancio": hud_cansancio, "hud_auto": hud_auto,
       "hud_nafta": hud_nafta, "hud_vida": hud_vida, "hud_chaleco": hud_chaleco}


# ---------- Apps del teléfono sin CEF (el cuadrado redondeado con su dibujo, como en un celular) ----------

def _app(p, c1, c2):
    p.shape("rect", (4, 4, 96, 96), c1, c2, r=22, borde=5, sombra=0.35)
    p.brillo((8, 6, 92, 40), 70, 4)


def _blanco(p, m):
    p.fill(m, (255, 255, 255), (225, 230, 240), borde=3, sombra=0.25)


def app_banco(p):
    _app(p, (60, 205, 120), (15, 120, 60))
    _blanco(p, p.mask(lambda d: (d.polygon([(u(50), u(18)), (u(84), u(36)), (u(16), u(36))], fill=255),
                                 d.rectangle([u(18), u(72), u(82), u(82)], fill=255),
                                 [d.rectangle([u(x), u(40), u(x + 8), u(70)], fill=255) for x in (22, 38, 54, 70)])))


def app_taxi(p):
    _app(p, (255, 215, 60), (215, 150, 0))
    p.poly([(30, 36), (68, 36), (78, 54), (20, 54)], (40, 40, 44), (15, 15, 18))
    p.poly([(34, 40), (48, 40), (48, 52), (27, 52)], (190, 225, 250), (90, 140, 190), sombra=0.2)
    p.poly([(52, 40), (66, 40), (72, 52), (52, 52)], (190, 225, 250), (90, 140, 190), sombra=0.2)
    p.shape("rect", (12, 52, 88, 72), (40, 40, 44), (15, 15, 18), r=7)
    p.shape("rect", (40, 26, 60, 34), (255, 255, 255), (220, 220, 225), r=2, sombra=0.2)
    for x in (20, 62):
        p.shape("ell", (x, 64, x + 18, 82), (90, 90, 96), (20, 20, 24), borde=4)


def app_maps(p):
    _app(p, (90, 175, 255), (20, 95, 210))
    p.linea([(10, 70), (40, 50), (60, 62), (92, 40)], (255, 255, 255), 5, c2=(225, 235, 250))
    m = p.mask(lambda d: (d.ellipse([u(32), u(14), u(68), u(50)], fill=255), d.polygon([(u(34), u(38)), (u(66), u(38)), (u(50), u(74))], fill=255),
                          d.ellipse([u(43), u(25), u(57), u(39)], fill=0)))
    p.fill(m, (255, 95, 85), (190, 25, 30), borde=5)


def app_miamerica(p):
    _app(p, (240, 80, 95), (160, 20, 45))
    pts = []
    for k in range(10):
        a = math.radians(-90 + k * 36)
        r = 36 if k % 2 == 0 else 15
        pts.append((50 + r * math.cos(a), 53 + r * math.sin(a)))
    p.poly(pts, (255, 235, 150), (230, 170, 40), sombra=0.3)


def app_llamadas(p):
    # tubo de teléfono clásico: un arco grueso con el auricular arriba a la izquierda y el micrófono abajo a la derecha
    def tubo(d):
        d.arc([u(18), u(14), u(86), u(82)], 95, 175, fill=255, width=int(u(13)))
        d.rounded_rectangle([u(14), u(20), u(36), u(48)], radius=u(7), fill=255)
        d.rounded_rectangle([u(52), u(66), u(80), u(88)], radius=u(7), fill=255)
    _app(p, (90, 230, 120), (20, 150, 60))
    _blanco(p, p.mask(tubo))


def app_mensajes(p):
    _app(p, (90, 230, 120), (20, 150, 60))
    _blanco(p, p.mask(lambda d: (d.ellipse([u(16), u(20), u(84), u(72)], fill=255),
                                 d.polygon([(u(26), u(60)), (u(40), u(66)), (u(18), u(82))], fill=255))))


def app_agenda(p):
    _app(p, (170, 178, 190), (90, 98, 112))
    _blanco(p, p.mask(lambda d: (d.ellipse([u(36), u(16), u(64), u(44)], fill=255), d.pieslice([u(20), u(48), u(80), u(108)], 180, 360, fill=255))))


# ---------- Datos de la concesionaria y formas de pago ----------

def dato_velocidad(p):
    p.shape("ell", (6, 10, 94, 98), (70, 72, 80), (20, 20, 24), borde=8)
    p.shape("ell", (14, 18, 86, 90), (35, 36, 42), (15, 15, 18), sombra=0.3)
    for k in range(7):
        a = math.radians(150 + k * 40)
        x1, y1 = 50 + 30 * math.cos(a), 54 + 30 * math.sin(a)
        x2, y2 = 50 + 24 * math.cos(a), 54 + 24 * math.sin(a)
        p.linea([(x1, y1), (x2, y2)], (255, 255, 255) if k < 5 else (255, 80, 70), 3)
    p.linea([(50, 54), (72, 34)], (255, 80, 70), 5, c2=(200, 30, 30))
    p.shape("ell", (43, 47, 57, 61), (220, 222, 228), (130, 135, 145), borde=3)


def suave(pts, n=3):
    for _ in range(n):
        q=[]
        for i in range(len(pts)):
            (x0,y0),(x1,y1)=pts[i],pts[(i+1)%len(pts)]
            q+= [(x0*.75+x1*.25,y0*.75+y1*.25),(x0*.25+x1*.75,y0*.25+y1*.75)]
        pts=q
    return pts

def costura(p, pts, color=(60,35,20,170), w=0.7):
    q=[(u(x),u(y)) for x,y in pts]
    lay=Image.new("RGBA",p.img.size,(0,0,0,0)); dl=ImageDraw.Draw(lay)
    dl.line(q, fill=color, width=max(1,int(u(w))), joint="curve")
    a=p.img.getchannel("A")
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"),a))
    p.img.alpha_composite(lay)

CL=(196,140,96); CM=(150,98,62); CO=(92,56,34); CX=(60,36,22)
def dato_asientos(p):
    # asiento de auto de costado con un poco de perspectiva: cuero, panel acolchado, costuras, varillas y riel
    # respaldo lado lejano (se ve un poco: da profundidad)
    p.poly(suave([(29,22),(45,19),(52,26),(64,62),(62,70),(50,71),(36,30)]), CM, CX, vertical=False, y0=30, y1=64)
    # respaldo: costado cercano
    back=suave([(18,26),(32,19),(44,22),(48,30),(58,64),(54,72),(36,74),(28,70),(24,56)])
    p.poly(back, CL, CO, vertical=False, y0=20, y1=58)
    # panel central acolchado (franja más clara, con costuras)
    ins=suave([(30,25),(40,23),(44,29),(53,63),(50,68),(41,68),(38,60)],2)
    p.poly(ins, (214,164,118), (150,100,64), vertical=False, y0=28, y1=58, sombra=0.35, borde=3)
    for t in (0.22,0.42,0.62,0.82):
        y=25+t*43; x0=31+t*7.5; x1=41+t*11
        costura(p, [(x0,y),(x1,y+0.6)], (70,40,22,190), 0.6)
    # apoyacabezas con varillas
    for x in (27,33):
        p.shape("rect",(x,14,x+2.6,24),(200,200,206),(110,110,118),vertical=False,y0=x,y1=x+3,sombra=0.2,borde=1)
    head=suave([(16,6),(34,3),(42,8),(41,16),(36,18),(19,19),(14,13)])
    p.poly(head, CL, CO, y0=3, y1=20)
    p.brillo((20,5,34,9),120,1.3)
    # almohadón: cara de arriba y costado
    p.poly(suave([(36,62),(80,57),(92,60),(90,66),(40,70)],2), (214,164,118),(160,108,70), y0=57, y1=68, sombra=0.35, borde=3)
    cush=suave([(34,66),(82,61),(93,63),(94,72),(88,79),(42,81),(33,76)])
    p.poly(cush, CL, CO, y0=60, y1=82)
    costura(p, [(40,69),(84,64.5),(91,66)], (70,40,22,190), 0.6)
    # tapa de plástico abajo, palanca y riel
    p.shape("rect",(40,79,88,86),(70,72,78),(30,31,35),r=2)
    p.linea([(80,83),(90,85)],(120,120,126),1.6,sombra=0.2)
    p.shape("rect",(36,86,94,92),(150,152,160),(60,62,68),r=1.5)
    # brillos del cuero
    p.brillo((22,30,30,62),95,1.6)
    p.brillo((46,62,86,66),110,1.2)
    p.brillo((60,70,90,74),60,1.5)


def dato_tanque(p):
    p.shape("rect", (56, 6, 76, 20), (60, 60, 64), (25, 25, 28), r=3)
    p.poly([(18, 18), (70, 18), (84, 32), (84, 94), (18, 94)], (235, 60, 50), (150, 20, 20), vertical=False, y0=18, y1=84)
    p.shape("rect", (24, 22, 50, 34), (0, 0, 0), r=4, sombra=0)
    p.linea([(32, 46), (70, 84)], (190, 35, 30), 5)
    p.linea([(70, 46), (32, 84)], (190, 35, 30), 5)
    p.brillo((22, 40, 27, 90), 120, 1.0, ell=False)


def dato_maletero(p):
    p.shape("rect", (36, 8, 64, 24), (70, 70, 76), (30, 30, 34), r=5)
    p.img.paste((0, 0, 0, 0), [int(u(42)), int(u(14)), int(u(58)), int(u(24))])
    p.shape("rect", (8, 22, 92, 92), (185, 120, 65), (110, 60, 25), vertical=False, y0=8, y1=92, r=8)
    for x in (26, 70):
        p.shape("rect", (x, 22, x + 6, 92), (120, 70, 35), (80, 45, 20), sombra=0.2)
    p.brillo((12, 26, 88, 34), 90, 2)


def dato_guantera(p):
    p.shape("rect", (6, 18, 94, 86), (75, 78, 86), (30, 32, 36), r=8)
    p.shape("rect", (14, 26, 86, 78), (50, 52, 58), (25, 26, 30), r=5, sombra=0.4)
    p.shape("rect", (38, 44, 62, 54), (200, 205, 212), (120, 125, 135), r=4)
    p.brillo((10, 20, 90, 28), 80, 2)


def dato_licencia(p):
    p.shape("rect", (6, 18, 94, 82), (240, 244, 250), (190, 198, 210), vertical=False, y0=6, y1=94, r=7)
    p.shape("rect", (6, 18, 94, 32), (50, 100, 190), (25, 60, 140), r=7, sombra=0.2)
    p.img.paste((0, 0, 0, 0), [0, 0, 1, 1])
    p.shape("rect", (14, 38, 40, 72), (170, 185, 205), (110, 125, 150), r=3, sombra=0.3)
    p.shape("ell", (21, 42, 33, 54), (90, 100, 120), sombra=0)
    for j, w in enumerate((40, 32, 36)):
        p.shape("rect", (48, 42 + j * 10, 48 + w, 46 + j * 10), (140, 150, 168), r=1.5, sombra=0)


def pago_efectivo(p):
    for k, dy in enumerate((0, -10)):
        p.shape("rect", (6, 34 + dy, 94, 80 + dy), (130, 210, 120), (50, 130, 60), vertical=False, y0=6, y1=94, r=4)
        p.shape("ell", (38, 44 + dy, 62, 70 + dy), (90, 170, 90), (40, 110, 50), sombra=0.3)
    p.d = None


# ---------- Botones de la llamada en la isla del teléfono ----------

def _tubo_boton(p, c1, c2, angulo):
    p.shape("ell", (6, 6, 94, 94), c1, c2, borde=6, sombra=0.35)
    p.brillo((18, 10, 82, 40), 80, 4)

    def tubo(d):
        d.arc([u(30), u(28), u(74), u(72)], 95, 175, fill=255, width=int(u(9)))
        d.rounded_rectangle([u(27), u(32), u(41), u(50)], radius=u(5), fill=255)
        d.rounded_rectangle([u(52), u(61), u(70), u(75)], radius=u(5), fill=255)
    _blanco(p, p.mask(tubo).rotate(angulo, resample=Image.BICUBIC, center=(N / 2, N / 2)))


def tel_atender(p):
    _tubo_boton(p, (90, 230, 120), (25, 160, 65), 0)


def tel_colgar(p):
    # el tubo acostado, como el botón rojo del iPhone
    _tubo_boton(p, (255, 105, 95), (205, 40, 35), -135)


OTROS = {"app_banco": app_banco, "app_taxi": app_taxi, "app_maps": app_maps, "app_miamerica": app_miamerica,
         "app_llamadas": app_llamadas, "app_mensajes": app_mensajes, "app_agenda": app_agenda,
         "dato_velocidad": dato_velocidad, "dato_asientos": dato_asientos, "dato_tanque": dato_tanque,
         "dato_maletero": dato_maletero, "dato_guantera": dato_guantera, "dato_licencia": dato_licencia,
         "pago_efectivo": pago_efectivo, "tel_atender": tel_atender, "tel_colgar": tel_colgar}


OBJETOS = [
    ("Sándwich", sandwich), ("Hamburguesa", hamburguesa), ("Pizza", pizza),
    ("Agua", agua), ("Gaseosa", gaseosa), ("Energizante", energizante),
    ("Celular", celular), ("Tarjeta", tarjeta), ("Radio", radio),
    ("Mochila", mochila), ("Botiquín", botiquin), ("Balas", balas),
    ("Latas", latas), ("Caña", cana), ("Llaves", llaves), ("Medicamento", insumos),
]

# id del objeto (tabla objetos) -> ícono; la textura en americarp.txd se llama obj_<id>.
POR_ID = {1: sandwich, 2: hamburguesa, 3: pizza, 4: agua, 5: gaseosa, 6: energizante, 7: celular, 8: tarjeta,
          9: radio, 10: mochila, 46: botiquin, 47: venda, 48: frasco}

_cache = {}


def icono(fn, px):
    if fn not in _cache:
        p = R()
        fn(p)
        _cache[fn] = p
    return _cache[fn].done(px)
