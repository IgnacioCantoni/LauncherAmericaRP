// salida_limpia.asi (AMERICA RP)
// SA-MP 0.3.7 sale con ExitProcess. Durante esa salida Windows descarga cef\client.dll
// (omp-cef 1.3.0), que toca la ventana del juego cuando el sistema de entrada de texto de
// Windows ya se apago, y Windows corta el proceso con 0xC0000602 (crash al cerrar).
// Esta ASI cambia el ExitProcess que importa samp.dll por TerminateProcess: SA-MP ya hizo
// su limpieza y CEF ya se apago ("Exit SA-MP ... Good bye"), asi que solo se salta la
// descarga de DLLs que es la que crashea.
// shortcut: parche alrededor de un bug de omp-cef; sacar esta ASI cuando omp-cef lo arregle.
#include <windows.h>

static void WINAPI salida_rapida(UINT codigo)
{
    TerminateProcess(GetCurrentProcess(), codigo);
}

static BOOL parchar(HMODULE m)
{
    BYTE *b = (BYTE *)m;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)(b + ((IMAGE_DOS_HEADER *)b)->e_lfanew);
    IMAGE_DATA_DIRECTORY dir = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    if (!dir.VirtualAddress) return FALSE;
    FARPROC real = GetProcAddress(GetModuleHandleA("kernel32.dll"), "ExitProcess");
    BOOL hecho = FALSE;
    for (IMAGE_IMPORT_DESCRIPTOR *d = (IMAGE_IMPORT_DESCRIPTOR *)(b + dir.VirtualAddress); d->Name; d++) {
        if (lstrcmpiA((char *)(b + d->Name), "kernel32.dll")) continue;
        IMAGE_THUNK_DATA *iat = (IMAGE_THUNK_DATA *)(b + d->FirstThunk);
        IMAGE_THUNK_DATA *nom = d->OriginalFirstThunk ? (IMAGE_THUNK_DATA *)(b + d->OriginalFirstThunk) : NULL;
        for (; iat->u1.Function; iat++, nom = nom ? nom + 1 : NULL) {
            BOOL es = (FARPROC)iat->u1.Function == real;
            if (!es && nom && !IMAGE_SNAP_BY_ORDINAL(nom->u1.Ordinal))
                es = !lstrcmpA((char *)((IMAGE_IMPORT_BY_NAME *)(b + nom->u1.AddressOfData))->Name, "ExitProcess");
            if (!es) continue;
            DWORD viejo;
            if (VirtualProtect(&iat->u1.Function, sizeof(DWORD), PAGE_READWRITE, &viejo)) {
                iat->u1.Function = (DWORD)(ULONG_PTR)salida_rapida;
                VirtualProtect(&iat->u1.Function, sizeof(DWORD), viejo, &viejo);
                hecho = TRUE;
            }
        }
    }
    return hecho;
}

static DWORD WINAPI esperar_samp(LPVOID p)
{
    (void)p;
    for (int i = 0; i < 1200; i++) { // hasta 2 minutos
        HMODULE s = GetModuleHandleA("samp.dll");
        if (s) { parchar(s); return 0; }
        Sleep(100);
    }
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD motivo, LPVOID r)
{
    (void)r;
    if (motivo == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        HMODULE s = GetModuleHandleA("samp.dll");
        if (s) parchar(s);
        else CloseHandle(CreateThread(NULL, 0, esperar_samp, NULL, 0, NULL));
    }
    return TRUE;
}
