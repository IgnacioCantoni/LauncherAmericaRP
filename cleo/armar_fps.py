# Arma actualizaciones/archivos/cleo/fps_libres.cs (bytecode de CLEO). Uso: python cleo/armar_fps.py actualizaciones/archivos/cleo/fps_libres.cs
# FPS sin tope, salvo mientras apuntás un arma a pie: arriba de unos 75 FPS el GTA no deja caminar
# apuntando (el MTA lo arregla igual, bajando a 70 solo al apuntar).
import struct,sys
def op(n): return struct.pack('<H',n)
def i8(v): return b'\x04'+struct.pack('<b',v)
def i16(v): return b'\x05'+struct.pack('<h',v)
def i32(v): return b'\x01'+struct.pack('<i',v if v<2**31 else v-2**32)
def lv(n): return b'\x03'+struct.pack('<H',n)
def s(t): return b'\x0e'+bytes([len(t)])+t.encode()
class L(str): pass                                    # etiqueta
def jmp(o,lbl): return (op(o)+b'\x01', lbl)          # se completa con -posición de la etiqueta (script CLEO)

# Apuntando vuelve el cmp esi, 11 original del SA-MP (unos 98 FPS, probado: deja caminar apuntando).
# Otro número cuelga el juego: el SA-MP calcula la espera con un 10 fijo (con 16 crasheó a los 3 s).
TOPE_APUNTANDO=11
code=[
 op(0x0000),
 L('loop'),
 op(0x0001)+i8(0),                                    # cada cuadro
 op(0x0A8C)+i32(0xBA6794)+i8(1)+i8(0)+i8(0),          # opción Frame limiter del menú = apagada
 op(0x0A8C)+i32(0x53E94C)+i8(1)+i8(0)+i8(1),          # espera mínima entre cuadros del GTA = 0
 # 4@: 0 = falta buscar el SA-MP, 1 = listo (3@ = el tope de su limitador), 2 = otra versión: no se toca
 op(0x00D6)+i8(0), op(0x0039)+lv(4)+i8(0), jmp(0x004D,'listo'),
 op(0x0A8D)+i32(0x731F60)+i8(4)+i8(1)+lv(2),          # el SA-MP pone 20000 acá (el GTA trae 5000): está cargado
 op(0x00D6)+i8(0), op(0x0039)+lv(2)+i16(20000), jmp(0x004D,'loop'),
 op(0x0006)+lv(4)+i8(2),
 op(0x0AA2)+s('samp.dll')+lv(0),                      # 0@ = dirección de samp.dll (una sola vez)
 op(0x0A8E)+lv(0)+i32(0xA1D86)+lv(1),                 # 1@ = cmp esi, 11 del limitador del SA-MP (0.3.7-R5)
 op(0x0A8D)+lv(1)+i8(4)+i8(1)+lv(2),
 op(0x00D6)+i8(0), op(0x0039)+lv(2)+i32(0x7D0BFE83), jmp(0x004D,'loop'),   # solo si es esa versión: 83 FE 0B 7D
 op(0x0A8E)+lv(1)+i8(2)+lv(3),                        # 3@ = dirección del 11 de cmp esi, 11
 op(0x0006)+lv(4)+i8(1),
 L('listo'),
 op(0x00D6)+i8(0), op(0x0039)+lv(4)+i8(1), jmp(0x004D,'loop'),
 op(0x0A8D)+i32(0xB6F1A8)+i8(2)+i8(0)+lv(5),          # 5@ = modo de la cámara (TheCamera.Cams[0].Mode)
 op(0x00D6)+i8(0), op(0x0039)+lv(5)+i8(53), jmp(0x004D,'libre'),          # 53 = apuntando un arma a pie
 op(0x0A8C)+lv(3)+i8(1)+i8(TOPE_APUNTANDO)+i8(1),     # el limitador original
 jmp(0x0002,'loop'),
 L('libre'),
 op(0x0A8C)+lv(3)+i8(1)+i8(0)+i8(1),                  # cmp esi, 0: nunca duerme
 jmp(0x0002,'loop'),
]
pos={}; n=0
for c in code:
    if isinstance(c,L): pos[str(c)]=n
    elif isinstance(c,tuple): n+=len(c[0])+4
    else: n+=len(c)
b=b''.join(c[0]+struct.pack('<i',-pos[c[1]]) if isinstance(c,tuple) else (b'' if isinstance(c,L) else c) for c in code)
assert len(b)==n and b[pos['loop']:pos['loop']+2]==op(1) and b[pos['libre']:pos['libre']+2]==op(0x0A8C)
open(sys.argv[1],'wb').write(b); print(len(b)); print(b.hex(' '))
