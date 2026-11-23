# Los objetos del inventario y de la tienda armados en 3D (render3d.py) para que se vean reales.
# Cada función recibe el lienzo de iconos.R y le deja la "foto" del objeto; después iconos.icono la achica.
import numpy as np
from PIL import Image
from render3d import (Escena, Mat, render, lin, angulo, entre, _smooth, esfera, caja, cilindro, tronco, capsula,
                      toro, elipsoide, mover, union, suave, restar, cortar, rot)
from iconos import N, u

# ---------------- ayudas ----------------


def revolucion(perfil, k=0.75):
    """Forma de revolución (botellas, frascos): perfil = [(y, radio), ...] de abajo hacia arriba."""
    ys = np.array([a for a, _ in perfil])
    rs = np.array([b for _, b in perfil])
    yc, h = (ys[0] + ys[-1]) / 2, (ys[-1] - ys[0]) / 2

    def f(p):
        r = np.interp(p[:, 1], ys, rs)
        return np.maximum((np.hypot(p[:, 0], p[:, 2]) - r) * k, np.abs(p[:, 1] - yc) - h)
    return f


def ruido(p, f=8.0, a=1.0):
    """Ruido suave (suma de senos girados): para textura de pan, carne, tela."""
    x, y, z = p[:, 0] * f, p[:, 1] * f, p[:, 2] * f
    return a * (np.sin(x * 1.7 + y * 0.6) * np.sin(y * 1.3 - z * 0.9) + 0.5 * np.sin(z * 2.9 + x * 1.1)
                * np.sin(y * 2.3 + 1.7) + 0.25 * np.sin(x * 5.1 - z * 4.3 + y * 3.7)) / 1.75


def con_ruido(f, frec, amp):
    return lambda p: f(p) + ruido(p, frec, amp)


def dentro(u, v, pts):
    """1 donde el punto (u,v) cae dentro del polígono pts."""
    r = np.zeros(len(u), bool)
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        c = ((y1 > v) != (y2 > v)) & (u < (x2 - x1) * (v - y1) / (y2 - y1 + 1e-12) + x1)
        r ^= c
    return r.astype(float)


def mezcla(base, encima, m):
    return base * (1 - m[:, None]) + encima * m[:, None]


def foto(p, esc, ancho=2.6):
    esc.ancho = ancho
    im = render(esc, N, pasos=160)
    p.img = im


METAL = Mat((205, 208, 214), metal=1, rugoso=0.22)
LATON = Mat((228, 175, 80), metal=1, rugoso=0.25)
ORO = Mat((240, 195, 90), metal=1, rugoso=0.2)

# ---------------- comida y bebida ----------------


def hamburguesa(p):
    e = Escena(yaw=-20, pitch=22)
    pan = lambda q, n: mezcla(lin((205, 120, 45)), lin((150, 75, 25)), _smooth(0.1, 0.5, q[:, 1]))
    tapa = cortar(elipsoide(0.95, 0.55, 0.95), lambda q: -(q[:, 1] - 0.0))
    e.add(mover(suave(0.06, tapa, cilindro(0.95, 0.05, 0.04)), y=0.2), Mat(pan, rugoso=0.45, brillo=0.6))
    rng = np.random.default_rng(3)
    for _ in range(14):
        a, r = rng.uniform(0, 2 * np.pi), rng.uniform(0.1, 0.7)
        x, z = r * np.cos(a), r * np.sin(a)
        y = 0.2 + 0.55 * np.sqrt(max(0, 1 - (x / 0.95) ** 2 - (z / 0.95) ** 2))
        g = rot(rng.uniform(-30, 30), rng.uniform(0, 180), 0)
        e.add(mover(elipsoide(0.05, 0.025, 0.08), x, y, z, g), Mat((250, 235, 195), rugoso=0.5))
    queso = lambda q: caja(0.9, 0.025, 0.9, 0.02)(q) - 0.0
    e.add(mover(queso, y=0.13, giro=rot(0, 45, 0)), Mat((255, 185, 30), rugoso=0.3, brillo=0.7, transl=0.2))
    lechuga = lambda q: np.maximum(np.abs(q[:, 1] - 0.05 * np.sin(np.arctan2(q[:, 2], q[:, 0]) * 9)) - 0.035,
                                   np.hypot(q[:, 0], q[:, 2]) - 1.02)
    e.add(mover(lechuga, y=0.17), Mat((95, 175, 40), rugoso=0.35, transl=0.3))
    carne = con_ruido(cilindro(0.98, 0.13, 0.08), 14, 0.012)
    e.add(mover(carne, y=-0.03), Mat(lambda q, n: lin((95, 50, 28)) * (0.8 + 0.3 * ruido(q, 30)[:, None]), rugoso=0.6))
    e.add(mover(cilindro(0.94, 0.17, 0.1), y=-0.33), Mat(pan, rugoso=0.5, brillo=0.5))
    foto(p, e)


def sandwich(p):
    e = Escena(yaw=-30, pitch=24)

    def triangulo(alto):
        pl = [(-1, -0.75), (1, -0.75), (-1, 0.95)]

        def f(q):
            x, z = q[:, 0], -q[:, 2]
            d = np.full(len(q), -9.0)
            for (x1, z1), (x2, z2) in zip(pl, pl[1:] + pl[:1]):
                nx, nz = z2 - z1, -(x2 - x1)
                l = np.hypot(nx, nz)
                d = np.maximum(d, ((x - x1) * nx + (z - z1) * nz) / l)
            return np.maximum(d + 0.12, np.abs(q[:, 1]) - alto + 0.06) - 0.06 if False else \
                np.linalg.norm(np.stack([np.maximum(d + 0.1, 0), np.maximum(np.abs(q[:, 1]) - alto + 0.06, 0)], 1), axis=1) \
                + np.minimum(np.maximum(d + 0.1, np.abs(q[:, 1]) - alto + 0.06), 0) - 0.06
        return f
    corteza = Mat(lambda q, n: mezcla(lin((175, 105, 45)), lin((190, 130, 60)), _smooth(0.55, 0.9, np.abs(n[:, 1]))
                                       * (0.92 + 0.08 * ruido(q, 25))), rugoso=0.6)
    e.add(mover(triangulo(0.12), y=0.32), corteza)
    e.add(mover(triangulo(0.12), y=-0.28), corteza)
    e.add(mover(lambda q: triangulo(0.035)(q) - 0.04, y=0.13), Mat((255, 190, 40), rugoso=0.3, transl=0.2))
    e.add(mover(lambda q: triangulo(0.04)(q) - 0.02 + 0.02 * np.sin(q[:, 0] * 22) * np.sin(q[:, 2] * 19), y=0.04),
          Mat((230, 120, 120), rugoso=0.4))
    lech = lambda q: triangulo(0.025)(q) - 0.07 + 0.05 * np.sin(q[:, 0] * 14 + q[:, 2] * 9)
    e.add(mover(lambda q: np.maximum(lech(q), np.abs(q[:, 1]) - 0.03), y=-0.08), Mat((100, 185, 50), rugoso=0.35, transl=0.3))
    foto(p, e)


def pizza(p):
    e = Escena(yaw=-15, pitch=40)
    ang = 0.36

    def porcion(q):
        x, z = q[:, 0], q[:, 2] + 1.1
        r = np.hypot(x, z)
        a = np.abs(np.arctan2(x, z))
        d2 = (a - ang) * r
        return np.maximum(np.maximum(d2, r - 2.0), np.abs(q[:, 1]) - 0.06) - 0.02
    queso = Mat(lambda q, n: mezcla(mezcla(lin((225, 150, 40)), lin((185, 95, 20)), (0.5 + 0.5 * ruido(q, 18)) * 0.8),
                                             lin((195, 60, 30)), _smooth(0.5, 0.9, ruido(q, 9)) * 0.8) * 0.8,
                rugoso=0.6, brillo=0.3)
    e.add(porcion, queso)
    borde = lambda q: np.maximum(np.abs(np.hypot(q[:, 0], q[:, 2] + 1.1) - 1.98) - 0.0,
                                 np.abs(np.arctan2(q[:, 0], q[:, 2] + 1.1)) - ang + 0.01)
    e.add(lambda q: np.maximum(np.hypot(np.hypot(q[:, 0], q[:, 2] + 1.1) - 1.95, q[:, 1] - 0.05) - 0.13,
                               (np.abs(np.arctan2(q[:, 0], q[:, 2] + 1.1)) - ang) * 2.0),
          Mat(lambda q, n: lin((215, 140, 60)) * (0.85 + 0.15 * ruido(q, 20)[:, None]), rugoso=0.55))
    for x, z in ((0.0, 0.55), (-0.22, 0.1), (0.22, 0.12), (0.0, -0.35), (-0.15, -0.6), (0.2, -0.65)):
        e.add(mover(cilindro(0.13, 0.025, 0.02), x, 0.07, z), Mat(lambda q, n: lin((135, 22, 15)) * (0.8 + 0.25 * ruido(q, 45)[:, None]), rugoso=0.45, brillo=0.45))
    foto(p, e)


def agua(p):
    e = Escena(yaw=-20, pitch=12)
    perfil = [(-0.95, 0.36), (-0.9, 0.4), (-0.3, 0.4), (-0.25, 0.37), (-0.2, 0.4), (0.25, 0.4), (0.5, 0.33),
              (0.68, 0.17), (0.72, 0.15)]
    plastico = Mat(lambda q, n: mezcla(lin((150, 200, 240)), lin((40, 110, 210)), entre(q[:, 1], -0.15, 0.2, 0.01)),
                   rugoso=0.08, brillo=1.0, transl=0.6)
    e.add(revolucion(perfil), plastico)
    e.add(mover(cilindro(0.17, 0.11, 0.03), y=0.82), Mat((40, 110, 220), rugoso=0.35))
    e.add(mover(cilindro(0.2, 0.02, 0.01), y=0.7), Mat((40, 110, 220), rugoso=0.35))
    foto(p, e)


def gaseosa(p):
    e = Escena(yaw=-25, pitch=18)

    def col(q, n):
        a, y = angulo(q), q[:, 1]
        banda = entre(y + 0.12 * np.sin(a * 2), -0.12, 0.06, 0.01)
        return mezcla(lin((205, 20, 25)), lin((248, 248, 248)), banda)
    _lata(e, col)
    foto(p, e)


def _lata(e, col, r=0.45, h=0.8):
    e.add(cilindro(r, h, 0.06), Mat(col, rugoso=0.22, brillo=0.9))
    e.add(mover(tronco(r, r * 0.8, 0.07, 0.02), y=h + 0.04), METAL)
    e.add(mover(restar(cilindro(r * 0.76, 0.03, 0.01), mover(cilindro(r * 0.66, 0.05), y=0.035)), y=h + 0.1), METAL)
    e.add(mover(caja(0.08, 0.012, 0.16, 0.01), 0, h + 0.115, 0.05), METAL)
    e.add(mover(tronco(r * 0.8, r, 0.05, 0.02), y=-h - 0.03), METAL)


def energizante(p):
    e = Escena(yaw=-25, pitch=16)
    rayo = [(0.18, 0.62), (-0.2, -0.02), (0.02, -0.02), (-0.12, -0.6), (0.24, 0.12), (0.03, 0.12), (0.2, 0.62)]

    def col(q, n):
        a, y = angulo(q), q[:, 1]
        uu = (a + 0.45) * 0.36
        m = dentro(uu, y, rayo)
        base = mezcla(lin((25, 26, 30)), lin((60, 62, 70)), entre(y, 0.72, 0.8, 0.005))
        return mezcla(base, lin((150, 230, 20)), m)
    _lata(e, col, r=0.36, h=0.92)
    foto(p, e)


def celular(p):
    e = Escena(yaw=-22, pitch=8)
    e.add(caja(0.48, 0.95, 0.06, 0.06), Mat((40, 42, 48), metal=1, rugoso=0.3))

    def pantalla(q, n):
        x, y = q[:, 0], q[:, 1]
        fondo = mezcla(lin((80, 120, 230)), lin((140, 70, 200)), _smooth(0.8, -0.8, y))
        gx = (x + 0.38) / 0.19
        gy = (0.66 - y) / 0.22
        i, j = np.floor(gx), np.floor(gy)
        fx, fy = gx - i, gy - j
        app = (i >= 0) & (i < 4) & (j >= 0) & (j < 6) & (fx > 0.12) & (fx < 0.88) & (fy > 0.12) & (fy < 0.8)
        tonos = np.array([lin(c) for c in ((70, 200, 90), (250, 250, 250), (255, 170, 40), (60, 150, 250),
                                           (240, 70, 70), (250, 210, 60), (150, 110, 250), (40, 190, 200))])
        c = tonos[((i + j * 3) % 8).astype(int)]
        r = mezcla(fondo, c, app.astype(float))
        isla = entre(x, -0.12, 0.12, 0.01) * entre(y, 0.8, 0.86, 0.01)
        return mezcla(r, lin((5, 5, 6)), isla)
    e.add(mover(caja(0.44, 0.91, 0.01, 0.01), z=0.058), Mat(pantalla, rugoso=0.05, brillo=1.0))
    foto(p, e)


def tarjeta(p):
    e = Escena(yaw=-18, pitch=35)

    def col(q, n):
        x, z = q[:, 0], q[:, 2]
        c = mezcla(lin((30, 70, 160)), lin((20, 35, 90)), _smooth(-0.9, 0.9, x + z * 0.5))
        c = mezcla(c, lin((70, 140, 230)), 0.35 * entre(x - z * 0.6, -0.2, 0.3, 0.1))
        num = sum(entre(x, -0.62 + k * 0.33, -0.4 + k * 0.33, 0.005) for k in range(4)) * entre(z, 0.28, 0.36, 0.005)
        c = mezcla(c, lin((225, 230, 245)), num * 0.9)
        logo = (np.hypot(x - 0.55, z + 0.36) < 0.13) * 1.0
        logo2 = (np.hypot(x - 0.72, z + 0.36) < 0.13) * 1.0
        c = mezcla(c, lin((240, 160, 30)), logo2)
        return mezcla(c, lin((225, 50, 40)), logo * (1 - logo2 * 0.0))
    e.add(caja(0.86, 0.025, 0.54, 0.02), Mat(col, rugoso=0.2, brillo=0.8))
    e.add(mover(caja(0.14, 0.012, 0.11, 0.02), -0.52, 0.025, -0.08), ORO)
    foto(p, e)


def radio(p):
    e = Escena(yaw=-25, pitch=14)
    e.add(caja(0.4, 0.75, 0.2, 0.08), Mat((45, 48, 52), rugoso=0.55))
    e.add(mover(cilindro(0.06, 0.38, 0.03), 0.22, 1.05, 0), Mat((30, 30, 32), rugoso=0.5))
    e.add(mover(cilindro(0.08, 0.06, 0.02), -0.18, 0.8, 0), Mat((30, 30, 32), rugoso=0.4))

    def frente(q, n):
        y = q[:, 1]
        rejilla = (np.sin(y * 70) > 0.3) * entre(y, -0.6, -0.05, 0.005) * entre(q[:, 0], -0.28, 0.28, 0.005)
        return mezcla(lin((55, 58, 64)), lin((15, 15, 17)), rejilla)
    e.add(mover(caja(0.34, 0.68, 0.02, 0.03), z=0.19), Mat(frente, rugoso=0.5))
    e.add(mover(caja(0.26, 0.13, 0.015, 0.02), 0, 0.38, 0.215), Mat((150, 220, 140), rugoso=0.1, brillo=1.0, transl=0.3))
    e.add(mover(esfera(0.05), 0.24, 0.66, 0.2), Mat((230, 40, 30), rugoso=0.2, brillo=0.9))
    foto(p, e)


def mochila(p):
    # mochila de tela (nylon azul) con fondo negro, cierre de lado a lado por arriba, bolsillo de adelante con
    # su cierre y dos correas con hebillas, bolsillos de red a los costados, manija arriba y las tiras de los hombros
    e = Escena(yaw=-32, pitch=14)

    def tela_col(base):
        def f(q, n):
            trama = 0.94 + 0.06 * np.sin(q[:, 0] * 260) * np.sin(q[:, 1] * 260 + q[:, 2] * 200)
            c = lin(base) * (trama * (0.93 + 0.07 * ruido(q, 30)))[:, None]
            return mezcla(c, lin((22, 22, 25)) * trama[:, None], _smooth(-0.42, -0.47, q[:, 1]))   # fondo negro
        return f
    tela = Mat(tela_col((26, 44, 88)), rugoso=0.7, brillo=0.3)
    negro = Mat(lambda q, n: lin((25, 25, 28)) * (0.92 + 0.08 * np.sin(q[:, 1] * 240))[:, None], rugoso=0.75, brillo=0.25)
    cuerpo = suave(0.12, caja(0.6, 0.62, 0.3, 0.24), mover(elipsoide(0.6, 0.4, 0.3), y=0.48))
    cuerpo = lambda q, c=cuerpo: c(q) - 0.04 * np.clip(1 - (q[:, 0] / 0.6) ** 2, 0, 1) * np.clip(1 - (q[:, 1] / 0.8) ** 2, 0, 1) \
        * (q[:, 2] > 0) + ruido(q, 7, 0.006)
    e.add(cuerpo, tela)

    def cierre(puntos, r=0.022):
        partes = [capsula(a, b, r) for a, b in zip(puntos, puntos[1:])]
        dientes = Mat(lambda q, n: lin((30, 30, 32)) * (0.7 + 0.3 * (np.sin((q[:, 0] + q[:, 1]) * 220) > 0))[:, None], rugoso=0.4, brillo=0.6)
        e.add(union(*partes), dientes)
    # cierre principal: el arco de arriba
    arco = []
    for t in np.linspace(-0.97, 0.97, 13):
        x = 0.6 * t
        arco.append((x, 0.48 + 0.38 * np.sqrt(max(0.0, 1 - t * t)) - 0.02, 0.17))
    cierre(arco)
    e.add(mover(caja(0.025, 0.06, 0.012, 0.01), 0.36, 0.78, 0.2, rot(0, 0, -40)), METAL)   # tirador
    # bolsillo de adelante
    bolsillo = mover(caja(0.44, 0.3, 0.1, 0.09), 0, -0.3, 0.31)
    e.add(bolsillo, Mat(tela_col((23, 39, 78)), rugoso=0.7, brillo=0.3))
    cierre([(-0.4, -0.02, 0.4), (0.4, -0.02, 0.4)], 0.018)
    e.add(mover(caja(0.022, 0.05, 0.012, 0.008), 0.22, -0.08, 0.42), METAL)
    for x in (-0.24, 0.24):   # correas con hebilla
        e.add(mover(caja(0.045, 0.34, 0.012, 0.008), x, -0.28, 0.415), negro)
        e.add(mover(caja(0.06, 0.05, 0.02, 0.012), x, -0.42, 0.43), Mat((15, 15, 17), rugoso=0.3, brillo=0.7))
    e.add(mover(caja(0.09, 0.04, 0.008, 0.006), 0, -0.22, 0.415), Mat((235, 235, 235), rugoso=0.5))   # etiqueta
    # bolsillos de red a los costados
    red = Mat(lambda q, n: mezcla(lin((15, 15, 17)), lin((60, 62, 68)),
                                  ((np.sin(q[:, 1] * 150) > 0.5) | (np.sin(q[:, 2] * 150) > 0.5)) * 1.0), rugoso=0.8, brillo=0.2)
    for sx in (-1, 1):
        e.add(mover(caja(0.05, 0.19, 0.2, 0.05), sx * 0.6, -0.36, 0.02), red)
    # manija y tiras de los hombros (atrás)
    e.add(mover(cortar(toro(0.13, 0.03), lambda q: -q[:, 1]), 0, 0.86, -0.12, rot(90, 0, 0)), negro)
    for sx in (-1, 1):
        x0 = sx * 0.28
        tira = union(capsula((x0, 0.7, -0.26), (sx * 0.4, 0.15, -0.46), 0.055),
                     capsula((sx * 0.4, 0.15, -0.46), (sx * 0.42, -0.45, -0.42), 0.055),
                     capsula((sx * 0.42, -0.45, -0.42), (sx * 0.5, -0.66, -0.3), 0.04))
        e.add(lambda q, t=tira: t(q * np.array([1, 1, 1])) + 0.0, negro)
    foto(p, e)


def botiquin(p):
    e = Escena(yaw=-25, pitch=20)

    def col(q, n):
        x, y = q[:, 0], q[:, 1]
        frente = _smooth(0.5, 0.8, n[:, 2])
        cruz = (entre(x, -0.1, 0.1, 0.005) * entre(y, -0.38, 0.32, 0.005) +
                entre(x, -0.35, 0.35, 0.005) * entre(y, -0.13, 0.07, 0.005)).clip(0, 1) * frente
        return mezcla(lin((245, 245, 248)), lin((215, 30, 30)), cruz)
    e.add(caja(0.9, 0.6, 0.35, 0.1), Mat(col, rugoso=0.25, brillo=0.8))
    e.add(mover(caja(0.92, 0.03, 0.37, 0.03), y=0.25), Mat((200, 200, 205), rugoso=0.3))
    e.add(mover(restar(caja(0.3, 0.14, 0.06, 0.06), caja(0.2, 0.06, 0.2, 0.0)), y=0.66), Mat((60, 60, 66), rugoso=0.4))
    foto(p, e)


def venda(p):
    e = Escena(yaw=-30, pitch=20)

    def col(q, n):
        x, y = q[:, 0], q[:, 1]
        frente = _smooth(0.5, 0.8, n[:, 2])
        banda = entre(y, 0.3, 0.55, 0.005)
        cruz = (entre(x, -0.07, 0.07, 0.005) * entre(y, -0.45, 0.05, 0.005) +
                entre(x, -0.25, 0.25, 0.005) * entre(y, -0.27, -0.13, 0.005)).clip(0, 1) * frente
        return mezcla(lin((248, 250, 255)), lin((40, 110, 210)), (banda + cruz).clip(0, 1))
    e.add(caja(0.55, 0.62, 0.4, 0.04), Mat(col, rugoso=0.4, brillo=0.5))
    foto(p, e)


def frasco(p):
    e = Escena(yaw=-20, pitch=18)

    def col(q, n):
        y = q[:, 1]
        etiqueta = entre(y, -0.45, 0.25, 0.005) * _smooth(-0.3, 0.2, n[:, 2] + np.abs(angulo(q)) * -0.2 + 0.4)
        c = mezcla(lin((235, 120, 20)), lin((250, 250, 250)), etiqueta)
        rojo = entre(y, 0.08, 0.16, 0.005) * etiqueta * entre(angulo(q), -0.9, 0.4, 0.01)
        lineas = sum(entre(y, -0.05 - k * 0.11, 0.0 - k * 0.11, 0.004) for k in range(3)) * etiqueta \
            * entre(angulo(q), -0.9, 0.5 - 0.0, 0.01)
        c = mezcla(c, lin((210, 40, 35)), rojo)
        return mezcla(c, lin((150, 150, 160)), lineas)
    e.add(mover(cilindro(0.42, 0.65, 0.06), y=-0.2), Mat(col, rugoso=0.12, brillo=1.0, transl=0.4))
    tapa = lambda q: cilindro(0.47, 0.17, 0.04)(q) + 0.008 * (np.sin(angulo(q) * 40) > 0)
    e.add(mover(tapa, y=0.62), Mat((250, 250, 250), rugoso=0.4))
    foto(p, e)


# ---------------- hallazgos de los trabajos ----------------


def latas(p):
    e = Escena(yaw=-20, pitch=25)

    def azul(q, n):
        return mezcla(lin((40, 90, 190)), lin((235, 235, 240)), entre(q[:, 1] - 0.35, -0.15, 0.1, 0.01))

    def roja(q, n):
        return mezcla(lin((200, 25, 30)), lin((240, 240, 240)), entre(q[:, 1] - 0.1 * np.sin(angulo(q) * 3), 0.05, 0.2, 0.01))
    abollada = lambda q: cilindro(0.34, 0.6, 0.05)(q) + 0.04 * np.sin(q[:, 1] * 9) * (np.sin(angulo(q) * 3) > 0)
    e.add(mover(abollada, 0.4, 0.3, -0.2), Mat(azul, rugoso=0.25, brillo=0.9))
    e.add(mover(tronco(0.34, 0.27, 0.05, 0.02), 0.4, 0.94, -0.2), METAL)
    acostada = lambda q: cilindro(0.34, 0.58, 0.05)(q) + 0.05 * np.maximum(0, np.sin(q[:, 1] * 6 + 1))
    g = rot(0, 0, 80) @ rot(0, 25, 0)
    e.add(mover(acostada, -0.3, -0.42, 0.25, g), Mat(roja, rugoso=0.25, brillo=0.9))
    foto(p, e)


def botellas(p):
    e = Escena(yaw=-20, pitch=12)
    perfil = [(-0.95, 0.27), (-0.9, 0.3), (0.15, 0.3), (0.42, 0.16), (0.55, 0.11), (0.88, 0.11), (0.92, 0.12)]
    for x, c in ((-0.36, (35, 110, 40)), (0.36, (120, 60, 15))):
        def col(q, n, c=c, x=x):
            y = q[:, 1]
            et = entre(y, -0.55, -0.05, 0.005)
            base = mezcla(lin(c), lin((235, 222, 190)), et)
            return mezcla(base, lin((200, 30, 30)), et * entre(y, -0.38, -0.24, 0.005))
        e.add(mover(revolucion(perfil), x, 0, x * 0.4), Mat(col, rugoso=0.06, brillo=1.0, transl=0.5))
        e.add(mover(cilindro(0.125, 0.04, 0.01), x, 0.93, x * 0.4), Mat((210, 180, 60), metal=1, rugoso=0.3))
    foto(p, e)


def ropa(p):
    # remera doblada, vista de arriba en diagonal
    e = Escena(yaw=-15, pitch=42)
    def tela_col(q, n):
        x, z = q[:, 0], q[:, 2]
        r = np.hypot(x / 1.3, (z + 0.85) / 1.0)
        dentro_cuello = (r < 0.22) * 1.0
        borde = entre(r, 0.22, 0.29, 0.008)
        c = lin((50, 100, 185)) * (0.92 + 0.08 * ruido(q, 60)[:, None])
        c = mezcla(c, lin((22, 45, 95)), dentro_cuello)
        return mezcla(c, lin((38, 80, 160)), borde)
    tela = Mat(tela_col, rugoso=0.8, brillo=0.2)
    cuerpo = con_ruido(caja(0.75, 0.12, 0.85, 0.1), 5, 0.015)
    e.add(cuerpo, tela)
    e.add(mover(caja(0.72, 0.03, 0.06, 0.03), 0, 0.12, 0.35), Mat((40, 85, 165), rugoso=0.8, brillo=0.2))
    for s in (-1, 1):
        e.add(mover(caja(0.08, 0.04, 0.5, 0.04), s * 0.62, 0.12, -0.15, rot(0, s * 12, 0)), tela)
    foto(p, e)


def radio_vieja(p):
    e = Escena(yaw=-25, pitch=14)
    madera = Mat(lambda q, n: mezcla(lin((150, 88, 42)), lin((115, 62, 28)),
                                     (0.5 + 0.5 * np.sin(q[:, 1] * 70 + 1.2 * np.sin(q[:, 0] * 3 + q[:, 2] * 2))) ** 4
                                     * (0.8 + 0.2 * ruido(q, 30))), rugoso=0.3, brillo=0.7)
    e.add(caja(0.95, 0.62, 0.35, 0.14), madera)

    def tela(q, n):
        return lin((70, 55, 40)) * (0.75 + 0.25 * (np.sin(q[:, 0] * 120) * np.sin(q[:, 1] * 120) > 0))[:, None]
    e.add(mover(caja(0.42, 0.45, 0.02, 0.05), -0.38, 0, 0.34), Mat(tela, rugoso=0.9, brillo=0.1))

    def dial(q, n):
        x = q[:, 0]
        marcas = (np.sin(x * 90) > 0.7) * 1.0
        aguja = entre(x, 0.42, 0.44, 0.003)
        c = mezcla(lin((245, 225, 160)), lin((90, 70, 40)), marcas * 0.6)
        return mezcla(c, lin((200, 30, 20)), aguja)
    e.add(mover(caja(0.33, 0.16, 0.02, 0.03), 0.48, 0.22, 0.345), Mat(dial, rugoso=0.1, brillo=1.0, transl=0.2))
    for x in (0.3, 0.66):
        e.add(mover(cilindro(0.1, 0.05, 0.02), x, -0.28, 0.38, rot(90, 0, 0)), METAL)
    foto(p, e)


def anteojos(p):
    e = Escena(yaw=-12, pitch=20)
    vidrio = Mat((15, 18, 25), rugoso=0.04, brillo=1.0)
    marco = Mat((25, 25, 28), rugoso=0.3, brillo=0.8)
    for s in (-1, 1):
        e.add(mover(elipsoide(0.42, 0.33, 0.05), s * 0.5, 0, 0), vidrio)
        anillo = lambda q: np.hypot(np.hypot(q[:, 0] / 0.44, q[:, 1] / 0.35) - 1.0, q[:, 2] / 0.4) * 0.4 - 0.03
        e.add(mover(anillo, s * 0.5, 0, 0), marco)
        e.add(capsula((s * 0.92, 0.15, 0), (s * 1.0, 0.13, -0.95), 0.035), marco)
    e.add(capsula((-0.1, 0.18, 0.02), (0.1, 0.18, 0.02), 0.035), marco)
    foto(p, e)


def bolso(p):
    e = Escena(yaw=-25, pitch=18)
    tela = Mat(lambda q, n: lin((50, 110, 60)) * (0.9 + 0.1 * ruido(q, 50)[:, None]), rugoso=0.7, brillo=0.3)
    cuerpo = con_ruido(lambda q: cilindro(0.42, 0.9, 0.25)((q @ rot(0, 0, 90))) , 6, 0.012)
    e.add(cuerpo, tela)
    for x in (-0.3, 0.3):
        e.add(mover(cortar(toro(0.25, 0.05), lambda q: -q[:, 1]), x, 0.38, 0, rot(90, 0, 0) @ rot(0, 0, 0)),
              Mat((30, 60, 35), rugoso=0.6))
    e.add(mover(caja(0.85, 0.015, 0.02, 0.01), 0, 0.41, 0.06), Mat((25, 25, 25), rugoso=0.4))
    e.add(mover(caja(0.06, 0.04, 0.02, 0.01), 0.45, 0.41, 0.09), METAL)
    foto(p, e)


def maletin(p):
    e = Escena(yaw=-25, pitch=14)
    cuero = Mat(lambda q, n: lin((38, 30, 26)) * (0.9 + 0.1 * ruido(q, 70)[:, None]), rugoso=0.35, brillo=0.7)
    e.add(caja(0.95, 0.6, 0.22, 0.08), cuero)
    e.add(mover(caja(0.97, 0.02, 0.24, 0.02), y=0.3), Mat((25, 20, 18), rugoso=0.5))
    e.add(mover(cortar(toro(0.24, 0.055), lambda q: -q[:, 1] * 0 - q[:, 1]), 0, 0.62, 0, rot(90, 0, 0)), cuero)
    for x in (-0.55, 0.55):
        e.add(mover(caja(0.09, 0.07, 0.03, 0.015), x, 0.48, 0.22), ORO)
    foto(p, e)


def reloj(p):
    e = Escena(yaw=-15, pitch=28)
    correa = Mat(lambda q, n: lin((60, 35, 20)) * (0.9 + 0.1 * ruido(q, 60)[:, None]), rugoso=0.6)
    e.add(mover(caja(0.22, 0.06, 0.9, 0.05), z=0.0), correa)
    e.add(cilindro(0.48, 0.1, 0.04), METAL)

    def esfera_col(q, n):
        a = np.arctan2(q[:, 0], -q[:, 2])
        r = np.hypot(q[:, 0], q[:, 2])
        marcas = (np.cos(a * 12) > 0.97) * entre(r, 0.3, 0.38, 0.005)
        hora = entre(r, 0, 0.22, 0.005) * (np.abs(np.sin(a - 2.2)) * r < 0.018) * (np.cos(a - 2.2) > 0)
        minuto = entre(r, 0, 0.33, 0.005) * (np.abs(np.sin(a - 0.0)) * r < 0.012) * (np.cos(a) > 0)
        seg = entre(r, 0, 0.35, 0.005) * (np.abs(np.sin(a - 4.2)) * r < 0.005) * (np.cos(a - 4.2) > 0)
        c = mezcla(lin((245, 245, 242)), lin((30, 30, 35)), np.clip(marcas + hora + minuto, 0, 1))
        return mezcla(c, lin((210, 30, 30)), seg)
    e.add(mover(cilindro(0.4, 0.03, 0.01), y=0.09), Mat(esfera_col, rugoso=0.05, brillo=1.0))
    e.add(mover(cilindro(0.06, 0.05, 0.02), 0.5, 0.0, 0, rot(0, 0, 90)), METAL)
    foto(p, e)


def cana(p):
    e = Escena(yaw=-20, pitch=15)
    g = rot(0, 0, -42)
    caña = lambda q: tronco(0.05, 0.015, 1.35)(q @ g)
    e.add(mover(caña, 0.1, 0.1, 0), Mat((150, 90, 40), rugoso=0.25, brillo=0.9))
    mango = lambda q: cilindro(0.075, 0.38, 0.03)(q @ g)
    e.add(mover(mango, -0.68, -0.77, 0), Mat((30, 30, 32), rugoso=0.7))
    e.add(mover(cilindro(0.22, 0.09, 0.03), -0.32, -0.55, 0.15, rot(90, 0, 0)), METAL)
    e.add(mover(cilindro(0.08, 0.1, 0.02), -0.32, -0.55, 0.28, rot(90, 0, 0)), Mat((40, 40, 44), rugoso=0.4))
    e.add(capsula((1.0, 1.1, 0), (1.02, -0.2, 0), 0.006), Mat((230, 230, 235), rugoso=0.3))
    e.add(mover(cortar(toro(0.07, 0.012), lambda q: q[:, 0] - 0.0), 1.06, -0.24, 0, rot(90, 0, 0)), METAL)
    foto(p, e)


# ---------------- balas ----------------


def _balas(p, punta, largo, punta_larga=0.32):
    e = Escena(yaw=-20, pitch=12)
    h = 0.35 + 0.35 * largo
    for x in (-0.6, 0, 0.6):
        e.add(mover(cilindro(0.2, h, 0.02), x, -0.9 + h), LATON)
        e.add(mover(cilindro(0.22, 0.05, 0.02), x, -0.86), LATON)
        tip = suave(0.05, tronco(0.2, 0.15, 0.16), mover(elipsoide(0.15, punta_larga, 0.15), y=0.14))
        e.add(mover(tip, x, -0.9 + 2 * h + 0.15), punta)
    foto(p, e)


COBRE = Mat((195, 110, 62), metal=1, rugoso=0.22)
PLOMO = Mat((165, 168, 175), metal=1, rugoso=0.32)


def balas_pistola(p):
    _balas(p, COBRE, 0.1, 0.22)


def balas_subfusil(p):
    _balas(p, PLOMO, 0.3, 0.26)


def balas_asalto(p):
    _balas(p, COBRE, 0.75, 0.42)


def balas_rifle(p):
    _balas(p, Mat((215, 218, 225), metal=1, rugoso=0.2), 1.0, 0.5)


def cartuchos(p):
    e = Escena(yaw=-20, pitch=14)
    for x in (-0.6, 0, 0.6):
        e.add(mover(cilindro(0.24, 0.6, 0.03), x, 0.15), Mat(lambda q, n: lin((200, 25, 25)) *
                                                             (0.9 + 0.1 * (np.sin(q[:, 1] * 60) > 0.9))[:, None], rugoso=0.3, brillo=0.8))
        e.add(mover(cilindro(0.25, 0.22, 0.02), x, -0.65), LATON)
        e.add(mover(cilindro(0.27, 0.03, 0.01), x, -0.86), LATON)
        e.add(mover(cilindro(0.18, 0.02, 0.01), x, 0.76), Mat((170, 20, 20), rugoso=0.4))
    foto(p, e)


def _ajustado(fn, lado=90):
    """Agranda la foto hasta llenar el cuadrado (lado de 100), así todos los íconos se ven del mismo tamaño."""
    def f(p):
        fn(p)
        caja = p.img.getchannel("A").getbbox()
        recorte = p.img.crop(caja)
        k = u(lado) / max(recorte.size)
        recorte = recorte.resize((max(1, int(recorte.width * k)), max(1, int(recorte.height * k))), Image.LANCZOS)
        p.img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        p.img.alpha_composite(recorte, ((N - recorte.width) // 2, (N - recorte.height) // 2))
    return f


# id del objeto (tabla objetos) -> ícono; la textura en americarp.txd se llama obj_<id>. Las armas (20 a 40) no
# tienen: el server las muestra con su modelo del juego.
POR_ID = {1: sandwich, 2: hamburguesa, 3: pizza, 4: agua, 5: gaseosa, 6: energizante, 7: celular, 8: tarjeta,
          9: radio, 10: mochila, 11: cana, 12: latas, 13: botellas, 14: ropa, 15: radio_vieja, 16: anteojos,
          17: bolso, 18: maletin, 19: reloj, 41: balas_pistola, 42: cartuchos, 43: balas_subfusil,
          44: balas_asalto, 45: balas_rifle, 46: botiquin, 47: venda, 48: frasco}
POR_ID = {k: _ajustado(f) for k, f in POR_ID.items()}
