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
         "tel_atender": tel_atender, "tel_colgar": tel_colgar}


_cache = {}


def icono(fn, px):
    if fn not in _cache:
        p = R()
        fn(p)
        _cache[fn] = p
    return _cache[fn].done(px)
