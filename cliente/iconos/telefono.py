# Texturas del teléfono sin CEF que no son íconos cuadrados: el teléfono entero (tel_cuerpo, tel_cuerpo_app),
# la isla de vidrio (los avisos) y la parte de arriba del teléfono que asoma abajo a la derecha cuando llega
# algo con el teléfono guardado.
# Se dibujan en píxeles de una pantalla de 1920x1080 (3 px por unidad de ancho y 2,41 de alto en el
# juego) y se achican a la textura, así en el juego no se deforman.
from PIL import Image, ImageDraw, ImageFilter, ImageChops

PX, PY = 3.0, 1080 / 448.0


def _rr(size, box, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=r, fill=255)
    return m


def _grad(size, c1, c2):
    t = Image.new("RGBA", (1, 256))
    for i in range(256):
        t.putpixel((0, i), tuple(int(c1[k] + (c2[k] - c1[k]) * i / 255) for k in range(len(c1))))
    return t.resize(size)


def tel_isla():
    """Isla de vidrio de 102 x 34,5 unidades, con la cámara arriba al medio."""
    W, H = int(102 * PX), int(34.5 * PY)
    m = _rr((W, H), (0, 0, W - 1, H - 1), H / 2)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # vidrio oscuro translúcido, un poco más claro arriba
    im.paste(_grad((W, H), (58, 58, 72, 190), (22, 22, 30, 205)), (0, 0), m)
    # borde de luz: más fuerte arriba, como el vidrio del iPhone
    borde = ImageChops.subtract(m, m.filter(ImageFilter.GaussianBlur(2.2)).point(lambda v: 255 if v > 250 else v))
    luz = _grad((W, H), (255, 255, 255, 150), (255, 255, 255, 45))
    luz.putalpha(ImageChops.multiply(luz.getchannel("A"), borde.point(lambda v: min(255, v * 3))))
    im.alpha_composite(luz)
    # reflejo en la mitad de arriba
    brillo = _grad((W, H), (255, 255, 255, 38), (255, 255, 255, 0))
    mb = _rr((W, H), (6, 3, W - 7, H // 2), H / 3)
    im.alpha_composite(Image.composite(brillo, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mb))
    # la cámara, igual que la isla chica del teléfono (30 x 7 unidades)
    cw, ch = 30 * PX, 7 * PY
    ImageDraw.Draw(im).rounded_rectangle([(W - cw) / 2, 1.2 * PY, (W + cw) / 2, 1.2 * PY + ch], radius=ch / 2, fill=(0, 0, 0, 255))
    return im.resize((256, 64), Image.LANCZOS)


# ---------------- el teléfono entero (cuerpo, fondo y vidrios en una sola imagen) ----------------
# Medidas de comunicacion/telefono.inc, en unidades con el origen en la esquina del teléfono (TEL_X, TEL_Y).
TW, TH = 118.0, 254.0
PAN = (5.0, 5.0, TW - 10, TH - 10)           # TEL_PANTALLA_*
CY = 5.0 + 12.0                             # TEL_CONTENIDO_Y
CX = TW / 2
WX, WW = 5.0 + 5.0, TW - 20                  # TEL_TARJETA_X / TEL_TARJETA_ANCHO
WY, WH = CY + 2.0, 58.0                     # el widget
DY, DH = 5.0 + 197.0, 36.0                  # el dock
MARGEN = 3.0                                # la textura sobra 3 unidades por lado (botones y sombra)
K = 2                                       # se dibuja al doble de 1920x1080 y se achica
ASP = 1.244                                 # ESTILO_ASPECTO


def _u(x, y):
    return ((x + MARGEN) * PX * K, (y + MARGEN) * PY * K)


def _box(x, y, w, h):
    a, b = _u(x, y)
    c, d = _u(x + w, y + h)
    return [a, b, c, d]


def _tam():
    return (int((TW + 2 * MARGEN) * PX * K), int((TH + 2 * MARGEN) * PY * K))


def _mrr(x, y, w, h, r):
    return _rr(_tam(), _box(x, y, w, h), r * PX * K)


def _caja(im, x, y, w, h, r, color):
    ImageDraw.Draw(im).rounded_rectangle(_box(x, y, w, h), radius=r * PX * K, fill=color)


def _fondo():
    """Fondo de pantalla: degradé azul y violeta con luces naranja, rosa y celeste y unas ondas suaves."""
    import numpy as np
    w, h = _tam()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    col = np.stack([12 + 30 * v, 14 + 10 * v, 48 + 40 * (1 - v)], -1)
    for cx, cy, r, c, k in ((0.85, 0.18, 0.45, (230, 90, 60), 1), (0.15, 0.45, 0.4, (110, 50, 220), 1),
                            (0.75, 0.75, 0.5, (20, 120, 255), 1), (0.3, 0.95, 0.35, (255, 70, 150), 0.7)):
        g = np.exp(-(((u - cx) / r) ** 2 + ((v - cy) / (r * 0.8)) ** 2)) * k
        col += g[..., None] * np.array(c, np.float32)
    onda = 0.5 + 0.5 * np.sin((u * 2.2 + v * 3.0 + 0.35 * np.sin(u * 5)) * 3.1)
    col *= (0.62 + 0.22 * onda[..., None])
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert("RGBA")


def _vidrio(im, fondo, x, y, w, h, r, tinte):
    """Vidrio esmerilado: el fondo desenfocado con un velo y el canto con luz, más fuerte arriba."""
    import numpy as np
    m = _mrr(x, y, w, h, r)
    im.paste(Image.alpha_composite(fondo.filter(ImageFilter.GaussianBlur(10 * K)), Image.new("RGBA", im.size, tinte)), (0, 0), m)
    canto = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(canto).rounded_rectangle(_box(x, y, w, h), radius=r * PX * K, outline=(255, 255, 255, 90), width=max(1, int(0.5 * PX * K)))
    b, d = _u(0, y)[1], _u(0, y + h)[1]
    k = np.clip(1.15 - (np.arange(im.size[1])[:, None] - b) / max(1, d - b), 0.25, 1)
    canto.putalpha(Image.fromarray((np.array(canto.getchannel("A"), np.float32) * k).astype(np.uint8)))
    im.alpha_composite(canto)


def _sombra_icono(im, cx, top, lado):
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle(_box(cx - lado / 2 + 0.3, top + 1.2, lado, lado * ASP), radius=lado * 0.24 * PX * K, fill=(0, 0, 0, 110))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(1.6 * K)))


def _pegar_icono(im, fn, cx, cy, lado):
    """Un ícono 3D (de iconos.icono) centrado en (cx, cy), cuadrado en pantalla."""
    from iconos import icono
    w, h = int(lado * PX * K), int(lado * ASP * PY * K)
    ic = icono(fn, 256).resize((w, h), Image.LANCZOS)
    x, y = _u(cx - lado / 2, cy - lado * ASP / 2)
    im.alpha_composite(ic, (int(x), int(y)))


def _cuerpo(app):
    """El teléfono: marco de titanio con sus botones, bisel negro y pantalla. En el inicio lleva el vidrio
    del widget (con su línea y los íconos de la línea y el saldo), el del dock y la sombra de cada app; en
    una app o una llamada, el fondo desenfocado y oscuro. La isla, la señal, la batería y la barrita de
    abajo van siempre (no cambian)."""
    import numpy as np
    im = Image.new("RGBA", _tam(), (0, 0, 0, 0))
    s = Image.new("RGBA", im.size, (0, 0, 0, 0))
    _caja(s, 1, 2, TW, TH, 12, (0, 0, 0, 120))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(3 * K)))
    for x, y, h in ((-1.6, 40, 10), (-1.6, 58, 18), (-1.6, 80, 18), (TW - 0.4, 62, 26)):
        _caja(im, x, y, 2.0, h, 0.8, (120, 122, 128, 255))
    w, h = im.size
    xx = np.linspace(0, 1, w)
    tono = 70 + 55 * np.exp(-((xx - 0.08) / 0.05) ** 2) + 40 * np.exp(-((xx - 0.94) / 0.04) ** 2) + 18 * np.sin(xx * 9)
    metal = np.repeat(np.stack([tono, tono * 1.02, tono * 1.07], -1)[None], h, 0)
    im.paste(Image.fromarray(np.clip(metal, 0, 255).astype(np.uint8)).convert("RGBA"), (0, 0), _mrr(0, 0, TW, TH, 12))
    canto = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(canto).rounded_rectangle(_box(0.3, 0.3, TW - 0.6, TH - 0.6), radius=11.7 * PX * K, outline=(230, 232, 238, 150),
                                            width=max(1, int(0.35 * PX * K)))
    im.alpha_composite(canto)
    _caja(im, 1.6, 2.0, TW - 3.2, TH - 4.0, 10.4, (4, 4, 6, 255))
    fondo = _fondo()
    if app:
        fondo = Image.alpha_composite(fondo.filter(ImageFilter.GaussianBlur(14 * K)), Image.new("RGBA", im.size, (6, 6, 14, 128)))
    pantalla = _mrr(*PAN, 8.6)
    im.paste(fondo, (0, 0), pantalla)
    if not app:
        from iconos import OTROS
        from otros3d import DATOS
        _vidrio(im, fondo, WX, WY, WW, WH, 6, (16, 10, 36, 95))
        ImageDraw.Draw(im).line([_u(WX + 6, WY + 40.5), _u(WX + WW - 6, WY + 40.5)], fill=(255, 255, 255, 50), width=K)
        _pegar_icono(im, OTROS["app_llamadas"], WX + 10, WY + 46.5, 6.5)
        _pegar_icono(im, DATOS["pago_efectivo"], WX + 10, WY + 54.5, 6.5)
        _vidrio(im, fondo, WX, DY, WW, DH, 8, (255, 255, 255, 34))
        for a in range(7):
            cx, top = (WX + WW / 8 + a * WW / 4, WY + 64) if a < 4 else (CX + (a - 5) * 28, 5.0 + 201)
            _sombra_icono(im, cx, top, 19)
    # isla con la cámara, señal, batería y la barrita
    _caja(im, CX - 14, 8, 28, 7.5, 3.75, (0, 0, 0, 255))
    x, y = _u(CX + 9 - 1.7, 9.6)
    ImageDraw.Draw(im).ellipse([x, y, x + 3.4 * PX * K, y + 3.4 * ASP * PY * K], fill=(20, 24, 40, 255))
    for b in range(4):
        a = 1.6 + b * 0.9
        _caja(im, 5 + 79 + b * 2.1, 5 + 9 - a, 1.4, a, 0.5, (255, 255, 255, 255))
    ImageDraw.Draw(im).rounded_rectangle(_box(5 + 89.5, 5 + 4.2, 10, 5), radius=1.6 * PX * K, outline=(255, 255, 255, 160), width=max(1, int(0.5 * PX * K)))
    _caja(im, 5 + 90.5, 5 + 5.2, 6.5, 3, 0.8, (255, 255, 255, 255))
    _caja(im, 5 + 100, 5 + 5.7, 0.9, 2, 0.4, (255, 255, 255, 140))
    _caja(im, CX - 18, 5 + PAN[3] - 5.5, 36, 1.8, 0.9, (255, 255, 255, 230))
    # reflejo del vidrio en diagonal
    a, b = _u(PAN[0], PAN[1])
    c, d = _u(PAN[0] + PAN[2], PAN[1] + PAN[3])
    ref = Image.new("L", im.size, 0)
    ImageDraw.Draw(ref).polygon([(a, b), (a + (c - a) * 0.55, b), (a, b + (d - b) * 0.38)], fill=22)
    ref = ImageChops.multiply(ref, pantalla).filter(ImageFilter.GaussianBlur(2 * K))
    brillo = Image.new("RGBA", im.size, (255, 255, 255, 0))
    brillo.putalpha(ref)
    im.alpha_composite(brillo)
    return im


def tel_cuerpo():
    """El teléfono en el inicio, 124 x 260 unidades (el teléfono y 3 de margen por lado)."""
    return _cuerpo(False).resize((512, 1024), Image.LANCZOS)


def tel_cuerpo_app():
    """El teléfono dentro de una app o en una llamada: el fondo desenfocado y oscuro."""
    return _cuerpo(True).resize((512, 1024), Image.LANCZOS)


def tel_asoma():
    """La parte de arriba del teléfono (120 x 74,7 unidades) que asoma abajo a la derecha con un aviso:
    la misma imagen que el teléfono abierto, cortada."""
    im = _cuerpo(True)
    x, y = _u(-1.0, -0.5)
    return im.crop((int(x), int(y), int(x + 120 * PX * K), int(y + 74.7 * PY * K))).resize((256, 128), Image.LANCZOS)


GRANDES = {"tel_isla": tel_isla, "tel_asoma": tel_asoma, "tel_cuerpo": tel_cuerpo, "tel_cuerpo_app": tel_cuerpo_app}
