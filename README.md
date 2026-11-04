# Launcher de AMERICA RP

Programa de Windows para entrar al server con un clic. Es un solo `AmericaRP.exe`, no necesita instalar nada (usa el .NET Framework 4.x que ya trae Windows 10 y 11).

## Qué hace

- **Jugar**: guarda tu nick y abre el GTA conectado directo al server. Usa los mismos datos que el cliente SA-MP (nick y carpeta del GTA en el registro, `HKCU\Software\SAMP`).
- **Estado del server**: cada 15 segundos muestra si está en línea, los jugadores y el ping.
- **Mi juego**: la carpeta del GTA y si están bien la versión 1.0, el SA-MP 0.3.7 (`samp.exe` y `samp.dll`) y los archivos del server. El resumen también está en la tarjeta del server, junto al botón JUGAR.
- **Noticias**: muestra `noticias.txt` de este repo.
- **Mods**: lista los archivos de `actualizaciones/archivos/` y cuáles le faltan al jugador. Antes de jugar (o con "Actualizar") baja los que no tenga o tenga distintos.
- **Fondo en video**: `fondo/video.bin` (armado desde el video del server) se repite en bucle detrás de todo. Va dentro del `.exe`.
- **Se actualiza solo**: al abrir, mira `launcher/version.txt`. Si hay una versión nueva, la baja de la Release de GitHub, revisa su huella, se reemplaza y se vuelve a abrir (ver abajo).
- **DirectX 9**: antes de jugar revisa que estén `d3dx9_25.dll` (la pide el SA-MP) y, con el ENB activo, `d3dx9_43.dll`. Si faltan, ofrece bajar el instalador oficial de Microsoft de junio de 2010, revisa su huella y lo instala en silencio (Windows pide permiso de administrador). Visual C++ no hace falta: CEF, CLEO y el cargador de ASI no lo usan.
- **Antes de jugar**: revisa que esté `text\american.gxt` (sin él el juego se cierra al cargar) y avisa si el GTA está en Archivos de programa o Windows (ahí no puede actualizar archivos), en OneDrive o en el Escritorio. Con el ENB activo le pone a `gta_sa.exe` el parche de 4 GB (Large Address Aware), para que no se quede sin memoria; la primera vez guarda la copia original como `gta_sa.exe.sin4gb`. No deja abrir un segundo GTA.
- **Archivos rápidos**: recuerda el tamaño y la fecha de cada archivo revisado (`%LOCALAPPDATA%\AmericaRP\huellas.txt`) y solo vuelve a leer los que cambiaron.
- **Si el juego se cierra de golpe**: el launcher sigue al GTA. Cuando se cierra vuelve a aparecer y, si fue un crash, lo avisa con el código y deja un informe para soporte en `%LOCALAPPDATA%\AmericaRP\informes` (versión, Windows, ENB, tiempo jugado y las últimas líneas del chat de SA-MP). También cierra los procesos del CEF que quedaron colgados.
- **Pantallas del server**: instala el cliente de CEF para el teléfono y las demás pantallas en HTML del server (ver abajo).
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

El ENB (ENBSeries v0.430 para GTA SA) es opcional: cada jugador lo activa o lo desactiva en MI JUEGO.

Con SA-MP 0.3.7 se usa la **versión ASI** del ENB. La versión `d3d9.dll` hace cerrar SA-MP al entrar ("An exception occurred"), y la v0.076 entra pero se ve mal (probado el 3/11/2026 con GTA 1.0 US y SA-MP 0.3.7-R5). El `.asi` lo carga el Ultimate ASI Loader (`dinput8.dll`, licencia MIT), que va en `actualizaciones/archivos/` con su licencia porque también lo usa CLEO.

La licencia de ENBSeries prohíbe repartir sus archivos a través de un launcher o gestor de descargas. Por eso, al activarlo, el launcher abre la página oficial (enbdev.com), el jugador baja `enbseries_gtasa_v0430.zip` y lo elige. El launcher revisa que sea esa versión (por la huella del `.asi`, en `Config.EnbAsiSha`) y que no pise archivos de otro mod (incluido otro `dinput8.dll`). Después instala `AsiVersion/enbseries.asi` y los ajustes y shaders de `WrapperVersion` (sin su `d3d9.dll`), y le suma el cargador. Al desactivarlo saca todo eso, solo los archivos que siguen iguales a como se instalaron.

Para cambiar cómo se ve (el preset del server), poné los `.ini` o `.fx` modificados en `paquetes/enb/archivos/` (nunca `.dll` ni `.asi` del ENB), corré `generar-manifiesto.bat` y hacé commit y push. Se instalan encima del ENB de cada jugador que lo tenga activado.

## CLEO

Todos los jugadores reciben CLEO 5.5.0 (licencia MIT, de github.com/cleolibrary/CLEO5) con las actualizaciones: `CLEO.asi` y la carpeta `cleo/`, que carga el mismo `dinput8.dll` del ENB. Si anda, en el menú principal del GTA aparece "CLEO" abajo a la izquierda. No se reparten el plugin de audio (`SA.Audio.cleo`) ni su `bass.dll`, porque el GTA ya tiene el `bass.dll` del SA-MP, ni NewOpcodes.

Scripts del server, en `actualizaciones/archivos/cleo/`:

- `fps_sin_limite.cs`: cada medio segundo saca los tres topes de FPS que hay:
  - la opción "Frame limiter" del menú (`0xBA6794`);
  - la espera mínima entre cuadros del GTA (el `cmp eax, 14` de `0x53E94C`; el SA-MP lo pone en 2);
  - el limitador del propio SA-MP, que con el "Frame limiter" apagado duerme hasta completar 10 ms por cuadro (tope de unos 97 a 99 FPS): el `cmp esi, 11` de `samp.dll + 0xA1D86` pasa a `cmp esi, 0`. Solo lo toca si el SA-MP está cargado y esos bytes son los de la 0.3.7-R5 (`83 FE 0B 7D`); con otra versión no hace nada.

  Lo arma `cleo/armar_fps.py` (el código, comentado, está ahí): `python cleo/armar_fps.py actualizaciones/archivos/cleo/fps_sin_limite.cs`.

  Los FPS quedan atados solo a tu PC (o al V-Sync de la placa de video). Con FPS muy altos el GTA tiene fallas conocidas (nadar o trepar cuesta más, algunas animaciones van más rápido).

Para sumar otro CLEO, poné su `.cs` (y sus archivos) en `actualizaciones/archivos/cleo/`, corré `generar-manifiesto.bat` y hacé commit y push. Ojo: con CLEO instalado cualquier jugador puede sumar sus propios scripts, incluidos trucos, así que lo que importa (dinero, armas, vida) se controla en el server.

## Pantallas del server (CEF)

El teléfono y las demás pantallas en HTML del server usan omp-cef (licencia MIT, github.com/aurora-mp/omp-cef). Antes de jugar, el launcher revisa si el GTA tiene su cliente (`cef.asi` y la carpeta `cef/`, unos 310 MB instalado) y, si falta o es de otra versión, baja el zip oficial del release (`Config.CefZipUrl`, unos 150 MB), revisa su huella (`Config.CefZipSha`) e instala solo `cef.asi` y `cef/`. La versión instalada queda anotada en `cef/americarp-version.txt`. Si algo falla se avisa y se juega igual, con los diálogos de siempre.

Para pasar a otra versión de omp-cef: cambiá la URL y la huella (SHA-256 del zip), volvé a compilar y repartí el `.exe`. La versión tiene que ser la misma que la del `Cef.dll` del server.

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

Pasá el link de la última Release: https://github.com/IgnacioCantoni/LauncherAmericaRP/releases/latest. El `.exe` no se sube al repo (está en `.gitignore`).

## Sacar una versión nueva del launcher

Los jugadores que ya lo tienen la reciben solos al abrirlo. En este orden:

1. Subí `Config.Version` en `src/Launcher.cs` (por ejemplo de `1.1.0` a `1.2.0`).
2. Doble clic en `compilar.bat`.
3. Doble clic en `publicar-launcher.bat`. Escribe `launcher/version.txt` con la versión y la huella del `.exe`.
4. En GitHub, Releases → Draft a new release, con la etiqueta `v` + la versión (`v1.2.0`), y subí `AmericaRP.exe`.
5. Recién después, commit y push de `launcher/version.txt`. Si lo subís antes que la Release, los launchers no encuentran el `.exe` y siguen con el que tienen.

Si el `.exe` bajado no coincide con la huella, no se instala. Si el jugador lo tiene en una carpeta donde Windows no deja escribir (como Archivos de programa), le ofrece abrir la página para bajarlo a mano.
