// carga_video.asi (AMERICA RP)
// 1) Cambia la pantalla de carga del GTA (las imagenes de loadscs.txd que se van fundiendo)
//    por el video del server, y saca la barra de carga gris: el video ya trae su circulo de carga.
//    El video va en americarp\carga.bin al lado de esta ASI (lo arma cliente/armar_carga.py),
//    en cuadros JPEG del tamanio original (1280x720).
//    Si el archivo falta o esta roto, se ven las pantallas de siempre, sin barra.
// 2) Mientras el SA-MP se conecta al server tapa la pantalla con la del server (americarp\conexion.bin,
//    lo arma cliente/armar_conexion.py) y pasa al espaniol los mensajes del SA-MP en el chat.
//    La pantalla se va sola cuando el server termina de conectar. Solo con SA-MP 0.3.7-R5.
// Direcciones de GTA SA 1.0 US (plugin-sdk y gta-reversed).
#include <windows.h>
#include <string.h>

#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_JPEG
#define STBI_ONLY_PNG
#define STBI_NO_STDIO
#define STBI_NO_HDR
#define STBI_NO_LINEAR
#include "stb_image.h"

typedef struct { float x1, y1, x2, y2; } Rect;   // CRect: izquierda, abajo, derecha, arriba (y1 es la de abajo)
typedef struct { unsigned char r, g, b, a; } Rgba;
typedef struct { void *textura; } Sprite;          // CSprite2d: solo el RwTexture*
typedef struct { void *padre; unsigned char *pixeles; void *paleta; int ancho, alto, prof, paso; } Raster;
typedef struct { Raster *raster; } Textura;

#define RenderSplash     0x58FF60
#define RenderLoadingBar 0x590370
static void (__attribute__((thiscall)) *const SpriteDibujar)(Sprite *, const Rect *, const Rgba *) = (void *)0x728350;
static void (*const RectDibujar)(const Rect *, const Rgba *) = (void *)0x727B60;
static void (*const PorCuadro)(void) = (void *)0x727350;
static Raster *(*const RasterCrear)(int, int, int, int) = (void *)0x7FB230;
static unsigned char *(*const RasterTrabar)(Raster *, unsigned char, int) = (void *)0x7FB2D0;
static Raster *(*const RasterDestrabar)(Raster *) = (void *)0x7FAEC0;
static Textura *(*const TexturaCrear)(Raster *) = (void *)0x7F37C0;

#define Ancho        (*(int *)0xC17044)
#define Alto         (*(int *)0xC17048)
#define Actual       (*(int *)0x8D093C)
#define Fundiendo    (*(unsigned char *)0xBAB31C)
#define DesdeNegro   (*(unsigned char *)0xBAB31E)
#define HaciaNegro   (*(unsigned char *)0xBAB31F)
#define Alfa         (*(unsigned char *)0xBAB320)
#define ParaBorrar   (*(unsigned char *)0xBAB33D)
#define Pantallas    ((Sprite *)0xBAB35C)

// carga.bin: "ARV1", cuadros, ancho, alto, cuadros por segundo, tamanio de cada cuadro y los JPEG seguidos.
static unsigned char *video;
static unsigned int cuadros, vancho, valto, fps, *tamanios, *inicios;
static int probado, mostrado = -1;
static DWORD arranque;
static Sprite cuadro;
static char carpeta[MAX_PATH];
static int sampEstado; // pantalla de conexion: 0 sin probar, 1 listo, -1 no es SA-MP 0.3.7-R5
static void prepararSamp(void);

// Deja en americarp\carga.log qué pasó en la última carga, para revisar si el video no aparece.
static void anotar(const char *texto)
{
    char ruta[MAX_PATH + 32];
    static int abierto;
    lstrcpyA(ruta, carpeta);
    lstrcatA(ruta, "americarp\\carga.log");
    HANDLE f = CreateFileA(ruta, FILE_APPEND_DATA, FILE_SHARE_READ, NULL, abierto ? OPEN_ALWAYS : CREATE_ALWAYS, 0, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    abierto = 1;
    DWORD n;
    WriteFile(f, texto, lstrlenA(texto), &n, NULL);
    WriteFile(f, "\r\n", 2, &n, NULL);
    CloseHandle(f);
}

static void cargar(void)
{
    char ruta[MAX_PATH + 32];
    lstrcpyA(ruta, carpeta);
    lstrcatA(ruta, "americarp\\carga.bin");
    HANDLE f = CreateFileA(ruta, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (f == INVALID_HANDLE_VALUE) { anotar("no esta americarp\\carga.bin"); return; }
    DWORD largo = GetFileSize(f, NULL), leido = 0;
    unsigned char *d = (largo > 20 && largo < 200u << 20) ? malloc(largo) : NULL;
    if (d && ReadFile(f, d, largo, &leido, NULL) && leido == largo && !memcmp(d, "ARV1", 4)) {
        unsigned int *c = (unsigned int *)(d + 4);
        unsigned long long pos = 20 + 4ull * c[0];
        if (c[0] > 0 && c[0] < 10000 && c[1] > 0 && c[1] <= 2048 && c[2] > 0 && c[2] <= 2048 && c[3] > 0 && c[3] <= 60 && pos <= largo) {
            tamanios = c + 4;
            inicios = malloc(4 * c[0]);
            for (unsigned int i = 0; inicios && i < c[0]; i++) { inicios[i] = (unsigned int)pos; pos += tamanios[i]; }
            if (inicios && pos == largo) { video = d; cuadros = c[0]; vancho = c[1]; valto = c[2]; fps = c[3]; d = NULL; }
        }
    }
    CloseHandle(f);
    free(d);
    char t[128];
    wsprintfA(t, video ? "video: %u cuadros de %ux%u a %u por segundo" : "carga.bin roto", cuadros, vancho, valto, fps);
    anotar(t);
}

// Pasa el cuadro n del video a la textura. Devuelve 0 si no se pudo.
static int poner(unsigned int n)
{
    int w, h, canales;
    unsigned char *rgba = stbi_load_from_memory(video + inicios[n], (int)tamanios[n], &w, &h, &canales, 4);
    if (!rgba) { anotar("un cuadro no se pudo leer"); return 0; }
    int ok = 0;
    if ((unsigned)w == vancho && (unsigned)h == valto) {
        if (!cuadro.textura) {
            Raster *r = RasterCrear(w, h, 32, 0x04 | 0x0500); // textura, 8888
            if (r) cuadro.textura = TexturaCrear(r);
            anotar(cuadro.textura ? "textura creada" : "no se pudo crear la textura");
        }
        Raster *r = cuadro.textura ? ((Textura *)cuadro.textura)->raster : NULL;
        unsigned char *p = r ? RasterTrabar(r, 0, 1) : NULL;
        if (p) {
            for (int y = 0; y < h; y++) {
                unsigned char *o = rgba + y * w * 4, *dst = p + y * r->paso;
                for (int x = 0; x < w; x++, o += 4, dst += 4) { dst[0] = o[2]; dst[1] = o[1]; dst[2] = o[0]; dst[3] = 255; }
            }
            RasterDestrabar(r);
            ok = 1;
        } else if (r) anotar("no se pudo escribir la textura");
    }
    stbi_image_free(rgba);
    return ok;
}

static void pantalla(void)
{
    if (!probado) { probado = 1; cargar(); arranque = GetTickCount(); }
    if (sampEstado == 0) prepararSamp();
    PorCuadro();
    Rect todo = { -5, Alto + 5.0f, Ancho + 5.0f, -5 };
    Rgba blanco = { 255, 255, 255, 255 };
    if (ParaBorrar && !Fundiendo) return;

    if (video) {
        unsigned int n = (unsigned int)((unsigned long long)(GetTickCount() - arranque) * fps / 1000 % cuadros);
        if ((int)n != mostrado && poner(n)) {
            if (mostrado < 0) anotar("primer cuadro dibujado");
            mostrado = (int)n;
        }
    }
    if (video && cuadro.textura && mostrado >= 0) {
        // El video es 16:9: en pantallas de otra forma se recorta lo que sobra, sin deformarlo.
        float w = (float)Ancho, h = (float)Alto;
        Rect r = todo;
        if (w / h < 16.0f / 9) { float a = h * 16 / 9; r.x1 = (w - a) / 2; r.x2 = r.x1 + a; r.y1 = h; r.y2 = 0; }
        else { float a = w * 9 / 16; r.y2 = (h - a) / 2; r.y1 = r.y2 + a; r.x1 = 0; r.x2 = w; }
        SpriteDibujar(&cuadro, &r, &blanco);
    } else {
        // Sin video: las pantallas de siempre, con el mismo fundido que el original.
        SpriteDibujar(&Pantallas[Actual], &todo, &blanco);
        if (Fundiendo && !DesdeNegro && !HaciaNegro && Actual > 0) {
            Rgba c = { 255, 255, 255, (unsigned char)(255 - Alfa) };
            SpriteDibujar(&Pantallas[Actual - 1], &todo, &c);
        }
    }
    if (Fundiendo && (DesdeNegro || HaciaNegro)) {
        Rgba negro = { 0, 0, 0, (unsigned char)(DesdeNegro ? 255 - Alfa : Alfa) };
        RectDibujar(&todo, &negro);
    }
}

static void escribir(DWORD dir, const void *bytes, SIZE_T n)
{
    DWORD viejo;
    if (VirtualProtect((void *)dir, n, PAGE_EXECUTE_READWRITE, &viejo)) {
        memcpy((void *)dir, bytes, n);
        VirtualProtect((void *)dir, n, viejo, &viejo);
        FlushInstructionCache(GetCurrentProcess(), (void *)dir, n);
    }
}

// ---------- Pantalla de conexion al server (SA-MP 0.3.7-R5) ----------
// Direcciones de samp.dll 0.3.7-R5 (sampapi): CNetGame* en +0x26EB94 y su estado en +0x3CD.
// Estados: 1 esperando, 2 conectando, 5 conectado, 6 entrando al juego, 11 server reiniciando.
#define SAMP_NETGAME   0x26EB94
#define SAMP_ESTADO    0x3CD
#define SAMP_CONECTADO 5
// Ultimo "call" de Render2dStuff antes del jmp a CFont::DrawFonts. No se usa ese jmp porque el
// limit adjuster de fastman92 lo pisa al arrancar y el juego terminaba crasheando.
#define Render2dLlamada 0x53E522
#define Render2dOriginal 0x447790
static int (*const TexturaBorrar)(void *) = (void *)0x7F3820; // RwTextureDestroy

typedef struct { const char *ingles, *espaniol; } Traduccion;
// Acentos en CP1252, que es lo que dibuja el chat del SA-MP. Las cadenas van cortadas donde
// sigue una letra que C leeria como parte del \x.
static const Traduccion textos[] = {
    { "{FFFFFF}SA-MP {B9C9BF}0.3.7-R5 {FFFFFF}Started", "{FFFFFF}Bienvenido a {F2BE50}AMERICA RP" },
    { "Connecting to %s:%d...", "Conectando al servidor..." },
    { "Server has accepted the connection.", "El servidor acept\xF3 la conexi\xF3n." },
    { "Connected. Joining the game...", "Conectado. Entrando al juego..." },
    { "Connected to {B9C9BF}%.64s", "Conectado a {B9C9BF}%.64s" },
    { "The server is full. Retrying...", "El servidor est\xE1 lleno. Reintentando..." },
    { "Server closed the connection.", "El servidor cerr\xF3 la conexi\xF3n." },
    { "Wrong server password.", "La contrase\xF1" "a del servidor no es correcta." },
    { "You are banned from this server.", "Est\xE1s bloqueado en este servidor." },
    { "The server didn't respond. Retrying..", "El servidor no responde. Reintentando..." },
    { "Lost connection to the server. Reconnecting..", "Se perdi\xF3 la conexi\xF3n con el servidor. Reconectando..." },
    { "CONNECTION REJECTED: Unable to allocate a player slot.", "Conexi\xF3n rechazada: no hay lugar en el servidor." },
    { "CONNECTION REJECTED: Bad mod version.", "Conexi\xF3n rechazada: versi\xF3n del juego incorrecta." },
    { "CONNECTION REJECTED: Unacceptable NickName", "Conexi\xF3n rechazada: el nombre no es v\xE1lido." },
    { "CONNECTION REJECTED: Incorrect Version.", "Conexi\xF3n rechazada: versi\xF3n del SA-MP incorrecta." },
    { "Please choose another nick between and 3-20 characters", "Eleg\xED otro nombre, de 3 a 20 letras." },
    { "Screenshot Taken - sa-mp-%03i.png", "Captura guardada: sa-mp-%03i.png" },
    { "Unable to save screenshot.", "No se pudo guardar la captura." },
};

// Pieza de conexion.bin (ver cliente/armar_conexion.py).
typedef struct { int tipo, ancla, x, y, w, h, bx, by, bw, bh; Sprite sprite; } Pieza;
static Pieza piezas[16];
static int npiezas, conexionProbada;
static DWORD samp, conectadoDesde;

// Busca el texto exacto (con su 0 al final) en samp.dll y cambia cada "push texto" del codigo por el nuestro.
static int traducir(const char *ingles, const char *espaniol, DWORD ini, DWORD fin, DWORD codigo, DWORD codigoFin)
{
    DWORD n = (DWORD)lstrlenA(ingles) + 1, dir = 0, cambios = 0;
    for (DWORD a = ini + 1; a + n <= fin; a++)
        if (((char *)a)[-1] == 0 && !memcmp((void *)a, ingles, n)) { dir = a; break; }
    if (!dir) return 0;
    for (DWORD a = codigo; a + 5 <= codigoFin; a++)
        if (*(unsigned char *)a == 0x68 && *(DWORD *)(a + 1) == dir) { escribir(a + 1, &espaniol, 4); cambios++; }
    return (int)cambios;
}

static void prepararSamp(void)
{
    samp = (DWORD)GetModuleHandleA("samp.dll");
    if (!samp) return; // todavia no cargo: se prueba de nuevo en el proximo cuadro
    sampEstado = -1;
    // R5, despues de "Connected to %.64s": "mov edx, [CNetGame*]" y "mov dword ptr [edx+3CDh], 5".
    if (memcmp((void *)(samp + 0x10A92), "\x8B\x15", 2) || *(DWORD *)(samp + 0x10A94) != samp + SAMP_NETGAME
        || memcmp((void *)(samp + 0x10A98), "\xC7\x82\xCD\x03\x00\x00\x05\x00\x00\x00", 10)) { anotar("el SA-MP no es 0.3.7-R5: sin pantalla de conexion ni traducciones"); return; }
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(samp + ((IMAGE_DOS_HEADER *)samp)->e_lfanew);
    IMAGE_SECTION_HEADER *sec = IMAGE_FIRST_SECTION(nt);
    // Se recorre de la primera seccion al final de la ultima: todo eso esta mapeado y se puede leer.
    DWORD total = 0, ini = samp + sec[0].VirtualAddress;
    DWORD fin = samp + sec[nt->FileHeader.NumberOfSections - 1].VirtualAddress + sec[nt->FileHeader.NumberOfSections - 1].Misc.VirtualSize;
    // El codigo es la primera seccion (.text) en la R5.
    DWORD codigo = ini, codigoFin = ini + sec[0].Misc.VirtualSize;
    if (!(sec[0].Characteristics & IMAGE_SCN_MEM_EXECUTE)) { anotar("samp.dll no empieza con el codigo: sin traducciones"); codigoFin = codigo; }
    for (unsigned i = 0; i < sizeof textos / sizeof textos[0]; i++) total += (DWORD)traducir(textos[i].ingles, textos[i].espaniol, ini, fin, codigo, codigoFin);
    char t[64];
    wsprintfA(t, "SA-MP 0.3.7-R5: %u mensajes traducidos", total);
    anotar(t);
    sampEstado = 1;
}

static void *textura(const unsigned char *rgba, int w, int h)
{
    Raster *r = RasterCrear(w, h, 32, 0x04 | 0x0500); // textura, 8888
    Textura *t = r ? TexturaCrear(r) : NULL;
    unsigned char *p = t ? RasterTrabar(r, 0, 1) : NULL;
    if (!p) return t;
    for (int y = 0; y < h; y++) {
        const unsigned char *o = rgba + y * w * 4;
        unsigned char *dst = p + y * r->paso;
        for (int x = 0; x < w; x++, o += 4, dst += 4) { dst[0] = o[2]; dst[1] = o[1]; dst[2] = o[0]; dst[3] = o[3]; }
    }
    RasterDestrabar(r);
    return t;
}

static void cargarConexion(void)
{
    char ruta[MAX_PATH + 32];
    lstrcpyA(ruta, carpeta);
    lstrcatA(ruta, "americarp\\conexion.bin");
    HANDLE f = CreateFileA(ruta, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (f == INVALID_HANDLE_VALUE) { anotar("no esta americarp\\conexion.bin: sin pantalla de conexion"); return; }
    DWORD largo = GetFileSize(f, NULL), leido = 0;
    unsigned char *d = (largo > 8 && largo < 64u << 20) ? malloc(largo) : NULL;
    if (d && ReadFile(f, d, largo, &leido, NULL) && leido == largo && !memcmp(d, "ACN1", 4)) {
        DWORD n = *(DWORD *)(d + 4), pos = 8;
        for (DWORD i = 0; i < n && npiezas < 16 && pos + 44 <= largo; i++) {
            int *c = (int *)(d + pos);
            pos += 44;
            if (c[10] <= 0 || (DWORD)c[10] > largo - pos) break;
            int w, h, canales;
            unsigned char *rgba = stbi_load_from_memory(d + pos, c[10], &w, &h, &canales, 4);
            pos += (DWORD)c[10];
            if (!rgba) continue;
            Pieza *p = &piezas[npiezas];
            memcpy(p, c, 10 * sizeof(int));
            p->sprite.textura = textura(rgba, w, h);
            stbi_image_free(rgba);
            if (p->sprite.textura) npiezas++;
        }
    }
    CloseHandle(f);
    free(d);
    char t[64];
    wsprintfA(t, "pantalla de conexion: %d piezas", npiezas);
    anotar(t);
}

// Libera las texturas cuando ya entro al server. Si se corta la conexion se vuelven a cargar.
static void borrarConexion(void)
{
    for (int i = 0; i < npiezas; i++) TexturaBorrar(piezas[i].sprite.textura);
    npiezas = 0;
    conexionProbada = 0;
}

static void conexion(void)
{
    if (sampEstado == 0) prepararSamp();
    if (sampEstado != 1) return;
    DWORD ng = *(DWORD *)(samp + SAMP_NETGAME), ahora = GetTickCount();
    int estado = ng ? *(int *)(ng + SAMP_ESTADO) : 0;
    // Al conectar se funde en medio segundo y despues se libera.
    if (estado != SAMP_CONECTADO) conectadoDesde = 0;
    else if (!conectadoDesde) conectadoDesde = ahora ? ahora : 1;
    int alfa = conectadoDesde ? 255 - (int)(ahora - conectadoDesde) * 255 / 500 : 255;
    if (alfa <= 0) { if (npiezas) borrarConexion(); return; }
    if (!conexionProbada) { conexionProbada = 1; cargarConexion(); }
    if (!npiezas) return;

    int tipo = estado == 6 || estado == SAMP_CONECTADO ? 3 : estado == 11 ? 4 : 2;
    float w = (float)Ancho, h = (float)Alto, s = h / 1080;
    Rgba color = { 255, 255, 255, (unsigned char)alfa };
    for (int i = 0; i < npiezas; i++) {
        Pieza *p = &piezas[i];
        if (p->tipo != 0 && p->tipo != 1 && p->tipo != tipo) continue;
        Rect r;
        if (p->ancla == 0) { // cubre la pantalla sin deformarse, como el video
            float e = w / p->w > h / p->h ? w / p->w : h / p->h;
            r.x1 = (w - p->w * e) / 2; r.x2 = r.x1 + p->w * e; r.y2 = (h - p->h * e) / 2; r.y1 = r.y2 + p->h * e;
        } else {
            float x = p->ancla == 2 ? w - (1920 - p->x) * s : p->x * s;
            r.x1 = x; r.x2 = x + p->w * s; r.y2 = p->y * s; r.y1 = (p->y + p->h) * s;
        }
        SpriteDibujar(&p->sprite, &r, &color);
        if (p->bw > 0) { // un tramo dorado que corre por la linea, ida y vuelta cada 1,6 segundos
            float tramo = p->bw / 4.0f, ida = (float)(ahora % 1600) / 800;
            float x = p->bx + (ida <= 1 ? ida : 2 - ida) * (p->bw - tramo);
            float x0 = p->ancla == 2 ? w - (1920 - x) * s : x * s;
            Rect b = { x0, (p->by + p->bh) * s, x0 + tramo * s, p->by * s };
            Rgba dorado = { 242, 190, 80, (unsigned char)alfa };
            RectDibujar(&b, &dorado);
        }
    }
}

// Va en lugar del ultimo call de Render2dStuff: hace lo que hacia y encima dibuja la pantalla de
// conexion, sobre el HUD y el radar. El chat del SA-MP se dibuja despues, asi que queda arriba.
static void dibujar2d(void)
{
    static int primera = 1;
    ((void (*)(void))Render2dOriginal)();
    if (primera) { primera = 0; anotar("dibujando en el juego"); }
    conexion();
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD motivo, LPVOID r)
{
    (void)r;
    if (motivo != DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(h);
    // Solo GTA SA 1.0 US: ahi RenderSplash empieza con "sub esp,18h; call CSprite2d::InitPerFrame".
    GetModuleFileNameA(h, carpeta, MAX_PATH);
    char *barra = strrchr(carpeta, '\\');
    if (barra) barra[1] = 0; else carpeta[0] = 0;
    if (memcmp((void *)RenderSplash, "\x83\xEC\x18\xE8", 4) || *(unsigned char *)RenderLoadingBar != 0x83) { anotar("no es GTA SA 1.0 US o ya lo cambio otro mod: no se toca nada"); return TRUE; }
    unsigned char salto[5] = { 0xE9 };
    *(DWORD *)(salto + 1) = (DWORD)pantalla - (RenderSplash + 5);
    escribir(RenderSplash, salto, 5);
    unsigned char volver = 0xC3;
    escribir(RenderLoadingBar, &volver, 1);
    unsigned char llamada[5] = { 0xE8 };
    *(DWORD *)(llamada + 1) = Render2dOriginal - (Render2dLlamada + 5);
    if (!memcmp((void *)Render2dLlamada, llamada, 5)) {
        *(DWORD *)(llamada + 1) = (DWORD)dibujar2d - (Render2dLlamada + 5);
        escribir(Render2dLlamada, llamada, 5);
    } else anotar("otro mod ya cambio Render2dStuff: sin pantalla de conexion");
    anotar("plugin cargado");
    return TRUE;
}
