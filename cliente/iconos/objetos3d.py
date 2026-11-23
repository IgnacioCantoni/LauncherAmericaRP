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


def poligono(u, v, pts):
    """Distancia con signo al polígono pts (negativa adentro), para extruir formas planas."""
    d = np.full(len(u), 1e9)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        ex, ey = x2 - x1, y2 - y1
        t = np.clip(((u - x1) * ex + (v - y1) * ey) / (ex * ex + ey * ey), 0, 1)
        d = np.minimum(d, np.hypot(u - x1 - t * ex, v - y1 - t * ey))
    return np.where(dentro(u, v, pts) > 0, -d, d)


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
    # medio sándwich de miga: el corte (miga con poros) mira a la cámara, pan tostado arriba y abajo,
    # jamón, queso que se cae un poco, tomate y lechuga ondulada
    e = Escena(yaw=-20, pitch=22)
    pl = [(-1, -0.75), (1, -0.75), (-1, 0.95)]
    hx, hz = 0.65, 0.76   # hacia afuera del corte

    def capa(alto, extra=0.0, onda=0.0, frec=14.0):
        def f(q):
            x, z = q[:, 0], q[:, 2]
            d = poligono(x, z, pl) - extra + onda * np.sin(x * frec + z * frec * 0.7)
            b = np.abs(q[:, 1]) - alto
            r = min(0.05, alto * 0.8)
            return np.minimum(np.maximum(d + r, b + r), 0) + np.hypot(np.maximum(d + r, 0), np.maximum(b + r, 0)) - r
        return f

    def pan(q, n):
        corte = _smooth(0.55, 0.8, n[:, 0] * hx + n[:, 2] * hz)
        poros = _smooth(0.55, 0.75, ruido(q, 55)) * 0.35
        miga = lin((240, 226, 190)) * (1 - poros)[:, None]
        tostado = mezcla(lin((205, 150, 80)), lin((170, 110, 50)), 0.5 + 0.5 * ruido(q, 20))
        costra = lin((150, 90, 40)) * (0.9 + 0.1 * ruido(q, 30)[:, None])
        c = mezcla(costra, tostado, _smooth(0.5, 0.8, np.abs(n[:, 1])))
        return mezcla(c, miga, corte)
    e.add(mover(capa(0.11), y=0.33), Mat(pan, rugoso=0.75, brillo=0.2))
    e.add(mover(capa(0.11), y=-0.3), Mat(pan, rugoso=0.75, brillo=0.2))
    e.add(mover(capa(0.03, 0.04, 0.012, 9), y=0.17), Mat((250, 185, 45), rugoso=0.35, brillo=0.6, transl=0.3))
    e.add(mover(capa(0.035, 0.02, 0.01, 19), y=0.1), Mat(lambda q, n: lin((225, 125, 120)) * (0.9 + 0.1 * ruido(q, 40)[:, None]), rugoso=0.4, brillo=0.5))
    for x, z in ((-0.15, -0.2), (0.35, -0.45), (-0.6, 0.3)):
        e.add(mover(cilindro(0.26, 0.03, 0.02), x, 0.03, z), Mat(lambda q, n: mezcla(lin((210, 40, 30)), lin((240, 120, 90)),
              _smooth(0.12, 0.05, np.hypot(q[:, 0] - x, q[:, 2] - z)) * 0.6), rugoso=0.2, brillo=0.9, transl=0.4))
    e.add(mover(lambda q: np.maximum(capa(0.02, 0.07, 0.05, 11)(q), np.abs(q[:, 1] - 0.02 * np.sin(q[:, 0] * 25)) - 0.02), y=-0.1),
          Mat(lambda q, n: lin((95, 180, 50)) * (0.85 + 0.15 * ruido(q, 25)[:, None]), rugoso=0.35, transl=0.4))
    foto(p, e)

def pizza(p):
    # porción de muzzarella con pepperoni: queso con burbujas y partes doradas, salsa en el borde, borde inflado
    e = Escena(yaw=-15, pitch=38)
    ang = 0.36

    def r_a(q):
        x, z = q[:, 0], q[:, 2] + 1.1
        return np.hypot(x, z), np.abs(np.arctan2(x, z))

    def porcion(q):
        r, a = r_a(q)
        d2 = (a - ang) * r
        burbujas = 0.012 * np.maximum(0, ruido(q, 16)) + 0.006 * ruido(q, 40)
        return np.maximum(np.maximum(d2, r - 1.92), np.abs(q[:, 1]) - 0.06) - 0.02 - burbujas

    def queso(q, n):
        r, a = r_a(q)
        c = mezcla(lin((225, 160, 55)), lin((235, 190, 95)), 0.5 + 0.5 * ruido(q, 22))
        c = mezcla(c, lin((180, 100, 30)), _smooth(0.35, 0.8, ruido(q, 11)) * 0.85)                # dorado
        c = mezcla(c, lin((190, 45, 25)), _smooth(1.72, 1.82, r) * 0.9)                            # salsa en el borde
        oregano = (_smooth(0.82, 0.86, ruido(q * 3.1, 30))) * 0.8
        return mezcla(c, lin((60, 90, 30)), oregano)
    e.add(porcion, Mat(queso, rugoso=0.45, brillo=0.5))
    e.add(lambda q: np.maximum(np.hypot(r_a(q)[0] - 1.95, q[:, 1] - 0.05) - 0.14 - ruido(q, 12, 0.01),
                               (r_a(q)[1] - ang) * 2.0),
          Mat(lambda q, n: mezcla(lin((225, 160, 80)), lin((165, 95, 40)), _smooth(0.3, 0.9, n[:, 1] + 0.3 * ruido(q, 15))), rugoso=0.6))
    for x, z in ((0.0, 0.55), (-0.22, 0.1), (0.22, 0.12), (0.0, -0.35), (-0.15, -0.6), (0.2, -0.65)):
        pep = lambda q, x=x, z=z: cilindro(0.13, 0.022, 0.02)(q - np.array([x, 0.075, z])) + \
            0.012 * (1 - np.clip(np.hypot(q[:, 0] - x, q[:, 2] - z) / 0.13, 0, 1))
        e.add(pep, Mat(lambda q, n, x=x, z=z: mezcla(lin((150, 30, 20)), lin((95, 15, 10)),
              _smooth(0.08, 0.13, np.hypot(q[:, 0] - x, q[:, 2] - z))) * (0.85 + 0.2 * ruido(q, 50)[:, None]), rugoso=0.35, brillo=0.6))
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
    # celular con marco de metal, vidrio negro alrededor de la pantalla, la isla, íconos redondeados, el dock y botones
    e = Escena(yaw=-26, pitch=10)
    e.add(caja(0.48, 0.96, 0.055, 0.07), Mat((150, 152, 160), metal=1, rugoso=0.25))
    e.add(mover(caja(0.465, 0.945, 0.01, 0.06), z=0.05), Mat((8, 8, 10), rugoso=0.05, brillo=1.0))
    for y, h in ((0.55, 0.08), (0.32, 0.11)):
        e.add(mover(caja(0.012, h, 0.02, 0.01), -0.49, y, 0), Mat((150, 152, 160), metal=1, rugoso=0.25))
    e.add(mover(caja(0.012, 0.15, 0.02, 0.01), 0.49, 0.45, 0), Mat((150, 152, 160), metal=1, rugoso=0.25))

    def pantalla(q, n):
        x, y = q[:, 0], q[:, 1]
        c = mezcla(lin((255, 140, 90)), lin((90, 60, 190)), _smooth(0.9, -0.9, y + 0.3 * x))
        c = mezcla(c, lin((40, 120, 200)), _smooth(0.0, 0.8, ruido(q, 3)) * 0.4)
        gx, gy = (x + 0.36) / 0.18, (0.7 - y) / 0.2
        i, j = np.floor(gx), np.floor(gy)
        fx, fy = gx - i - 0.5, gy - j - 0.5
        cuadro = np.maximum(np.abs(fx) - 0.22, np.abs(fy) - 0.24)
        redondo = np.hypot(np.maximum(np.abs(fx) - 0.22, 0), np.maximum(np.abs(fy) - 0.24, 0))
        app = ((i >= 0) & (i < 4) & (j >= 0) & (j < 5) & ((cuadro < 0) | (redondo < 0.12)) & (redondo < 0.12)) * 1.0
        tonos = np.array([lin(t) for t in ((70, 200, 90), (250, 250, 250), (255, 170, 40), (60, 150, 250),
                                           (240, 70, 70), (250, 210, 60), (150, 110, 250), (40, 190, 200))])
        c = mezcla(c, tonos[((i * 3 + j * 5) % 8).astype(int)], app)
        dock = entre(y, -0.88, -0.66, 0.01) * entre(x, -0.4, 0.4, 0.01)
        c = mezcla(c, lin((235, 235, 245)), dock * 0.35)
        gd = (x + 0.36) / 0.18
        fd = gd - np.floor(gd) - 0.5
        app_d = dock * (np.abs(fd) < 0.3) * entre(y, -0.85, -0.69, 0.01) * (gd >= 0) * (gd < 4)
        c = mezcla(c, tonos[(np.floor(gd) % 8).astype(int)], app_d)
        c = mezcla(c, lin((250, 250, 250)), entre(x, -0.36, -0.22, 0.005) * entre(y, 0.84, 0.87, 0.005))   # la hora
        isla = (np.hypot(np.maximum(np.abs(x) - 0.08, 0), y - 0.855) < 0.035) * 1.0
        c = mezcla(c, lin((3, 3, 4)), isla)
        return c * (1 + 0.35 * entre(x + y * 0.5, 0.05, 0.3, 0.05))[:, None]   # reflejo del vidrio
    e.add(mover(caja(0.43, 0.91, 0.005, 0.05), z=0.058), Mat(pantalla, rugoso=0.04, brillo=1.0))
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
    # handy: cuerpo de goma, antena gruesa, perilla con estrías, pantalla con números, teclado, parlante y botón PTT
    e = Escena(yaw=-28, pitch=14)
    goma = Mat(lambda q, n: lin((40, 42, 46)) * (0.92 + 0.08 * ruido(q, 80)[:, None]), rugoso=0.65, brillo=0.35)
    e.add(caja(0.38, 0.72, 0.18, 0.12), goma)
    e.add(mover(tronco(0.07, 0.045, 0.42, 0.03), 0.2, 1.12, 0), Mat((25, 25, 27), rugoso=0.6))
    e.add(mover(cilindro(0.09, 0.05, 0.02), 0.2, 0.73, 0), Mat((60, 62, 66), rugoso=0.5))
    perilla = lambda q: cilindro(0.08, 0.08, 0.02)(q) + 0.008 * (np.sin(angulo(q) * 24) > 0)
    e.add(mover(perilla, -0.17, 0.8, 0), Mat((30, 30, 32), rugoso=0.4))
    e.add(mover(caja(0.02, 0.18, 0.08, 0.02), -0.39, 0.3, 0), Mat((25, 25, 27), rugoso=0.5))   # PTT

    def frente(q, n):
        x, y = q[:, 0], q[:, 1]
        c = lin((52, 55, 60))
        agujeros = ((np.hypot((x * 18) % 1 - 0.5, (y * 18) % 1 - 0.5) < 0.28) * entre(y, -0.66, -0.3, 0.005)
                    * entre(x, -0.27, 0.27, 0.005))
        c = mezcla(c, lin((10, 10, 12)), agujeros * 1.0)
        tx, ty = (x + 0.24) / 0.16, (0.0 - y) / 0.09
        i, j = np.floor(tx), np.floor(ty)
        tecla = (i >= 0) & (i < 3) & (j >= 0) & (j < 3) & (tx - i > 0.15) & (tx - i < 0.85) & (ty - j > 0.18) & (ty - j < 0.82)
        return mezcla(c, lin((120, 124, 132)), tecla * 1.0)
    e.add(mover(caja(0.33, 0.66, 0.015, 0.04), z=0.185), Mat(frente, rugoso=0.5, brillo=0.4))

    def lcd(q, n):
        x, y = q[:, 0], q[:, 1] - 0.4
        c = lin((150, 205, 120))
        seg = entre(x, -0.2, 0.12, 0.004) * entre(y, 0.0, 0.05, 0.004) + entre(x, -0.2, -0.02, 0.004) * entre(y, -0.06, -0.03, 0.004) \
            + entre(x, 0.14, 0.2, 0.004) * entre(y, -0.06, 0.05, 0.004) * (np.sin(y * 120) > 0)   # canal, nombre y señal
        return mezcla(c, lin((25, 45, 25)), np.clip(seg, 0, 1))
    e.add(mover(caja(0.26, 0.12, 0.012, 0.02), 0, 0.4, 0.2), Mat(lcd, rugoso=0.08, brillo=1.0, transl=0.3))
    e.add(mover(esfera(0.035), 0.24, 0.62, 0.19), Mat((240, 40, 30), rugoso=0.1, brillo=1.0, transl=0.6))
    e.add(mover(caja(0.14, 0.03, 0.006, 0.004), -0.12, 0.6, 0.2), Mat((200, 200, 205), rugoso=0.4))   # marca
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
    # dos latas usadas: una aplastada parada (con los pliegues de acordeón) y otra acostada y abollada
    e = Escena(yaw=-20, pitch=26)

    def azul(q, n):
        return mezcla(lin((35, 85, 180)), lin((235, 235, 240)), entre(q[:, 1] - 0.08 * np.sin(angulo(q) * 2), -0.05, 0.08, 0.01))

    def roja(q, n):
        return mezcla(lin((195, 25, 30)), lin((240, 240, 240)), entre(q[:, 1] - 0.12 * np.sin(angulo(q) * 2), -0.05, 0.08, 0.01))

    def lata(col, h, abollar, x, y, z, giro=None):
        def cuerpo(q):
            pliegue = abollar * (0.5 * np.sin(q[:, 1] * 30) + 0.5 * np.sin(angulo(q) * 5 + q[:, 1] * 9)) * \
                (np.abs(q[:, 1]) < h - 0.06)
            return cilindro(0.34, h, 0.05)(q) + 0.035 * pliegue
        e.add(mover(cuerpo, x, y, z, giro), Mat(col, rugoso=0.25, brillo=0.9))
        e.add(mover(mover(tronco(0.34, 0.27, 0.05, 0.02), y=h + 0.03), x, y, z, giro), METAL)
        tapa = restar(cilindro(0.26, 0.02, 0.01), mover(cilindro(0.22, 0.04), y=0.025))
        e.add(mover(mover(tapa, y=h + 0.08), x, y, z, giro), METAL)
        e.add(mover(mover(caja(0.06, 0.01, 0.12, 0.008), 0, h + 0.09, 0.04), x, y, z, giro), METAL)
        e.add(mover(mover(tronco(0.27, 0.34, 0.04, 0.02), y=-h - 0.02), x, y, z, giro), METAL)
    lata(azul, 0.32, 1.0, 0.38, 0.05, -0.15)
    lata(roja, 0.58, 0.35, -0.28, -0.42, 0.3, rot(0, 0, 82) @ rot(0, 30, 0))
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
    # ropa usada: una remera arrugada tirada encima de un jean doblado
    e = Escena(yaw=-18, pitch=48)
    remera = [(-0.34, -0.5), (0.34, -0.5), (0.34, 0.25), (0.62, 0.05), (0.78, 0.35), (0.42, 0.68), (0.14, 0.72),
              (0.0, 0.6), (-0.14, 0.72), (-0.42, 0.68), (-0.78, 0.35), (-0.62, 0.05), (-0.34, 0.25)]

    def forma(q):
        x, z = q[:, 0], -q[:, 2]
        arrugas = 0.035 * ruido(q, 5) + 0.012 * ruido(q, 13)
        d = poligono(x, z, remera) + 0.06
        cuello = np.hypot(x / 1.4, z - 0.62) - 0.13
        d = np.maximum(d, -cuello)
        b = np.abs(q[:, 1] - arrugas) - 0.025
        return np.minimum(np.maximum(d, b), 0) + np.hypot(np.maximum(d, 0), np.maximum(b, 0)) - 0.03

    def tela(q, n):
        x, z = q[:, 0], -q[:, 2]
        c = lin((150, 40, 45)) * (0.88 + 0.12 * ruido(q, 70)[:, None]) * (0.95 + 0.05 * np.sin(x * 300)[:, None])
        c = mezcla(c, lin((175, 120, 115)), _smooth(0.4, 0.9, ruido(q, 4)) * 0.35)    # desteñida
        c = mezcla(c, lin((120, 30, 35)), entre(np.hypot(x / 1.4, z - 0.62), 0.13, 0.17, 0.006))   # el cuello
        return c
    e.add(mover(forma, 0.05, 0.12, 0.05, rot(0, -15, 0)), Mat(tela, rugoso=0.85, brillo=0.15))

    def denim(q, n):
        x, z = q[:, 0], q[:, 2]
        sarga = 0.9 + 0.1 * np.sin((x + z) * 260)
        c = lin((45, 75, 125)) * (sarga * (0.9 + 0.1 * ruido(q, 25)))[:, None]
        costura = entre(x, 0.58, 0.6, 0.004) + entre(z, 0.38, 0.4, 0.004)
        return mezcla(c, lin((210, 150, 60)), np.clip(costura, 0, 1))
    e.add(mover(con_ruido(caja(0.72, 0.09, 0.48, 0.07), 6, 0.01), -0.05, -0.05, -0.05, rot(0, 12, 0)), Mat(denim, rugoso=0.8, brillo=0.2))
    e.add(mover(cilindro(0.025, 0.01, 0.005), 0.45, 0.045, 0.3), LATON)
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
