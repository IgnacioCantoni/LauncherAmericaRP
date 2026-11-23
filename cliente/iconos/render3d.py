# Motor 3D chico para que los íconos se vean reales: cada objeto se arma con formas (cilindros, cajas, esferas)
# y se "fotografía" con luz de estudio, reflejos del ambiente, sombras suaves y oclusión. Solo usa numpy.
# Las formas son funciones de distancia (SDF): devuelven cuánto falta para tocar la superficie.
import numpy as np
from PIL import Image

# ---------------- vectores ----------------


def v3(x, y, z):
    return np.array([x, y, z], dtype=np.float64)


def norm(a):
    return a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-9)


def rot(ax=0.0, ay=0.0, az=0.0):
    """Matriz de giro en grados (primero x, después y, después z)."""
    ax, ay, az = np.radians([ax, ay, az])
    cx, sx, cy, sy, cz, sz = np.cos(ax), np.sin(ax), np.cos(ay), np.sin(ay), np.cos(az), np.sin(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


# ---------------- formas (p: puntos (M,3) en coordenadas de la forma) ----------------


def esfera(r):
    return lambda p: np.linalg.norm(p, axis=1) - r


def caja(sx, sy, sz, r=0.0):
    """Caja de medio-lados sx, sy, sz con bordes redondeados de radio r."""
    h = np.array([sx - r, sy - r, sz - r])

    def f(p):
        q = np.abs(p) - h
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - r
    return f


def cilindro(r, h, rb=0.0):
    """Cilindro parado (eje y) de radio r y medio alto h, con el canto redondeado rb."""
    def f(p):
        d = np.stack([np.hypot(p[:, 0], p[:, 2]) - r + rb, np.abs(p[:, 1]) - h + rb], axis=1)
        return np.minimum(d.max(axis=1), 0) + np.linalg.norm(np.maximum(d, 0), axis=1) - rb
    return f


def tronco(r1, r2, h, rb=0.0):
    """Cono cortado parado: radio r1 abajo (y=-h) y r2 arriba (y=+h)."""
    def f(p):
        y = p[:, 1]
        t = np.clip((y + h) / (2 * h), 0, 1)
        r = r1 + (r2 - r1) * t
        k = np.hypot(1.0, (r1 - r2) / (2 * h))
        d1 = (np.hypot(p[:, 0], p[:, 2]) - r) / k
        d2 = np.abs(y) - h
        d = np.stack([d1 + rb, d2 + rb], axis=1)
        return np.minimum(d.max(axis=1), 0) + np.linalg.norm(np.maximum(d, 0), axis=1) - rb
    return f


def capsula(a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a

    def f(p):
        pa = p - a
        t = np.clip((pa @ ba) / (ba @ ba), 0, 1)
        return np.linalg.norm(pa - t[:, None] * ba, axis=1) - r
    return f


def toro(R, r):
    """Anillo acostado (en el plano xz)."""
    return lambda p: np.hypot(np.hypot(p[:, 0], p[:, 2]) - R, p[:, 1]) - r


def elipsoide(rx, ry, rz):
    rr = np.array([rx, ry, rz])

    def f(p):
        k0 = np.linalg.norm(p / rr, axis=1)
        k1 = np.linalg.norm(p / (rr * rr), axis=1)
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
    return f


def mover(f, x=0.0, y=0.0, z=0.0, giro=None):
    """La forma f trasladada a (x,y,z) y girada con la matriz giro."""
    c = np.array([x, y, z])
    if giro is None:
        return lambda p: f(p - c)
    inv = giro  # p_local = R^T (p - c)  ->  (p - c) @ R
    return lambda p: f((p - c) @ inv)


def union(*fs):
    return lambda p: np.min([f(p) for f in fs], axis=0)


def suave(k, *fs):
    """Unión que redondea la juntura (k = tamaño del redondeo)."""
    def f(p):
        d = fs[0](p)
        for g in fs[1:]:
            e = g(p)
            h = np.clip(0.5 + 0.5 * (e - d) / k, 0, 1)
            d = e * (1 - h) + d * h - k * h * (1 - h)
        return d
    return f


def restar(f, *gs):
    return lambda p: np.max([f(p)] + [-g(p) for g in gs], axis=0)


def cortar(f, g):
    return lambda p: np.maximum(f(p), g(p))


def hueco(f, grosor):
    return lambda p: np.abs(f(p)) - grosor


# ---------------- materiales ----------------


def lin(c):
    """Color sRGB 0-255 a lineal."""
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


class Mat:
    def __init__(self, color, metal=0.0, rugoso=0.5, brillo=0.5, transl=0.0):
        """color: (r,g,b) 0-255 o una función (p, n) -> (M,3) lineal. brillo: cuánto refleja un no-metal (0..1)."""
        self.color = color
        self.metal = metal
        self.rugoso = rugoso
        self.brillo = brillo
        self.transl = transl  # luz que pasa (vidrio, plástico fino): aclara del lado contrario a la luz

    def albedo(self, p, n):
        if callable(self.color):
            return self.color(p, n)
        return np.broadcast_to(lin(self.color), p.shape).copy()


# ---------------- escena y cámara ----------------


class Escena:
    def __init__(self, yaw=-28.0, pitch=24.0, ancho=2.3):
        self.partes = []  # (sdf, Mat)
        self.yaw, self.pitch, self.ancho = yaw, pitch, ancho

    def add(self, f, mat):
        self.partes.append((f, mat))
        return f

    def sdf(self, p):
        return np.min([f(p) for f, _ in self.partes], axis=0)

    def ids(self, p):
        return np.argmin([f(p) for f, _ in self.partes], axis=0)


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ambiente(d, rug):
    """Estudio de fotos: una caja de luz grande arriba, una tira a la izquierda, una más débil a la derecha."""
    w = 0.08 + rug * 0.6
    y = d[:, 1]
    c = np.full(len(d), 0.035)
    c = c + 1.6 * _smooth(0.55 - w, 0.75 + w * 0.3, y)                                     # caja de arriba
    izq = _smooth(-0.55 + w, -0.80 - w * 0.2, d[:, 0]) * _smooth(0.55 + w, 0.15 - w, np.abs(y))
    der = _smooth(0.60 - w, 0.85 + w * 0.2, d[:, 0]) * _smooth(0.45 + w, 0.10 - w, np.abs(y))
    c = c + 1.25 * izq + 0.45 * der
    c = c + 0.10 * _smooth(-0.1, -0.6, y)                                                 # piso claro
    return np.repeat(c[:, None], 3, axis=1) * np.array([1.0, 0.98, 0.95])


LUCES = [  # dirección hacia la luz (mundo), intensidad
    (norm(v3(-0.55, 0.85, 0.55)), 2.4),
    (norm(v3(0.75, 0.35, 0.45)), 0.55),
    (norm(v3(0.2, 0.4, -0.9)), 0.9),   # contraluz: marca el borde
]


def render(esc, px=640, pasos=110, sombras=True):
    """Devuelve una imagen RGBA px x px con el objeto (fondo transparente)."""
    R = rot(-esc.pitch, esc.yaw, 0)
    fwd = R @ v3(0, 0, -1)
    right = R @ v3(1, 0, 0)
    up = R @ v3(0, 1, 0)
    s = esc.ancho / 2
    g = (np.arange(px) + 0.5) / px * 2 - 1
    gx, gy = np.meshgrid(g * s, -g * s)
    org = gx.reshape(-1, 1) * right + gy.reshape(-1, 1) * up - fwd * 4.0
    M = len(org)
    t = np.zeros(M)
    vivo = np.ones(M, bool)
    golpe = np.zeros(M, bool)
    for _ in range(pasos):
        idx = np.nonzero(vivo)[0]
        if not len(idx):
            break
        d = esc.sdf(org[idx] + fwd * t[idx, None])
        t[idx] += d
        hit = d < 1e-3
        golpe[idx[hit]] = True
        lejos = t[idx] > 8.0
        vivo[idx[hit | lejos]] = False
    img = np.zeros((M, 4))
    h = np.nonzero(golpe)[0]
    if len(h):
        p = org[h] + fwd * t[h, None]
        e = 1e-3
        n = norm(np.stack([esc.sdf(p + v3(e, 0, 0)) - esc.sdf(p - v3(e, 0, 0)),
                           esc.sdf(p + v3(0, e, 0)) - esc.sdf(p - v3(0, e, 0)),
                           esc.sdf(p + v3(0, 0, e)) - esc.sdf(p - v3(0, 0, e))], axis=1))
        ids = esc.ids(p)
        v = -fwd
        # oclusión ambiental
        ao = np.ones(len(p))
        for i, dd in enumerate((0.02, 0.05, 0.1, 0.18)):
            ao -= (dd - esc.sdf(p + n * dd)) * (1.6 / (i + 1))
        ao = np.clip(ao, 0.25, 1)
        col = np.zeros((len(p), 3))
        for k, (_, mat) in enumerate(esc.partes):
            sel = ids == k
            if not sel.any():
                continue
            pp, nn, aa = p[sel], n[sel], ao[sel]
            alb = mat.albedo(pp, nn)
            ndv = np.clip(nn @ v, 0, 1)
            f0 = np.where(mat.metal > 0.5, 1.0, 0.0) * alb + (1 - mat.metal) * 0.04 * (0.5 + mat.brillo)
            if mat.metal <= 0.5:
                f0 = np.full_like(alb, 0.04 * (0.5 + mat.brillo))
            fres = f0 + (1 - f0) * ((1 - ndv) ** 5)[:, None] * (0.25 + 0.75 * mat.brillo) * (1 - mat.rugoso * 0.7)
            difu = alb * (1 - mat.metal)
            luz = np.zeros_like(alb)
            esp = np.zeros_like(alb)
            sh_cache = None
            for j, (L, I) in enumerate(LUCES):
                ndl = np.clip(nn @ L, 0, 1)
                if j == 0 and sombras:
                    sh_cache = _sombra(esc, pp + nn * 2e-3, L)
                    ndl = ndl * sh_cache
                luz += (ndl * I)[:, None]
                if mat.transl:
                    luz += (np.clip(-(nn @ L), 0, 1) * I * mat.transl)[:, None]
                hh = norm(L + v)
                expo = 2.0 / max(mat.rugoso ** 4, 1e-4) - 2
                spec = np.clip(nn @ hh, 0, 1) ** expo * (expo + 8) / 25.0
                if j == 0 and sombras:
                    spec = spec * sh_cache
                esp += (spec * I * ndl.clip(0, 1) ** 0.0)[:, None]
            r = 2 * (nn @ v)[:, None] * nn - v
            env = ambiente(r, mat.rugoso)
            amb = ambiente(nn, 1.0) * 0.35 + 0.08
            c = difu * (luz + amb * aa[:, None]) + fres * (env * aa[:, None]) + fres * esp * (1 - mat.rugoso * 0.6)
            col[sel] = c
        # tono fílmico y gamma
        col = col * 0.9
        col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14)
        col = np.clip(col, 0, 1) ** (1 / 2.2)
        img[h, :3] = col
        img[h, 3] = 1
    out = (img.reshape(px, px, 4) * 255).round().astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _sombra(esc, p, L, k=10.0):
    res = np.ones(len(p))
    t = np.full(len(p), 0.02)
    for _ in range(40):
        d = esc.sdf(p + L * t[:, None])
        res = np.minimum(res, np.clip(k * d / t, 0, 1))
        t += np.clip(d, 0.01, 0.15)
    return 0.15 + 0.85 * np.clip(res, 0, 1)


# ---------------- ayudas para pintar etiquetas ----------------


def angulo(p):
    """Ángulo alrededor del eje y, de -pi a pi (0 mirando a la cámara si el objeto no está girado)."""
    return np.arctan2(p[:, 0], p[:, 2])


def entre(a, lo, hi, borde=0.004):
    return _smooth(lo - borde, lo + borde, a) * (1 - _smooth(hi - borde, hi + borde, a))
