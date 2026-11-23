# Celdas del inventario sin CEF: el ícono del objeto sobre la caja de la celda, en una sola textura, así cada
# celda sigue siendo un solo TextDraw (el inventario con el maletero abierto ya está cerca del tope de 256
# TextDraws por jugador). Dos por objeto: inv_<id> (la caja llena) e inv_<id>_e (elegida, verde).
# La celda mide 31 x 29 unidades en el juego (93 x 70 px en 1920x1080): se dibuja en esos píxeles y se
# achica a 128x64, así en el juego el ícono no se deforma.
from PIL import Image

LLENA = (0x36, 0x36, 0x3A, 255)      # INV_COLOR_CELDA_LLENA de inventario/pantalla.inc del server
ELEGIDA = (0x24, 0x8A, 0x3D, 255)    # INV_COLOR_SELECCION
W, H = 93 * 2, 70 * 2
LADO = 116                           # el ícono, cuadrado en pantalla, con margen arriba y abajo


def celda(icono, elegida=False):
    im = Image.new("RGBA", (W, H), ELEGIDA if elegida else LLENA)
    ic = icono.resize((LADO, LADO), Image.LANCZOS)
    im.alpha_composite(ic, ((W - LADO) // 2, (H - LADO) // 2))
    return im.resize((128, 64), Image.LANCZOS)


# Botones del panel del vehículo (tecla 2): el ícono sobre el fondo verde (encendido, abierto) o rojo, en una
# sola textura. El botón mide 32 x 32 unidades (96 x 77 px en 1920x1080) y el ícono 24 de lado, cuadrado en pantalla.
VERDE = (0x30, 0xD1, 0x58, 255)      # ESTILO_VERDE
ROJO = (0xFF, 0x45, 0x3A, 255)       # ESTILO_ROJO


def boton(icono, encendido):
    im = Image.new("RGBA", (96 * 2, 77 * 2), VERDE if encendido else ROJO)
    ic = icono.resize((144, 144), Image.LANCZOS)
    im.alpha_composite(ic, ((im.width - 144) // 2, (im.height - 144) // 2))
    return im.resize((128, 128), Image.LANCZOS)
