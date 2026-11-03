# Launcher de AMERICA RP

Programa de Windows para entrar al server con un clic. Es un solo `AmericaRP.exe`, no necesita instalar nada (usa el .NET Framework 4.x que ya trae Windows 10 y 11).

## Qué hace

- **Jugar**: guarda tu nick y abre el GTA conectado directo al server. Usa los mismos datos que el cliente SA-MP (nick y carpeta del GTA en el registro, `HKCU\Software\SAMP`).
- **Estado del server**: cada 15 segundos muestra si está en línea, los jugadores y el ping.
- **Mi juego**: la carpeta del GTA y si están bien la versión 1.0, el SA-MP 0.3.7 (`samp.exe` y `samp.dll`) y los archivos del server. El resumen también está en la tarjeta del server, junto al botón JUGAR.
- **Noticias**: muestra `noticias.txt` de este repo.
- **Mods**: lista los archivos de `actualizaciones/archivos/` y cuáles le faltan al jugador. Antes de jugar (o con "Actualizar") baja los que no tenga o tenga distintos.
- **Fondo en video**: `fondo/video.bin` (armado desde el video del server) se repite en bucle detrás de todo. Va dentro del `.exe`.
- **Redes y soporte**: links de Discord, YouTube, TikTok, Instagram y Soporte en el pie; aparecen los que tengan link en `Config.Redes`.
- **Tipografías**: Montserrat Bold Italic (títulos, la misma del video) y Barlow (textos), con licencia libre SIL OFL (ver `fuentes/`). Van dentro del `.exe`.

## Compilar

Doble clic en `compilar.bat`. Deja `AmericaRP.exe` en esta carpeta.

Para probar la lógica sin abrir la ventana: `AmericaRP.exe --prueba` (en Linux, `mono AmericaRP.exe --prueba`).

## Configurar

Arriba de `src/Launcher.cs`, en `Config`:

- `Host` y `Puerto`: la IP pública (o dominio) y el puerto del server. Hoy está en `127.0.0.1:7777`, que solo sirve en la PC donde corre el server.
- `Redes`: los links del pie.
- `NoticiasUrl`, `ManifiestoUrl` y `EnbUrl`: apuntan a este repo. Si se dejan vacías, esa función se apaga.

Después de cambiarlos, volvé a compilar y repartí el `.exe` nuevo.

## Publicar noticias

Editá `noticias.txt`, commit y push. Los launchers la leen al abrirse.

## Modo GTA Full: ENB

El ENB es un paquete opcional: cada jugador lo activa o lo desactiva en MI JUEGO. Al activarlo se baja e instala en su carpeta del GTA; al desactivarlo se sacan esos mismos archivos (solo los que siguen iguales a los instalados).

1. Copiá los archivos del ENB en `paquetes/enb/archivos/`, con las mismas carpetas que van dentro del GTA (por ejemplo `d3d9.dll`, `enbseries.ini` y la carpeta `enbseries/`).
2. Doble clic en `generar-manifiesto.bat`.
3. Commit y push.

Antes de repartirlo, revisá la licencia de ENBSeries en enbdev.com y la del preset que uses.

## Cambiar el video de fondo

Con Python y ffmpeg instalados: `python fondo/armar_video.py tu-video.mp4`. Rehace `fondo/video.bin` (cuadros JPEG de 1100x660, sin sonido). Después volvé a compilar.

## Publicar archivos o mods

1. Copiá los archivos en `actualizaciones/archivos/`, con las mismas carpetas que tienen dentro del GTA. Ejemplo: `actualizaciones/archivos/models/gta3.img` se instala en `<GTA>/models/gta3.img`.
2. Doble clic en `generar-manifiesto.bat`. Rehace `actualizaciones/manifiesto.txt` con la huella (SHA-256) de cada archivo.
3. Commit y push de las dos cosas.

Cada launcher compara la huella de cada archivo con la de su copia y baja solo los distintos. Si un archivo bajado no coincide con el manifiesto, no se instala. Ninguna ruta puede salir de la carpeta del GTA.

Para instalar el SA-MP solo, subí `samp.exe`, `samp.dll` y el resto de los archivos del cliente 0.3.7 a `actualizaciones/archivos/`.

Límite: GitHub no acepta archivos de más de 100 MB en el repo.

## Repartir el launcher

Subí `AmericaRP.exe` como archivo de una Release de GitHub (Releases → Draft a new release) y pasá ese link. El `.exe` no se sube al repo (está en `.gitignore`).
