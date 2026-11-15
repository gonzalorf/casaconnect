"""Detecta solapamientos entre los pads de una placa ya colocada.

    python tools/verificar_colocacion.py

Calcula la caja de cada componente a partir de sus pads (contemplando la
rotacion) y avisa si dos se pisan. Es el chequeo que conviene correr
despues de colocar por script, antes de abrir KiCad.
"""
import math
import re
import sys
from pathlib import Path

PCB = Path(__file__).parent.parent / "kicad" / "CasaConnect" / "CasaConnect.kicad_pcb"
MARGEN = 0.4      # separacion minima deseada entre cobre de componentes distintos


def bloques(t):
    for m in re.finditer(r"\(footprint\s", t):
        i, n, j = m.start(), 0, m.start()
        while j < len(t):
            if t[j] == "(":
                n += 1
            elif t[j] == ")":
                n -= 1
                if n == 0:
                    yield t[i:j + 1]
                    break
            j += 1


def caja(bloque):
    ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', bloque)
    pos = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)", bloque)
    if not ref or not pos:
        return None
    fx, fy = float(pos.group(1)), float(pos.group(2))
    rot = math.radians(float(pos.group(3) or 0))
    xs, ys = [], []
    for pm in re.finditer(
            r"\(pad\s+\"[^\"]*\"[^()]*(?:\([^()]*\))*?"
            r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)[^)]*\)\s*\(size\s+([\d.]+)\s+([\d.]+)\)",
            bloque):
        px, py, sw, sh = map(float, pm.groups())
        rx = px * math.cos(rot) + py * math.sin(rot)
        ry = -px * math.sin(rot) + py * math.cos(rot)
        xs += [fx + rx - sw / 2, fx + rx + sw / 2]
        ys += [fy + ry - sh / 2, fy + ry + sh / 2]
    if not xs:
        return None
    return ref.group(1), min(xs), min(ys), max(xs), max(ys)


def main():
    cajas = [c for c in map(caja, bloques(PCB.read_text(encoding="utf-8"))) if c]
    print(f"{len(cajas)} componentes con pads legibles\n")

    choques = []
    for i, a in enumerate(cajas):
        for b in cajas[i + 1:]:
            if (a[1] - MARGEN < b[3] and b[1] - MARGEN < a[3] and
                    a[2] - MARGEN < b[4] and b[2] - MARGEN < a[4]):
                choques.append((a[0], b[0]))

    if choques:
        print(f"SOLAPAMIENTOS ({len(choques)}):")
        for a, b in choques:
            print(f"   {a} <-> {b}")
    else:
        print("Sin solapamientos entre pads.")

    xs = [c[1] for c in cajas] + [c[3] for c in cajas]
    ys = [c[2] for c in cajas] + [c[4] for c in cajas]
    print(f"\nOcupa  x {min(xs):.1f} .. {max(xs):.1f} mm"
          f"  ·  y {min(ys):.1f} .. {max(ys):.1f} mm")
    print(f"Contorno sugerido en Edge.Cuts: "
          f"{max(xs) + 4:.0f} x {max(ys) + 4:.0f} mm")
    sys.exit(1 if choques else 0)


if __name__ == "__main__":
    main()
