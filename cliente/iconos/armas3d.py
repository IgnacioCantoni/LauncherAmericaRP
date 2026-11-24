# Las armas del inventario (ids 20 a 40) en 3D con el motor de render3d.py.
# Cada arma se dibuja de costado en su plano (x hacia la boca del cañón, y hacia arriba, z el espesor) con
# perfiles planos extruidos y cilindros; después armar() la gira (las largas en diagonal, para llenar la celda)
# y la inclina un poco hacia arriba para que el costado agarre la luz de arriba.
import numpy as np
from render3d import (Escena, Mat, lin, _smooth, esfera, caja, cilindro, tronco, capsula, toro, mover, union,
                      suave, restar, rot)
from objetos3d import foto, mezcla, ruido, poligono, revolucion, LATON, _ajustado

# ---------------- materiales ----------------

def canto(n):
    """1 en los cantos redondeados (la normal ni de frente ni de costado): ahí se gasta la pintura y brilla."""
    a = np.abs(n[:, 2])
    return _smooth(0.12, 0.35, a) * _smooth(0.95, 0.75, a)


def gastado(color, claro, k=0.85, f=140.0, rug=0.42, metal=1):
    """Acero pavonado o pintado: color parejo con un poco de grano y los cantos gastados (más claros)."""
    def c(q, n):
        base = lin(color) * (0.92 + 0.08 * ruido(q, f))[:, None]
        return mezcla(base, lin(claro), canto(n) * k)
    return Mat(c, metal=metal, rugoso=rug)


ACERO = gastado((62, 64, 72), (175, 178, 186))               # pavonado
ACERO_CLARO = gastado((150, 153, 160), (215, 218, 225), 0.6, rug=0.35)
CROMO = gastado((205, 208, 215), (245, 246, 248), 0.5, rug=0.26)
NEGRO = gastado((24, 25, 27), (80, 82, 86), 0.6, 200, rug=0.5, metal=0)   # polímero
GOMA = Mat((24, 24, 26), rugoso=0.8, brillo=0.2)


def _veta(base, oscuro, f=34.0, cuadros=None):
    """Madera con la veta a lo largo del arma (eje x), poros y los cantos un poco más claros (gastados).
    cuadros = (x0, x1, y0, y1): zona con el cuadriculado de agarre."""
    def c(q, n):
        x, y, z = q[:, 0], q[:, 1], q[:, 2]
        t = np.sin(y * f + 2.6 * ruido(q * np.array([0.22, 1, 1]), 3.0) + z * 7) * 0.5 + 0.5
        t = t ** 3 + 0.3 * (np.sin(y * f * 3.1 + x * 0.8 + ruido(q, 9.0)) * 0.5 + 0.5)
        col = mezcla(lin(base), lin(oscuro), np.clip(t * 0.6, 0, 1))
        col = col * (1 - 0.18 * (ruido(q * np.array([0.3, 4, 4]), 60) > 0.55))[:, None]     # poros
        col = mezcla(col, lin(base) * 1.5, canto(n) * 0.35)
        if cuadros:
            x0, x1, y0, y1 = cuadros
            zona = (x > x0) & (x < x1) & (y > y0) & (y < y1)
            rombo = np.abs(((x * 30 + y * 22) % 1) - 0.5) + np.abs(((x * 30 - y * 22) % 1) - 0.5)
            col = col * (1 - 0.45 * (zona & (rombo < 0.35)))[:, None]
        return col
    return c


MADERA = Mat(_veta((150, 72, 30), (62, 26, 10)), rugoso=0.26, brillo=0.85)
NOGAL = Mat(_veta((112, 56, 26), (40, 18, 8), cuadros=(-0.8, -0.38, -0.2, 0.2)), rugoso=0.24, brillo=0.85)
FRESNO = Mat(_veta((214, 170, 112), (150, 100, 55), 22), rugoso=0.4, brillo=0.6)


def _texturado(color, f=160.0, k=0.25):
    """Plástico granulado (cachas, empuñaduras), con los cantos más claros."""
    return Mat(lambda q, n: mezcla(lin(color) * (1 - k * (ruido(q, f) > 0.3) - 0.12 * (ruido(q, f * 2.3) > 0.5))[:, None],
                                   lin(color) * 2.6, canto(n) * 0.5), rugoso=0.7, brillo=0.3)


GRANULADO = _texturado((20, 21, 23), 220, 0.35)

# ---------------- ayudas ----------------


def acotar(f, lo, hi):
    """Solo calcula la forma f cerca de su caja (lo, hi): lejos alcanza con la distancia a la caja."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    c, h = (lo + hi) / 2, (hi - lo) / 2

    def g(p):
        q = np.abs(p - c) - h
        d = np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0)
        cerca = d < 0.03
        if cerca.any():
            d[cerca] = f(p[cerca])
        return d
    return g


def perfil(pts, h, r=0.03, huecos=(), z=0.0):
    """Perfil plano (x, y) extruido con espesor 2h y cantos redondeados r; huecos: otros polígonos que se restan."""
    def d2(x, y):
        d = poligono(x, y, pts)
        for hp in huecos:
            d = np.maximum(d, -poligono(x, y, hp))
        return d

    def f(q):
        a = d2(q[:, 0], q[:, 1]) + r
        b = np.abs(q[:, 2] - z) - h + r
        return np.minimum(np.maximum(a, b), 0) + np.hypot(np.maximum(a, 0), np.maximum(b, 0)) - r
    xs, ys = [a for a, _ in pts], [b for _, b in pts]
    return acotar(f, (min(xs) - 0.01, min(ys) - 0.01, z - h - 0.01), (max(xs) + 0.01, max(ys) + 0.01, z + h + 0.01))


def tubo(x0, x1, y, r, rb=0.01, z=0.0):
    """Cilindro acostado a lo largo de x (cañones, tubos)."""
    return mover(cilindro(r, (x1 - x0) / 2, rb), (x0 + x1) / 2, y, z, rot(0, 0, -90))


def giro_x(perf, y=0.0, k=0.8):
    """Forma de revolución a lo largo de x: perf = [(x, radio), ...] de atrás hacia adelante."""
    return mover(revolucion(perf, k), 0, y, 0, rot(0, 0, -90))


def guardamonte(x0, x1, y0, y1, g=0.035, h=0.05):
    """El arco del gatillo: un aro plano debajo del arma."""
    ext = [(x0, y0), (x1, y0), (x1, y1 + 0.06), (x1 - 0.06, y1), (x0, y1)]
    inn = [(x0 + g, y0 + 0.01), (x1 - g, y0 + 0.01), (x1 - g, y1 + 0.07), (x1 - 0.07, y1 + g), (x0 + g, y1 + g)]
    return perfil(ext, h, 0.015, [inn])


def gatillo(x, y, h=0.03):
    return perfil([(x, y), (x + 0.04, y), (x + 0.02, y - 0.1), (x - 0.03, y - 0.15), (x - 0.01, y - 0.08)], h, 0.012)


def armar(partes, az=0.0, ancho=2.6, yaw=-14, pitch=12, incl=-28):
    """Pone las partes en la escena giradas az grados (en el plano de la foto) e inclinadas hacia arriba."""
    G = rot(incl, 0, az)
    e = Escena(yaw=yaw, pitch=pitch)
    e.persp = 6.0          # con perspectiva el metal de las caras planas tiene degradé, como en una foto
    for f, m in partes:
        if callable(m.color):   # la textura sigue al arma (veta, granulado)
            m = Mat((lambda fn: lambda q, n: fn(q @ G, n @ G))(m.color), m.metal, m.rugoso, m.brillo, m.transl)
        e.add(mover(f, giro=G), m)
    return e


def perno(x, y, z, r=0.022, mat=None):
    """Pasador o tornillo en el costado (cabeza redonda mirando a +z)."""
    return (mover(cilindro(r, 0.012, 0.006), x, y, z, rot(90, 0, 0)), mat or ACERO_CLARO)


def costado(pts, z, h=0.012, mat=None):
    """Pieza fina pegada al costado derecho (palanca, tapa del expulsor)."""
    return (perfil(pts, h, 0.008, z=z), mat or ACERO)


def _rayas(x0, x1, y0, y1, paso, ancho, h):
    """Ranuras verticales (estrías de la corredera, del guardamanos) para restar de un volumen."""
    return [mover(caja(ancho, (y1 - y0) / 2, h), x, (y0 + y1) / 2, 0) for x in np.arange(x0, x1, paso)]

# ---------------- armas blancas ----------------


def manopla(p):
    def anillos(q):
        x, y = q[:, 0], q[:, 1]
        cx = np.clip(np.round((x + 0.495) / 0.33) * 0.33 - 0.495, -0.495, 0.495)
        aro = np.abs(np.hypot(x - cx, y - 0.22) - 0.155) - 0.05
        qx, qy = np.abs(x) - 0.56, np.abs(y + 0.02) - 0.02
        palma = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - 0.08
        return np.minimum(aro, palma)
    f = lambda q: np.maximum(anillos(q) + 0.04, np.abs(q[:, 2]) - 0.1) - 0.04
    e = armar([(acotar(f, (-0.9, -0.45, -0.12), (0.9, 0.45, 0.12)), Mat((225, 180, 90), metal=1, rugoso=0.32))], az=0, yaw=-10, pitch=14, incl=-24)
    foto(p, e, 2.2)


def palo_golf(p):
    partes = [
        (giro_x([(-1.62, 0.0), (-1.6, 0.075), (-0.95, 0.06), (-0.9, 0.0)]),
         Mat(lambda q, n: lin((30, 30, 32)) * (1 - 0.3 * (np.sin(q[:, 0] * 120 + np.arctan2(q[:, 2], q[:, 1]) * 3) > 0.6))[:, None], rugoso=0.7, brillo=0.3)),
        (giro_x([(-0.95, 0.03), (1.3, 0.022), (1.45, 0.035), (1.5, 0.0)]), CROMO),
        (perfil([(1.36, 0.08), (1.5, 0.08), (1.62, -0.1), (1.86, -0.42), (1.82, -0.55), (1.36, -0.55), (1.3, -0.4)], 0.07, 0.035),
         Mat(lambda q, n: lin((200, 203, 210)) * (1 - 0.35 * ((np.sin(q[:, 1] * 120) > 0.7) & (q[:, 0] > 1.42) & (q[:, 1] < -0.12)))[:, None], metal=1, rugoso=0.3)),
    ]
    foto(p, armar(partes, az=38, yaw=-10), 3.0)


def porra(p):
    rayas = Mat(lambda q, n: lin((30, 30, 33)) * (1 - 0.35 * (np.sin(q[:, 0] * 90) > 0.5) * (q[:, 0] < -0.75))[:, None], rugoso=0.55, brillo=0.45)
    lateral = Mat(lambda q, n: lin((30, 30, 33)) * (1 - 0.35 * (np.sin(q[:, 1] * 90) > 0.5) * (q[:, 1] < -0.15))[:, None], rugoso=0.55, brillo=0.45)
    partes = [(giro_x([(-1.25, 0.0), (-1.23, 0.075), (1.38, 0.075), (1.4, 0.0)]), rayas),
              (mover(cilindro(0.068, 0.25, 0.03), -0.65, -0.25, 0), lateral),
              (mover(cilindro(0.09, 0.03, 0.02), -0.65, -0.5, 0), NEGRO)]
    foto(p, armar(partes, az=32), 3.0)


def cuchillo(p):
    filo = [(0.0, 0.15), (0.78, 0.15), (1.28, 0.0), (1.05, -0.1), (0.5, -0.15), (0.0, -0.13)]

    def hoja(q):
        d = poligono(q[:, 0], q[:, 1], filo)
        grosor = 0.012 + 0.03 * np.clip((q[:, 1] + 0.13) / 0.28, 0, 1) ** 0.7
        return np.maximum(d, np.abs(q[:, 2]) - grosor) * 0.6
    def acero_hoja(q, n):
        c = mezcla(lin((150, 154, 162)), lin((215, 218, 225)), _smooth(0.0, -0.04, q[:, 1]))        # bisel del filo más claro
        canal = (np.abs(q[:, 1] - 0.06) < 0.018) & (q[:, 0] > 0.12) & (q[:, 0] < 0.7)
        return c * (1 - 0.55 * canal)[:, None] * (0.94 + 0.06 * np.sin(q[:, 0] * 300))[:, None]
    acero = Mat(acero_hoja, metal=1, rugoso=0.32)
    mango = [(-0.95, 0.1), (-0.06, 0.12), (-0.06, -0.12), (-0.25, -0.12), (-0.33, -0.08), (-0.42, -0.13),
             (-0.52, -0.08), (-0.61, -0.13), (-0.7, -0.08), (-0.82, -0.14), (-0.95, -0.1)]
    partes = [(acotar(hoja, (-0.02, -0.17, -0.05), (1.3, 0.17, 0.05)), acero),
              (perfil([(-0.08, 0.2), (0.0, 0.2), (0.0, -0.22), (-0.08, -0.22)], 0.06, 0.02), ACERO_CLARO),
              (perfil(mango, 0.065, 0.04), _texturado((32, 32, 34), 120, 0.15)),
              (perfil([(-1.05, 0.1), (-0.94, 0.1), (-0.94, -0.12), (-1.05, -0.1)], 0.06, 0.03), ACERO_CLARO)]
    for x in (-0.3, -0.7):
        partes.append((mover(cilindro(0.03, 0.07, 0.01), x, 0.0, 0, rot(90, 0, 0)), CROMO))
    foto(p, armar(partes, az=30), 2.6)


def bate(p):
    perf = [(-1.52, 0.0), (-1.5, 0.095), (-1.44, 0.095), (-1.4, 0.055), (-0.6, 0.06), (0.3, 0.115), (1.4, 0.135), (1.48, 0.1), (1.5, 0.0)]

    def color(q, n):
        c = _veta((205, 150, 90), (140, 85, 40), 20)(q, n)
        cinta = (q[:, 0] > -1.4) & (q[:, 0] < -0.55)
        espiral = np.sin(q[:, 0] * 60 + np.arctan2(q[:, 2], q[:, 1])) > 0.85
        return mezcla(c, lin((28, 28, 30)) * (1 - 0.3 * espiral)[:, None], cinta * 1.0)
    foto(p, armar([(giro_x(perf), Mat(color, rugoso=0.35, brillo=0.7))], az=35), 3.0)


def pala(p):
    partes = [(giro_x([(-1.4, 0.0), (-1.4, 0.05), (0.62, 0.05), (0.64, 0.0)]), FRESNO),
              (perfil([(-1.36, 0.05), (-1.55, 0.17), (-1.8, 0.17), (-1.8, -0.17), (-1.55, -0.17), (-1.36, -0.05)], 0.045, 0.03,
                      [[(-1.5, 0.11), (-1.74, 0.11), (-1.74, -0.11), (-1.5, -0.11), (-1.43, 0.0)]]), NEGRO),
              (giro_x([(0.55, 0.0), (0.55, 0.06), (0.85, 0.075), (0.9, 0.0)]), ACERO),
              (perfil([(0.82, 0.08), (0.88, 0.3), (1.38, 0.32), (1.68, 0.0), (1.38, -0.32), (0.88, -0.3), (0.82, -0.08)], 0.018, 0.012),
               Mat(lambda q, n: mezcla(lin((40, 42, 46)), lin((165, 168, 175)), _smooth(1.45, 1.6, q[:, 0] + 0.25 * np.abs(q[:, 1]))), metal=1, rugoso=0.45))]
    foto(p, armar(partes, az=35, incl=-30), 3.2)


def taco(p):
    def color(q, n):
        x = q[:, 0]
        a = np.arctan2(q[:, 2], q[:, 1])
        c = _veta((228, 196, 140), (190, 150, 95), 14)(q, n)
        puntas = (x < -0.2) & (x - (-0.2) < -0.75 * (1 - np.abs(np.cos(2 * a))))
        c = mezcla(c, lin((30, 22, 18)), puntas * 1.0)
        c = mezcla(c, lin((20, 20, 22)), (x < -1.1) * 1.0)
        c = mezcla(c, lin((235, 235, 230)), ((np.abs(x + 1.1) < 0.012) | (np.abs(x + 0.2) < 0.01)) * 1.0)
        c = mezcla(c, lin((240, 240, 235)), (x > 1.62) * 1.0)
        return mezcla(c, lin((40, 90, 180)), (x > 1.71) * 1.0)
    perf = [(-1.75, 0.0), (-1.74, 0.07), (1.73, 0.028), (1.74, 0.0)]
    foto(p, armar([(giro_x(perf), Mat(color, rugoso=0.25, brillo=0.85))], az=42), 3.6)


def katana(p):
    def centro(x):
        return 0.09 * (x / 2.0) ** 2

    def hoja(q):
        x, y = q[:, 0], q[:, 1] - centro(q[:, 0])
        ancho = 0.075 - 0.01 * x / 2
        d = np.maximum(np.abs(y) - ancho, -x)
        punta = np.hypot(x - 1.75, y + 0.35) - 0.42      # kissaki curvo
        d = np.maximum(d, np.where(x > 1.6, punta, -1))
        grosor = 0.012 + 0.022 * np.clip((y + ancho) / (2 * ancho), 0, 1) ** 0.6
        return np.maximum(d, np.abs(q[:, 2]) - grosor) * 0.6

    def acero(q, n):
        y = q[:, 1] - centro(q[:, 0])
        hamon = -0.025 + 0.006 * np.sin(q[:, 0] * 18)
        return mezcla(lin((185, 190, 198)), lin((235, 238, 242)), _smooth(hamon + 0.015, hamon - 0.015, y))

    def ito(q, n):
        x, y = q[:, 0], q[:, 1]
        rombo = np.abs(((x * 9 + y * 6) % 1) - 0.5) + np.abs(((x * 9 - y * 6) % 1) - 0.5)
        return mezcla(lin((25, 25, 40)), lin((235, 230, 215)), (rombo < 0.3) * 1.0)
    partes = [(acotar(hoja, (0.0, -0.1, -0.04), (2.2, 0.2, 0.04)), Mat(acero, metal=1, rugoso=0.42)),
              (perfil([(-0.02, 0.09), (0.12, 0.09), (0.12, -0.09), (-0.02, -0.09)], 0.04, 0.015), LATON),
              (mover(cilindro(0.21, 0.025, 0.012), -0.05, 0, 0, rot(0, 0, -90)), Mat((40, 36, 32), metal=1, rugoso=0.45)),
              (perfil([(-0.85, 0.075), (-0.08, 0.08), (-0.08, -0.08), (-0.85, -0.07)], 0.06, 0.05), Mat(ito, rugoso=0.6, brillo=0.3)),
              (perfil([(-0.93, 0.07), (-0.84, 0.075), (-0.84, -0.075), (-0.93, -0.065)], 0.065, 0.03), Mat((40, 36, 32), metal=1, rugoso=0.45))]
    foto(p, armar(partes, az=36), 3.2)

# ---------------- pistolas ----------------


def _pistola(corredera_mat, armazon_mat, cacha_mat, largo=0.95, grande=False):
    s = 1.18 if grande else 1.0
    top = 0.5 * s
    zc, za = 0.13 * s, 0.12 * s           # medio espesor de la corredera y del armazón
    corredera = perfil([(-0.92, 0.2), (largo, 0.2), (largo, top - 0.06), (largo - 0.06, top), (-0.88, top), (-0.92, top - 0.05)], zc, 0.035)
    corredera = restar(corredera, *_rayas(-0.84, -0.56, 0.24, top - 0.05, 0.045, 0.011, 0.2),
                       *_rayas(largo - 0.3, largo - 0.1, 0.24, top - 0.05, 0.045, 0.011, 0.2),
                       mover(caja(0.18, 0.075, 0.05, 0.01), 0.02, top - 0.12, zc))
    armazon = perfil([(-0.86, 0.2), (largo - 0.08, 0.2), (largo - 0.08, 0.04), (-0.05, 0.04), (-0.5, 0.0), (-0.86, 0.06)], za, 0.03)
    armazon = restar(armazon, *_rayas(0.3, largo - 0.1, 0.03, 0.09, 0.11, 0.025, 0.3))     # ranuras del riel
    partes = [(corredera, corredera_mat), (armazon, armazon_mat),
              (perfil([(-0.86, 0.12), (-0.47, 0.12), (-0.5, -0.05), (-0.57, -0.2), (-0.54, -0.32), (-0.61, -0.45), (-0.58, -0.58),
                      (-0.64, -0.7), (-0.63, -0.84), (-0.68, -0.89), (-1.02, -0.89), (-1.05, -0.83), (-1.0, -0.4), (-0.95, -0.04),
                      (-1.02, 0.07)], 0.125 * s, 0.07), cacha_mat),
              (perfil([(-1.04, -0.87), (-0.67, -0.87), (-0.65, -0.95), (-1.06, -0.95)], 0.12 * s, 0.03), armazon_mat),   # base del cargador
              (guardamonte(-0.48, 0.05, 0.04, -0.27), armazon_mat),
              (gatillo(-0.2, 0.0), ACERO),
              # el cañón asomando por la ventana del expulsor
              (perfil([(-0.14, top - 0.18), (0.18, top - 0.18), (0.18, top - 0.05), (-0.14, top - 0.05)], zc - 0.035, 0.02), ACERO_CLARO),
              costado([(-0.42, 0.17), (-0.02, 0.17), (0.0, 0.21), (-0.12, 0.23), (-0.42, 0.21)], za + 0.008),    # retén de corredera
              costado([(0.08, 0.1), (0.18, 0.1), (0.18, 0.15), (0.08, 0.15)], za + 0.008),                         # palanca de desarme
              perno(-0.62, 0.1, za + 0.006), perno(-0.3, 0.07, za + 0.006),
              (perfil([(-0.86, top), (-0.74, top), (-0.74, top + 0.06), (-0.86, top + 0.06)], 0.06, 0.012), ACERO),
              (perfil([(largo - 0.14, top), (largo - 0.07, top), (largo - 0.08, top + 0.05), (largo - 0.13, top + 0.05)], 0.03, 0.01), ACERO),
              (perfil([(-0.97, top - 0.06), (-0.88, top - 0.04), (-0.88, top - 0.16), (-0.97, top - 0.14)], 0.05, 0.015), ACERO)]
    return partes, top


def pistola(p):
    partes, top = _pistola(ACERO, NEGRO, GRANULADO)
    partes.append((tubo(0.9, 1.0, 0.36, 0.05), Mat((20, 20, 22), rugoso=0.6)))
    foto(p, armar(partes, az=4, yaw=-16, pitch=14), 2.3)


def silenciador(p):
    partes, top = _pistola(ACERO, NEGRO, GRANULADO)
    partes.append((restar(tubo(0.9, 2.0, 0.35, 0.13, 0.04), *[mover(caja(0.004, 0.2, 0.2), x, 0.35, 0) for x in (1.0, 1.06, 1.9)]),
                   gastado((38, 39, 43), (120, 122, 128), 0.7, rug=0.5)))
    foto(p, armar(partes, az=14, yaw=-16, pitch=14), 3.2)


def desert_eagle(p):
    """Desert Eagle: el cañón poligonal fijo arriba adelante con el riel encima, la corredera solo atrás, el
    armazón largo hasta la boca, martillo a la vista, guardamonte cuadrado con gancho y la empuñadura de goma
    con dedos. Acero inoxidable satinado: el cañón y la corredera más claros que el armazón."""
    def cromo(osc, claro, k):
        # el reflejo del cromo horneado en bandas a lo alto (una cara plana sola refleja un color parejo)
        def c(q, n):
            y = q[:, 1]
            banda = _smooth(0.25, 0.85, 0.5 + 0.5 * np.sin(y * 11.0 + 0.6) + 0.15 * ruido(q, 3.0))
            col = mezcla(lin(osc), lin(claro), banda)
            return mezcla(col, lin((250, 251, 253)), canto(n) * k)
        return Mat(c, metal=1, rugoso=0.2)
    inox = cromo((70, 73, 82), (236, 238, 243), 0.6)
    inox_osc = cromo((52, 54, 61), (188, 191, 199), 0.5)
    boca = 1.4
    # cañón: la parte ancha de abajo y la de arriba más angosta (la sección triangular), con el riel encima
    canon = [(perfil([(0.08, 0.24), (boca, 0.24), (boca, 0.44), (0.08, 0.44)], 0.115, 0.03), inox),
             (perfil([(0.08, 0.42), (boca, 0.42), (boca, 0.53), (0.08, 0.53)], 0.075, 0.03), inox),
             (restar(perfil([(0.12, 0.52), (boca - 0.03, 0.52), (boca - 0.03, 0.585), (0.12, 0.585)], 0.05, 0.01),
                     *_rayas(0.2, boca - 0.05, 0.56, 0.6, 0.08, 0.016, 0.06)), inox_osc),
             (tubo(boca - 0.02, boca + 0.005, 0.34, 0.055), Mat((12, 12, 14), rugoso=0.7)),          # boca
             (perfil([(boca - 0.16, 0.585), (boca - 0.05, 0.585), (boca - 0.07, 0.64), (boca - 0.14, 0.64)], 0.022, 0.006), inox_osc)]
    # corredera: atrás, con las estrías, la ventana del expulsor y el seguro redondo
    corredera = restar(perfil([(-1.0, 0.22), (0.1, 0.22), (0.1, 0.55), (-0.96, 0.55), (-1.0, 0.5)], 0.13, 0.035),
                       *_rayas(-0.93, -0.6, 0.27, 0.52, 0.042, 0.011, 0.2),
                       mover(caja(0.17, 0.07, 0.05, 0.01), -0.2, 0.42, 0.13))
    armazon = restar(perfil([(-0.92, 0.23), (boca - 0.02, 0.23), (boca - 0.02, 0.07), (0.12, 0.05), (-0.05, 0.02),
                             (-0.55, 0.0), (-0.92, 0.06)], 0.12, 0.03),
                     *_rayas(0.25, boca - 0.1, 0.06, 0.12, 0.1, 0.022, 0.3))                       # ranuras de abajo
    empunadura = [(-0.88, 0.1), (-0.52, 0.1), (-0.55, -0.06), (-0.62, -0.2), (-0.58, -0.31), (-0.66, -0.43), (-0.62, -0.55),
                  (-0.69, -0.67), (-0.67, -0.82), (-0.72, -0.94), (-1.1, -0.94), (-1.13, -0.86), (-1.07, -0.4), (-1.0, -0.04),
                  (-1.06, 0.07)]
    partes = canon + [(corredera, inox), (armazon, inox_osc),
              (perfil(empunadura, 0.14, 0.08), GRANULADO),
              (perfil([(-1.12, -0.92), (-0.7, -0.92), (-0.68, -1.0), (-1.14, -1.0)], 0.13, 0.03), inox_osc),     # base del cargador
              (guardamonte(-0.52, 0.14, 0.03, -0.33), inox_osc),
              (perfil([(0.14, -0.2), (0.2, -0.2), (0.2, -0.3), (0.14, -0.33)], 0.05, 0.01), inox_osc),            # gancho del guardamonte
              (gatillo(-0.24, -0.01), ACERO),
              # martillo atrás, con el agujero, y el seguro (palanca redonda) al costado de la corredera
              (perfil([(-1.0, 0.24), (-1.06, 0.26), (-1.18, 0.4), (-1.13, 0.46), (-1.03, 0.4), (-0.98, 0.32)], 0.045, 0.015,
                      [[(-1.11, 0.36), (-1.08, 0.36), (-1.08, 0.39), (-1.11, 0.39)]]), ACERO),
              (mover(cilindro(0.06, 0.018, 0.008), -0.78, 0.44, 0.145, rot(90, 0, 0)), ACERO),
              costado([(-0.78, 0.425), (-0.6, 0.43), (-0.6, 0.455), (-0.78, 0.46)], 0.15),
              costado([(-0.46, 0.2), (-0.05, 0.2), (-0.03, 0.235), (-0.16, 0.255), (-0.46, 0.24)], 0.128),   # retén de corredera
              perno(-0.66, 0.12, 0.126), perno(-0.32, 0.1, 0.126), perno(0.6, 0.15, 0.126),
              (perfil([(-0.97, 0.55), (-0.84, 0.55), (-0.84, 0.61), (-0.97, 0.61)], 0.06, 0.012), ACERO)]       # mira de atrás
    foto(p, armar(partes, az=4, yaw=-16, pitch=14), 2.9)


# ---------------- escopetas ----------------


def _culata(mat, x1=-0.6, y_top=0.2, y_bot=0.0):
    """Culata de madera con la garganta (donde va la mano) y la cantonera de goma."""
    pts = [(x1, y_top), (-0.95, 0.17), (-1.55, 0.13), (-1.55, -0.38), (-1.45, -0.37), (-0.85, -0.16), (-0.74, -0.1),
           (x1 - 0.1, y_bot - 0.12), (x1, y_bot)]
    return [(perfil(pts, 0.11, 0.08), mat),
            (perfil([(-1.62, 0.14), (-1.53, 0.14), (-1.53, -0.39), (-1.62, -0.39)], 0.11, 0.035), GOMA)]


def escopeta(p):
    estriado = restar(perfil([(0.15, 0.17), (0.8, 0.17), (0.82, 0.0), (0.15, -0.02)], 0.1, 0.06),
                      *_rayas(0.22, 0.78, -0.05, 0.2, 0.06, 0.012, 0.03 + 0.1) )
    partes = _culata(MADERA) + [
        (restar(perfil([(-0.65, 0.28), (0.05, 0.28), (0.05, 0.0), (-0.32, -0.02), (-0.65, 0.0)], 0.1, 0.035),
                mover(caja(0.16, 0.06, 0.03, 0.01), -0.22, 0.17, 0.1)), ACERO),
        (guardamonte(-0.52, -0.2, 0.0, -0.22), ACERO), (gatillo(-0.32, -0.02), ACERO),
        perno(-0.5, 0.06, 0.105), perno(-0.08, 0.06, 0.105),
        (tubo(1.3, 1.37, 0.07, 0.052), ACERO_CLARO),
        (tubo(0.0, 1.55, 0.2, 0.055), ACERO), (tubo(0.0, 1.35, 0.07, 0.048), ACERO),
        (perfil([(0.05, 0.27), (1.55, 0.27), (1.55, 0.29), (0.05, 0.29)], 0.02, 0.008), ACERO),
        (mover(esfera(0.025), 1.5, 0.3, 0), CROMO),
        (estriado, MADERA),
        (mover(caja(0.1, 0.035, 0.012, 0.01), -0.22, 0.17, 0.085), ACERO_CLARO),
    ]
    foto(p, armar(partes, az=30), 3.4)


def recortada(p):
    madera = Mat(_veta((120, 60, 28), (55, 25, 10)), rugoso=0.3, brillo=0.75)
    partes = [
        (perfil([(-0.36, 0.2), (-0.65, 0.17), (-0.95, 0.06), (-1.0, -0.06), (-0.9, -0.42), (-0.72, -0.48),
                 (-0.62, -0.34), (-0.58, -0.12), (-0.36, -0.02)], 0.1, 0.05), madera),
        (perfil([(-0.4, 0.24), (0.05, 0.24), (0.05, -0.02), (-0.4, -0.04)], 0.13, 0.03), ACERO_CLARO),
        (guardamonte(-0.4, -0.08, -0.02, -0.22), ACERO), (gatillo(-0.22, -0.04), ACERO),
        (tubo(0.0, 0.9, 0.17, 0.07, 0.01, 0.07), ACERO), (tubo(0.0, 0.9, 0.17, 0.07, 0.01, -0.07), ACERO),
        (perfil([(0.0, 0.23), (0.9, 0.23), (0.9, 0.27), (0.0, 0.27)], 0.025, 0.01), ACERO),
        (perfil([(0.05, 0.11), (0.55, 0.11), (0.5, 0.0), (0.05, -0.01)], 0.08, 0.04), madera),
        (mover(capsula((-0.33, 0.25, 0.06), (-0.42, 0.34, 0.06), 0.025), 0, 0, 0), ACERO_CLARO),
        (mover(capsula((-0.33, 0.25, -0.06), (-0.42, 0.34, -0.06), 0.025), 0, 0, 0), ACERO_CLARO),
    ]
    # las bocas de los dos cañones, huecas
    partes = [(restar(f, mover(cilindro(0.05, 0.1), 0.9, 0.17, 0.07, rot(0, 0, -90)),
                      mover(cilindro(0.05, 0.1), 0.9, 0.17, -0.07, rot(0, 0, -90))) if k in (4, 5) else f, m)
              for k, (f, m) in enumerate(partes)]
    foto(p, armar(partes, az=20, yaw=-24, pitch=16), 2.4)


def escopeta_combate(p):
    escudo = restar(tubo(0.05, 0.85, 0.22, 0.085, 0.015),
                    *[mover(cilindro(0.028, 0.2), x, 0.22 + dy, 0, rot(90, 0, 0)) for x in np.arange(0.12, 0.8, 0.1)
                      for dy in (-0.035, 0.035)])
    partes = [
        # culata plegable de chapa, doblada arriba del cajón
        (perfil([(-1.2, 0.36), (-0.55, 0.36), (-0.55, 0.3), (-1.2, 0.3)], 0.08, 0.02), ACERO),
        (perfil([(-1.25, 0.42), (-1.15, 0.42), (-1.15, -0.25), (-1.25, -0.25)], 0.1, 0.03), ACERO),
        (perfil([(-1.2, 0.0), (-0.6, 0.12), (-0.6, 0.05), (-1.2, -0.08)], 0.06, 0.02), ACERO),
        (perfil([(-0.65, 0.28), (0.05, 0.28), (0.05, 0.0), (-0.65, 0.0)], 0.11, 0.03), NEGRO),
        (perfil([(-0.6, 0.02), (-0.4, 0.02), (-0.52, -0.42), (-0.72, -0.4)], 0.1, 0.075), GRANULADO),
        (guardamonte(-0.42, -0.1, 0.0, -0.22), NEGRO), (gatillo(-0.25, -0.02), ACERO),
        (escudo, ACERO), (tubo(0.0, 1.3, 0.22, 0.05), ACERO), (tubo(0.0, 1.15, 0.06, 0.05), ACERO),
        (restar(perfil([(0.2, 0.12), (0.75, 0.12), (0.78, -0.08), (0.2, -0.09)], 0.11, 0.06),
                *_rayas(0.26, 0.74, -0.12, 0.15, 0.05, 0.01, 0.2)), NEGRO),
        (mover(caja(0.03, 0.05, 0.04, 0.01), 1.22, 0.3, 0), ACERO),
    ]
    foto(p, armar(partes, az=26), 3.0)

# ---------------- subfusiles ----------------


def micro_uzi(p):
    partes = [
        (perfil([(-0.62, 0.3), (0.55, 0.3), (0.55, 0.0), (-0.62, 0.0)], 0.12, 0.04), ACERO),
        (tubo(0.5, 0.78, 0.15, 0.05), ACERO), (tubo(0.5, 0.58, 0.15, 0.075, 0.02), ACERO),
        (perfil([(-0.18, 0.02), (0.12, 0.02), (0.07, -0.58), (-0.2, -0.58)], 0.115, 0.07), GRANULADO),
        (perfil([(-0.17, -0.55), (0.05, -0.55), (0.04, -0.95), (-0.18, -0.95)], 0.08, 0.02), ACERO),
        (guardamonte(0.1, 0.42, 0.0, -0.22), ACERO), (gatillo(0.22, -0.02), ACERO),
        (mover(caja(0.05, 0.035, 0.05, 0.02), 0.25, 0.33, 0), ACERO_CLARO),
        (perfil([(-0.6, 0.38), (-0.52, 0.38), (-0.52, 0.3), (-0.6, 0.3)], 0.07, 0.015), ACERO),
        (perfil([(0.42, 0.38), (0.5, 0.38), (0.5, 0.3), (0.42, 0.3)], 0.04, 0.01), ACERO),
        perno(-0.45, 0.08, 0.125), perno(0.35, 0.08, 0.125), perno(-0.1, 0.22, 0.125, 0.018),
        costado([(-0.42, 0.17), (-0.26, 0.17), (-0.26, 0.21), (-0.42, 0.21)], 0.125),
        # culata de alambre plegada debajo
        (perfil([(-0.6, 0.0), (-0.58, -0.06), (-0.2, -0.06), (-0.2, -0.01)], 0.05, 0.015), ACERO),
    ]
    foto(p, armar(partes, az=6, yaw=-16, pitch=14), 2.2)


def mp5(p):
    curva = [(0.08, 0.06), (0.25, 0.06), (0.32, -0.25), (0.45, -0.55), (0.27, -0.62), (0.15, -0.33)]
    partes = [
        (perfil([(-1.15, 0.3), (-0.55, 0.28), (-0.55, 0.08), (-1.05, -0.14), (-1.15, -0.14)], 0.1, 0.04,
                [[(-1.05, 0.2), (-0.7, 0.2), (-0.7, 0.12), (-1.0, -0.04)]]), NEGRO),
        (perfil([(-0.6, 0.32), (0.55, 0.32), (0.55, 0.05), (-0.6, 0.05)], 0.11, 0.06), ACERO),
        (perfil([(-0.5, 0.06), (0.02, 0.06), (0.02, -0.02), (-0.5, -0.02)], 0.1, 0.03), NEGRO),
        (perfil([(-0.45, 0.0), (-0.25, 0.0), (-0.35, -0.42), (-0.55, -0.4)], 0.1, 0.075), GRANULADO),
        (guardamonte(-0.25, 0.0, -0.02, -0.2), NEGRO), (gatillo(-0.12, -0.03), ACERO),
        (perfil(curva, 0.07, 0.03), ACERO),
        perno(-0.4, 0.03, 0.105), perno(-0.05, 0.03, 0.105), perno(-0.52, 0.2, 0.115, 0.02),
        costado([(0.72, 0.33), (0.86, 0.33), (0.9, 0.42), (0.84, 0.43)], 0.06, 0.015),
        (restar(giro_x([(0.5, 0.0), (0.5, 0.13), (1.0, 0.11), (1.02, 0.0)], 0.12),
                *_rayas(0.6, 0.98, 0.0, 0.3, 0.07, 0.008, 0.3)), NEGRO),
        (tubo(0.45, 1.05, 0.3, 0.05), ACERO), (tubo(1.0, 1.2, 0.17, 0.04), ACERO),
        (mover(cilindro(0.06, 0.05, 0.01), -0.42, 0.4, 0, rot(90, 0, 0)), ACERO),
        (mover(toro(0.05, 0.015), 1.0, 0.43, 0, rot(0, 0, 90)), ACERO),
        (perfil([(0.97, 0.35), (1.03, 0.35), (1.03, 0.43), (0.97, 0.43)], 0.02, 0.008), ACERO),
    ]
    foto(p, armar(partes, az=18), 2.8)


def tec9(p):
    escudo = restar(tubo(0.3, 0.88, 0.16, 0.085, 0.015),
                    *[mover(cilindro(0.03, 0.2), x, 0.16, 0, rot(90, 0, 0)) for x in np.arange(0.38, 0.84, 0.09)])
    partes = [
        (perfil([(-0.55, 0.28), (0.32, 0.28), (0.32, 0.04), (-0.55, 0.04)], 0.1, 0.03), NEGRO),
        (escudo, ACERO), (tubo(0.85, 0.95, 0.16, 0.04), ACERO),
        (perfil([(-0.55, 0.06), (-0.33, 0.06), (-0.42, -0.5), (-0.62, -0.48), (-0.62, -0.1)], 0.1, 0.075), GRANULADO),
        (guardamonte(-0.33, -0.04, 0.04, -0.18), NEGRO), (gatillo(-0.18, 0.02), ACERO),
        (perfil([(0.0, 0.05), (0.18, 0.05), (0.22, -0.8), (0.04, -0.8)], 0.07, 0.02), ACERO),
        (mover(caja(0.07, 0.03, 0.03, 0.015), -0.15, 0.25, 0.1), ACERO_CLARO),
        (mover(toro(0.06, 0.018), -0.6, 0.18, 0, rot(0, 0, 90)), ACERO),
        perno(-0.45, 0.12, 0.105), perno(0.2, 0.12, 0.105), perno(-0.1, 0.22, 0.105, 0.018),
    ]
    foto(p, armar(partes, az=8, yaw=-16, pitch=14), 2.2)

# ---------------- rifles ----------------


def ak47(p):
    banana = [(-0.02, 0.0), (0.18, 0.0), (0.27, -0.3), (0.42, -0.58), (0.58, -0.78), (0.38, -0.88), (0.22, -0.66), (0.08, -0.36)]
    partes = [
        (perfil([(-0.62, 0.22), (-1.5, 0.12), (-1.5, -0.38), (-1.4, -0.38), (-0.62, 0.03)], 0.1, 0.075), MADERA),
        (perfil([(-1.56, 0.13), (-1.49, 0.13), (-1.49, -0.39), (-1.56, -0.39)], 0.1, 0.03), ACERO),
        (perfil([(-0.65, 0.24), (0.15, 0.24), (0.15, 0.0), (-0.65, 0.0)], 0.1, 0.03), ACERO),
        (perfil([(-0.6, 0.27), (0.12, 0.27), (0.12, 0.22), (-0.6, 0.22)], 0.09, 0.03), ACERO),
        (perfil([(-0.48, 0.02), (-0.3, 0.02), (-0.4, -0.4), (-0.58, -0.38)], 0.09, 0.07), MADERA),
        (guardamonte(-0.3, -0.04, 0.0, -0.18), ACERO), (gatillo(-0.18, -0.02), ACERO),
        (perfil(banana, 0.07, 0.03), Mat(lambda q, n: mezcla(lin((150, 68, 28)) * (1 - 0.3 * (np.sin((q[:, 0] * 0.45 - q[:, 1]) * 55) > 0.85))[:, None],
                                                    lin((210, 120, 60)), canto(n) * 0.5), rugoso=0.3, brillo=0.8)),
        (perfil([(0.15, 0.2), (0.75, 0.18), (0.75, 0.02), (0.15, -0.0)], 0.1, 0.07), MADERA),
        (tubo(0.75, 1.36, 0.06, 0.014), ACERO_CLARO),
        costado([(-0.55, 0.19), (0.02, 0.18), (0.08, 0.13), (0.03, 0.12), (-0.02, 0.15), (-0.55, 0.16)], 0.11),
        perno(-0.58, 0.05, 0.105, 0.018), perno(-0.2, 0.05, 0.105, 0.018), perno(0.1, 0.05, 0.105, 0.018), perno(-0.4, 0.21, 0.105, 0.016),
        (tubo(0.15, 0.95, 0.31, 0.04), ACERO), (tubo(0.18, 0.62, 0.31, 0.065, 0.03), MADERA),
        (tubo(0.15, 1.45, 0.14, 0.04), ACERO), (tubo(1.4, 1.55, 0.14, 0.05), ACERO),
        (perfil([(0.92, 0.36), (1.0, 0.36), (1.0, 0.1), (0.92, 0.1)], 0.07, 0.02), ACERO),
        (perfil([(1.3, 0.15), (1.38, 0.15), (1.36, 0.36), (1.32, 0.36)], 0.04, 0.012), ACERO),
        (perfil([(0.1, 0.24), (0.2, 0.24), (0.2, 0.32), (0.1, 0.3)], 0.06, 0.012), ACERO),
        (mover(caja(0.05, 0.025, 0.04, 0.015), 0.02, 0.15, 0.12), ACERO_CLARO),
    ]
    foto(p, armar(partes, az=28), 3.4)


def m4(p):
    partes = [
        (perfil([(-1.45, 0.28), (-0.98, 0.3), (-0.98, 0.02), (-1.42, -0.2), (-1.48, -0.2)], 0.1, 0.05,
                [[(-1.3, 0.2), (-1.08, 0.21), (-1.08, 0.12), (-1.3, 0.04)]]), NEGRO),
        (tubo(-1.0, -0.6, 0.2, 0.06), NEGRO),
        (perfil([(-0.62, 0.2), (0.12, 0.2), (0.12, -0.04), (-0.4, -0.06), (-0.62, 0.0)], 0.1, 0.03), ACERO),
        (perfil([(-0.62, 0.38), (0.18, 0.38), (0.18, 0.2), (-0.62, 0.2)], 0.1, 0.03), ACERO),
        (perfil([(-0.55, 0.38), (-0.45, 0.58), (0.12, 0.58), (0.15, 0.38)], 0.04, 0.015,
                [[(-0.42, 0.42), (-0.38, 0.51), (0.06, 0.51), (0.08, 0.42)]]), ACERO),
        (perfil([(-0.5, 0.0), (-0.32, 0.0), (-0.45, -0.42), (-0.63, -0.38)], 0.09, 0.07), GRANULADO),
        (guardamonte(-0.32, -0.04, -0.02, -0.2), ACERO), (gatillo(-0.18, -0.03), ACERO),
        (perfil([(-0.1, -0.04), (0.12, -0.04), (0.18, -0.6), (-0.05, -0.62)], 0.07, 0.02), ACERO),
        (restar(giro_x([(0.15, 0.0), (0.15, 0.13), (0.82, 0.12), (0.84, 0.0)], 0.24),
                *_rayas(0.25, 0.8, 0.1, 0.4, 0.06, 0.012, 0.3)), NEGRO),
        (perfil([(0.84, 0.2), (0.92, 0.2), (0.91, 0.5), (0.86, 0.5)], 0.04, 0.012), ACERO),
        (tubo(0.82, 1.4, 0.24, 0.035), ACERO),
        (restar(tubo(1.36, 1.52, 0.24, 0.048), *[mover(caja(0.06, 0.008, 0.2), 1.47, 0.24 + dy, 0) for dy in (-0.022, 0.022)]), ACERO),
        costado([(-0.22, 0.23), (0.08, 0.23), (0.08, 0.33), (-0.22, 0.33)], 0.1, 0.01, ACERO_CLARO),
        (tubo(-0.58, -0.4, 0.3, 0.035, 0.01, 0.09), ACERO),
        (perfil([(-0.72, 0.33), (-0.6, 0.33), (-0.6, 0.38), (-0.72, 0.38)], 0.05, 0.012), ACERO),
        perno(-0.52, 0.06, 0.105), perno(0.0, 0.1, 0.105), perno(-0.55, 0.28, 0.105, 0.018),
        costado([(-0.08, -0.06), (0.0, -0.06), (0.0, 0.02), (-0.08, 0.02)], 0.105),
    ]
    foto(p, armar(partes, az=28), 3.3)


def _rifle(stock_mat):
    culata = [(-1.62, 0.12), (-0.7, 0.2), (-0.45, 0.17), (0.85, 0.13), (0.9, 0.06), (0.0, 0.02), (-0.4, -0.02),
              (-0.58, -0.14), (-0.75, -0.18), (-1.62, -0.38)]
    return [
        (perfil(culata, 0.1, 0.08), stock_mat),
        (perfil([(-1.68, 0.12), (-1.6, 0.12), (-1.6, -0.39), (-1.68, -0.39)], 0.1, 0.035), GOMA),
        (tubo(-0.55, 0.1, 0.22, 0.075, 0.02), ACERO),
        (tubo(0.1, 1.7, 0.22, 0.045), ACERO),
        (capsula((-0.38, 0.22, 0.07), (-0.36, 0.1, 0.22), 0.022), ACERO_CLARO),
        (mover(esfera(0.05), -0.36, 0.1, 0.22), ACERO_CLARO),
        (guardamonte(-0.4, -0.1, 0.0, -0.2), ACERO), (gatillo(-0.25, -0.02), ACERO),
        (tubo(-0.62, -0.5, 0.22, 0.06), ACERO_CLARO),
        (mover(toro(0.04, 0.012), -1.25, -0.27, 0, rot(0, 0, 90)), ACERO_CLARO),
        (mover(toro(0.04, 0.012), 0.6, 0.0, 0, rot(0, 0, 90)), ACERO_CLARO),
        perno(-0.05, 0.22, 0.075, 0.02), perno(-0.45, 0.22, 0.075, 0.02),
    ]


def rifle_caza(p):
    partes = _rifle(NOGAL) + [(perfil([(1.6, 0.25), (1.66, 0.25), (1.65, 0.33), (1.61, 0.33)], 0.025, 0.01), ACERO)]
    foto(p, armar(partes, az=28), 3.5)


def francotirador(p):
    vidrio = Mat((30, 80, 140), metal=1, rugoso=0.08)
    partes = _rifle(_texturado((40, 44, 36), 90, 0.15)) + [
        (giro_x([(-0.7, 0.0), (-0.7, 0.1), (-0.55, 0.1), (-0.42, 0.06), (0.28, 0.06), (0.45, 0.115), (0.62, 0.115), (0.62, 0.0)], 0.47), ACERO),
        (mover(cilindro(0.05, 0.08, 0.01), -0.05, 0.56, 0), ACERO),
        (mover(cilindro(0.05, 0.07, 0.01), -0.05, 0.47, 0.1, rot(90, 0, 0)), ACERO),
        (mover(cilindro(0.1, 0.005), 0.625, 0.47, 0, rot(0, 0, -90)), vidrio),
        (mover(cilindro(0.075, 0.005), -0.705, 0.47, 0, rot(0, 0, -90)), vidrio),
        (tubo(0.7, 1.1, 0.03, 0.018, 0.005, 0.05), ACERO), (tubo(0.7, 1.1, 0.03, 0.018, 0.005, -0.05), ACERO),
        (perfil([(-0.35, 0.29), (-0.25, 0.29), (-0.25, 0.42), (-0.35, 0.42)], 0.04, 0.012), ACERO),
        (perfil([(0.15, 0.27), (0.25, 0.27), (0.25, 0.42), (0.15, 0.42)], 0.04, 0.012), ACERO),
        (tubo(1.65, 1.85, 0.22, 0.06), ACERO),
    ]
    foto(p, armar(partes, az=28), 3.7)


POR_ID = {20: manopla, 21: palo_golf, 22: porra, 23: cuchillo, 24: bate, 25: pala, 26: taco, 27: katana,
          28: pistola, 29: silenciador, 30: desert_eagle, 31: escopeta, 32: recortada, 33: escopeta_combate,
          34: micro_uzi, 35: mp5, 36: tec9, 37: ak47, 38: m4, 39: rifle_caza, 40: francotirador}
POR_ID = {k: _ajustado(f) for k, f in POR_ID.items()}
