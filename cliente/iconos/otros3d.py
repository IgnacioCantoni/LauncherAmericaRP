# Íconos del HUD sin CEF y de la concesionaria en 3D (mismo motor que objetos3d.py).
# Los del HUD van chicos dentro de los círculos: formas simples y llenas, con volumen y brillo.
import numpy as np
from render3d import (Escena, Mat, lin, angulo, entre, _smooth, esfera, caja, cilindro, tronco, capsula, toro,
                      elipsoide, mover, union, suave, restar, cortar, rot)
from objetos3d import foto, mezcla, ruido, con_ruido, dentro, _ajustado, METAL, LATON, ORO

ROJO = Mat((205, 30, 28), rugoso=0.18, brillo=0.9)
CUBIERTO = Mat((215, 218, 226), metal=1, rugoso=0.45)   # más rugoso que METAL: de frente no se ve negro


def extruir(d2, h, r=0.12):
    """Una forma plana (d2: distancia en x,y) con espesor 2h y los cantos redondeados."""
    def f(q):
        a = d2(q[:, 0], q[:, 1]) + r
        b = np.abs(q[:, 2]) - h + r
        return np.minimum(np.maximum(a, b), 0) + np.hypot(np.maximum(a, 0), np.maximum(b, 0)) - r
    return f


def _corazon2d(x, y):
    # corazón de alto 1 con la punta abajo en (0,0)
    x = np.abs(x)
    d1 = np.hypot(x - 0.25, y - 0.75) - np.sqrt(2) / 4
    t = np.maximum(x + y, 0) * 0.5
    d2 = np.sqrt(np.minimum(x ** 2 + (y - 1) ** 2, (x - t) ** 2 + (y - t) ** 2)) * np.sign(x - y)
    return np.where(y + x > 1, d1, d2)

# ---------------- HUD ----------------


def hud_hambre(p):
    e = Escena(yaw=0, pitch=8)
    g = rot(-40, 0, 12)   # inclinados hacia arriba: reflejan la luz de arriba y no el fondo oscuro
    # tenedor: mango, cuello y cuatro dientes
    e.add(mover(union(caja(0.15, 0.55, 0.07, 0.06), mover(caja(0.26, 0.12, 0.05, 0.04), y=0.6),
                      *[mover(caja(0.05, 0.25, 0.045, 0.04), x, 0.92) for x in (-0.21, -0.07, 0.07, 0.21)]),
                -0.38, -0.15, 0, g), CUBIERTO)
    # cuchillo: hoja con el filo curvo y mango
    hoja = cortar(caja(0.22, 0.55, 0.045, 0.04), lambda q: np.hypot(q[:, 0] + 0.6, q[:, 1] + 0.3) - 1.0)
    e.add(mover(union(mover(hoja, y=0.55), mover(caja(0.15, 0.45, 0.07, 0.06), y=-0.45)), 0.4, -0.05, 0, rot(-40, 0, -12)), CUBIERTO)
    foto(p, e, 3.0)


def hud_sed(p):
    e = Escena(yaw=0, pitch=10)
    gota = suave(0.25, esfera(0.62), mover(tronco(0.35, 0.0, 0.5), y=0.62))
    e.add(mover(gota, y=-0.25), Mat((40, 130, 235), rugoso=0.05, brillo=1.0, transl=0.8))
    foto(p, e)


def hud_cansancio(p):
    e = Escena(yaw=-10, pitch=8)
    luna = extruir(lambda x, y: np.maximum(np.hypot(x, y) - 0.85, -(np.hypot(x - 0.42, y - 0.3) - 0.72)), 0.2, 0.15)
    crateres = lambda q, n: lin((248, 205, 80)) * (1 - 0.2 * sum(
        _smooth(0.11, 0.05, np.hypot(q[:, 0] - a, q[:, 1] - b)) for a, b in ((-0.5, -0.3), (-0.2, -0.62), (-0.62, 0.15))))[:, None]
    e.add(luna, Mat(crateres, rugoso=0.45, brillo=0.4))
    foto(p, e)


def hud_auto(p):
    e = Escena(yaw=-48, pitch=16)
    pintura = Mat((210, 25, 25), rugoso=0.12, brillo=1.0)
    e.add(caja(0.95, 0.2, 0.42, 0.14), pintura)
    e.add(mover(suave(0.05, caja(0.52, 0.17, 0.38, 0.12)), -0.08, 0.3, 0), pintura)
    vidrio = Mat((25, 35, 50), rugoso=0.05, brillo=1.0)
    e.add(mover(caja(0.53, 0.12, 0.36, 0.08), -0.08, 0.31, 0.03), vidrio)
    e.add(mover(caja(0.02, 0.15, 0.39, 0.01), -0.08, 0.3, 0), pintura)
    for x in (-0.58, 0.58):
        for z in (-0.38, 0.38):
            e.add(mover(cilindro(0.2, 0.08, 0.04), x, -0.2, z, rot(90, 0, 0)), Mat((25, 25, 28), rugoso=0.7))
            e.add(mover(cilindro(0.1, 0.085, 0.02), x, -0.2, z, rot(90, 0, 0)), METAL)
    e.add(mover(caja(0.02, 0.05, 0.1, 0.02), 0.95, 0.02, 0.27), Mat((255, 235, 150), rugoso=0.1, brillo=1.0, transl=0.5))
    foto(p, e)


def hud_nafta(p):
    e = Escena(yaw=-25, pitch=10)
    e.add(caja(0.42, 0.8, 0.28, 0.08), ROJO)
    e.add(mover(caja(0.3, 0.2, 0.02, 0.03), 0, 0.42, 0.28), Mat((170, 230, 190), rugoso=0.05, brillo=1.0, transl=0.4))
    e.add(mover(caja(0.5, 0.06, 0.34, 0.03), 0, -0.84), Mat((70, 72, 78), rugoso=0.4))
    e.add(mover(caja(0.45, 0.04, 0.31, 0.03), 0, 0.82), Mat((60, 62, 66), rugoso=0.4))
    manguera = union(capsula((0.42, 0.3, 0), (0.62, 0.3, 0), 0.075), capsula((0.62, 0.3, 0), (0.66, -0.3, 0), 0.075))
    e.add(manguera, Mat((30, 30, 32), rugoso=0.5))
    e.add(mover(caja(0.09, 0.18, 0.09, 0.04), 0.66, 0.48, 0), Mat((40, 40, 44), rugoso=0.4))
    foto(p, e)


def hud_vida(p):
    e = Escena(yaw=0, pitch=8)
    e.add(extruir(lambda x, y: _corazon2d(x / 1.7, (y + 0.85) / 1.7) * 1.7, 0.28, 0.25), Mat((215, 25, 35), rugoso=0.12, brillo=1.0))
    foto(p, e)


def hud_chaleco(p):
    e = Escena(yaw=0, pitch=6)
    tela = Mat(lambda q, n: lin((45, 60, 85)) * (0.9 + 0.1 * ruido(q, 50)[:, None]), rugoso=0.75, brillo=0.25)

    def cuerpo(q):
        x, y = q[:, 0], q[:, 1]
        d = caja(0.78, 0.85, 0.18, 0.15)(q)
        cuello = np.maximum(np.abs(x) - (y - 0.1) * 0.5, 0.1 - y)       # la V del cuello
        sisas = np.hypot(np.abs(x) - 1.0, y - 0.5) - 0.42                # los huecos de los brazos
        return np.maximum(np.maximum(d, -cuello), -sisas)
    e.add(cuerpo, tela)
    for x in (-0.33, 0.33):
        e.add(mover(caja(0.25, 0.22, 0.05, 0.05), x, -0.2, 0.17), Mat((60, 78, 108), rugoso=0.6, brillo=0.3))
    e.add(mover(caja(0.8, 0.07, 0.2, 0.04), 0, -0.6, 0.0), Mat((30, 40, 58), rugoso=0.6))
    foto(p, e)


def hud_perla(p):
    e = Escena(yaw=0, pitch=8)
    # nácar: blanco crema con un tornasol rosa y celeste según hacia dónde mira la superficie
    nacar = lambda q, n: lin((232, 218, 200)) * (1 + 0.14 * np.stack([np.sin(4 * n[:, 1]), np.sin(4 * n[:, 0] + 2), np.cos(4 * n[:, 1] + 1)], 1))
    e.add(esfera(0.8), Mat(nacar, rugoso=0.08, brillo=1.0, transl=0.2))
    foto(p, e)


# ---------------- concesionaria ----------------


def dato_velocidad(p):
    e = Escena(yaw=0, pitch=12)
    g = rot(90, 0, 0)
    e.add(mover(toro(0.85, 0.09), giro=g), METAL)

    def dial(q, n):
        x, y = q[:, 0], q[:, 1]
        a = np.arctan2(x, y)
        r = np.hypot(x, y)
        marcas = (np.abs(((a + np.pi) % (np.pi / 8)) - np.pi / 16) > np.pi / 16 - 0.035) * entre(r, 0.58, 0.72, 0.01) * (np.abs(a) < 2.4)
        rojas = marcas * (a > 1.3)
        c = mezcla(lin((22, 22, 26)), lin((240, 240, 240)), marcas * (1 - rojas))
        return mezcla(c, lin((230, 40, 30)), rojas)
    e.add(mover(cilindro(0.8, 0.03, 0.01), giro=g), Mat(dial, rugoso=0.3, brillo=0.6))
    e.add(capsula((0, 0, 0.06), (0.42, 0.38, 0.06), 0.035), Mat((235, 40, 30), rugoso=0.2, brillo=0.9))
    e.add(mover(cilindro(0.1, 0.05, 0.02), 0, 0, 0.06, g), METAL)
    foto(p, e)


def dato_asientos(p):
    e = Escena(yaw=-55, pitch=10)
    cuero = Mat(lambda q, n: lin((150, 95, 55)) * (0.88 + 0.12 * ruido(q, 45)[:, None])
                * (1 - 0.25 * (np.abs(np.sin(q[:, 1] * 14)) < 0.08) * (np.abs(q[:, 0]) < 0.3))[:, None], rugoso=0.4, brillo=0.6)
    e.add(mover(caja(0.42, 0.13, 0.5, 0.12), 0, -0.4, 0.15), cuero)
    e.add(mover(caja(0.42, 0.62, 0.13, 0.12), 0, 0.28, -0.32, rot(-12, 0, 0)), cuero)
    for x in (-0.42, 0.42):
        e.add(mover(caja(0.06, 0.55, 0.15, 0.06), x, 0.25, -0.3, rot(-12, 0, 0)), cuero)
    e.add(mover(caja(0.26, 0.15, 0.1, 0.09), 0, 1.12, -0.52, rot(-12, 0, 0)), cuero)
    for x in (-0.12, 0.12):
        e.add(capsula((x, 0.85, -0.47), (x, 0.97, -0.5), 0.022), METAL)
    e.add(mover(caja(0.36, 0.06, 0.45, 0.03), 0, -0.6, 0.15), Mat((40, 40, 44), rugoso=0.5))
    for x in (-0.25, 0.25):
        e.add(mover(caja(0.03, 0.03, 0.6, 0.01), x, -0.68, 0.15), METAL)
    foto(p, e)


def dato_tanque(p):
    e = Escena(yaw=-25, pitch=12)

    def cuerpo(q):
        d = caja(0.6, 0.78, 0.25, 0.1)(q)
        # la X estampada en el costado
        x, y = q[:, 0], q[:, 1] + 0.1
        x1 = np.minimum(np.abs(x - y * 0.75), np.abs(x + y * 0.75)) * 0.8
        canal = (x1 < 0.06) & (np.abs(x) < 0.45) & (np.abs(y) < 0.55)
        return d + 0.015 * canal
    e.add(cuerpo, ROJO)
    e.add(mover(restar(caja(0.4, 0.14, 0.06, 0.06), mover(caja(0.25, 0.06, 0.2), y=-0.02)), -0.15, 0.9), ROJO)
    e.add(mover(tronco(0.14, 0.1, 0.12, 0.02), 0.42, 0.88, 0, rot(0, 0, -25)), Mat((50, 50, 54), rugoso=0.4))
    foto(p, e)


PINTURA = Mat((200, 25, 25), rugoso=0.12, brillo=1.0)
GOMA = Mat((25, 25, 28), rugoso=0.7)
VIDRIO = Mat((25, 35, 50), rugoso=0.05, brillo=1.0)


def _auto(e, abierto, adelante, color=(200, 25, 25)):
    """Un auto visto desde atrás (baúl) o desde adelante (capó), con la tapa abierta o cerrada."""
    s = 1 if not adelante else -1          # la punta que mira a la cámara queda en z = +0.9

    def pintura(q, n):
        hueco = (np.abs(q[:, 0]) < 0.62) & (q[:, 1] > -0.07) & (q[:, 1] < 0.26) & (q[:, 2] > 0.23) & (q[:, 2] < 0.87)
        return mezcla(lin(color), lin((28, 28, 30)), (hueco & abierto) * 1.0)
    cuerpo = caja(0.75, 0.25, 0.9, 0.12)
    if abierto:
        cuerpo = restar(cuerpo, mover(caja(0.6, 0.3, 0.3), 0, 0.25, 0.55))
    e.add(cuerpo, Mat(pintura, rugoso=0.15, brillo=1.0))
    chapa = Mat(color, rugoso=0.12, brillo=1.0)
    e.add(mover(caja(0.62, 0.2, 0.45, 0.12), 0, 0.4, -0.25), chapa)
    e.add(mover(caja(0.56, 0.15, 0.46, 0.08), 0, 0.42, -0.24), VIDRIO)
    if abierto:
        e.add(mover(caja(0.6, 0.03, 0.32, 0.03), 0, 0.56, 0.385, rot(-65, 0, 0)), chapa)
        if adelante:   # el motor adentro
            e.add(mover(caja(0.3, 0.1, 0.18, 0.04), 0, 0.08, 0.55), Mat((150, 152, 158), metal=1, rugoso=0.4))
            e.add(mover(caja(0.22, 0.04, 0.12, 0.03), 0, 0.19, 0.55), Mat((30, 30, 32), rugoso=0.5))
        else:          # una caja en el baúl
            e.add(mover(caja(0.22, 0.14, 0.16, 0.02), 0.2, 0.05, 0.58, rot(0, 15, 0)), Mat((190, 145, 90), rugoso=0.8, brillo=0.2))
    else:
        e.add(mover(caja(0.6, 0.006, 0.3, 0.003), 0, 0.25, 0.55), Mat(tuple(int(c * 0.55) for c in color), rugoso=0.3))   # la junta de la tapa
    luz = Mat((255, 240, 190), rugoso=0.05, brillo=1.0, transl=0.8) if adelante else Mat((230, 30, 25), rugoso=0.08, brillo=1.0, transl=0.6)
    for x in (-0.55, 0.55):
        e.add(mover(caja(0.14, 0.06, 0.02, 0.02), x, 0.1, 0.9), luz)
        for z in (-0.6, 0.55):
            e.add(mover(cilindro(0.22, 0.08, 0.04), x * 1.36, -0.25, z, rot(0, 0, 90)), GOMA)
    e.add(mover(caja(0.78, 0.07, 0.06, 0.04), 0, -0.2, 0.9), Mat((35, 35, 38), rugoso=0.5))
    e.add(mover(caja(0.2, 0.05, 0.02, 0.01), 0, -0.03, 0.91), Mat((240, 240, 235), rugoso=0.4))


def dato_maletero(p):
    # la cola de un auto con el baúl abierto, visto desde atrás y un poco de arriba
    e = Escena(yaw=-35, pitch=26)
    _auto(e, True, False)
    foto(p, e)


def dato_guantera(p):
    e = Escena(yaw=-10, pitch=18)
    plastico = Mat(lambda q, n: lin((55, 57, 62)) * (0.92 + 0.08 * ruido(q, 90)[:, None]), rugoso=0.6, brillo=0.4)
    e.add(caja(0.95, 0.55, 0.2, 0.1), plastico)
    e.add(mover(caja(0.75, 0.38, 0.05, 0.06), 0, -0.02, 0.18), Mat((45, 47, 52), rugoso=0.55, brillo=0.4))
    e.add(mover(caja(0.2, 0.05, 0.04, 0.04), 0, 0.22, 0.25), METAL)
    foto(p, e)


def dato_licencia(p):
    e = Escena(yaw=-12, pitch=62)   # casi de arriba: chica en la ficha se lee como tarjeta

    def col(q, n):
        x, z = q[:, 0], q[:, 2]
        c = mezcla(lin((240, 243, 248)), lin((45, 95, 185)), (z < -0.32) * 1.0)
        foto_m = entre(x, -0.72, -0.3, 0.005) * entre(z, -0.22, 0.4, 0.005)
        c = mezcla(c, lin((165, 180, 200)), foto_m)
        cara = (np.hypot(x + 0.51, z + 0.02) < 0.09) + (np.hypot((x + 0.51) / 1.4, z - 0.25) < 0.14)
        c = mezcla(c, lin((85, 95, 115)), cara.clip(0, 1) * foto_m)
        lineas = sum(entre(z, -0.12 + k * 0.17, -0.06 + k * 0.17, 0.004) for k in range(3)) * entre(x, -0.15, 0.65, 0.005)
        return mezcla(c, lin((140, 150, 168)), lineas)
    e.add(caja(0.86, 0.025, 0.54, 0.02), Mat(col, rugoso=0.2, brillo=0.8))
    foto(p, e)


def pago_efectivo(p):
    e = Escena(yaw=-20, pitch=30)

    def billete(q, n):
        x, z = q[:, 0], q[:, 2]
        c = lin((120, 175, 110)) * (0.9 + 0.1 * ruido(q, 40)[:, None])
        marco = 1 - entre(x, -0.78, 0.78, 0.01) * entre(z, -0.38, 0.38, 0.01)
        c = mezcla(c, lin((80, 130, 75)), marco)
        ovalo = np.hypot(x / 1.3, z) < 0.25
        return mezcla(c, lin((70, 120, 70)), ovalo * 1.0)
    rng = np.random.default_rng(5)
    for k in range(5):
        e.add(mover(caja(0.86, 0.018, 0.44, 0.01), 0, -0.2 + k * 0.045, 0, rot(0, rng.uniform(-6, 6), 0)), Mat(billete, rugoso=0.7, brillo=0.2))
    e.add(mover(caja(0.12, 0.13, 0.46, 0.01), 0, -0.1, 0), Mat((225, 215, 185), rugoso=0.6, brillo=0.3))
    foto(p, e)


# ---------------- panel del vehículo (tecla 2): una imagen por estado ----------------


def pv_motor(p):
    # V8: block gris, dos tapas de válvulas rojas en V, el filtro de aire redondo arriba y las poleas adelante
    e = Escena(yaw=-30, pitch=24)
    bloque = Mat((140, 142, 148), metal=1, rugoso=0.45)
    e.add(caja(0.42, 0.42, 0.62, 0.08), bloque)
    rojo = Mat((200, 30, 28), rugoso=0.2, brillo=0.9)
    for sx in (-1, 1):
        e.add(mover(caja(0.14, 0.1, 0.58, 0.07), sx * 0.42, 0.42, 0, rot(0, 0, sx * -35)), rojo)
        for z in (-0.4, -0.13, 0.13, 0.4):   # escapes
            e.add(capsula((sx * 0.45, 0.05, z), (sx * 0.62, -0.12, z), 0.045), Mat((120, 110, 100), metal=1, rugoso=0.4))
    e.add(mover(cilindro(0.38, 0.08, 0.04), 0, 0.68, 0), CUBIERTO)
    e.add(mover(cilindro(0.12, 0.04, 0.02), 0, 0.78, 0), METAL)
    e.add(mover(cilindro(0.22, 0.04, 0.02), 0, -0.12, 0.66, rot(90, 0, 0)), Mat((40, 40, 44), rugoso=0.5))
    e.add(mover(cilindro(0.12, 0.04, 0.02), 0.22, 0.22, 0.66, rot(90, 0, 0)), Mat((40, 40, 44), rugoso=0.5))
    e.add(mover(caja(0.36, 0.08, 0.5, 0.04), 0, -0.48, 0), Mat((60, 62, 66), rugoso=0.5))
    foto(p, e)


def _faro(p, prendido):
    e = Escena(yaw=-20, pitch=8)
    g = rot(90, 0, 0)
    e.add(mover(toro(0.62, 0.1), giro=g), METAL)
    e.add(mover(cilindro(0.64, 0.12, 0.04), 0, 0, -0.12, g), Mat((40, 40, 44), rugoso=0.5))
    vidrio = Mat((255, 245, 200), rugoso=0.05, brillo=1.0, transl=1.0) if prendido else Mat((70, 75, 85), rugoso=0.05, brillo=1.0)
    e.add(mover(elipsoide(0.6, 0.6, 0.18), 0, 0, 0.0), vidrio)
    e.add(mover(esfera(0.12), 0, 0, 0.12), Mat((255, 255, 240), rugoso=0.1, brillo=1.0) if prendido else METAL)
    foto(p, e)


def _resplandor(p):
    """Un halo amarillo detrás del faro prendido (después de ajustar el tamaño: el faro queda igual de grande)."""
    from PIL import Image, ImageDraw, ImageFilter
    n = p.img.width
    halo = Image.new("RGBA", p.img.size, (255, 230, 140, 0))
    m = Image.new("L", p.img.size, 0)
    ImageDraw.Draw(m).ellipse([n * 0.1, n * 0.1, n * 0.9, n * 0.9], fill=180)
    halo.putalpha(m.filter(ImageFilter.GaussianBlur(n * 0.05)))
    halo.alpha_composite(p.img)
    p.img = halo


def pv_luces_on(p):
    _ajustado(lambda q: _faro(q, True), 72)(p)
    _resplandor(p)


def pv_luces_off(p):
    _ajustado(lambda q: _faro(q, False), 72)(p)


def _candado(p, abierto):
    e = Escena(yaw=-20, pitch=10)
    e.add(mover(caja(0.55, 0.42, 0.2, 0.12), y=-0.32), Mat((235, 190, 90), metal=1, rugoso=0.55))
    e.add(mover(union(mover(cilindro(0.07, 0.05), y=0.04), mover(caja(0.025, 0.09, 0.06), y=-0.08)), 0, -0.3, 0.19, rot(90, 0, 0)),
          Mat((20, 20, 22), rugoso=0.5))
    R, r = 0.34, 0.075
    arco = lambda q: np.maximum(np.hypot(np.hypot(q[:, 0], q[:, 1]) - R, q[:, 2]) - r, -q[:, 1])
    forma = union(arco, capsula((R, 0, 0), (R, -0.32, 0), r), capsula((-R, 0, 0), (-R, -0.32, 0), r))
    if abierto:   # sube y gira sobre la pata izquierda: la derecha queda afuera
        g, c = rot(0, 25, 0), np.array([-R, 0.0, 0.0])
        e.add(lambda q: forma(((q - np.array([0, 0.62, 0])) - c) @ g + c), CUBIERTO)
    else:
        e.add(mover(forma, y=0.4), CUBIERTO)
    foto(p, e)


def pv_traba_on(p):    # destrabado
    _candado(p, True)


def pv_traba_off(p):   # trabado
    _candado(p, False)


def pv_capo_on(p):
    e = Escena(yaw=-35, pitch=26)
    _auto(e, True, True, (215, 218, 225))
    foto(p, e)


def pv_capo_off(p):
    e = Escena(yaw=-35, pitch=26)
    _auto(e, False, True, (215, 218, 225))
    foto(p, e)


def pv_maletero_on(p):
    e = Escena(yaw=-35, pitch=26)
    _auto(e, True, False, (215, 218, 225))
    foto(p, e)


def pv_maletero_off(p):
    e = Escena(yaw=-35, pitch=26)
    _auto(e, False, False, (215, 218, 225))
    foto(p, e)


def pv_aparcar(p):
    e = Escena(yaw=-18, pitch=6)

    def cartel(q, n):
        x, y = q[:, 0], q[:, 1]
        palo = entre(x, -0.32, -0.14, 0.006) * entre(y, -0.45, 0.45, 0.006)
        r = np.hypot(x + 0.05, y - 0.18)
        panza = entre(r, 0.13, 0.3, 0.006) * (x > -0.06)
        tapa = entre(x, -0.15, -0.04, 0.006) * (entre(y, 0.3, 0.48, 0.006) + entre(y, -0.12, 0.06, 0.006))
        p_ = np.clip(palo + panza + tapa, 0, 1) * _smooth(0.5, 0.8, n[:, 2])
        return mezcla(lin((25, 90, 200)), lin((250, 250, 250)), p_)
    e.add(caja(0.62, 0.62, 0.05, 0.1), Mat(cartel, rugoso=0.25, brillo=0.8))
    e.add(mover(cilindro(0.06, 0.55), 0, -1.15, -0.1), METAL)
    foto(p, e)


def _baulera(p, abierta):
    e = Escena(yaw=-30, pitch=22)
    plast = Mat((35, 36, 40), rugoso=0.35, brillo=0.7)
    e.add(caja(0.7, 0.32, 0.5, 0.2), plast)
    tapa = caja(0.72, 0.18, 0.52, 0.18)
    if abierta:
        e.add(mover(tapa, 0, 0.75, -0.62, rot(-70, 0, 0)), plast)
        e.add(mover(caja(0.62, 0.02, 0.42, 0.02), 0, 0.31, 0), Mat((15, 15, 17), rugoso=0.8))
    else:
        e.add(mover(tapa, 0, 0.42, 0), plast)
        e.add(mover(caja(0.12, 0.05, 0.02, 0.02), 0, 0.3, 0.52), METAL)
    e.add(mover(caja(0.5, 0.04, 0.02, 0.01), 0, 0.0, 0.5), Mat((200, 30, 25), rugoso=0.1, brillo=1.0, transl=0.5))
    foto(p, e)


def pv_baulera_on(p):
    _baulera(p, True)


def pv_baulera_off(p):
    _baulera(p, False)


PANEL = {n: f for n, f in list(globals().items()) if n.startswith("pv_")}
PANEL = {k: f if k.startswith("pv_luces") else _ajustado(f) for k, f in PANEL.items()}

HUD = {"hud_hambre": hud_hambre, "hud_sed": hud_sed, "hud_cansancio": hud_cansancio, "hud_auto": hud_auto,
       "hud_nafta": hud_nafta, "hud_vida": hud_vida, "hud_chaleco": hud_chaleco,
       "hud_perla": hud_perla}
DATOS = {"dato_velocidad": dato_velocidad, "dato_asientos": dato_asientos, "dato_tanque": dato_tanque,
         "dato_maletero": dato_maletero, "dato_guantera": dato_guantera, "dato_licencia": dato_licencia,
         "pago_efectivo": pago_efectivo}
HUD = {k: _ajustado(f) for k, f in HUD.items()}
DATOS = {k: _ajustado(f) for k, f in DATOS.items()}
