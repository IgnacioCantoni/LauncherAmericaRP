// escribir_campo.asi (AMERICA RP)
// Sin CEF, las ventanas del server que piden un texto (un nombre, un SMS...) son TextDraws, y los TextDraws
// no reciben teclas. Esta ASI deja escribir directo en el campo: cuando el server abre una ventana con campo,
// selecciona los TextDraws con un color propio (0x6B6A70FF, VENT_COLOR_HOVER_CAMPO en interfaz/ventanas.inc
// del server). Mientras esa selección está activa y el chat del SA-MP está cerrado, esta ASI toma el teclado
// de la ventana del juego (las teclas no llegan al SA-MP, así la T no abre el chat) y le manda al server lo
// escrito con el comando /vcampo:
//   /vcampo h            al tomar el teclado (el server cambia la ayuda del campo)
//   /vcampo t <texto>    lo escrito hasta ahora, como mucho cada 150 ms
//   /vcampo e <texto>    al apretar Enter (equivale al botón verde)
// Esc y las F pasan igual (Esc cierra la ventana). Ctrl+V pega. Mientras escribe, la cámara y los controles
// quedan quietos.
// Solo funciona con samp.dll 0.3.7-R5-1 (direcciones de SAMP-API, BlastHack, MIT); con otra versión no hace
// nada y en el server se sigue escribiendo por el chat.
// Se compila con:
//   i686-w64-mingw32-gcc -O2 -s -shared -nostdlib -e _DllMain@12 -o escribir_campo.asi escribir_campo.c -lkernel32 -luser32
#include <windows.h>

#define SAMP_R5_ENTRADA     0xCBC90     // AddressOfEntryPoint de samp.dll 0.3.7-R5-1
#define SAMP_SELECCION      0x26EB68    // CTextDrawSelection* (m_bIsActive, m_hoveredColor)
#define SAMP_ENTRADA_CHAT   0x26EB84    // CInput*
#define SAMP_CHAT_ABIERTO   5344        // CInput::m_bEnabled (estructura empaquetada)
#define SAMP_CHAT_ENVIAR    0x69900     // CInput::Send(const char*)
#define SAMP_JUEGO          0x26EBAC    // CGame*
#define SAMP_MODO_CURSOR    0x61        // CGame::m_nCursorMode
#define SAMP_PONER_CURSOR   0xA06F0     // CGame::SetCursorMode(int, BOOL)
#define CURSOR_TRABA_TODO   2           // CURSOR_LOCKCAMANDCONTROL

#define LARGO_MAXIMO        110         // "/vcampo e " + esto entra en los 128 del chat del SA-MP
#define ESPERA_ENVIO        150
#define RELOJ_ENVIO         0x4A43      // id del SetTimer

typedef void (__attribute__((thiscall)) *Enviar_t)(void *entrada, const char *texto);
typedef void (__attribute__((thiscall)) *PonerCursor_t)(void *juego, int modo, BOOL ocultar);

static DWORD base;
static HWND ventana;
static WNDPROC anterior;
static BOOL tomado;
static char escrito[LARGO_MAXIMO + 1];
static int largo;
static DWORD ultimo_envio;
static BOOL pendiente;
static int modo_guardado;

static BOOL es_r5(DWORD b)
{
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(b + ((IMAGE_DOS_HEADER *)b)->e_lfanew);
    return nt->OptionalHeader.AddressOfEntryPoint == SAMP_R5_ENTRADA;
}

static BYTE *puntero(DWORD direccion)
{
    return *(BYTE **)(base + direccion);
}

// El color de selección puede quedar guardado en cualquier orden de bytes: se aceptan los cuatro.
static BOOL es_color_campo(DWORD c)
{
    return c == 0x6B6A70FF || c == 0xFF6B6A70 || c == 0xFF706A6B || c == 0x706A6BFF;
}

static BOOL campo_abierto(void)
{
    BYTE *sel = puntero(SAMP_SELECCION), *chat = puntero(SAMP_ENTRADA_CHAT);
    if (!sel || !*(BOOL *)sel || !es_color_campo(*(DWORD *)(sel + 4)))
        return FALSE;
    return !(chat && *(BOOL *)(chat + SAMP_CHAT_ABIERTO));
}

static void mandar(const char *texto)
{
    BYTE *chat = puntero(SAMP_ENTRADA_CHAT);
    if (chat)
        ((Enviar_t)(base + SAMP_CHAT_ENVIAR))(chat, texto);
}

static void enviar(char tipo)
{
    char linea[16 + LARGO_MAXIMO];
    wsprintfA(linea, largo ? "/vcampo %c %s" : "/vcampo %c", tipo, escrito);
    mandar(linea);
    ultimo_envio = GetTickCount();
    pendiente = FALSE;
    KillTimer(ventana, RELOJ_ENVIO);
}

// Después de cada cambio: enseguida, o al vencer la espera si se mandó hace muy poco.
static void cambio(void)
{
    if (GetTickCount() - ultimo_envio >= ESPERA_ENVIO)
        enviar('t');
    else if (!pendiente)
    {
        pendiente = TRUE;
        SetTimer(ventana, RELOJ_ENVIO, ESPERA_ENVIO, NULL);
    }
}

static void poner_cursor(int modo)
{
    BYTE *juego = puntero(SAMP_JUEGO);
    if (juego)
        ((PonerCursor_t)(base + SAMP_PONER_CURSOR))(juego, modo, FALSE);
}

static void tomar(void)
{
    BYTE *juego = puntero(SAMP_JUEGO);
    tomado = TRUE;
    largo = 0;
    escrito[0] = '\0';
    pendiente = FALSE;
    modo_guardado = juego ? *(int *)(juego + SAMP_MODO_CURSOR) : 0;
    if (modo_guardado != CURSOR_TRABA_TODO)
        poner_cursor(CURSOR_TRABA_TODO);
    mandar("/vcampo h");
}

static void soltar(void)
{
    BYTE *juego = puntero(SAMP_JUEGO);
    tomado = FALSE;
    pendiente = FALSE;
    KillTimer(ventana, RELOJ_ENVIO);
    // Si la ventana se cerró pero queda otro panel seleccionado, vuelve el modo que tenía; si se cerró todo,
    // el SA-MP ya lo sacó.
    if (juego && *(int *)(juego + SAMP_MODO_CURSOR) == CURSOR_TRABA_TODO && modo_guardado != CURSOR_TRABA_TODO)
        poner_cursor(modo_guardado);
}

static void agregar(unsigned char c)
{
    if (largo < LARGO_MAXIMO)
    {
        escrito[largo++] = (char)c;
        escrito[largo] = '\0';
    }
}

static void pegar(void)
{
    if (!OpenClipboard(ventana))
        return;
    HANDLE h = GetClipboardData(CF_TEXT);
    const unsigned char *t = h ? (const unsigned char *)GlobalLock(h) : NULL;
    if (t)
    {
        for (; *t; t++)
        {
            if (*t >= 32)
                agregar(*t);
            else if (*t == '\n' || *t == '\t')
                agregar(' ');
        }
        GlobalUnlock(h);
    }
    CloseClipboard();
}

static LRESULT CALLBACK procesar(HWND h, UINT m, WPARAM w, LPARAM l)
{
    BOOL quiere = campo_abierto();
    if (quiere && !tomado)
        tomar();
    else if (!quiere && tomado)
        soltar();
    if (tomado)
    {
        switch (m)
        {
        case WM_CHAR:
            if (w == '\r')
                enviar('e');
            else
            {
                if (w == '\b')
                {
                    if (largo > 0)
                        escrito[--largo] = '\0';
                }
                else if (w == 0x16)
                    pegar();
                else if (w >= 32)
                    agregar((unsigned char)w);
                else
                    return 0;
                cambio();
            }
            return 0;
        case WM_KEYDOWN:
        case WM_KEYUP:
            // Esc cierra la ventana y las F siguen andando (captura, chat...); el resto no le llega al SA-MP.
            if (w == VK_ESCAPE || (w >= VK_F1 && w <= VK_F12))
                break;
            return 0;
        case WM_TIMER:
            if (w == RELOJ_ENVIO)
            {
                if (pendiente)
                    enviar('t');
                return 0;
            }
            break;
        }
    }
    return CallWindowProcA(anterior, h, m, w, l);
}

static BOOL CALLBACK buscar_ventana(HWND h, LPARAM l)
{
    DWORD pid;
    (void)l;
    GetWindowThreadProcessId(h, &pid);
    if (pid == GetCurrentProcessId() && IsWindowVisible(h) && !GetWindow(h, GW_OWNER))
    {
        ventana = h;
        return FALSE;
    }
    return TRUE;
}

static DWORD WINAPI esperar_samp(LPVOID p)
{
    (void)p;
    // Hasta que el SA-MP arma su chat (ya puso su propio manejo de la ventana del juego), y un poco más.
    for (int i = 0; i < 6000; i++) // hasta 10 minutos
    {
        if (!base)
        {
            DWORD s = (DWORD)(ULONG_PTR)GetModuleHandleA("samp.dll");
            if (s)
            {
                if (!es_r5(s))
                    return 0;
                base = s;
            }
        }
        if (base && puntero(SAMP_ENTRADA_CHAT))
        {
            Sleep(3000);
            EnumWindows(buscar_ventana, 0);
            if (!ventana)
                return 0;
            anterior = (WNDPROC)SetWindowLongA(ventana, GWL_WNDPROC, (LONG)(ULONG_PTR)procesar);
            return 0;
        }
        Sleep(100);
    }
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD motivo, LPVOID r)
{
    (void)r;
    if (motivo == DLL_PROCESS_ATTACH)
    {
        DisableThreadLibraryCalls(h);
        CloseHandle(CreateThread(NULL, 0, esperar_samp, NULL, 0, NULL));
    }
    return TRUE;
}
