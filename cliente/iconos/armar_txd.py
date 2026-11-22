# Arma americarp.txd: deja tal cual las texturas que ya tiene (el puño) y agrega/reemplaza obj_<id>
# (objetos) y hud_* (HUD sin CEF) con los íconos realistas, en el mismo formato que el puño (D3D9, 8888 con alfa, un nivel).
# Uso: python3 txd.py <carpeta de iconos.py> <txd entrada> <txd salida> <lado>
import struct, sys
sys.path.insert(0, sys.argv[1])
from iconos import HUD, POR_ID, icono

VER = 0x1803FFFF


def chunk(t, data):
    return struct.pack("<III", t, len(data), VER) + data


def leer(path):
    d = open(path, "rb").read()
    t, s, v = struct.unpack_from("<III", d, 0)
    assert t == 0x16
    off, fin, tex = 12, 12 + s, []
    while off < fin:
        t, s, v = struct.unpack_from("<III", d, off)
        if t == 0x15:
            nombre = d[off + 12 + 12 + 8: off + 12 + 12 + 40].split(b"\0")[0].decode()
            tex.append((nombre, d[off:off + 12 + s]))
        off += 12 + s
    return tex


def textura(nombre, im):
    w, h = im.size
    r, g, b, a = im.split()
    from PIL import Image
    bgra = Image.merge("RGBA", (b, g, r, a)).tobytes()
    cab = struct.pack("<II", 9, 0x1106) + nombre.encode().ljust(32, b"\0") + b"".ljust(32, b"\0")
    cab += struct.pack("<IIHHBBBB", 0x500, 21, w, h, 32, 1, 4, 1)
    cab += struct.pack("<I", len(bgra)) + bgra
    return chunk(0x15, chunk(0x1, cab) + chunk(0x3, b""))


def main():
    _, carpeta, entrada, salida, lado = sys.argv
    lado = int(lado)
    viejas = [(n, c) for n, c in leer(entrada) if not n.startswith(("obj_", "hud_"))]
    nuevas = [(f"obj_{k}", textura(f"obj_{k}", icono(POR_ID[k], lado))) for k in sorted(POR_ID)]
    nuevas += [(n, textura(n, icono(f, lado))) for n, f in HUD.items()]
    todas = viejas + nuevas
    cuerpo = chunk(0x1, struct.pack("<HH", len(todas), 0)) + b"".join(c for _, c in todas) + chunk(0x3, b"")
    open(salida, "wb").write(chunk(0x16, cuerpo))
    # se vuelve a leer para comprobar que quedó bien armado
    leidas = leer(salida)
    assert [n for n, _ in leidas] == [n for n, _ in todas], leidas
    assert leidas[0][1] == viejas[0][1], "el puño tiene que quedar igual"
    print("texturas:", [n for n, _ in leidas])


main()
