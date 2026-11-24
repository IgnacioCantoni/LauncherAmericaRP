# Launcher de AMERICA RP

Programa de Windows para entrar al server con un clic. Es un solo `AmericaRP.exe`, no necesita instalar nada (usa el .NET Framework 4.x que ya trae Windows 10 y 11).

Licencia MIT (ver `LICENSE`). Firma del `.exe`: ver [Code signing policy](#code-signing-policy).

## Qué hace

- **Jugar**: guarda tu nick y abre el GTA conectado directo al server. Usa los mismos datos que el cliente SA-MP (nick y carpeta del GTA en el registro, `HKCU\Software\SAMP`).
- **Estado del server**: cada 15 segundos muestra si está en línea, los jugadores y el ping.
- **Estado del juego**: la carpeta del GTA y si están bien la versión 1.0, el SA-MP 0.3.7 (`samp.exe` y `samp.dll`) y los archivos del server, en las opciones del cliente (los tres puntos). Lo primero que falta se ve en la tarjeta del cliente, en INICIO.
- **Noticias**: dos listas, PARCHES DEL SERVER (`parches.txt`) y LAUNCHER (`launcher/novedades.txt`), cada entrada con su fecha, etiqueta y título (ver abajo). Un punto rosa en la pestaña avisa si hay un parche que el jugador no abrió.
- **Mods**: catálogo de mods opcionales que elige el staff (ver "Mods opcionales"). Cada jugador instala y saca los que quiera con un clic. Los archivos que el server reparte a todos (`actualizaciones/archivos/`) se bajan solos antes de jugar, y su estado está en la tarjeta del cliente, en INICIO.
- **Diseño**: el mismo de las pantallas del server (conexión, ingreso y personajes): paneles de vidrio sobre la playa y botones en degradé dorado a rosa. La imagen de fondo es `cliente/conexion-fondo.jpg`, la misma de la pantalla de conexión, y va dentro del `.exe` escalada al tamaño de la ventana (1440x810 si entra en la pantalla; si no, 1280x720). Los paneles usan una copia borrosa que se arma una sola vez al abrir.
- **Se actualiza solo**: al abrir, mira `launcher/version.txt`. Si hay una versión nueva, la baja de la Release de GitHub, revisa su huella, se reemplaza y se vuelve a abrir (ver abajo).
- **DirectX 9**: antes de jugar revisa que estén `d3dx9_25.dll` (la pide el SA-MP) y, con el ENB activo, `d3dx9_43.dll`. Si faltan, ofrece bajar el instalador oficial de Microsoft de junio de 2010, revisa su huella y lo instala en silencio (Windows pide permiso de administrador). Los archivos que reparte el launcher no usan Visual C++ (CEF, CLEO, SilentPatch, los limit adjusters y el cargador de ASI vienen con todo adentro).
- **DLL de los mods**: antes de jugar lee qué DLL importan los ASI (raíz, `scripts`, `plugins`), los plugins de CLEO, `samp.dll`, `dinput8.dll` y `d3d9.dll`, y busca cada una junto al archivo, en la carpeta del GTA y en Windows (SysWOW64, y WinSxS para las de Visual C++ 2005/2008). Si falta una de Microsoft, ofrece instalar su paquete oficial de 32 bits: DirectX (el de arriba) o Visual C++ 2005 a 2022, bajado de Microsoft, con la firma de Microsoft revisada antes de correrlo en silencio. Si falta una que viene con el mod (por ejemplo `DllTricks.dll` del fastman92), avisa qué mod está incompleto y ofrece moverlo a `_prohibidos\<fecha>` (no se borra), porque si no el GTA tira "Unable to load ... Error: 126" en cada arranque.
- **Antes de jugar**: revisa que esté `text\american.gxt` (sin él el juego se cierra al cargar) y avisa si el GTA está en Archivos de programa o Windows (ahí no puede actualizar archivos), en OneDrive o en el Escritorio. Con el ENB activo le pone a `gta_sa.exe` el parche de 4 GB (Large Address Aware), para que no se quede sin memoria; la primera vez guarda la copia original como `gta_sa.exe.sin4gb`. No deja abrir un segundo GTA.
- **Archivos rápidos**: recuerda el tamaño y la fecha de cada archivo revisado (`%LOCALAPPDATA%\AmericaRP\huellas.txt`) y solo vuelve a leer los que cambiaron.
- **Si el juego se cierra de golpe**: el launcher sigue al GTA. Cuando se cierra vuelve a aparecer y, si fue un crash, lo avisa con el código y deja un informe para soporte en `%LOCALAPPDATA%\AmericaRP\informes` (versión, Windows, ENB, tiempo jugado y las últimas líneas del chat de SA-MP). También cierra los procesos del CEF que quedaron colgados.
- **Pantallas del server**: instala el cliente de CEF para el teléfono y las demás pantallas en HTML del server (ver abajo).
- **Soporte**: la pestaña SOPORTE abre un formulario como el de NewGamers: elegís qué te pasa (no abre, se cierra solo, no conecta, descarga o instalación, otra cosa), contás qué pasó y "COPIAR PARA DISCORD" arma el mensaje, con el informe técnico si lo dejás marcado (versión del launcher, nick, Windows, carpeta, cada revisión, el ENB y el último cierre de golpe). Si `Config.Redes` tiene el link de Soporte, ofrece abrirlo.
- **Clientes**: en INICIO se elige el cliente, como el selector de juego de NewGamers pero sin repartir el GTA: OFICIAL (el GTA del jugador con los archivos del server), o CUSTOM (otra carpeta del jugador, con los mods y aportes que quiera; su ENB y sus mods se anotan aparte). Al elegir uno, SA-MP pasa a abrir ese GTA. La tarjeta muestra si está listo o lo primero que falta.
- **Opciones del juego**: los tres puntos del cliente elegido muestran el estado completo, abren la carpeta del GTA, repara archivos (borra la memoria de huellas y revisa todo de cero), mueve la carpeta a otro lugar (la copia entera, la revisa y cambia la ruta; la vieja no se borra hasta que el jugador lo decida) o elige otra.
- **Novedades del launcher**: NOTICIAS > LAUNCHER muestra `launcher/novedades.txt`, con el mismo formato que los parches.
- **Dos monitores**: con más de un monitor el GTA abre el cuadro "Device Selection" (elegir pantalla), que no tiene botón en la barra de tareas. El launcher no se esconde hasta que aparece la primera ventana del GTA y la trae al frente, así ese cuadro no queda tapado.
- **Ajustes**: pestaña AJUSTES con una opción que se guarda en `%LOCALAPPDATA%\AmericaRP\ajustes.txt`: esconder el launcher en la bandeja (al lado del reloj) mientras jugás, que viene activado. Las versiones nuevas del launcher se instalan siempre solas, sin preguntar (desde la 1.4.0). También abre la carpeta de informes de cierres.
- **Archivos prohibidos**: en cada JUGAR lee `prohibidos.txt` de este repo y saca del GTA lo que coincida (ver abajo).
- **Comunidad**: la tarjeta de arriba a la derecha tiene el botón del Discord (con una invitación que no venza muestra los miembros y conectados) y abajo YouTube, TikTok e Instagram; aparecen los que tengan link en `Config.Redes`. Sin link de Discord, el botón dice "DISCORD MUY PRONTO".
- **Tarjeta de JUGAR**: tu nick, tu última partida, los jugadores y el ping del server elegido y tus horas jugadas.
- **Tipografía**: Inter (ExtraBold en títulos, SemiBold en negritas y Regular en textos), la misma del teléfono del server, con licencia libre SIL OFL (ver `fuentes/`). Va dentro del `.exe`.

## Compilar

Doble clic en `compilar.bat`. Deja `AmericaRP.exe` en esta carpeta, con la estrella de ícono (`fondo/icono.ico`, lo arma `fondo/armar_icono.py`).

GitHub también lo compila solo en cada push a `main` que toque el código (`.github/workflows/compilar.yml`): queda en Actions como artefacto `AmericaRP`. Es el que se firma (ver abajo).

Para probar la lógica sin abrir la ventana: `AmericaRP.exe --prueba` (en Linux, `mono AmericaRP.exe --prueba`).

## Configurar

Arriba de `src/Launcher.cs`, en `Config`:

- `Servidores`: los servers que se eligen en INICIO (nombre, IP o dominio y puerto). Hoy DESARROLLO está en `127.0.0.1:7777` (el server de la PC del staff) y OFICIAL todavía no tiene IP: aparece como "Todavía sin IP" y no se puede elegir hasta completarla. El launcher consulta todos cada 15 segundos y muestra si están en línea y su ping; JUGAR entra al elegido.
- `Redes`: los links de la tarjeta COMUNIDAD (Discord, YouTube, TikTok e Instagram) y el de Soporte, que se ofrece después de copiar el mensaje en SOPORTE.
- `ParchesUrl`, `NovedadesUrl`, `ManifiestoUrl` y `EnbUrl`: apuntan a este repo. Si se dejan vacías, esa función se apaga.

Después de cambiarlos, volvé a compilar y repartí el `.exe` nuevo.

## Publicar noticias

Editá `parches.txt` (cambios del server) o `launcher/novedades.txt` (cambios del launcher), commit y push. Los launchers los leen al abrirse. Las entradas se despliegan: la primera viene abierta y las demás muestran su título hasta tocarlas. Las líneas con `#` antes de la primera entrada son comentarios y la más nueva va arriba. Desde la 1.5.0 el launcher ya no lee `noticias.txt`; queda en el repo para las versiones viejas hasta que todos se actualicen.

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

- `fps_libres.cs`: FPS sin tope siempre, también en vehículos y apuntando. Las fallas del GTA con FPS muy altos (los vehículos que frenan de golpe al soltar el acelerador, no poder caminar apuntando con la Desert Eagle) las arreglan Framerate Vigilante y SilentPatch (ver abajo); probado el 2026-11-20. Ese día se probó antes limitar en los vehículos y al apuntar (a 98 FPS con la Desert Eagle tampoco se caminaba) y se descartó. Cada cuadro:
  - apaga la opción "Frame limiter" del menú (`0xBA6794`) y la espera mínima entre cuadros del GTA (el `cmp eax, 14` de `0x53E94C`; el SA-MP lo pone en 2);
  - pasa el limitador del SA-MP (`cmp esi, 11` de `samp.dll + 0xA1D86`, unos 98 FPS) a `cmp esi, 0`, que nunca duerme. Con el Frame limiter apagado el SA-MP hace `if (ms < N) Sleep(10 - ms)`: un `N` mayor que 11 sin cambiar el 10 le pasa un negativo a `Sleep` y cuelga el juego. Solo lo toca si el SA-MP está cargado y esos bytes son los de la 0.3.7-R5 (`83 FE 0B 7D`); con otra versión no hace nada.
  - no usa el Frame limiter del menú para limitar en ningún caso: prenderlo minimiza el juego un segundo.

  Lo arma `cleo/armar_fps.py` (el código, comentado, está ahí): `python cleo/armar_fps.py actualizaciones/archivos/cleo/fps_libres.cs`.

- `hud_propio.cs` (desde 2026-11-20): sin CEF el server dibuja su propio HUD arriba a la derecha (dinero, arma con sus balas, vida y chaleco), y este script esconde esos del GTA: pone `ret` (`C3`) al principio de `CHud::DrawAmmo` (`0x5893B0`), `CHud::DrawWeaponIcon` (`0x58D7D0`) y las barras de vida (`0x589270`) y chaleco (`0x5890A0`), y `90 E9` en `0x58F47D` para saltear el dinero (las direcciones del MTA, `Client/game_sa/CHudSA.h`). Lo repite cada segundo. Si en la carpeta del GTA está `cef.asi` (con CEF), termina sin tocar nada. Lo arma `cleo/armar_hud.py`: `python cleo/armar_hud.py actualizaciones/archivos/cleo/hud_propio.cs`.
- `sens_igual.cs`: iguala la sensibilidad vertical del mouse a la horizontal. El GTA deja la vertical fija en 0.0015 (`0xB6EC18`) y la barra del menú solo mueve la horizontal (`0xB6EC1C`, 0.0025 de fábrica); cada cuadro copia la horizontal en la vertical, así la barra mueve las dos. Son 41 bytes: `00 00 01 00 04 00 8D 0A 01 1C EC B6 00 04 04 04 00 03 00 00 8C 0A 01 18 EC B6 00 04 04 03 00 00 04 00 02 00 01 FE FF FF FF`.

- `models/txd/americarp.txd` (no es un CLEO, va con las actualizaciones): el puño del HUD sin CEF. Es la textura `fist` de `hud.txd` sin el recuadro negro, solo el puño con su contorno sobre fondo transparente, 128x128 en 8888. El server la usa como sprite de TextDraw `americarp:puno`. También trae los íconos de los objetos que se venden en la tienda 24/7 y la farmacia (`obj_<id>`, el id de la tabla `objetos` del server: `americarp:obj_2` es la hamburguesa), de 64x64 en el mismo formato, y los íconos del HUD sin CEF (`hud_hambre`, `hud_sed`, `hud_cansancio`, `hud_auto`, `hud_nafta`, `hud_vida` y `hud_chaleco`), cada uno una sola imagen en lugar de las piezas que armaba el server. Además las apps del teléfono sin CEF (`app_banco`, `app_taxi`, `app_maps`, `app_miamerica`, `app_llamadas`, `app_mensajes`, `app_agenda`) y los datos y pagos de la concesionaria (`dato_velocidad`, `dato_asientos`, `dato_tanque`, `dato_maletero`, `dato_guantera`, `dato_licencia`, `pago_efectivo`). Para el inventario sin CEF, una celda por objeto con su caja ya dibujada (`inv_<id>` llena e `inv_<id>_e` elegida, 128x64, de `cliente/iconos/celdas.py`); los íconos de los objetos (los de la tienda, la caña, lo que se encuentra trabajando y las balas) se arman en 3D en `cliente/iconos/objetos3d.py` y las 21 armas en `cliente/iconos/armas3d.py` (de costado, las largas en diagonal, con cámara con perspectiva para que el metal tenga degradé), la placa balística (49) y los chalecos común, táctico y pesado con sus placas (50 a 70, con una barra de una rayita por placa) en `cliente/iconos/chaleco3d.py`, y se fotografían con luz de estudio, reflejos y sombras con `cliente/iconos/render3d.py` (solo numpy). Para los avisos del teléfono: la isla de vidrio (`tel_isla`, 256x64), la parte de arriba del teléfono que asoma (`tel_asoma`, 256x128) y los botones de la llamada (`tel_atender`, `tel_colgar`); la isla y la parte que asoma se dibujan con `cliente/iconos/telefono.py`. Los del HUD y la concesionaria también son 3D (`cliente/iconos/otros3d.py`); los botones del panel del vehículo sin CEF también (`pv_<botón>_1` con fondo verde y `pv_<botón>_0` rojo, 128x128, de `boton` en `cliente/iconos/celdas.py`); los demás (apps y botones del teléfono) se dibujan con `cliente/iconos/iconos.py` y se meten en el .txd con `python cliente/iconos/armar_txd.py cliente/iconos actualizaciones/archivos/models/txd/americarp.txd actualizaciones/archivos/models/txd/americarp.txd 64` (deja el puño como está); después hay que rehacer el manifiesto.

Arreglos de los bugs del propio GTA, en `actualizaciones/archivos/` (todos con licencia MIT, cada uno con su `-LICENSE.txt`). Son los que trae NewGamers para jugar con FPS libres:

- `FramerateVigilante.SA.asi` y `FramerateVigilante.ini` (github.com/GTAmodding/FramerateVigilante): arregla la física que depende de los FPS con el limitador apagado. Su `FPSlimit` solo vale con el limitador del menú prendido, y `fps_libres.cs` lo apaga.
- `SilentPatchSA.asi` y `SilentPatchSA.ini` (github.com/CookiePLMonster/SilentPatch): arreglos generales del GTA para PC, incluida la espera de 14 ms entre cuadros. Ojo: SilentPatch respeta `Documents\GTA San Andreas User Files\device_remembered.set` (la pantalla elegida con "recordar") y deja de preguntar la pantalla. Con dos monitores uno viejo hizo que el GTA se cerrara al arrancar (2026-11-20); borrarlo vuelve a mostrar la elección.
- `III.VC.SA.LimitAdjuster.asi` y su `.ini` (github.com/ThirteenAG/III.VC.SA.LimitAdjuster), con la configuración de NewGamers: sube los límites de edificios, objetos, vehículos y otros, para que el GTA no se cierre con mapeos grandes.
- `stream.ini` con 512 MB de memoria de streaming (traía 13 MB): con poca memoria el GTA carga y descarga el mapa todo el tiempo al manejar y bajan los FPS. El `gta_sa.exe` 1.0 US que se usa puede usar hasta 4 GB (Large Address Aware).

NewGamers también trae el limit adjuster de fastman92 y RefreshRateFix de DarkP1xel; no se reparten porque no tienen una licencia que permita hacerlo, y el primero hace lo mismo que el de ThirteenAG y SilentPatch ya usa la frecuencia del monitor (`UseDesktopRefreshRate`).

Hasta el 2026-11-09 se repartía `fps_sin_limite.cs`, sin tope nunca: está en `prohibidos.txt` para que el launcher lo quite de los GTA que lo recibieron.

Para sumar otro CLEO, poné su `.cs` (y sus archivos) en `actualizaciones/archivos/cleo/`, corré `generar-manifiesto.bat` y hacé commit y push. Ojo: con CLEO instalado cualquier jugador puede sumar sus propios scripts, incluidos trucos, así que lo que importa (dinero, armas, vida) se controla en el server.

## Pantallas del server (CEF)

El teléfono y las demás pantallas en HTML del server usan omp-cef (licencia MIT, github.com/aurora-mp/omp-cef). Antes de jugar, el launcher revisa si el GTA tiene su cliente (`cef.asi` y la carpeta `cef/`, unos 310 MB instalado) y, si falta o es de otra versión, baja el zip oficial del release (`Config.CefZipUrl`, unos 150 MB), revisa su huella (`Config.CefZipSha`) e instala solo `cef.asi` y `cef/`. La versión instalada queda anotada en `cef/americarp-version.txt`. Si algo falla se avisa y se juega igual, con los diálogos de siempre.

En AJUSTES, "Jugar sin las pantallas del server (CEF)" deja de bajarlo y lo apaga renombrando `cef.asi` a `cef.asi.off` (la carpeta `cef/` queda, así prenderlo de nuevo no baja nada). Va por cliente: se puede tener el oficial con CEF y el personalizado sin.

Para pasar a otra versión de omp-cef: cambiá la URL y la huella (SHA-256 del zip), volvé a compilar y repartí el `.exe`. La versión tiene que ser la misma que la del `Cef.dll` del server.


Dos arreglos van con las actualizaciones para todos, porque el cliente de CEF los necesita:

- `salida_limpia.asi`: el SA-MP sale con `ExitProcess`, y al descargarse `cef\client.dll` Windows corta el GTA con 0xC0000602, así que cada salida contaba como crash. Esta ASI cambia ese `ExitProcess` de samp.dll por `TerminateProcess` con el mismo código, cuando el SA-MP y el CEF ya se apagaron. Fuente en `cliente/salida_limpia.c`. Se compila con `i686-w64-mingw32-gcc -O2 -s -shared -nostdlib -e _DllMain@12 -o salida_limpia.asi salida_limpia.c -lkernel32`. Sacarla cuando omp-cef lo arregle.
- `escribir_campo.asi`: sin CEF, las ventanas del server que piden un texto (nombre, SMS, contacto...) son TextDraws, que no reciben teclas. Cuando el server abre una con campo, selecciona los TextDraws con el color `0x6B6A70FF`; mientras esa selección está activa y el chat está cerrado, esta ASI toma el teclado de la ventana del juego (la T no abre el chat) y manda lo escrito con `/vcampo` (`h` al empezar, `t <texto>` cada 150 ms como mucho, `e <texto>` con Enter). Esc y las F pasan igual, y Ctrl+V pega. Usa direcciones de samp.dll 0.3.7-R5-1 (SAMP-API de BlastHack); con otra versión no hace nada y se escribe por el chat. Fuente en `cliente/escribir_campo.c`. Se compila con `i686-w64-mingw32-gcc -O2 -s -shared -nostdlib -e _DllMain@12 -o escribir_campo.asi escribir_campo.c -lkernel32 -luser32`.
- Sin `wndmode.ini`: la ventana sin bordes del Ultimate ASI Loader se repartió un día y se sacó, porque con dos monitores el GTA crasheaba después de elegir la pantalla. `prohibidos.txt` la saca de las carpetas que la recibieron. Con el ENB activo, el `enblocal.ini` del paquete ENB (`paquetes/enb/archivos`) sigue pidiendo ventana sin bordes (`ForceBorderless` y `ForceBorderlessFullscreen`).
## Video de la pantalla de carga del GTA

Mientras el GTA carga, en vez de las imágenes de siempre (las de `loadscs.txd`) y su barra gris, se ve la imagen del server, fija, con una barra de carga dorada propia abajo que avanza con lo que lleva cargado el GTA. Lo hace `carga_video.asi`, que va con las actualizaciones junto con `americarp/carga.bin` (la imagen en JPEG de 1280x720; también acepta un video en cuadros, que se repite mientras dure la carga). Si `carga.bin` falta o está roto, se ven las pantallas de siempre, sin barra. Solo funciona con GTA SA 1.0 US; en otra versión la ASI no toca nada. Cada vez que arranca el GTA deja en `americarp/carga.log` qué pasó (si cargó la imagen, si pudo crear la textura, si dibujó el primer cuadro).

- Fuente en `cliente/carga_video.c` (lee los JPEG con `cliente/stb_image.h`, de dominio público). Se compila con `i686-w64-mingw32-gcc -O2 -s -shared -static-libgcc -o carga_video.asi carga_video.c` desde `cliente/`.
- Para cambiar la imagen: reemplazá `cliente/carga.jpg` (mejor 16:9; si no, se recorta lo que sobra), corré `python cliente/armar_carga.py` (necesita ffmpeg; con `python cliente/armar_carga.py algo.mp4` arma un video), después `generar-manifiesto.bat`, commit y push. Suena la música de carga del GTA.

## Pantalla de conexión al server

Cuando termina la carga y el SA-MP se conecta al server, la misma `carga_video.asi` tapa el juego con la pantalla del server: la playa de fondo, el logo, el estado ("Conectando con el servidor…", "Entrando al juego…" o "El servidor se está reiniciando…") y una línea con un tramo dorado que corre. Cuando el server termina de conectar se funde en medio segundo y queda lo que muestre el server. Si se corta la conexión, vuelve a aparecer.

También pasa al español los mensajes del SA-MP en el chat ("Conectando al servidor...", "Conectado. Entrando al juego...", los rechazos y reintentos, la captura con F8). El de conexión ya no muestra la IP. Lo hace cambiando en memoria cada `push "texto en inglés"` de `samp.dll` por el texto nuestro, sin tocar el archivo.

- Solo con SA-MP 0.3.7-R5 (el estado lo lee de `samp.dll + 0x26EB94`, `+0x3CD`). Con otra versión no hace nada de esto y lo anota en `americarp/carga.log`, igual que cuántos mensajes tradujo y cuántas piezas cargó.
- Las imágenes van en `americarp/conexion.bin`. Para cambiar el fondo, reemplazá `cliente/conexion-fondo.jpg` (mejor 16:9), corré `python cliente/armar_conexion.py` (necesita Pillow; con `python cliente/armar_conexion.py vista.png` deja además cómo se ve en 1920x1080), después `generar-manifiesto.bat`, commit y push. Los textos y el logo están en ese mismo script.
- El fondo se escala para cubrir la pantalla; el logo y el estado van pegados a la izquierda y el consejo a la derecha, así en 4:3 no se cortan.

### Ingreso y selección de personaje

Después de conectar, la ASI dibuja las pantallas del server (desde la 0.7.8 de GABU-RP): el cuadro de ingreso, la selección de personaje y un fondo simple para el registro y la creación de personaje. Las pide el server con un TextDraw invisible que dice `ACN:` y la pantalla (`I`, `F` o `S` con las ranuras, ver `gamemode/cuentas/pantallas.inc` en GABU-RP). La ASI dibuja lo fijo (el vidrio, los íconos, los botones) y el SA-MP dibuja encima los TextDraws del server con lo que cambia (nombres, números, el personaje en 3D). Sin marca del server, a los 4 segundos de conectar se funde como antes.

- En el ingreso esconde el cartel de contraseña del SA-MP (lo deja abierto lejos de la pantalla: es el que manda la clave), dibuja un punto por letra en el campo propio y hace que ENTRAR y "Salir del servidor" funcionen como los botones del cartel. Enter y Esc andan como siempre.
- Las piezas están en el mismo `americarp/conexion.bin`, desde el tipo 10. Las arma `cliente/pantallas.py` (lo llama `armar_conexion.py`, que con `vista.png` deja también `vista-ingreso.png` y `vista-seleccion.png`). Van estiradas a toda la pantalla como los TextDraws, en medidas de 1920x1080: si se mueve algo, hay que moverlo igual en GABU-RP.
- Usa más direcciones de `samp.dll` 0.3.7-R5 (el cartel en `+0x26EB50`, los TextDraws en el pool `+0x3DE` / `+0x1C`, el foco de DXUT en `+0x142780`). Al arrancar revisa los bytes de esas partes del código; si no coinciden, no dibuja estas pantallas, lo anota en `americarp/carga.log` y se ve el cartel de siempre.
- Skins y autos nítidos: el SA-MP arma la imagen de cada vista previa de los TextDraws de modelo en 256x256 y la muestra sin suavizar, así que en un cuadro grande (el personaje de la selección, el auto de la concesionaria) se ve en escalones. Para skins y vehículos la ASI la pasa a 1024x1024 con filtro lineal (con una profundidad propia de 1024, porque la del SA-MP es de 256): se achica en vez de estirarse y los bordes quedan suaves. Los objetos siguen igual. Si los bytes de `samp.dll` no coinciden, lo anota en `carga.log` y quedan como siempre.

## Cambiar la imagen de fondo

El fondo del launcher y de su pantalla de carga es `cliente/conexion-fondo.jpg`, la misma playa de la pantalla de conexión del juego: si la cambiás, cambian las dos (después de compilar el launcher y de correr `python cliente/armar_conexion.py`). Mejor 16:9 y de 1440x810 o más grande; si no es 16:9 se recorta lo que sobra, sin deformarla. La estrella es `fondo/arranque-estrella.png` (con transparencia) y el ícono `fondo/icono.ico` (se arma con `python fondo/armar_icono.py`). La playa y la estrella son imágenes propias del server, hechas con Gemini, y van con la licencia MIT del repo.

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
2. Doble clic en `compilar.bat`. Cuando la firma esté andando, en vez de eso bajá de Actions el artefacto `AmericaRP-firmado` de ese push (la firma cambia la huella, así que el `.exe` del paso 3 y el de la Release tienen que ser el firmado).
3. Doble clic en `publicar-launcher.bat`. Escribe `launcher/version.txt` con la versión y la huella del `.exe`.
4. En GitHub, Releases → Draft a new release, con la etiqueta `v` + la versión (`v1.2.0`), y subí `AmericaRP.exe`.
5. Recién después, commit y push de `launcher/version.txt`. Si lo subís antes que la Release, los launchers no encuentran el `.exe` y siguen con el que tienen.

Si el `.exe` bajado no coincide con la huella, no se instala. Si el jugador lo tiene en una carpeta donde Windows no deja escribir (como Archivos de programa), le ofrece abrir la página para bajarlo a mano.

## Code signing policy

Free code signing provided by SignPath.io, certificate by SignPath Foundation.

- Se firma solo `AmericaRP.exe`, compilado por GitHub Actions desde este repositorio (`.github/workflows/compilar.yml`). Los archivos de otros proyectos que reparte el launcher (CLEO, Ultimate ASI Loader, SilentPatch, etc.) no se firman con este certificado.
- Autores y revisores: [IgnacioCantoni](https://github.com/IgnacioCantoni). Los cambios de otras personas se revisan antes de entrar a `main`.
- Aprobación: [IgnacioCantoni](https://github.com/IgnacioCantoni) aprueba a mano cada versión antes de firmarla.

### Privacidad

El launcher no junta datos personales ni manda información a nadie. Solo se conecta para consultar el estado de los servers de AMERICA RP, para bajar sus archivos y actualizaciones desde GitHub y, si el jugador acepta, los instaladores oficiales de DirectX y Visual C++ desde Microsoft. El nick y los ajustes quedan en la PC del jugador. El formulario de SOPORTE no manda nada: copia el mensaje para que el jugador lo pegue donde quiera.

