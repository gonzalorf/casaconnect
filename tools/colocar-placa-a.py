"""Escribe las coordenadas de los 23 componentes de la Placa A en el .kicad_pcb.

Posicionar 23 componentes con el mouse es lento y, en el caso del zocalo
del ESP32, directamente riesgoso: las tres tiras tienen que quedar a
distancias exactas o la placa no entra.

    1. Guardar la placa en KiCad (Ctrl+S) y CERRAR el programa
    2. python tools/colocar-placa-a.py
    3. Reabrir la placa

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
SOCKET_X = 12.0          # donde arranca el pin 1 de las tres tiras
SOCKET_Y = 18.0          # fila izquierda (J2)
SEP_09 = 22.86           # 0.9 pulgadas -> MCU-001
SEP_10 = 25.40           # 1.0 pulgadas -> MCU-002

# designador -> (x, y, rotacion)
POSICIONES = {
    # --- enlace a la Placa B, sobre el borde superior ---
    "J8":  (SOCKET_X, 6.0, 0),

    # --- zocalo del ESP32: las tres tiras, distancias exactas ---
    "J2":  (SOCKET_X, SOCKET_Y, 0),
    "J3":  (SOCKET_X, SOCKET_Y + SEP_09, 0),
    "J3B": (SOCKET_X, SOCKET_Y + SEP_10, 0),

    # --- interfaz, sobre el borde derecho ---
    "J6":  (74.0, 18.0, 0),      # OLED
    "J7":  (74.0, 30.0, 0),      # I2C de expansion
    "R9":  (64.0, 24.0, 0),      # pull-up I2C (SDA)
    "R10": (64.0, 36.0, 0),      # pull-up I2C (SCL)

    # --- pull-ups de rele, en fila entre el ESP32 y J4 ---
    # Verticales (rot 90): cada una ocupa 10.16 mm a lo alto.
    "R1":  (14.0, 57.0, 90),
    "R2":  (19.0, 57.0, 90),
    "R3":  (24.0, 57.0, 90),
    "R4":  (29.0, 57.0, 90),
    "R5":  (34.0, 57.0, 90),
    "R6":  (39.0, 57.0, 90),
    "R7":  (44.0, 57.0, 90),
    "R8":  (49.0, 57.0, 90),

    # --- alimentacion, toda junta abajo y pegada a J4 (masa en estrella) ---
    "J4":  (14.0, 70.0, 0),      # header de 10 al modulo de reles
    "J1":  (44.0, 70.0, 0),      # entrada de 5 V
    "F1":  (44.0, 60.0, 0),      # portafusible
    "J5":  (60.0, 70.0, 0),      # salida 5 V al JD-VCC
    "C1":  (76.0, 68.0, 0),      # reservorio de 1000 uF
    "C2":  (76.0, 56.0, 0),      # desacople del riel de 5 V
    "C3":  (6.0, 26.0, 0),       # desacople de 3V3, cerca del pin del zocalo
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
        if ref in POSICIONES:
            x, y, rot = POSICIONES[ref]
            bloque = reposicionar(bloque, x, y, rot)
            movidos.append((ref, x, y, rot))
        elif ref:
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

    faltan = set(POSICIONES) - {r for r, *_ in movidos}
    if faltan:
        print(f"No estaban en la placa: {', '.join(sorted(faltan))}")

    print("\nReabri la placa en KiCad y ajusta a ojo lo que haga falta.")
    print("Para volver atras, renombra el archivo de copia.")


if __name__ == "__main__":
    main()
