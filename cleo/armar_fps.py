# Arma actualizaciones/archivos/cleo/fps_sin_limite.cs (bytecode de CLEO). Uso: python cleo/armar_fps.py actualizaciones/archivos/cleo/fps_sin_limite.cs
import struct,sys
def op(n): return struct.pack('<H',n)
def i8(v): return b'\x04'+struct.pack('<b',v)
def i16(v): return b'\x05'+struct.pack('<h',v)
def i32(v): return b'\x01'+struct.pack('<i',v if v<2**31 else v-2**32)
def lv(n): return b'\x03'+struct.pack('<H',n)
def s(t): return b'\x0e'+bytes([len(t)])+t.encode()
LOOP=2
def jmp(o,lbl): return op(o)+b'\x01'+struct.pack('<i',-lbl)
code=[
 op(0x0000),
 # :loop (posición 2)
 op(0x0001)+i16(500),
 op(0x0A8C)+i32(0xBA6794)+i8(1)+i8(0)+i8(0),          # opción Frame limiter del menú = apagada
 op(0x0A8C)+i32(0x53E94C)+i8(1)+i8(0)+i8(1),          # espera mínima entre cuadros del GTA = 0
 op(0x00D6)+i8(0), op(0x0039)+lv(4)+i8(0), jmp(0x004D,LOOP),   # 4@ = ya se revisó el SA-MP
 op(0x0A8D)+i32(0x731F60)+i8(4)+i8(1)+lv(2),          # el SA-MP pone 20000 acá (el GTA trae 5000): está cargado
 op(0x00D6)+i8(0), op(0x0039)+lv(2)+i16(20000), jmp(0x004D,LOOP),
 op(0x0006)+lv(4)+i8(1),
 op(0x0AA2)+s('samp.dll')+lv(0),                      # 0@ = dirección de samp.dll
 op(0x0A8E)+lv(0)+i32(0xA1D86)+lv(1),                 # 1@ = cmp esi, 11 del limitador del SA-MP (0.3.7-R5)
 op(0x0A8D)+lv(1)+i8(4)+i8(1)+lv(2),
 op(0x00D6)+i8(0), op(0x0039)+lv(2)+i32(0x7D0BFE83), jmp(0x004D,LOOP),   # solo si es esa versión: 83 FE 0B 7D
 op(0x0A8E)+lv(1)+i8(2)+lv(3),
 op(0x0A8C)+lv(3)+i8(1)+i8(0)+i8(1),                  # cmp esi, 0: nunca duerme
 jmp(0x0002,LOOP),
]
b=b''.join(code)
assert b[2:4]==op(1)
open(sys.argv[1],'wb').write(b); print(len(b)); print(b.hex(' '))
