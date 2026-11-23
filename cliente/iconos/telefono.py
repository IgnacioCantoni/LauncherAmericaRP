# Texturas del teléfono sin CEF que no son íconos cuadrados: la isla de vidrio (los avisos) y la parte
# de arriba del teléfono que asoma abajo a la derecha cuando llega algo con el teléfono guardado.
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


def tel_asoma():
    """La parte de arriba del teléfono (120 x 74,7 unidades, con el trazo negro), con el mismo marco y fondo
    que el teléfono de TextDraws."""
    W, H = int(120 * PX), int(74.7 * PY)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    alto = H + 60  # el resto del teléfono queda abajo, fuera de la pantalla
    caja = lambda dx, dy, r: _rr((W, alto), (dx, dy, W - 1 - dx, alto - 1), r)
    capa = Image.new("RGBA", (W, alto), (0, 0, 0, 0))
    capa.paste((0, 0, 0, 255), (0, 0), caja(0, 0, 30))
    capa.paste(_grad((W, alto), (214, 217, 223, 255), (170, 174, 182, 255)), (0, 0), caja(PX, PX, 27))
    capa.paste((5, 5, 5, 255), (0, 0), caja(3.5 * PX, 3.5 * PX, 19.5))
    # pantalla con las manchas de color del fondo
    pan = Image.new("RGBA", (W, alto), (22, 11, 51, 255))
    d = ImageDraw.Draw(pan)
    for cx, cy, r, c in ((62, 34, 34, (255, 95, 109, 170)), (24, 80, 30, (123, 47, 247, 170)), (100, 90, 28, (10, 132, 255, 120))):
        d.ellipse([(cx - r) * PX, (cy - r) * PY, (cx + r) * PX, (cy + r) * PY], fill=c)
    pan = pan.filter(ImageFilter.GaussianBlur(26))
    capa.paste(pan, (0, 0), caja(6 * PX, 6 * PY, 14))
    im.alpha_composite(capa.crop((0, 0, W, H)))
    return im.resize((256, 128), Image.LANCZOS)


GRANDES = {"tel_isla": tel_isla, "tel_asoma": tel_asoma}
