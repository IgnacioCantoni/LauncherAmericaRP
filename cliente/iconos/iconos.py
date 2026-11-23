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


_cache = {}


def icono(fn, px):
    if fn not in _cache:
        p = R()
        fn(p)
        _cache[fn] = p
    return _cache[fn].done(px)
