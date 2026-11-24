# Texturas de la interfaz sin CEF que no son íconos: las esquinas redondas de los paneles (esq_*), la tecla de
# vidrio del marcador del teléfono (tel_tecla) y el velocímetro (vel_fondo, vel_arco_<k>, lado_fondo,
# lado_arco_<k>). Se dibujan 4 veces más grandes y se achican, para que los bordes queden suaves.
import numpy as np
from PIL import Image

SS = 4
VEL_PASOS = 26          # vel_arco_0 .. vel_arco_26 (vehiculos/hud.inc: HUD_ARCO_PASOS)
VEL_ROJOS = 4           # los últimos pasos del arco, en rojo
LADO_PASOS = 12         # lado_arco_0 .. lado_arco_12 (HUD_PUNTOS)
ARCO = 270.0            # grados del arco del velocímetro, de abajo a la izquierda a abajo a la derecha


def _grilla(n):
    """Coordenadas de cada píxel en [-1, 1] (y hacia arriba), radio y ángulo (0 arriba, en el sentido del reloj)."""
    t = (np.arange(n) + 0.5) / n * 2 - 1
    x, y = np.meshgrid(t, -t)
    r = np.hypot(x, y)
    a = np.degrees(np.arctan2(x, y))           # 0 arriba, 90 a la derecha
    return x, y, r, a


def _img(rgb, alfa, lado):
    n = rgb.shape[0]
    im = np.dstack([np.clip(rgb, 0, 255), np.clip(alfa, 0, 1) * 255]).astype(np.uint8)
    return Image.fromarray(im, "RGBA").resize((lado, lado), Image.LANCZOS) if n != lado else Image.fromarray(im, "RGBA")


def _sobre(fondo_rgb, fondo_a, rgb, a):
    """Pone una capa (rgb, a) encima de otra (premultiplicando)."""
    a_out = a + fondo_a * (1 - a)
    rgb_out = (rgb * a[..., None] + fondo_rgb * (fondo_a * (1 - a))[..., None]) / np.maximum(a_out, 1e-6)[..., None]
    return rgb_out, a_out


def _disco(r, radio, borde):
    """1 adentro del círculo y 0 afuera, con el borde suave de 'borde' de ancho."""
    return np.clip((radio - r) / borde + 0.5, 0, 1)


def _arco(r, a, radio, ancho, desde, hasta, borde):
    """Un arco de 'ancho' alrededor de 'radio', entre los ángulos desde y hasta (en grados, 0 arriba), con
    las puntas redondas."""
    n = r.shape[0]
    x = r * np.sin(np.radians(a))
    y = r * np.cos(np.radians(a))
    dentro = (a >= desde) & (a <= hasta) if hasta - desde < 360 else np.ones_like(r, bool)
    d = np.where(dentro, np.abs(r - radio) - ancho / 2, 9.0)
    for ang in (desde, hasta):
        px, py = radio * np.sin(np.radians(ang)), radio * np.cos(np.radians(ang))
        d = np.minimum(d, np.hypot(x - px, y - py) - ancho / 2)
    return np.clip(-d / borde + 0.5, 0, 1)


def _angulo_vel(a):
    """El ángulo del arco del velocímetro: 0 al empezar (abajo a la izquierda) y ARCO al terminar."""
    return (a + ARCO / 2)


# ---------------- esquinas de los paneles ----------------


def _esquina(cual):
    """Un cuarto de círculo blanco que llena el cuadrado; el centro del círculo va en la esquina de adentro.
    cual: 'ai' arriba a la izquierda, 'ad', 'bi', 'bd'. El TextDraw le pone el color."""
    n = 64 * SS
    t = (np.arange(n) + 0.5) / n
    x, y = np.meshgrid(t, t)
    cx = 1.0 if cual[1] == "i" else 0.0
    cy = 1.0 if cual[0] == "a" else 0.0
    r = np.hypot(x - cx, y - cy)
    alfa = np.clip((1.0 - r) * n / 1.5 + 0.5, 0, 1)
    return _img(np.full((n, n, 3), 255.0), alfa, 64)


# ---------------- tecla del teléfono ----------------


def tel_tecla():
    """Tecla redonda de vidrio esmerilado: un velo claro, más brillante arriba, y el canto con luz."""
    n = 128 * SS
    x, y, r, a = _grilla(n)
    b = 1.5 / n * 2
    disco = _disco(r, 0.96, b)
    luz = 0.16 + 0.10 * np.clip(y, 0, 1)                      # más claro arriba
    canto = np.clip(1 - np.abs(r - 0.93) / 0.04, 0, 1) * (0.25 + 0.35 * np.clip(y + 0.3, 0, 1))
    alfa = disco * (luz + canto)
    return _img(np.full((n, n, 3), 255.0), alfa, 128)


# ---------------- velocímetro ----------------


def _cara(n, r, x, y, cara=0.92):
    """Trazo negro, bisel de metal y la cara de vidrio oscuro de un reloj."""
    b = 1.5 / n * 2
    rgb = np.zeros((n, n, 3))
    alfa = _disco(r, 1.0, b)                                    # trazo negro
    metal = 120 + 90 * np.clip((y - x) * 0.7 + 0.3, 0, 1)        # claro arriba a la izquierda
    bisel = _disco(r, 0.965, b)
    rgb, alfa = _sobre(rgb, alfa, np.repeat(metal[..., None], 3, 2) * np.array([1, 1.01, 1.04]), bisel)
    fondo = (34 - 20 * np.clip(r / cara, 0, 1))[..., None] * np.array([1, 1.04, 1.18]) + 4
    rgb, alfa = _sobre(rgb, alfa, fondo, _disco(r, cara, b))
    # reflejo del vidrio arriba
    reflejo = _disco(np.hypot(x * 0.9, (y - 0.55) * 1.6), 0.55, 0.25) * 0.10
    rgb, alfa = _sobre(rgb, alfa, np.full((n, n, 3), 255.0), reflejo * _disco(r, cara, b))
    return rgb, alfa


def vel_fondo():
    """La esfera del velocímetro: trazo, bisel, cara oscura, marcas en los 270 grados (las últimas en rojo) y
    el arco apagado por donde se prende la velocidad."""
    n = 192 * SS
    x, y, r, a = _grilla(n)
    b = 1.5 / n * 2
    rgb, alfa = _cara(n, r, x, y)
    for i in range(VEL_PASOS + 1):
        ang = -ARCO / 2 + ARCO * i / VEL_PASOS
        mayor = i % 2 == 0
        rojo = i > VEL_PASOS - VEL_ROJOS
        r0, r1 = (0.78, 0.89) if mayor else (0.82, 0.89)
        s, c = np.sin(np.radians(ang)), np.cos(np.radians(ang))
        # distancia al segmento de la marca
        t = np.clip(x * s + y * c, r0, r1)
        d = np.hypot(x - t * s, y - t * c) - (0.018 if mayor else 0.011)
        m = np.clip(-d / b + 0.5, 0, 1) * (0.9 if mayor else 0.6)
        col = np.array([255, 69, 58]) if rojo else np.array([235, 238, 245])
        rgb, alfa = _sobre(rgb, alfa, np.broadcast_to(col, (n, n, 3)).astype(float), m)
    pista = _arco(r, a, 0.68, 0.075, -ARCO / 2, ARCO / 2, b) * 0.16
    rgb, alfa = _sobre(rgb, alfa, np.full((n, n, 3), 255.0), pista)
    return _img(rgb, alfa, 192)


def _vel_arco(k):
    """El arco prendido hasta el paso k: blanco con un brillo alrededor y la punta roja al final del arco."""
    def f():
        n = 192 * SS
        x, y, r, a = _grilla(n)
        b = 1.5 / n * 2
        hasta = -ARCO / 2 + ARCO * k / VEL_PASOS
        rgb, alfa = np.zeros((n, n, 3)), np.zeros((n, n))
        if k == 0:
            return _img(rgb, alfa, 192)
        corte = -ARCO / 2 + ARCO * (VEL_PASOS - VEL_ROJOS) / VEL_PASOS
        blanco = _arco(r, a, 0.68, 0.085, -ARCO / 2, min(hasta, corte), b)
        rojo = _arco(r, a, 0.68, 0.085, corte, hasta, b) if hasta > corte else np.zeros_like(r)
        brillo = _arco(r, a, 0.68, 0.2, -ARCO / 2, hasta, 0.08) * 0.22
        col_brillo = np.where((a > corte)[..., None] & (hasta > corte), np.array([255, 80, 70]), np.array([170, 205, 255]))
        rgb, alfa = _sobre(rgb, alfa, col_brillo.astype(float), brillo)
        rgb, alfa = _sobre(rgb, alfa, np.full((n, n, 3), 248.0), blanco)
        rgb, alfa = _sobre(rgb, alfa, np.broadcast_to(np.array([255, 69, 58]), (n, n, 3)).astype(float), rojo)
        return _img(rgb, alfa, 192)
    return f


def lado_fondo():
    """Los relojes chicos del estado y la gasolina: trazo, bisel, cara oscura y el anillo apagado."""
    n = 96 * SS
    x, y, r, a = _grilla(n)
    b = 1.5 / n * 2
    rgb, alfa = _cara(n, r, x, y, 0.9)
    pista = _arco(r, a, 0.74, 0.13, -180, 180, b) * 0.16
    rgb, alfa = _sobre(rgb, alfa, np.full((n, n, 3), 255.0), pista)
    return _img(rgb, alfa, 96)


def _lado_arco(k):
    """El anillo prendido hasta el paso k, desde arriba en el sentido del reloj. Es blanco: el TextDraw le pone
    el color (verde, amarillo, naranja o rojo)."""
    def f():
        n = 96 * SS
        x, y, r, a = _grilla(n)
        b = 1.5 / n * 2
        a360 = np.where(a < 0, a + 360, a)                      # 0 arriba y de 0 a 360 en el sentido del reloj
        rgb, alfa = np.full((n, n, 3), 255.0), np.zeros((n, n))
        if k == 0:
            return _img(rgb, alfa, 96)
        hasta = 360.0 * k / LADO_PASOS
        anillo = _arco(r, a360, 0.74, 0.13, 0.0, hasta, b) if k < LADO_PASOS else np.clip(-(np.abs(r - 0.74) - 0.065) / b + 0.5, 0, 1)
        brillo = (_arco(r, a360, 0.74, 0.3, 0.0, hasta, 0.1) if k < LADO_PASOS else np.clip(1 - np.abs(r - 0.74) / 0.15, 0, 1)) * 0.25
        alfa = np.maximum(anillo, brillo)
        return _img(rgb, alfa, 96)
    return f


INTERFAZ = {"esq_ai": lambda: _esquina("ai"), "esq_ad": lambda: _esquina("ad"),
            "esq_bi": lambda: _esquina("bi"), "esq_bd": lambda: _esquina("bd"),
            "tel_tecla": tel_tecla, "vel_fondo": vel_fondo, "lado_fondo": lado_fondo}
INTERFAZ.update({f"vel_arco_{k}": _vel_arco(k) for k in range(VEL_PASOS + 1)})
INTERFAZ.update({f"lado_arco_{k}": _lado_arco(k) for k in range(LADO_PASOS + 1)})
