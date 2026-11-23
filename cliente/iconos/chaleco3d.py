# Chalecos antibalas del inventario y la placa balística (objetos 49 a 70), en 3D con el mismo motor que
# objetos3d.py. Son portaplacas de nylon: el común verde oliva, el táctico color coyote con cargadores y el pesado
# negro con cuello, hombreras y faldón. Abajo llevan una barra con una rayita por placa (4, 6 u 8), llenas las que
# tiene puestas, así en la celda se ve de un vistazo sin leer el nombre.
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw
from render3d import Escena, Mat, lin, _smooth, caja, cilindro, mover, rot, elipsoide
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


HEBILLA = Mat((22, 22, 24), rugoso=0.45, brillo=0.5)
# (tela, cintas, ribete, abrojo) de cada tier
COLORES = {1: ((52, 58, 46), (40, 45, 36), (28, 30, 26), (70, 76, 62)),
           2: ((150, 124, 88), (118, 96, 66), (70, 58, 42), (170, 145, 108)),
           3: ((62, 64, 70), (46, 48, 53), (24, 25, 28), (88, 90, 96))}


def _chaleco(tier):
    tela_c, cinta_c, ribete_c, abrojo_c = COLORES[tier]
    TELA, CINTA = _nylon(tela_c), _nylon(cinta_c, 420.0)
    RIBETE = Mat(ribete_c, rugoso=0.75, brillo=0.2)
    ABROJO = Mat(lambda q, n: lin(abrojo_c) * (0.8 + 0.2 * ruido(q, 900))[:, None], rugoso=0.95, brillo=0.1)

    def molle(q, n):
        cos = (np.abs(((q[:, 0] + 0.6) % 0.2) - 0.1) < 0.012).astype(float)
        return lin(cinta_c) * (0.95 - 0.35 * cos + 0.05 * ruido(q, 300))[:, None]
    MOLLE = Mat(molle, rugoso=0.85, brillo=0.15)

    def f(p):
        e = Escena(yaw=-16, pitch=10)
        e.persp = 6.0
        # media silueta (x >= 0) desde el fondo del cuello en V, en sentido horario; la otra mitad es su espejo
        der = [(0.0, 0.42), (0.27, 0.86), (0.27, 1.0), (0.56, 1.0), (0.56, 0.66), (0.66, 0.42), (0.78, 0.28),
               (0.78, -0.84), (0.7, -0.94), (0.0, -0.94)]
        pts = der + [(-x, y) for x, y in reversed(der[1:-1])]
        e.add(perfil(pts, 0.11, 0.06), TELA)
        for s in (1, -1):
            e.add(perfil([(0.0, 0.42), (s * 0.27, 0.86), (s * 0.29, 0.84), (0.0, 0.38)], 0.115, 0.01), RIBETE)
            e.add(perfil([(s * 0.56, 0.66), (s * 0.66, 0.42), (s * 0.78, 0.28), (s * 0.8, 0.31), (s * 0.68, 0.45), (s * 0.58, 0.68)],
                         0.115, 0.01), RIBETE)
            # hombrera acolchada con su hebilla
            e.add(mover(caja(0.15, 0.1, 0.05, 0.04), s * 0.415, 0.93, 0.12), TELA)
            e.add(mover(caja(0.1, 0.045, 0.02, 0.015), s * 0.415, 0.8, 0.13), HEBILLA)
            e.add(mover(caja(0.06, 0.12, 0.012, 0.008), s * 0.415, 0.66, 0.125), CINTA)
            # costados de la faja que asoman atrás
            e.add(mover(caja(0.06, 0.48, 0.08, 0.04), s * 0.82, -0.36, -0.05), CINTA)
        e.add(mover(caja(0.3, 0.12, 0.012, 0.01), 0, 0.2, 0.115), ABROJO)
        if tier == 1:
            # el común: tres filas de cintas MOLLE
            for y in (-0.22, -0.44, -0.66):
                e.add(mover(caja(0.62, 0.055, 0.014, 0.01), 0, y, 0.115), MOLLE)
        else:
            # táctico y pesado: una fila de cintas y tres portacargadores con su tapa
            e.add(mover(caja(0.62, 0.05, 0.014, 0.01), 0, -0.2, 0.115), MOLLE)
            for x in (-0.42, 0.0, 0.42):
                e.add(mover(caja(0.18, 0.3, 0.07, 0.04), x, -0.58, 0.16), CINTA)
                e.add(mover(caja(0.19, 0.08, 0.075, 0.03), x, -0.3, 0.17), TELA)
                e.add(mover(caja(0.05, 0.03, 0.01, 0.008), x, -0.36, 0.25), ABROJO)
        if tier == 3:
            # el pesado: cuello alto alrededor de la V, hombreras anchas y faldón abajo
            for s in (1, -1):
                e.add(perfil([(0.0, 0.5), (s * 0.3, 1.02), (s * 0.4, 1.0), (s * 0.12, 0.42)], 0.14, 0.05), CINTA)
                e.add(mover(elipsoide(0.2, 0.1, 0.13), s * 0.6, 0.8, 0.04), TELA)
            e.add(perfil([(-0.3, -0.9), (0.3, -0.9), (0.24, -1.28), (-0.24, -1.28)], 0.09, 0.05), TELA)
            e.add(mover(caja(0.12, 0.05, 0.01, 0.008), 0, -1.1, 0.09), ABROJO)
        foto(p, e, 2.6 if tier == 3 else 2.4)
    return f


def placa(p):
    """Placa balística: cerámica gris oscura con el corte de tirador arriba, la funda texturada y una etiqueta."""
    e = Escena(yaw=-24, pitch=14)
    e.persp = 6.0
    g = rot(-12, 0, 8)
    pts = [(-0.62, 0.55), (-0.32, 0.85), (0.32, 0.85), (0.62, 0.55), (0.62, -0.85), (-0.62, -0.85)]
    funda = Mat(lambda q, n: mezcla(lin((48, 50, 54)) * (0.85 + 0.15 * ruido(q, 500))[:, None], lin((110, 112, 118)), canto(n) * 0.5),
                rugoso=0.7, brillo=0.3)
    e.add(mover(perfil(pts, 0.07, 0.05), giro=g), funda)
    etiqueta = Mat(lambda q, n: mezcla(lin((225, 225, 220)), lin((30, 30, 30)),
                                       ((np.abs(((q[:, 1] + 1) % 0.07) - 0.035) < 0.008) & (np.abs(q[:, 0]) < 0.24)).astype(float)),
                   rugoso=0.6, brillo=0.3)
    e.add(mover(caja(0.32, 0.2, 0.012, 0.01), 0, -0.35, 0.075, g), etiqueta)
    foto(p, e, 2.3)


@lru_cache(maxsize=None)
def _base(tier):
    """El chaleco solo, una vez por proceso y tier (los íconos con distintas placas lo comparten)."""
    p = R()
    _ajustado(_chaleco(tier), 80)(p)
    return p.img


def _con_barra(tier, placas, total):
    def f(p):
        im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        im.alpha_composite(_base(tier), (0, -int(u(5))))
        d = ImageDraw.Draw(im)
        color = (60, 200, 90, 255) if placas * 2 > total else (235, 190, 40, 255) if placas > 0 else (230, 60, 50, 255)
        hueco, alto, y = u(1.6), u(4.2), u(91)
        ancho = (u(86) - (total - 1) * hueco) / total
        x0 = (N - (total * ancho + (total - 1) * hueco)) / 2
        for i in range(total):
            x = x0 + i * (ancho + hueco)
            d.rounded_rectangle((x, y, x + ancho, y + alto), radius=u(1), fill=color if i < placas else (70, 70, 74, 230),
                                outline=(0, 0, 0, 200), width=max(1, int(u(0.4))))
        p.img = im
    return f


# id del objeto (database/035) -> ícono: 49 la placa; 50-54 el común con 0 a 4 placas, 55-61 el táctico con 0 a
# 6 y 62-70 el pesado con 0 a 8.
POR_ID = {49: _ajustado(placa)}
_id = 50
for _tier in (1, 2, 3):
    _total = 2 + 2 * _tier
    for _p in range(_total + 1):
        POR_ID[_id] = _con_barra(_tier, _p, _total)
        _id += 1
assert _id == 71
