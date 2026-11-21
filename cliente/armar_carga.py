# Arma actualizaciones/archivos/americarp/carga.bin (la pantalla de carga del GTA) desde
# cliente/carga.jpg (una imagen fija) o un video (.mp4). Necesita ffmpeg. Uso: python cliente/armar_carga.py [origen]
# Formato que lee carga_video.asi: "ARV1", cuadros, ancho, alto, fps (enteros de 4 bytes),
# el tamanio de cada cuadro y despues los JPEG seguidos.
import glob, os, struct, subprocess, sys, tempfile

ANCHO, ALTO, FPS = 1280, 720, 24  # mejor el tamaño del video original; más grande pesa mucho más
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
origen = sys.argv[1] if len(sys.argv) > 1 else os.path.join(raiz, "cliente", "carga.jpg")
imagen = os.path.splitext(origen)[1].lower() in (".jpg", ".jpeg", ".png")
destino = os.path.join(raiz, "actualizaciones", "archivos", "americarp", "carga.bin")

with tempfile.TemporaryDirectory() as tmp:
    # Se llena el 16:9 sin deformar: se escala al alto (o al ancho) y se recorta lo que sobra.
    llenar = "scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos,crop=%d:%d" % (ANCHO, ALTO, ANCHO, ALTO)
    if imagen:  # un solo cuadro: la ASI lo deja fijo y le dibuja la barra de carga abajo
        cmd = ["-vf", llenar + ",format=yuvj420p", "-frames:v", "1", "-q:v", "2"]
    else:
        cmd = ["-an", "-vf", "fps=%d,%s,format=yuvj420p" % (FPS, llenar), "-q:v", "4"]
    subprocess.run(["ffmpeg", "-v", "error", "-i", origen] + cmd + [os.path.join(tmp, "%04d.jpg")], check=True)
    cuadros = [open(f, "rb").read() for f in sorted(glob.glob(os.path.join(tmp, "*.jpg")))]

datos = b"ARV1" + struct.pack("<4I", len(cuadros), ANCHO, ALTO, FPS)
datos += struct.pack("<%dI" % len(cuadros), *map(len, cuadros)) + b"".join(cuadros)

# Revisión: se vuelve a leer como lo hace la ASI.
n, w, h, f = struct.unpack_from("<4I", datos, 4)
assert datos[:4] == b"ARV1" and (n, w, h, f) == (len(cuadros), ANCHO, ALTO, FPS)
assert 20 + 4 * n + sum(struct.unpack_from("<%dI" % n, datos, 20)) == len(datos)
assert all(c[:2] == b"\xff\xd8" for c in cuadros)

os.makedirs(os.path.dirname(destino), exist_ok=True)
open(destino, "wb").write(datos)
print("Listo: %s (%d cuadros, %.1f MB)" % (destino, n, len(datos) / 1048576))
