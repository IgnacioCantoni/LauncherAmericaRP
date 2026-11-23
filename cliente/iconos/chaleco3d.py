# Chaleco antibalas del inventario (objetos 49 a 58: de 100% a 10%), en 3D con el mismo motor que objetos3d.py.
# Es un portaplacas de nylon: frente con el cuello en V, hombreras con hebilla, tres filas de cintas MOLLE,
# parche de abrojo arriba y el ribete de los bordes. Abajo lleva una barra de 10 rayitas con lo que le queda,
# así en la celda se ve de un vistazo sin leer el nombre.
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw
from render3d import Escena, Mat, lin, _smooth, caja, cilindro, mover, rot
from objetos3d import foto, mezcla, ruido, _ajustado
from armas3d import perfil, canto
from iconos import N, u, R


def _nylon(color, f=260.0):
    """Cordura: trama fina en cruz, un poco de grano y los bordes gastados más claros."""
    def c(q, n):
        trama = 0.5 + 0.5 * np.sin(q[:, 0] * f) * np.sin(q[:, 1] * f)
        base = lin(color) * (0.86 + 0.08 * trama + 0.08 * ruido(q, 40))[:, None]
        return mezcla(base, lin(color) * 1.9, canto(n) * 0.35)
    return Mat(c, rugoso=0.82, brillo=0.18)


TELA = _nylon((52, 58, 46))          # verde oliva oscuro
CINTA = _nylon((40, 45, 36), 420.0)
RIBETE = Mat((28, 30, 26), rugoso=0.75, brillo=0.2)
ABROJO = Mat(lambda q, n: lin((70, 76, 62)) * (0.8 + 0.2 * ruido(q, 900))[:, None], rugoso=0.95, brillo=0.1)
HEBILLA = Mat((22, 22, 24), rugoso=0.45, brillo=0.5)


def _chaleco(p):
    e = Escena(yaw=-16, pitch=10)
    e.persp = 6.0
    # media silueta (x >= 0) desde el fondo del cuello en V, en sentido horario; la otra mitad es su espejo
    der = [(0.0, 0.42), (0.27, 0.86), (0.27, 1.0), (0.56, 1.0), (0.56, 0.66), (0.66, 0.42), (0.78, 0.28),
           (0.78, -0.84), (0.7, -0.94), (0.0, -0.94)]
    pts = der + [(-x, y) for x, y in reversed(der[1:-1])]
    e.add(perfil(pts, 0.11, 0.06), TELA)
    # ribete del cuello y de las sisas (una tira más oscura apenas afuera del frente)
    for s in (1, -1):
        e.add(perfil([(0.0, 0.42), (s * 0.27, 0.86), (s * 0.29, 0.84), (0.0, 0.38)][::s], 0.115, 0.01), RIBETE)
        e.add(perfil([(s * 0.56, 0.66), (s * 0.66, 0.42), (s * 0.78, 0.28), (s * 0.8, 0.31), (s * 0.68, 0.45), (s * 0.58, 0.68)][::s],
                     0.115, 0.01), RIBETE)
        # hombrera acolchada con su hebilla de plástico
        e.add(mover(caja(0.15, 0.1, 0.05, 0.04), s * 0.415, 0.93, 0.12), TELA)
        e.add(mover(caja(0.1, 0.045, 0.02, 0.015), s * 0.415, 0.8, 0.13), HEBILLA)
        e.add(mover(caja(0.06, 0.12, 0.012, 0.008), s * 0.415, 0.66, 0.125), CINTA)
    # parche de abrojo arriba, en el pecho
    e.add(mover(caja(0.3, 0.12, 0.012, 0.01), 0, 0.2, 0.115), ABROJO)
    # tres filas de cintas MOLLE, cosidas cada tanto (las costuras son rayas más oscuras)
    def molle(q, n):
        cos = (np.abs(((q[:, 0] + 0.6) % 0.2) - 0.1) < 0.012).astype(float)
        return lin((38, 42, 34)) * (0.95 - 0.35 * cos + 0.05 * ruido(q, 300))[:, None]
    for y in (-0.22, -0.44, -0.66):
        e.add(mover(caja(0.62, 0.055, 0.014, 0.01), 0, y, 0.115), Mat(molle, rugoso=0.85, brillo=0.15))
    # costados del faja (cummerbund) que asoman atrás
    for s in (1, -1):
        e.add(mover(caja(0.06, 0.48, 0.08, 0.04), s * 0.82, -0.36, -0.05), CINTA)
    foto(p, e, 2.4)


@lru_cache(maxsize=1)
def _base():
    """El chaleco solo, una vez por proceso (los 10 íconos lo comparten)."""
    p = R()
    _ajustado(_chaleco, 80)(p)
    return p.img


def _con_barra(decenas):
    def f(p):
        im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        im.alpha_composite(_base(), (0, -int(u(5))))
        d = ImageDraw.Draw(im)
        color = (60, 200, 90, 255) if decenas >= 6 else (235, 190, 40, 255) if decenas >= 3 else (230, 60, 50, 255)
        ancho, hueco, alto, y = u(7.2), u(1.6), u(4.2), u(91)
        x0 = (N - (10 * ancho + 9 * hueco)) / 2
        for i in range(10):
            x = x0 + i * (ancho + hueco)
            d.rounded_rectangle((x, y, x + ancho, y + alto), radius=u(1), fill=color if i < decenas else (70, 70, 74, 230),
                                outline=(0, 0, 0, 200), width=max(1, int(u(0.4))))
        p.img = im
    return f


# id del objeto (database/034) -> ícono: 49 es el de 100%, 58 el de 10%.
POR_ID = {49 + i: _con_barra(10 - i) for i in range(10)}
