"""Convierte un video en fondo/video.bin, el fondo animado que va dentro de AmericaRP.exe.

Uso: python armar_video.py video.mp4   (necesita ffmpeg instalado)

Formato de video.bin: "AMRPVID1", fps (int32), cantidad de cuadros (int32) y después,
por cada cuadro, el largo (int32) y un JPEG de 1100x660 (el tamaño de la ventana).
"""
import glob, os, struct, subprocess, sys, tempfile

FPS = 24
video = sys.argv[1]
salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video.bin")
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-an", "-vf",
                    "fps=%d,scale=-2:660,crop=1100:660" % FPS, "-q:v", "8",
                    os.path.join(tmp, "%05d.jpg")], check=True)
    cuadros = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
    with open(salida, "wb") as f:
        f.write(b"AMRPVID1" + struct.pack("<ii", FPS, len(cuadros)))
        for c in cuadros:
            datos = open(c, "rb").read()
            f.write(struct.pack("<i", len(datos)) + datos)
print("%s: %d cuadros, %.1f MB" % (salida, len(cuadros), os.path.getsize(salida) / 1e6))
