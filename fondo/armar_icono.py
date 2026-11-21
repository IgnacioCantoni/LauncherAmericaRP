# Uso: python fondo/armar_icono.py fondo/arranque-estrella.png fondo/icono.ico
# Arma fondo/icono.ico: la estrella brillante en los tamaños grandes y una estrella dorada nítida en los chicos.
import io, math, struct, sys
from PIL import Image, ImageDraw
src = Image.open(sys.argv[1]).convert('RGBA'); src = src.crop(src.getbbox())
def grande(s):
    m = max(src.size); c = Image.new('RGBA', (m, m)); c.paste(src, ((m - src.width) // 2, (m - src.height) // 2))
    return c.resize((s, s), Image.LANCZOS)
def chica(s):
    k = 8; S = s * k; im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im)
    pts = lambda r, ri: [(S / 2 + math.cos(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else ri), S / 2 + 0.04 * S + math.sin(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else ri)) for i in range(10)]
    d.polygon(pts(S * 0.5, S * 0.21), fill=(70, 40, 0, 255))
    d.polygon(pts(S * 0.42, S * 0.175), fill=(255, 196, 70, 255))
    d.polygon(pts(S * 0.2, S * 0.085), fill=(255, 240, 190, 255))
    return im.resize((s, s), Image.LANCZOS)
imgs = [(s, chica(s) if s <= 32 else grande(s)) for s in (16, 20, 24, 32, 48, 64, 128, 256)]
datos = []
for s, im in imgs:
    b = io.BytesIO(); im.save(b, 'PNG'); datos.append(b.getvalue())
out = struct.pack('<HHH', 0, 1, len(imgs)); off = 6 + 16 * len(imgs)
for (s, _), d in zip(imgs, datos):
    out += struct.pack('<BBBBHHII', s % 256, s % 256, 0, 0, 1, 32, len(d), off); off += len(d)
open(sys.argv[2], 'wb').write(out + b''.join(datos))
