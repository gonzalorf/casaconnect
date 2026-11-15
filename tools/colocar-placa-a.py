"""Escribe las coordenadas de los 23 componentes de la Placa A en el .kicad_pcb.

Posicionar 23 componentes con el mouse es lento y, en el caso del zocalo
del ESP32, directamente riesgoso: las tres tiras tienen que quedar a
distancias exactas o la placa no entra.

    1. Guardar la placa en KiCad (Ctrl+S) y CERRAR el programa
    2. python tools/colocar-placa-a.py            <- coloca los 23
       python tools/colocar-placa-a.py F1 C2      <- solo esos dos
    3. Reabrir la placa

Pasarle designadores sirve para corregir algo puntual sin deshacer los
ajustes que hayas hecho a mano en el resto.

ESTO ES UN PUNTO DE PARTIDA, NO EL DISENO FINAL
-----------------------------------------------
Las posiciones estan calculadas sin ver los contornos reales de cada
huella, asi que puede haber solapamientos. La idea es que abras el
resultado y lo refines a ojo, que es mucho mas rapido que arrancar de
cero.

CRITERIOS DE LA DISTRIBUCION
----------------------------
* El zocalo del ESP32 (J2/J3/J3B) con las distancias exactas: 22.86 mm
  a J3 (placas de 0.9") y 25.4 mm a J3B (las de 1.0").
* Las 8 resistencias de pull-up en el camino entre el ESP32 y J4, el
  header que va al modulo de reles.
* Toda la alimentacion junta abajo a la derecha, pegada a J4: es la
  regla de masa en estrella, para que los 560 mA de las bobinas no
  compartan recorrido con la masa del ESP32.
* Los conectores que miran hacia afuera (J8, J6, J1, J5) sobre bordes.
"""

import re
import shutil
import sys
from pathlib import Path

PCB = Path(__file__).parent.parent / "kicad" / "CasaConnect" / "CasaConnect.kicad_pcb"

# Geometria del zocalo
#
# OJO: las huellas PinHeader/PinSocket de KiCad corren a lo largo del eje
# Y: el pin 1 queda arriba y los demas bajan. Asi que la separacion entre
# las filas del zocalo va en X, y cada tira ocupa 19 x 2.54 = 45.72 mm de
# alto.
SOCKET_X = 16.0          # columna izquierda del ESP32 (J2)
SOCKET_Y = 12.0          # donde arranca el pin 1 de las tres tiras
SEP_09 = 22.86           # 0.9 pulgadas -> MCU-001
SEP_10 = 25.40           # 1.0 pulgadas -> MCU-002

# designador -> (x, y, rotacion)
POSICIONES = {
    # --- enlace a la Placa B, borde izquierdo ---
    "J8":  (6.0, SOCKET_Y, 0),                      # 1x20, 48.3 mm de alto

    # --- zocalo del ESP32: tres tiras verticales, separacion exacta en X ---
    "J2":  (SOCKET_X, SOCKET_Y, 0),
    "J3":  (SOCKET_X + SEP_09, SOCKET_Y, 0),
    "J3B": (SOCKET_X + SEP_10, SOCKET_Y, 0),

    # --- desacople de 3V3, arriba del pin 1 de J2 ---
    "C3":  (14.0, 6.0, 0),

    # --- pull-ups de rele: columna entre el ESP32 y J4 ---
    # Horizontales. OJO: en estas huellas el pad 1 esta en el ORIGEN,
    # no centrado, asi que cada una se extiende 10.16 mm hacia la
    # DERECHA del punto de colocacion.
    "R1":  (46.0, 12.0, 0),
    "R2":  (46.0, 17.0, 0),
    "R3":  (46.0, 22.0, 0),
    "R4":  (46.0, 27.0, 0),
    "R5":  (46.0, 32.0, 0),
    "R6":  (46.0, 37.0, 0),
    "R7":  (46.0, 42.0, 0),
    "R8":  (46.0, 47.0, 0),

    # --- header al modulo de 8 reles ---
    "J4":  (62.0, 12.0, 0),                         # 1x10, 22.9 mm de alto

    # --- interfaz, borde derecho ---
    "J6":  (76.0, 12.0, 0),                         # OLED
    "J7":  (76.0, 26.0, 0),                         # I2C de expansion
    "R9":  (86.0, 14.0, 0),                         # pull-up I2C (SDA)
    "R10": (86.0, 20.0, 0),                         # pull-up I2C (SCL)

    # --- alimentacion, abajo y agrupada (masa en estrella) ---
    "J1":  (62.0, 48.0, 0),                         # entrada de 5 V
    # OJO con F1: mide 35.6 x 13.1 mm pero sus pads estan solo en x=0
    # y x=10.16. El cuerpo se extiende 23 mm mas alla del ultimo pad,
    # asi que hay que mirar el courtyard y no los pads.
    "F1":  (49.0, 62.0, 0),                         # portafusible
    "J5":  (78.0, 48.0, 0),                         # salida al JD-VCC
    "C1":  (92.0, 48.0, 0),                         # reservorio 1000 uF
    "C2":  (87.0, 62.0, 0),                         # desacople de 5 V
}


def bloques_footprint(texto):
    """Genera (inicio, fin) de cada bloque (footprint ...) por balance de parentesis."""
    for m in re.finditer(r"\(footprint\s", texto):
        i = m.start()
        nivel, j = 0, i
        while j < len(texto):
            if texto[j] == "(":
                nivel += 1
            elif texto[j] == ")":
                nivel -= 1
                if nivel == 0:
                    yield i, j + 1
                    break
            j += 1


def referencia(bloque):
    m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', bloque)
    return m.group(1) if m else None


def reposicionar(bloque, x, y, rot):
    """Reemplaza el (at ...) de primer nivel del footprint."""
    # El primero que aparece en el bloque es el del footprint; los de los
    # pads y las propiedades vienen despues y estan mas indentados.
    nuevo = f"(at {x:g} {y:g}" + (f" {rot:g})" if rot else ")")
    return re.sub(r"\(at\s+-?[\d.]+\s+-?[\d.]+(?:\s+-?[\d.]+)?\s*\)",
                  nuevo, bloque, count=1)


def main():
    if not PCB.exists():
        sys.exit(f"No existe {PCB}")

    pedidos = {a.upper() for a in sys.argv[1:]}
    if pedidos:
        desconocidos = pedidos - set(POSICIONES)
        if desconocidos:
            sys.exit("Sin posicion definida: " + ", ".join(sorted(desconocidos)))
        print("Moviendo solo: " + ", ".join(sorted(pedidos)))
        print()

    texto = PCB.read_text(encoding="utf-8")
    bloques = list(bloques_footprint(texto))
    if not bloques:
        sys.exit("La placa no tiene componentes. Guardala en KiCad (Ctrl+S) primero.")

    copia = PCB.with_suffix(".kicad_pcb.antes-de-colocar")
    shutil.copy2(PCB, copia)
    print(f"Copia de seguridad: {copia.name}\n")

    salida, cursor, movidos, sin_posicion = [], 0, [], []
    for ini, fin in bloques:
        salida.append(texto[cursor:ini])
        bloque = texto[ini:fin]
        ref = referencia(bloque)
        if ref in POSICIONES and (not pedidos or ref in pedidos):
            x, y, rot = POSICIONES[ref]
            bloque = reposicionar(bloque, x, y, rot)
            movidos.append((ref, x, y, rot))
        elif ref and not pedidos:
            sin_posicion.append(ref)
        salida.append(bloque)
        cursor = fin
    salida.append(texto[cursor:])

    PCB.write_text("".join(salida), encoding="utf-8")

    for ref, x, y, rot in sorted(movidos):
        print(f"  {ref:5} -> x={x:6.2f}  y={y:6.2f}  rot={rot}")
    print(f"\n{len(movidos)} componente(s) colocado(s).")

    if sin_posicion:
        print(f"\nSin posicion definida: {', '.join(sorted(sin_posicion))}")

    faltan = (pedidos or set(POSICIONES)) - {r for r, *_ in movidos}
    if faltan:
        print(f"No estaban en la placa: {', '.join(sorted(faltan))}")

    print("\nReabri la placa en KiCad y ajusta a ojo lo que haga falta.")
    print("Para volver atras, renombra el archivo de copia.")


if __name__ == "__main__":
    main()
