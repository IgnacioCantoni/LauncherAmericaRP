# Arma actualizaciones/archivos/cleo/hud_propio.cs (bytecode de CLEO). Uso: python cleo/armar_hud.py actualizaciones/archivos/cleo/hud_propio.cs
# Sin CEF el server dibuja su propio HUD arriba a la derecha (dinero, arma, vida y chaleco): este script
# esconde esos cuatro del GTA. El radar, las estrellas, la barra de aire y la hora quedan como siempre.
# Con CEF (está cef.asi en la carpeta del GTA; sin CEF el launcher lo renombra a cef.asi.off) no hace nada.
# Direcciones del GTA SA 1.0 US, las mismas que usa el MTA (Client/game_sa/CHudSA.h y CHudSA.cpp).
import struct,sys
def op(n): return struct.pack('<H',n)
def i8(v): return b'\x04'+struct.pack('<b',v)
def i16(v): return b'\x05'+struct.pack('<h',v)
def i32(v): return b'\x01'+struct.pack('<i',v if v<2**31 else v-2**32)
def s(t): return b'\x0e'+bytes([len(t)])+t.encode()
class L(str): pass                                    # etiqueta
def jmp(o,lbl): return (op(o)+b'\x01', lbl)          # se completa con -posición de la etiqueta (script CLEO)

RET=0xC3
code=[
 op(0x0000),
 op(0x00D6)+i8(0), op(0x0AAB)+s('cef.asi'), jmp(0x004D,'ocultar'),
 op(0x0A93),                                          # con CEF: termina
 L('ocultar'),                                        # se repite por si algo lo vuelve a poner
 op(0x0A8C)+i32(0x5893B0)+i8(1)+i32(RET)+i8(1),       # CHud::DrawAmmo: ret
 op(0x0A8C)+i32(0x58D7D0)+i8(1)+i32(RET)+i8(1),       # CHud::DrawWeaponIcon: ret
 op(0x0A8C)+i32(0x589270)+i8(1)+i32(RET)+i8(1),       # la barra de vida: ret
 op(0x0A8C)+i32(0x5890A0)+i8(1)+i32(RET)+i8(1),       # la barra del chaleco: ret
 op(0x0A8C)+i32(0x58F47D)+i8(2)+i32(0xE990)+i8(1),    # el dinero: nop + jmp (90 E9) saltea el dibujo
 op(0x0001)+i16(1000),
 jmp(0x0002,'ocultar'),
]
pos={}; n=0
for c in code:
    if isinstance(c,L): pos[str(c)]=n
    elif isinstance(c,tuple): n+=len(c[0])+4
    else: n+=len(c)
b=b''.join(c[0]+struct.pack('<i',-pos[c[1]]) if isinstance(c,tuple) else (b'' if isinstance(c,L) else c) for c in code)
assert len(b)==n and b[pos['ocultar']:pos['ocultar']+2]==op(0x0A8C)
open(sys.argv[1],'wb').write(b); print(len(b)); print(b.hex(' '))
