"""Detecta solapamientos FISICOS entre componentes de una placa colocada.

    python tools/verificar_colocacion.py

Usa el courtyard de cada huella: el rectangulo que marca el espacio que
ocupa el componente de verdad. Mirar solo los pads no alcanza. El
portafusible de 5x20, por ejemplo, tiene sus dos pads en x=0 y x=10.16
pero el cuerpo se extiende hasta x=33: un chequeo por pads lo deja pasar
y despues se pisa con lo que tenga al lado.

Lee los courtyards de la instalacion de KiCad. Si no la encuentra, cae a
los pads y lo avisa.
"""

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verificar_huellas import dir_huellas  # noqa: E402

PCB = Path(__file__).parent.parent / "kicad" / "CasaConnect" / "CasaConnect.kicad_pcb"
MARGEN = 0.5          # separacion minima deseada entre componentes

# Parejas cuyo solapamiento es intencional. J3 y J3B son las dos tiras
# alternativas del zocalo del ESP32, a 2.54 mm: sus courtyards llevan
# margen de seguridad y se pisan 1 mm, pero los cuerpos reales (2.54 mm
# de ancho) quedan justo tocandose, que es lo buscado.
ESPERADOS = {frozenset(("J3", "J3B"))}

_cache = {}


def extension_courtyard(base, huella):
    """(minx, miny, maxx, maxy) del courtyard en coordenadas locales."""
    if huella in _cache:
        return _cache[huella]
    resultado = None
    if base is not None and ":" in huella:
        lib, nombre = huella.split(":", 1)
        ruta = base / (lib + ".pretty") / (nombre + ".kicad_mod")
        if ruta.exists():
            texto = ruta.read_text(encoding="utf-8", errors="replace")
            xs, ys = [], []
            for m in re.finditer(r"\(fp_\w+\b(.*?)\(layer \"F\.CrtYd\"", texto, re.S):
                for a, b in re.findall(r"\((?:start|end|center|mid|xy) "
                                       r"([-\d.]+) ([-\d.]+)\)", m.group(1)):
                    xs.append(float(a))
                    ys.append(float(b))
            if xs:
                resultado = (min(xs), min(ys), max(xs), max(ys))
    _cache[huella] = resultado
    return resultado


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


def caja(bloque, base):
    ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', bloque)
    huella = re.search(r'\(footprint\s+"([^"]+)"', bloque)
    pos = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)", bloque)
    if not (ref and huella and pos):
        return None

    fx, fy = float(pos.group(1)), float(pos.group(2))
    rot = math.radians(float(pos.group(3) or 0))

    ext = extension_courtyard(base, huella.group(1))
    fuente = "courtyard"
    if ext is None:
        fuente = "pads"
        xs, ys = [], []
        for pm in re.finditer(
                r"\(pad\s+\"[^\"]*\"[^()]*(?:\([^()]*\))*?"
                r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)[^)]*\)\s*\(size\s+([\d.]+)\s+([\d.]+)\)",
                bloque):
            px, py, sw, sh = map(float, pm.groups())
            xs += [px - sw / 2, px + sw / 2]
            ys += [py - sh / 2, py + sh / 2]
        if not xs:
            return None
        ext = (min(xs), min(ys), max(xs), max(ys))

    # Rotar las cuatro esquinas y volver a encajonar
    esquinas = [(ext[0], ext[1]), (ext[2], ext[1]), (ext[2], ext[3]), (ext[0], ext[3])]
    xs, ys = [], []
    for px, py in esquinas:
        xs.append(fx + px * math.cos(rot) + py * math.sin(rot))
        ys.append(fy - px * math.sin(rot) + py * math.cos(rot))
    return ref.group(1), min(xs), min(ys), max(xs), max(ys), fuente


def main():
    base = dir_huellas()
    if base is None:
        print("KiCad no encontrado: se usan los pads, que subestiman el tamano.\n")

    cajas = [c for c in (caja(b, base) for b in bloques(
        PCB.read_text(encoding="utf-8"))) if c]
    por_pads = [c[0] for c in cajas if c[5] == "pads"]
    print(f"{len(cajas)} componentes medidos por courtyard"
          + (f" ({len(por_pads)} por pads: {', '.join(por_pads)})" if por_pads else "")
          + "\n")

    choques = []
    for i, a in enumerate(cajas):
        for b in cajas[i + 1:]:
            solape_x = min(a[3], b[3]) - max(a[1], b[1])
            solape_y = min(a[4], b[4]) - max(a[2], b[2])
            if frozenset((a[0], b[0])) in ESPERADOS:
                continue
            if solape_x > -MARGEN and solape_y > -MARGEN:
                choques.append((a[0], b[0], max(solape_x, 0), max(solape_y, 0)))

    if choques:
        print(f"SOLAPAMIENTOS ({len(choques)}):")
        for a, b, sx, sy in sorted(choques, key=lambda c: -(c[2] * c[3])):
            print(f"   {a:5} <-> {b:5}   se pisan {sx:5.2f} x {sy:5.2f} mm")
    else:
        print("Sin solapamientos.")

    xs = [c[1] for c in cajas] + [c[3] for c in cajas]
    ys = [c[2] for c in cajas] + [c[4] for c in cajas]
    print(f"\nOcupa  x {min(xs):.1f} .. {max(xs):.1f} mm"
          f"  ·  y {min(ys):.1f} .. {max(ys):.1f} mm")
    print(f"Contorno sugerido en Edge.Cuts: {max(xs) + 4:.0f} x {max(ys) + 4:.0f} mm")
    sys.exit(1 if choques else 0)


if __name__ == "__main__":
    main()
