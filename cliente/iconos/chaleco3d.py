# Chalecos antibalas del inventario y la placa balística (objetos 49 a 70), en 3D con el mismo motor que
# objetos3d.py. Son portaplacas de cordura curvados al torso, con ribete y costuras en los bordes, tirantes con hebilla,
# faja a los costados y cintas MOLLE: el común verde oliva, el táctico camuflado (multicam) con tres portacargadores
# y el pesado negro con cuello, hombreras, faldón y cinco portacargadores. Abajo llevan una barra con una rayita por placa (4, 6 u 8), llenas las que
# tiene puestas, así en la celda se ve de un vistazo sin leer el nombre.
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw
from render3d import Escena, Mat, lin, _smooth, caja, mover, rot, elipsoide, capsula
from objetos3d import foto, mezcla, ruido, poligono, _ajustado
from armas3d import perfil, canto
from iconos import N, u, R


CURVA = 0.32   # cuánto se curva el chaleco alrededor del torso


def curvar(f):
    """El chaleco envuelve el pecho: lo de los costados va hacia atrás (z baja con x²)."""
    return lambda p: f(np.column_stack([p[:, 0], p[:, 1], p[:, 2] + CURVA * p[:, 0] ** 2])) * 0.8


def _cordura(color, camo=False, f=300.0):
    """Nylon cordura: trama fina, grano, cantos gastados. camo: patrón multicam con manchas."""
    def c(q, n):
        x, y = q[:, 0], q[:, 1]
        trama = 0.5 + 0.5 * np.sin(x * f) * np.sin(y * f)
        if camo:
            b = np.broadcast_to(lin((160, 142, 106)), (len(q), 3)).copy()
            b = mezcla(b, lin((118, 94, 64)), _smooth(0.25, 0.32, ruido(q, 13.0)))
            b = mezcla(b, lin((104, 106, 72)), _smooth(0.38, 0.45, ruido(q * 1.3 + 4.1, 11.0)))
            b = mezcla(b, lin((188, 174, 140)), _smooth(-0.62, -0.7, ruido(q + 9.7, 15.0)))
            b = mezcla(b, lin((70, 56, 42)), _smooth(0.6, 0.66, ruido(q * 2.1 + 2.3, 19.0)))
        else:
            b = np.broadcast_to(lin(color), (len(q), 3)).copy()
        b = b * (0.84 + 0.1 * trama + 0.08 * ruido(q, 55))[:, None]
        return mezcla(b, b * 1.7, canto(n) * 0.3)
    return Mat(c, rugoso=0.85, brillo=0.15)


def _costura(mat_color, pts, adentro=0.055):
    """Le suma a un color la costura punteada que corre paralela al borde del perfil pts."""
    base = mat_color.color

    def c(q, n):
        col = base(q, n)
        d = poligono(q[:, 0], q[:, 1], pts)
        linea = (np.abs(d + adentro) < 0.0045) & (np.sin((q[:, 0] + q[:, 1]) * 140) > -0.2) & (n[:, 2] > 0.6)
        return mezcla(col, col * 0.45, linea.astype(float))
    return Mat(c, rugoso=mat_color.rugoso, brillo=mat_color.brillo)


def _borde(pts, h, ancho=0.028):
    """Ribete: la cinta que cubre el canto del perfil, un poco más gruesa que la tela."""
    def f(q):
        d = poligono(q[:, 0], q[:, 1], pts)
        a = np.abs(d + ancho) - ancho + 0.02
        b = np.abs(q[:, 2]) - h - 0.012 + 0.02
        return np.minimum(np.maximum(a, b), 0) + np.hypot(np.maximum(a, 0), np.maximum(b, 0)) - 0.02
    return f


def _molle(e, MOLLE, filas, x0, x1, z, alto=0.05, paso=0.13):
    """Cintas MOLLE: filas de cinta cosidas cada 'paso' (entre costura y costura la cinta se abomba un poco)."""
    for y in filas:
        n = int(round((x1 - x0) / paso))
        for i in range(n):
            cx = x0 + (i + 0.5) * paso
            e.add(curvar(mover(caja(paso / 2 - 0.0015, alto / 2, 0.016, 0.01), cx, y, z)), MOLLE)


def _portacargador(e, TELA, CINTA, ABROJO, x, y, z, ancho=0.17, alto=0.32):
    e.add(curvar(mover(caja(ancho / 2, alto / 2, 0.085, 0.045), x, y, z + 0.06)), TELA)
    # tapa con el canto redondeado que cae por delante y su tirador
    e.add(curvar(mover(caja(ancho / 2 + 0.01, 0.07, 0.095, 0.035), x, y + alto / 2 - 0.05, z + 0.07)), CINTA)
    e.add(curvar(mover(caja(0.035, 0.04, 0.012, 0.008), x, y + alto / 2 - 0.13, z + 0.16)), ABROJO)
    e.add(curvar(mover(caja(0.022, 0.014, 0.01, 0.006), x, y + alto / 2 - 0.18, z + 0.165)), ABROJO)


def _chaleco(tier):
    camo = tier == 2
    tela_c = {1: (58, 66, 50), 2: (176, 158, 118), 3: (40, 41, 45)}[tier]
    oscuro = {1: (42, 48, 37), 2: (120, 100, 70), 3: (28, 29, 32)}[tier]
    TELA = _cordura(tela_c, camo)
    CINTA = _cordura(oscuro, f=480.0) if not camo else _cordura(tela_c, True, 480.0)
    RIBETE = Mat(oscuro, rugoso=0.8, brillo=0.15)
    HEBILLA = Mat((18, 18, 20), rugoso=0.4, brillo=0.55)

    def molle(q, n):
        col = CINTA.color(q, n)
        tack = (np.abs(((q[:, 0] + 0.6) % 0.13) - 0.065) > 0.059).astype(float)
        return col * (1 - 0.45 * tack)[:, None]
    MOLLE = Mat(molle, rugoso=0.85, brillo=0.15)
    abc = (tela_c if not camo else (150, 130, 95))
    ABROJO = Mat(lambda q, n: lin(abc) * (0.75 + 0.25 * ruido(q, 900))[:, None] * 1.05, rugoso=0.97, brillo=0.05)

    ancho = 0.66 if tier < 3 else 0.7
    # panel de adelante (mitad derecha y su espejo): corte de tirador arriba, escote apenas curvo
    der = [(0.0, 0.56), (0.16, 0.6), (0.3, 0.64), (0.36, 0.64), (ancho, 0.36), (ancho, -0.82), (ancho - 0.06, -0.9),
           (0.0, -0.9)]
    pts = der + [(-x, y) for x, y in reversed(der[1:-1])]
    h = 0.075 if tier < 3 else 0.09
    e = Escena(yaw=-18, pitch=8)
    e.persp = 6.0
    e.add(curvar(perfil(pts, h, 0.06)), _costura(TELA, pts))
    e.add(curvar(_borde(pts, h)), RIBETE)
    for s in (1, -1):
        # tirantes acolchados que suben al hombro y se van para atrás, con su hebilla
        e.add(curvar(mover(caja(0.11, 0.17, 0.05, 0.045), s * 0.27, 0.76, -0.02, rot(-30, 0, 0))), TELA)
        e.add(curvar(mover(caja(0.11, 0.13, 0.05, 0.045), s * 0.27, 0.9, -0.2, rot(-75, 0, 0))), TELA)
        e.add(curvar(mover(caja(0.06, 0.03, 0.02, 0.01), s * 0.27, 0.7, h + 0.03)), HEBILLA)
        e.add(curvar(mover(caja(0.035, 0.09, 0.008, 0.004), s * 0.27, 0.66, h + 0.012)), CINTA)
        # faja (cummerbund) que asoma a los costados, con elástico
        e.add(curvar(mover(caja(0.09, 0.42, 0.06, 0.04), s * (ancho + 0.05), -0.38, -0.04)), CINTA)
        for y in (-0.2, -0.36, -0.52):
            e.add(curvar(mover(caja(0.092, 0.022, 0.065, 0.015), s * (ancho + 0.05), y, -0.04)), MOLLE)
    # asa de arrastre arriba atrás, entre los tirantes
    # abrojo para el parche arriba
    e.add(curvar(mover(caja(0.24, 0.085, 0.01, 0.008), 0, 0.38, h + 0.002)), ABROJO)
    if tier == 1:
        _molle(e, MOLLE, (0.18, 0.04, -0.1, -0.24, -0.38, -0.52, -0.66), -0.52, 0.52, h + 0.004)
    else:
        _molle(e, MOLLE, (0.18, 0.04), -0.52, 0.52, h + 0.004)
        xs = (-0.4, -0.2, 0.0, 0.2, 0.4) if tier == 3 else (-0.38, 0.0, 0.38)
        w = 0.17 if tier == 3 else 0.2
        for x in xs:
            _portacargador(e, TELA, CINTA, ABROJO, x, -0.5, h, w, 0.34)
    if tier == 3:
        for s in (1, -1):
            # cuello alto alrededor del escote y hombreras blindadas
            e.add(curvar(capsula((s * 0.0, 0.6, -0.04), (s * 0.2, 0.74, -0.12), 0.055)), TELA)
            e.add(curvar(mover(elipsoide(0.2, 0.13, 0.08), s * 0.5, 0.74, -0.1, rot(-10, 0, s * -28))), TELA)
            e.add(curvar(mover(caja(0.16, 0.018, 0.085, 0.012), s * 0.5, 0.7, -0.08, rot(-10, 0, s * -28))), MOLLE)
        # faldón contra golpes abajo
        fpts = [(-0.28, -0.88), (0.28, -0.88), (0.22, -1.26), (-0.22, -1.26)]
        e.add(curvar(perfil(fpts, 0.06, 0.05, z=0.01)), _costura(TELA, fpts, 0.045))
    return lambda p: foto(p, e, 2.65 if tier == 3 else 2.45)


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
