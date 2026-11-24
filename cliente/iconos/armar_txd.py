# Arma americarp.txd: deja tal cual las texturas que ya tiene (el puño) y agrega/reemplaza obj_<id>
# (objetos, armas y chalecos), inv_* (celdas del inventario), hud_* (HUD sin CEF), app_* y tel_* (teléfono) y dato_*/pago_* (concesionaria) con los íconos realistas, en el mismo formato que el puño (D3D9, 8888 con alfa, un nivel).
# Uso: python3 txd.py <carpeta de iconos.py> <txd entrada> <txd salida> <lado>
import struct, sys
sys.path.insert(0, sys.argv[1])
from iconos import OTROS, icono
from otros3d import HUD, DATOS, PANEL
from telefono import GRANDES
from objetos3d import POR_ID
from armas3d import POR_ID as ARMAS
from chaleco3d import POR_ID as CHALECOS
from mas3d import MAS
from interfaz import INTERFAZ
import iconos
from multiprocessing import Pool
from celdas import celda, boton

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


_TODAS = []


def _foto(i):
    p = iconos.R()
    _TODAS[i](p)
    return p.img


def _fotografiar(fns):
    """Renderiza todos los íconos en paralelo (uno por núcleo) y los deja en la caché de iconos.icono."""
    _TODAS[:] = list(dict.fromkeys(fns))
    with Pool() as pl:
        imgs = pl.map(_foto, range(len(_TODAS)))
    for fn, im in zip(_TODAS, imgs):
        r = iconos.R()
        r.img = im
        iconos._cache[fn] = r


def main():
    _, carpeta, entrada, salida, lado = sys.argv
    lado = int(lado)
    viejas = [(n, c) for n, c in leer(entrada) if not n.startswith(("obj_", "inv_", "hud_", "app_", "dato_", "pago_", "tel_", "pv_", "aviso_", "caj_", "ico_", "esq_", "vel_", "lado_"))]
    objetos = {**POR_ID, **ARMAS, **CHALECOS}
    _fotografiar(list(objetos.values()) + list(HUD.values()) + list(DATOS.values()) + list(OTROS.values()) + list(PANEL.values()) + list(MAS.values()))
    nuevas = [(f"obj_{k}", textura(f"obj_{k}", icono(objetos[k], lado))) for k in sorted(objetos)]
    for k in sorted(objetos):
        grande = icono(objetos[k], 256)
        nuevas += [(f"inv_{k}", textura(f"inv_{k}", celda(grande))), (f"inv_{k}_e", textura(f"inv_{k}_e", celda(grande, True)))]
    nuevas += [(n, textura(n, icono(f, lado))) for n, f in list(HUD.items()) + list(DATOS.items()) + list(OTROS.items()) + list(MAS.items())]
    nuevas += [(n, textura(n, f())) for n, f in list(GRANDES.items()) + list(INTERFAZ.items())]
    # panel del vehículo: pv_<botón>_1 (verde) y pv_<botón>_0 (rojo); algunos cambian de forma según el estado
    for b in ("motor", "luces", "traba", "capo", "maletero", "aparcar", "baulera"):
        for estado, sufijo in ((1, "_on"), (0, "_off")):
            fn = PANEL.get(f"pv_{b}{sufijo}") or PANEL[f"pv_{b}"]
            nuevas.append((f"pv_{b}_{estado}", textura(f"pv_{b}_{estado}", boton(icono(fn, 256), estado == 1))))
    todas = viejas + nuevas
    cuerpo = chunk(0x1, struct.pack("<HH", len(todas), 0)) + b"".join(c for _, c in todas) + chunk(0x3, b"")
    open(salida, "wb").write(chunk(0x16, cuerpo))
    # se vuelve a leer para comprobar que quedó bien armado
    leidas = leer(salida)
    assert [n for n, _ in leidas] == [n for n, _ in todas], leidas
    assert leidas[0][1] == viejas[0][1], "el puño tiene que quedar igual"
    print("texturas:", [n for n, _ in leidas])


main()
