// carga_video.asi (AMERICA RP)
// Cambia la pantalla de carga del GTA (las imagenes de loadscs.txd que se van fundiendo)
// por el video del server, y saca la barra de carga gris: el video ya trae su circulo de carga.
// El video va en americarp\carga.bin al lado de esta ASI (lo arma cliente/armar_carga.py).
// Si el archivo falta o esta roto, se ven las pantallas de siempre, sin barra.
// Direcciones de GTA SA 1.0 US (plugin-sdk y gta-reversed).
#include <windows.h>
#include <string.h>

#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_JPEG
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

static void cargar(void)
{
    char ruta[MAX_PATH + 32];
    lstrcpyA(ruta, carpeta);
    lstrcatA(ruta, "americarp\\carga.bin");
    HANDLE f = CreateFileA(ruta, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
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
}

// Pasa el cuadro n del video a la textura. Devuelve 0 si no se pudo.
static int poner(unsigned int n)
{
    int w, h, canales;
    unsigned char *rgba = stbi_load_from_memory(video + inicios[n], (int)tamanios[n], &w, &h, &canales, 4);
    if (!rgba) return 0;
    int ok = 0;
    if ((unsigned)w == vancho && (unsigned)h == valto) {
        if (!cuadro.textura) {
            Raster *r = RasterCrear(w, h, 32, 0x04 | 0x0500); // textura, 8888
            if (r) cuadro.textura = TexturaCrear(r);
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
        }
    }
    stbi_image_free(rgba);
    return ok;
}

static void pantalla(void)
{
    if (!probado) { probado = 1; cargar(); arranque = GetTickCount(); }
    PorCuadro();
    Rect todo = { -5, Alto + 5.0f, Ancho + 5.0f, -5 };
    Rgba blanco = { 255, 255, 255, 255 };
    if (ParaBorrar && !Fundiendo) return;

    if (video) {
        unsigned int n = (unsigned int)((unsigned long long)(GetTickCount() - arranque) * fps / 1000 % cuadros);
        if ((int)n != mostrado && poner(n)) mostrado = (int)n;
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

BOOL WINAPI DllMain(HINSTANCE h, DWORD motivo, LPVOID r)
{
    (void)r;
    if (motivo != DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(h);
    // Solo GTA SA 1.0 US: ahi RenderSplash empieza con "sub esp,18h; call CSprite2d::InitPerFrame".
    if (memcmp((void *)RenderSplash, "\x83\xEC\x18\xE8", 4) || *(unsigned char *)RenderLoadingBar != 0x83) return TRUE;
    GetModuleFileNameA(h, carpeta, MAX_PATH);
    char *barra = strrchr(carpeta, '\\');
    if (barra) barra[1] = 0; else carpeta[0] = 0;
    unsigned char salto[5] = { 0xE9 };
    *(DWORD *)(salto + 1) = (DWORD)pantalla - (RenderSplash + 5);
    escribir(RenderSplash, salto, 5);
    unsigned char volver = 0xC3;
    escribir(RenderLoadingBar, &volver, 1);
    return TRUE;
}
