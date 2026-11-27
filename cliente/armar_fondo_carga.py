# Agrega (o reemplaza) fondo_carga en americarp.txd: el fondo de la pantalla de carga de los interiores del
# server (gamemode/interfaz/carga.inc). Es la playa de la pantalla de conexión (cliente/conexion-fondo.jpg) en 1024x512,
# oscurecida abajo para que se lea el texto centrado encima. El GTA la estira a la pantalla.
# Mismo formato que las otras texturas (D3D9, 8888, un nivel).
# Uso: python cliente/armar_fondo_carga.py   (después, generar-manifiesto.bat)
import os, struct
from PIL import Image

raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
txd = os.path.join(raiz, "actualizaciones", "archivos", "models", "txd", "americarp.txd")
NOMBRE, VER = "fondo_carga", 0x1803FFFF


def chunk(t, data):
    return struct.pack("<III", t, len(data), VER) + data


def fondo():
    im = Image.open(os.path.join(raiz, "cliente", "conexion-fondo.jpg")).convert("RGB")
    w, h = im.size
    alto = w * 9 // 16
    im = im.crop((0, (h - alto) // 2, w, (h - alto) // 2 + alto)).resize((1024, 512), Image.LANCZOS)
    sombra = Image.new("L", im.size)
    for y in range(512):
        sombra.paste(int(255 * min(0.82, max(0.0, (y - 200) / 312) ** 1.3 * 0.9 + 0.12)), (0, y, 1024, y + 1))
    return Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, sombra).convert("RGBA")


def textura(im):
    r, g, b, a = im.split()
    bgra = Image.merge("RGBA", (b, g, r, a)).tobytes()
    cab = struct.pack("<II", 9, 0x1106) + NOMBRE.encode().ljust(32, b"\0") + b"".ljust(32, b"\0")
    cab += struct.pack("<IIHHBBBB", 0x500, 21, im.size[0], im.size[1], 32, 1, 4, 1)
    cab += struct.pack("<I", len(bgra)) + bgra
    return chunk(0x15, chunk(0x1, cab) + chunk(0x3, b""))


d = open(txd, "rb").read()
t, s, _ = struct.unpack_from("<III", d, 0)
assert t == 0x16
off, tex = 12, []
while off < 12 + s:
    t, tam, _ = struct.unpack_from("<III", d, off)
    if t == 0x15:
        nombre = d[off + 32: off + 64].split(b"\0")[0].decode()
        if nombre != NOMBRE:
            tex.append(d[off:off + 12 + tam])
    off += 12 + tam
tex.append(textura(fondo()))
open(txd, "wb").write(chunk(0x16, chunk(0x1, struct.pack("<HH", len(tex), 0)) + b"".join(tex) + chunk(0x3, b"")))
print("americarp.txd:", len(tex), "texturas, con", NOMBRE)
