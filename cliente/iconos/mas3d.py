# Más íconos 3D para las pantallas sin CEF (mismo motor que objetos3d.py): los avisos en pantalla (aviso_*), los
# botones del cajero (caj_*) y los de /stats, /ayuda y las licencias (ico_*).
import numpy as np
from render3d import (Escena, Mat, lin, entre, _smooth, esfera, caja, cilindro, tronco, capsula, toro, elipsoide,
                      mover, union, suave, cortar, rot)
from objetos3d import foto, mezcla, ruido, _ajustado, METAL, ORO
from armas3d import perfil
from otros3d import extruir

BLANCO = Mat((246, 246, 248), rugoso=0.25, brillo=0.6)
NEGRO = Mat((22, 22, 24), rugoso=0.35, brillo=0.6)
PAPEL = Mat(lambda q, n: lin((240, 238, 230)) * (0.95 + 0.05 * ruido(q, 90))[:, None], rugoso=0.75, brillo=0.2)
DORADO = Mat((245, 185, 40), rugoso=0.16, brillo=0.9)  # dorado esmaltado: el metal de verdad refleja oscuro de frente
MADERA = Mat(lambda q, n: lin((120, 70, 35)) * (0.82 + 0.18 * np.sin(q[:, 0] * 40 + 3 * ruido(q, 6)))[:, None],
             rugoso=0.45, brillo=0.45)


def _laca(color):
    """Esmalte brillante: los avisos y las flechas."""
    return Mat(color, rugoso=0.12, brillo=1.0)


def _billete():
    def c(q, n):
        x, z = q[:, 0], q[:, 2]
        b = lin((120, 175, 110)) * (0.9 + 0.1 * ruido(q, 40)[:, None])
        marco = 1 - entre(x, -0.78, 0.78, 0.01) * entre(z, -0.38, 0.38, 0.01)
        b = mezcla(b, lin((80, 130, 75)), marco)
        return mezcla(b, lin((70, 120, 70)), (np.hypot(x / 1.3, z) < 0.25) * 1.0)
    return Mat(c, rugoso=0.7, brillo=0.2)


def _flecha(largo=0.9, ancho=0.18, punta=0.42, h=0.1):
    """Flecha plana apuntando a +y, centrada, para extruir."""
    pts = [(-ancho, -largo / 2), (ancho, -largo / 2), (ancho, largo / 2 - punta), (punta, largo / 2 - punta), (0, largo / 2),
           (-punta, largo / 2 - punta), (-ancho, largo / 2 - punta)]
    return perfil(pts, h, 0.04)


# ---------------- avisos: una placa esmaltada con su signo en relieve ----------------


def _disco(e, color):
    e.add(mover(cilindro(0.85, 0.13, 0.1), giro=rot(90, 0, 0)), _laca(color))
    e.add(mover(toro(0.85, 0.05), giro=rot(90, 0, 0)), Mat(tuple(int(c * 0.7) for c in color), rugoso=0.2, brillo=0.9))


def aviso_bien(p):
    e = Escena(yaw=-14, pitch=12)
    _disco(e, (40, 175, 80))
    e.add(union(capsula((-0.4, 0.02, 0.15), (-0.12, -0.28, 0.15), 0.1), capsula((-0.12, -0.28, 0.15), (0.42, 0.34, 0.15), 0.1)), BLANCO)
    foto(p, e)


def aviso_mal(p):
    e = Escena(yaw=-14, pitch=12)
    _disco(e, (215, 45, 40))
    e.add(union(capsula((-0.32, -0.32, 0.15), (0.32, 0.32, 0.15), 0.1), capsula((-0.32, 0.32, 0.15), (0.32, -0.32, 0.15), 0.1)), BLANCO)
    foto(p, e)


def aviso_atencion(p):
    e = Escena(yaw=-14, pitch=12)
    e.add(perfil([(0.0, 0.86), (0.92, -0.72), (-0.92, -0.72)], 0.13, 0.12), _laca((250, 195, 30)))
    e.add(capsula((0, 0.32, 0.14), (0, -0.2, 0.14), 0.085), NEGRO)
    e.add(mover(esfera(0.09), 0, -0.45, 0.14), NEGRO)
    foto(p, e)


def aviso_info(p):
    e = Escena(yaw=-14, pitch=12)
    _disco(e, (30, 120, 230))
    e.add(capsula((0, 0.12, 0.15), (0, -0.42, 0.15), 0.1), BLANCO)
    e.add(mover(esfera(0.11), 0, 0.4, 0.15), BLANCO)
    foto(p, e)


# ---------------- cajero ----------------


def _ranura(e):
    """La boca del cajero: una placa de acero cepillado con la ranura negra."""
    e.add(caja(0.95, 0.16, 0.3, 0.05), Mat((150, 155, 165), metal=1, rugoso=0.35))
    e.add(mover(caja(0.7, 0.05, 0.05, 0.02), 0, 0.0, 0.29), NEGRO)


def caj_depositar(p):
    e = Escena(yaw=-12, pitch=14)
    _ranura(e)
    for k in range(3):
        e.add(mover(caja(0.6, 0.38, 0.012, 0.008), 0, 0.42 + k * 0.03, 0.27 - k * 0.03, rot(-8, 0, 0)), _billete())
    e.add(mover(_flecha(0.7), 0.0, 0.45, 0.4, rot(0, 0, 180)), _laca((45, 185, 85)))
    foto(p, e, 2.7)


def caj_retirar(p):
    e = Escena(yaw=-12, pitch=14)
    _ranura(e)
    for k in range(3):
        e.add(mover(caja(0.6, 0.38, 0.012, 0.008), 0, -0.4 - k * 0.03, 0.27 - k * 0.03, rot(8, 0, 0)), _billete())
    e.add(mover(_flecha(0.7), 0.0, -0.45, 0.4, rot(0, 0, 180)), _laca((240, 150, 30)))
    foto(p, e, 2.7)


def caj_transferir(p):
    e = Escena(yaw=-10, pitch=12)
    tarjeta = Mat(lambda q, n: mezcla(lin((30, 70, 160)), lin((20, 35, 90)), _smooth(-0.9, 0.9, q[:, 0] + q[:, 1])), rugoso=0.2, brillo=0.8)
    e.add(mover(caja(0.62, 0.4, 0.02, 0.02), -0.3, -0.25, -0.1, rot(0, 0, 8)), tarjeta)
    e.add(mover(caja(0.62, 0.4, 0.02, 0.02), 0.3, 0.2, -0.2, rot(0, 0, -8)), DORADO)
    e.add(mover(_flecha(0.95), 0.0, 0.45, 0.15, rot(0, 0, -90)), _laca((45, 185, 85)))
    e.add(mover(_flecha(0.95), 0.0, -0.05, 0.15, rot(0, 0, 90)), _laca((40, 130, 230)))
    foto(p, e, 2.8)


def caj_movimientos(p):
    e = Escena(yaw=-14, pitch=10)

    def ticket(q, n):
        x, y = q[:, 0], q[:, 1]
        c = PAPEL.albedo(q, n)
        lineas = sum(entre(y, 0.55 - k * 0.22, 0.6 - k * 0.22, 0.004) for k in range(6)) * entre(x, -0.4, 0.2, 0.004)
        montos = sum(entre(y, 0.55 - k * 0.22, 0.6 - k * 0.22, 0.004) for k in range(6)) * entre(x, 0.27, 0.42, 0.004)
        c = mezcla(c, lin((120, 120, 128)), lineas)
        return mezcla(c, lin((40, 150, 70)), montos)
    # borde de abajo cortado en zigzag
    dientes = [(0.5 - k * 0.1, -0.9 + (0.07 if k % 2 else 0)) for k in range(11)]
    pts = [(-0.5, 0.85), (0.5, 0.85)] + dientes
    e.add(mover(perfil(pts, 0.015, 0.01), giro=rot(0, 0, -6)), Mat(ticket, rugoso=0.75, brillo=0.2))
    foto(p, e, 2.3)


def caj_todo(p):
    e = Escena(yaw=-22, pitch=28)
    rng = np.random.default_rng(11)
    for k in range(14):
        e.add(mover(caja(0.86, 0.018, 0.44, 0.01), 0, -0.35 + k * 0.042, 0, rot(0, rng.uniform(-3, 3), 0)), _billete())
    e.add(mover(caja(0.14, 0.32, 0.46, 0.01), 0, -0.07, 0), Mat((225, 215, 185), rugoso=0.6, brillo=0.3))
    foto(p, e)


def caj_salir(p):
    e = Escena(yaw=-24, pitch=8)
    e.add(caja(0.5, 0.88, 0.06, 0.02), Mat((70, 72, 80), rugoso=0.4))                      # marco
    e.add(mover(caja(0.42, 0.8, 0.05, 0.02), -0.12, 0, 0.18, rot(0, -40, 0)), MADERA)       # hoja entreabierta
    e.add(mover(esfera(0.05), 0.06, 0.0, 0.42), ORO)
    e.add(mover(_flecha(0.75), 0.55, -0.1, 0.25, rot(0, 0, -90)), _laca((45, 185, 85)))
    foto(p, e, 2.8)


# ---------------- /stats, /ayuda y licencias ----------------


def ico_banco(p):
    e = Escena(yaw=-22, pitch=12)
    marmol = Mat(lambda q, n: lin((232, 230, 224)) * (0.92 + 0.08 * ruido(q, 25))[:, None], rugoso=0.35, brillo=0.5)
    e.add(mover(caja(0.95, 0.06, 0.45, 0.02), 0, -0.78), marmol)
    e.add(mover(caja(0.85, 0.06, 0.4, 0.02), 0, -0.66), marmol)
    for x in (-0.6, -0.2, 0.2, 0.6):
        e.add(mover(cilindro(0.1, 0.5, 0.02), x, -0.1, 0.12), marmol)
    e.add(mover(caja(0.85, 0.07, 0.4, 0.02), 0, 0.46), marmol)
    e.add(mover(perfil([(-0.95, 0.0), (0.95, 0.0), (0.0, 0.45)], 0.38, 0.03), 0, 0.53, 0.0), marmol)
    e.add(mover(cilindro(0.09, 0.01, 0.005), 0, 0.68, 0.39, rot(90, 0, 0)), ORO)
    foto(p, e)


def _estrella(r1=0.9, r2=0.4, puntas=5):
    return [(r * np.sin(a), r * np.cos(a)) for i in range(puntas * 2)
            for a, r in [(np.pi * i / puntas, r1 if i % 2 == 0 else r2)]]


def ico_nivel(p):
    e = Escena(yaw=-16, pitch=10)
    e.add(perfil(_estrella(), 0.16, 0.07), DORADO)
    foto(p, e)


def ico_organizacion(p):
    e = Escena(yaw=-16, pitch=10)
    escudo = [(-0.72, 0.8), (0.72, 0.8), (0.72, 0.05), (0.45, -0.5), (0.0, -0.9), (-0.45, -0.5), (-0.72, 0.05)]
    e.add(perfil(escudo, 0.14, 0.1), Mat((200, 150, 35), rugoso=0.18, brillo=0.9))
    interior = [(x * 0.8, y * 0.8 + 0.02) for x, y in escudo]
    e.add(perfil(interior, 0.16, 0.06), _laca((35, 75, 150)))
    e.add(mover(perfil(_estrella(0.32, 0.14), 0.05, 0.02), 0, 0.05, 0.17), DORADO)
    foto(p, e)


def ico_moto(p):
    e = Escena(yaw=-8, pitch=6)
    goma = Mat((25, 25, 28), rugoso=0.7)
    pintura = _laca((215, 110, 30))
    for x in (-0.6, 0.62):
        e.add(mover(toro(0.3, 0.09), x, -0.4, 0, rot(90, 0, 0)), goma)
        e.add(mover(cilindro(0.16, 0.04, 0.02), x, -0.4, 0, rot(90, 0, 0)), METAL)
    e.add(mover(elipsoide(0.32, 0.15, 0.17), 0.05, 0.06, 0), pintura)                         # tanque
    e.add(mover(caja(0.32, 0.05, 0.13, 0.04), -0.38, 0.06, 0, rot(0, 0, -6)), NEGRO)          # asiento
    e.add(mover(caja(0.2, 0.14, 0.12, 0.05), -0.05, -0.2, 0), Mat((60, 62, 68), metal=1, rugoso=0.3))   # motor
    e.add(capsula((0.62, -0.4, 0), (0.42, 0.25, 0), 0.04), METAL)                              # horquilla
    e.add(capsula((0.38, 0.3, -0.2), (0.38, 0.3, 0.2), 0.03), NEGRO)                           # manubrio
    e.add(capsula((-0.6, -0.4, 0.06), (-0.05, -0.25, 0.06), 0.035), METAL)                      # basculante
    e.add(mover(caja(0.16, 0.04, 0.12, 0.03), -0.66, -0.02, 0, rot(0, 0, 12)), pintura)        # guardabarros
    e.add(capsula((-0.15, -0.3, 0.12), (-0.62, -0.18, 0.14), 0.04), METAL)                      # escape
    foto(p, e)


def ico_pasos(p):
    e = Escena(yaw=-20, pitch=8)
    e.add(mover(cilindro(0.06, 0.95, 0.02), 0, -0.05, 0), MADERA)
    tabla1 = [(-0.15, 0.13), (0.62, 0.13), (0.8, 0.0), (0.62, -0.13), (-0.15, -0.13)]
    tabla2 = [(x * -1, y) for x, y in tabla1]
    e.add(mover(perfil(tabla1, 0.035, 0.02), 0, 0.55, 0.08), _laca((40, 140, 70)))
    e.add(mover(perfil(tabla2, 0.035, 0.02), 0, 0.2, 0.08, rot(0, 0, 0)), _laca((45, 100, 190)))
    e.add(mover(cilindro(0.3, 0.04, 0.03), 0, -0.98, 0), Mat((90, 92, 96), rugoso=0.6))
    foto(p, e)


def ico_chat(p):
    e = Escena(yaw=-14, pitch=10)
    e.add(mover(extruir(lambda x, y: np.minimum(np.hypot((x + 0.25) / 1.4, y - 0.25) - 0.42,
                                                 np.hypot(x + 0.62, y + 0.2) - 0.12), 0.1, 0.08), z=-0.15),
          _laca((40, 130, 230)))
    e.add(mover(extruir(lambda x, y: np.minimum(np.hypot((x - 0.28) / 1.4, y + 0.22) - 0.4,
                                                 np.hypot(x - 0.66, y + 0.66) - 0.11), 0.1, 0.08), z=0.12),
          Mat((245, 245, 248), rugoso=0.2, brillo=0.8))
    for dx in (-0.22, 0.0, 0.22):
        e.add(mover(esfera(0.065), 0.28 + dx, -0.22, 0.22), Mat((90, 95, 105), rugoso=0.3))
    foto(p, e)


def ico_mapa(p):
    e = Escena(yaw=-18, pitch=34)

    def papel(k):
        def c(q, n):
            x, z = q[:, 0], q[:, 2]
            b = mezcla(lin((205, 225, 190)), lin((150, 200, 225)), _smooth(0.1, 0.25, ruido(q + k, 3.0)))
            calles = (np.abs(np.sin(x * 9 + k)) < 0.06) + (np.abs(np.sin(z * 7 - k)) < 0.06)
            return mezcla(b, lin((245, 240, 225)), calles.clip(0, 1) * 0.9)
        return Mat(c, rugoso=0.6, brillo=0.25)
    for i, (x, ang) in enumerate(((-0.6, 12), (0.0, -12), (0.6, 12))):
        e.add(mover(caja(0.3, 0.012, 0.6, 0.008), x, 0.0, 0, rot(0, 0, ang)), papel(i * 1.7))
    rojo = _laca((215, 35, 35))
    e.add(mover(suave(0.1, esfera(0.2), mover(tronco(0.15, 0.0, 0.25), y=-0.28)), 0.1, 0.55, 0.05), rojo)
    e.add(mover(esfera(0.07), 0.1, 0.6, 0.23), BLANCO)
    foto(p, e)


def ico_staff(p):
    e = Escena(yaw=-24, pitch=18)
    oscura = Mat(lambda q, n: lin((80, 42, 22)) * (0.82 + 0.18 * np.sin(q[:, 1] * 30 + 3 * ruido(q, 6)))[:, None],
                 rugoso=0.3, brillo=0.7)
    g = rot(0, 0, 35)
    e.add(mover(cilindro(0.22, 0.4, 0.05), 0.1, 0.25, 0, g @ rot(0, 0, 90)), oscura)          # cabeza del mazo
    for d in (-0.25, 0.25):
        e.add(mover(cilindro(0.235, 0.035, 0.01), 0.1 + d * np.cos(np.radians(35)), 0.25 + d * np.sin(np.radians(35)), 0,
                    g @ rot(0, 0, 90)), ORO)
    e.add(capsula((0.1, 0.25, 0), (0.62, -0.5, 0), 0.06), oscura)                              # mango
    e.add(mover(cilindro(0.5, 0.08, 0.03), -0.25, -0.75, 0), oscura)                           # base
    foto(p, e, 2.7)


MAS = {n: _ajustado(f) for n, f in list(globals().items()) if n.startswith(("aviso_", "caj_", "ico_")) and callable(f)}
