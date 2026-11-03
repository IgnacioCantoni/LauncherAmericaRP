# Launcher de AMERICA RP

Programa de Windows para entrar al server con un clic. Es un solo `AmericaRP.exe`, no necesita instalar nada (usa el .NET Framework 4.x que ya trae Windows 10 y 11).

## Qué hace

- **Jugar**: guarda tu nick y abre el GTA conectado directo al server. Usa los mismos datos que el cliente SA-MP (nick y carpeta del GTA en el registro, `HKCU\Software\SAMP`).
- **Estado del server**: cada 15 segundos muestra si está en línea, los jugadores y el ping.
- **Mi juego**: la carpeta del GTA y si están bien la versión 1.0, el SA-MP 0.3.7 (`samp.exe` y `samp.dll`) y los archivos del server. El resumen también está en la tarjeta del server, junto al botón JUGAR.
- **Noticias**: muestra `noticias.txt` de este repo.
- **Mods**: lista los archivos de `actualizaciones/archivos/` y cuáles le faltan al jugador. Antes de jugar (o con "Actualizar") baja los que no tenga o tenga distintos.
- **Fondo animado**: pasa las fotos de `fondos/` acercándolas y corriéndolas despacio, y fundiendo una con la siguiente. Sin fotos, muestra una ciudad de noche dibujada con autos que pasan.
- **Redes y soporte**: links de Discord, YouTube, TikTok, Instagram y Soporte en el pie; aparecen los que tengan link en `Config.Redes`.
- **Tipografías**: Bebas Neue (títulos) y Barlow (textos), con licencia libre SIL OFL (ver `fuentes/`). Van dentro del `.exe`.

## Compilar

Doble clic en `compilar.bat`. Deja `AmericaRP.exe` en esta carpeta.

Para probar la lógica sin abrir la ventana: `AmericaRP.exe --prueba` (en Linux, `mono AmericaRP.exe --prueba`).

## Configurar

Arriba de `src/Launcher.cs`, en `Config`:

- `Host` y `Puerto`: la IP pública (o dominio) y el puerto del server. Hoy está en `127.0.0.1:7777`, que solo sirve en la PC donde corre el server.
- `Redes`: los links del pie.
- `NoticiasUrl`, `ManifiestoUrl` y `FondosUrl`: apuntan a este repo. Si se dejan vacías, esa función se apaga.

Después de cambiarlos, volvé a compilar y repartí el `.exe` nuevo.

## Publicar noticias

Editá `noticias.txt`, commit y push. Los launchers la leen al abrirse.

## Poner fotos de fondo

1. Sacá capturas en el server con F8 (quedan en `Documentos\GTA San Andreas User Files\SAMP\screens`). Quedan mejor de noche, con poca interfaz en pantalla (sin chat ni HUD).
2. Copialas a `fondos/` con nombres simples (por ejemplo `noche-plaza.jpg`) y anotá cada nombre en `fondos/lista.txt`, en el orden en que querés que pasen. Hasta 12.
3. Commit y push. Los launchers las bajan al abrirse y las guardan para la próxima vez.

## Publicar archivos o mods

1. Copiá los archivos en `actualizaciones/archivos/`, con las mismas carpetas que tienen dentro del GTA. Ejemplo: `actualizaciones/archivos/models/gta3.img` se instala en `<GTA>/models/gta3.img`.
2. Doble clic en `generar-manifiesto.bat`. Rehace `actualizaciones/manifiesto.txt` con la huella (SHA-256) de cada archivo.
3. Commit y push de las dos cosas.

Cada launcher compara la huella de cada archivo con la de su copia y baja solo los distintos. Si un archivo bajado no coincide con el manifiesto, no se instala. Ninguna ruta puede salir de la carpeta del GTA.

Para instalar el SA-MP solo, subí `samp.exe`, `samp.dll` y el resto de los archivos del cliente 0.3.7 a `actualizaciones/archivos/`.

Límite: GitHub no acepta archivos de más de 100 MB en el repo.

## Repartir el launcher

Subí `AmericaRP.exe` como archivo de una Release de GitHub (Releases → Draft a new release) y pasá ese link. El `.exe` no se sube al repo (está en `.gitignore`).
