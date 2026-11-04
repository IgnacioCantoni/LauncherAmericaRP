# Launcher de AMERICA RP

Programa de Windows para entrar al server con un clic. Es un solo `AmericaRP.exe`, no necesita instalar nada (usa el .NET Framework 4.x que ya trae Windows 10 y 11).

## Qué hace

- **Jugar**: guarda tu nick y abre el GTA conectado directo al server. Usa los mismos datos que el cliente SA-MP (nick y carpeta del GTA en el registro, `HKCU\Software\SAMP`).
- **Estado del server**: cada 15 segundos muestra si está en línea, los jugadores y el ping.
- **Mi juego**: la carpeta del GTA y si están bien la versión 1.0, el SA-MP 0.3.7 (`samp.exe` y `samp.dll`) y los archivos del server. El resumen también está en la tarjeta del server, junto al botón JUGAR.
- **Noticias**: muestra `noticias.txt` de este repo, cada noticia con su fecha, etiqueta y título (ver abajo).
- **Mods**: catálogo de mods opcionales que elige el staff (ver "Mods opcionales"). Cada jugador instala y saca los que quiera con un clic. Los archivos que el server reparte a todos (`actualizaciones/archivos/`) se bajan solos antes de jugar, y su estado está en la tarjeta del cliente, en INICIO.
- **Imagen de fondo**: `fondo/fondo.jpg` va dentro del `.exe`, escalada al tamaño de la ventana (1440x810 si entra en la pantalla; si no, 1280x720).
- **Se actualiza solo**: al abrir, mira `launcher/version.txt`. Si hay una versión nueva, la baja de la Release de GitHub, revisa su huella, se reemplaza y se vuelve a abrir (ver abajo).
- **DirectX 9**: antes de jugar revisa que estén `d3dx9_25.dll` (la pide el SA-MP) y, con el ENB activo, `d3dx9_43.dll`. Si faltan, ofrece bajar el instalador oficial de Microsoft de junio de 2010, revisa su huella y lo instala en silencio (Windows pide permiso de administrador). Visual C++ no hace falta: CEF, CLEO y el cargador de ASI no lo usan.
- **Antes de jugar**: revisa que esté `text\american.gxt` (sin él el juego se cierra al cargar) y avisa si el GTA está en Archivos de programa o Windows (ahí no puede actualizar archivos), en OneDrive o en el Escritorio. Con el ENB activo le pone a `gta_sa.exe` el parche de 4 GB (Large Address Aware), para que no se quede sin memoria; la primera vez guarda la copia original como `gta_sa.exe.sin4gb`. No deja abrir un segundo GTA.
- **Archivos rápidos**: recuerda el tamaño y la fecha de cada archivo revisado (`%LOCALAPPDATA%\AmericaRP\huellas.txt`) y solo vuelve a leer los que cambiaron.
- **Si el juego se cierra de golpe**: el launcher sigue al GTA. Cuando se cierra vuelve a aparecer y, si fue un crash, lo avisa con el código y deja un informe para soporte en `%LOCALAPPDATA%\AmericaRP\informes` (versión, Windows, ENB, tiempo jugado y las últimas líneas del chat de SA-MP). También cierra los procesos del CEF que quedaron colgados.
- **Pantallas del server**: instala el cliente de CEF para el teléfono y las demás pantallas en HTML del server (ver abajo).
- **Soporte**: la pestaña SOPORTE abre un formulario como el de NewGamers: elegís qué te pasa (no abre, se cierra solo, no conecta, descarga o instalación, otra cosa), contás qué pasó y "COPIAR PARA DISCORD" arma el mensaje, con el informe técnico si lo dejás marcado (versión del launcher, nick, Windows, carpeta, cada revisión, el ENB y el último cierre de golpe). Si `Config.Redes` tiene el link de Soporte, ofrece abrirlo.
- **Clientes**: en INICIO se elige el cliente, como el selector de juego de NewGamers pero sin repartir el GTA: OFICIAL (el GTA del jugador con los archivos del server), o CUSTOM (otra carpeta del jugador, con los mods y aportes que quiera; su ENB y sus mods se anotan aparte). Al elegir uno, SA-MP pasa a abrir ese GTA. La tarjeta muestra si está listo o lo primero que falta.
- **Opciones del juego**: los tres puntos del cliente elegido muestran el estado completo, abren la carpeta del GTA, repara archivos (borra la memoria de huellas y revisa todo de cero), mueve la carpeta a otro lugar (la copia entera, la revisa y cambia la ruta; la vieja no se borra hasta que el jugador lo decida) o elige otra.
- **Novedades del launcher**: AJUSTES > NOVEDADES muestra `launcher/novedades.txt`, con el mismo formato que las noticias.
- **Dos monitores**: con más de un monitor el GTA abre el cuadro "Device Selection" (elegir pantalla), que no tiene botón en la barra de tareas. El launcher no se esconde hasta que aparece la primera ventana del GTA y la trae al frente, así ese cuadro no queda tapado.
- **Ajustes**: pestaña AJUSTES con dos opciones que se guardan en `%LOCALAPPDATA%\AmericaRP\ajustes.txt`: esconder el launcher en la bandeja (al lado del reloj) mientras jugás, que viene activado, y actualizar el launcher sin preguntar, que viene desactivado. También abre la carpeta de informes de cierres.
- **Archivos prohibidos**: en cada JUGAR lee `prohibidos.txt` de este repo y saca del GTA lo que coincida (ver abajo).
- **Redes y soporte**: links de Discord, YouTube, TikTok, Instagram y Soporte en el pie; aparecen los que tengan link en `Config.Redes`.
- **Tipografía**: Inter (ExtraBold en títulos, SemiBold en negritas y Regular en textos), la misma del teléfono del server, con licencia libre SIL OFL (ver `fuentes/`). Va dentro del `.exe`.

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

Editá `noticias.txt`, commit y push. Los launchers la leen al abrirse. Las noticias se despliegan: la primera viene abierta y las demás muestran su título hasta tocarlas. Los cambios del server van aparte, en `parches.txt` (mismo formato): si tiene alguno, NOTICIAS muestra arriba la opción PARCHES DEL SERVER. En `parches.txt` y `launcher/novedades.txt`, las líneas con `#` antes de la primera entrada son comentarios. La más nueva va arriba y su título sale también en INICIO.

```
## 2026-11-04 | Actualización | Teléfono nuevo
Ahora el teléfono se abre con /telefono.
- Se cierra con Esc.
- Tiene chat y contactos.
```

Cada `## fecha | etiqueta | título` abre una noticia; las líneas de abajo son su texto y las que empiezan con `- ` salen como puntos. Las etiquetas con color propio son Actualización, Arreglo, Evento y Aviso; cualquier otra sale en gris. Un archivo sin `## ` se muestra entero, como antes.

## Archivos prohibidos

`prohibidos.txt` tiene un archivo por línea. Cada vez que alguien toca JUGAR, el launcher lo lee y revisa la carpeta del GTA:

- `cleo/aimbot.cs`: esa ruta exacta. Con `*` y `?` de comodines: `cleo/*wallhack*`.
- `s0beit.asi` (sin `/`): ese nombre en cualquier carpeta.
- Una huella SHA-256 (64 letras y números, la saca `certutil -hashfile archivo SHA256`): ese archivo aunque le cambien el nombre. Se revisan solo `.cs`, `.cleo`, `.asi`, `.dll`, `.lua`, `.luac`, `.exe` y `.sf` de menos de 50 MB.
- `#` empieza un comentario.

Lo que coincide no se borra: se mueve a `<GTA>\_prohibidos\<fecha>` y el jugador ve qué se sacó. Nunca saca `gta_sa.exe`, `samp.exe`, `samp.dll` ni nada que reparta el launcher, aunque una regla lo agarre. Para sumar uno, agregá la línea, commit y push: llega en el próximo JUGAR, sin versión nueva del launcher.

Solo frena a quien entra por el launcher. Quien abre `samp.exe` a mano se lo salta, así que contra trampas lo que vale es lo que controle el server.

## Modo GTA Full: ENB

El ENB (ENBSeries v0.430 para GTA SA) es opcional: cada jugador lo activa o lo desactiva en las opciones del cliente (los tres puntos, en INICIO).

Con SA-MP 0.3.7 se usa la **versión ASI** del ENB. La versión `d3d9.dll` hace cerrar SA-MP al entrar ("An exception occurred"), y la v0.076 entra pero se ve mal (probado el 3/11/2026 con GTA 1.0 US y SA-MP 0.3.7-R5). El `.asi` lo carga el Ultimate ASI Loader (`dinput8.dll`, licencia MIT), que va en `actualizaciones/archivos/` con su licencia porque también lo usa CLEO.

La licencia de ENBSeries prohíbe repartir sus archivos a través de un launcher o gestor de descargas. Por eso, al activarlo, el launcher abre la página oficial (enbdev.com), el jugador baja `enbseries_gtasa_v0430.zip` y lo elige. El launcher revisa que sea esa versión (por la huella del `.asi`, en `Config.EnbAsiSha`) y que no pise archivos de otro mod (incluido otro `dinput8.dll`). Después instala `AsiVersion/enbseries.asi` y los ajustes y shaders de `WrapperVersion` (sin su `d3d9.dll`), y le suma el cargador. Al desactivarlo no borra nada: le cambia el nombre a `enbseries.asi` por `enbseries.asi.desactivado` (el cargador solo lee `.asi`), así volver a activarlo es al instante y sin bajar el zip. Un ENB 0.430 puesto a mano también se reconoce, por la huella de su `.asi`.

Para cambiar cómo se ve (el preset del server), poné los `.ini` o `.fx` modificados en `paquetes/enb/archivos/` (nunca `.dll` ni `.asi` del ENB), corré `generar-manifiesto.bat` y hacé commit y push. Se instalan encima del ENB de cada jugador que lo tenga activado.

El preset del server hoy cambia dos cosas: `enblocal.ini` pide ventana sin bordes, y `enbseries.ini` apaga las sombras complejas (`EnableComplexShadow=false`), porque con `ShadowResolution=1` parpadeaban al mover la cámara (confirmado el 4/11/2026).

## CLEO

Todos los jugadores reciben CLEO 5.5.0 (licencia MIT, de github.com/cleolibrary/CLEO5) con las actualizaciones: `CLEO.asi` y la carpeta `cleo/`, que carga el mismo `dinput8.dll` del ENB. Si anda, en el menú principal del GTA aparece "CLEO" abajo a la izquierda. No se reparten el plugin de audio (`SA.Audio.cleo`) ni su `bass.dll`, porque el GTA ya tiene el `bass.dll` del SA-MP, ni NewOpcodes. Tampoco `SA.Text.cleo` (textos en pantalla): ningún script del server lo usa y Windows Defender lo marca como Trojan:Win32/Wacatac.H!ml, un falso positivo que lo borra apenas se baja.

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


Dos arreglos van con las actualizaciones para todos, porque el cliente de CEF los necesita:

- `salida_limpia.asi`: el SA-MP sale con `ExitProcess`, y al descargarse `cef\client.dll` Windows corta el GTA con 0xC0000602, así que cada salida contaba como crash. Esta ASI cambia ese `ExitProcess` de samp.dll por `TerminateProcess` con el mismo código, cuando el SA-MP y el CEF ya se apagaron. Fuente en `cliente/salida_limpia.c`. Se compila con `i686-w64-mingw32-gcc -O2 -s -shared -nostdlib -e _DllMain@12 -o salida_limpia.asi salida_limpia.c -lkernel32`. Sacarla cuando omp-cef lo arregle.
- Sin `wndmode.ini`: la ventana sin bordes del Ultimate ASI Loader se repartió un día y se sacó, porque con dos monitores el GTA crasheaba después de elegir la pantalla. `prohibidos.txt` la saca de las carpetas que la recibieron. Con el ENB activo, el `enblocal.ini` del paquete ENB (`paquetes/enb/archivos`) sigue pidiendo ventana sin bordes (`ForceBorderless` y `ForceBorderlessFullscreen`).
## Video de la pantalla de carga del GTA

Mientras el GTA carga, en vez de las imágenes de siempre (las de `loadscs.txd`) y su barra gris, se ve el video del server, que ya trae su propio círculo de carga. Lo hace `carga_video.asi`, que va con las actualizaciones junto con `americarp/carga.bin` (el video en cuadros JPEG de 1280x720 como el original, a 24 por segundo, unos 21 MB). El video se repite mientras dure la carga. Si `carga.bin` falta o está roto, se ven las pantallas de siempre, sin barra. Solo funciona con GTA SA 1.0 US; en otra versión la ASI no toca nada. Cada vez que arranca el GTA deja en `americarp/carga.log` qué pasó (si cargó el video, si pudo crear la textura, si dibujó el primer cuadro).

- Fuente en `cliente/carga_video.c` (lee los JPEG con `cliente/stb_image.h`, de dominio público). Se compila con `i686-w64-mingw32-gcc -O2 -s -shared -static-libgcc -o carga_video.asi carga_video.c` desde `cliente/`.
- Para cambiar el video: reemplazá `cliente/carga.mp4` (mejor 16:9), corré `python cliente/armar_carga.py` (necesita ffmpeg), después `generar-manifiesto.bat`, commit y push. El sonido del video no se usa: suena la música de carga del GTA.

## Cambiar la imagen de fondo

Reemplazá `fondo/fondo.jpg` por otra imagen 16:9 (mejor de 1440x810 o más grande) y volvé a compilar. Si no es 16:9 se recorta lo que sobra, sin deformarla.

## Publicar archivos o mods

1. Copiá los archivos en `actualizaciones/archivos/`, con las mismas carpetas que tienen dentro del GTA. Ejemplo: `actualizaciones/archivos/models/gta3.img` se instala en `<GTA>/models/gta3.img`.
2. Doble clic en `generar-manifiesto.bat`. Rehace `actualizaciones/manifiesto.txt` con la huella (SHA-256) de cada archivo.
3. Commit y push de las dos cosas.

Cada launcher compara la huella de cada archivo con la de su copia y baja solo los distintos. Si un archivo bajado no coincide con el manifiesto, no se instala. Ninguna ruta puede salir de la carpeta del GTA.

Para instalar el SA-MP solo, subí `samp.exe`, `samp.dll` y el resto de los archivos del cliente 0.3.7 a `actualizaciones/archivos/`.

Límite: GitHub no acepta archivos de más de 100 MB en el repo.

## Mods opcionales

Los mods de la pestaña MODS los publica el staff desde este repo. Los jugadores no suben mods desde el launcher: un mod puede traer un `.asi` o un `.dll`, que es código que corre en la PC de cada jugador, así que solo entra lo que revisó un moderador. Si un jugador quiere sumar uno, lo pasa por Discord.

Para sumar un mod:

1. Elegí un id en minúsculas, sin espacios (por ejemplo `hud-limpio`).
2. Copiá sus archivos en `mods/<id>/archivos/`, con las mismas carpetas que van dentro del GTA (`mods/hud-limpio/archivos/models/hud.txd`).
3. Opcional: una foto en `mods/<id>/imagen.jpg` (se ve en 150x86, conviene 16:9).
4. Agregalo en `mods/catalogo.txt`: `## hud-limpio | HUD limpio | Interfaz | Autor` y abajo la descripción.
5. Doble clic en `generar-manifiesto.bat`, commit y push.

Para actualizarlo, cambiá sus archivos y repetí el paso 5: a quien lo tenga le aparece ACTUALIZAR. Para sacarlo del catálogo, borrá su entrada (a quien ya lo tenga no se le borra).

Protecciones:
- Cada archivo se baja y se revisa contra su huella SHA-256 antes de ponerlo. Ninguna ruta puede salir de la carpeta del GTA.
- Un mod nunca pisa archivos del server (`actualizaciones`, el ENB, `gta_sa.exe`, `samp.exe`, `samp.dll`...) ni archivos de otro mod instalado. En esos casos no se instala y avisa por qué.
- Lo que el mod reemplaza del jugador se guarda en `%LOCALAPPDATA%\AmericaRP\mods\<id>\` y vuelve a su lugar al sacarlo. Si una instalación nueva falla a mitad de camino, la carpeta queda como estaba.
- `prohibidos.txt` no saca archivos de mods instalados.

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
