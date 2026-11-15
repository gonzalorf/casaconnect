"""Dice que falta rutear, lista los puentes y chequea si es fabricable en casa.

    python tools/estado_ruteo.py

Para cada red arma un grafo con los pads, las pistas y las vias, y mira
si todo quedo en una sola pieza. Lo que aparezca partido en dos o mas
grupos es una conexion pendiente.

Ademas:
  * Lista las pistas de F.Cu, que en este proyecto no son cobre sino
    PUENTES DE ALAMBRE: la cara superior no se etcha.
  * Avisa si hay pistas o vias demasiado finas para etching casero.

Nota de formato: KiCad 10 referencia las redes por NOMBRE entre comillas,
(net "GND"), no por numero.
"""

import math
import re
import sys
from pathlib import Path

PCB = Path(__file__).parent.parent / "kicad" / "CasaConnect" / "CasaConnect.kicad_pcb"
TOL = 0.02              # mm; dos puntos mas cerca que esto son el mismo nodo

# Minimos para hacerla en casa (ver docs/circuito-v1.md, seccion 9)
ANCHO_MIN_SENAL = 0.6
ANCHO_MIN_POTENCIA = 1.5
TALADRO_VIA_MIN = 0.8
REDES_POTENCIA = {"GND", "+5V", "+5V_IN", "+3V3", "+5V_PUERTOS"}


class Union:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def une(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def bloques(t, clave):
    for m in re.finditer(r"\(" + clave + r"[\s(]", t):
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


def campo(b, nombre, patron=r'"([^"]*)"'):
    m = re.search(r"\(" + nombre + r"\s+" + patron + r"\s*\)", b)
    return m.group(1) if m else None


def xy(b, nombre):
    m = re.search(r"\(" + nombre + r"\s+(-?[\d.]+)\s+(-?[\d.]+)", b)
    return (float(m.group(1)), float(m.group(2))) if m else None


def leer():
    t = PCB.read_text(encoding="utf-8")

    pads = []
    for fb in bloques(t, "footprint"):
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', fb)
        pos = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)", fb)
        if not (ref and pos):
            continue
        fx, fy = float(pos.group(1)), float(pos.group(2))
        rot = math.radians(float(pos.group(3) or 0))
        for pb in bloques(fb, "pad"):
            num = re.match(r'\(pad\s+"([^"]*)"', pb)
            local = xy(pb, "at")
            red = campo(pb, "net")
            if not (num and num.group(1) and local and red):
                continue
            px, py = local
            pads.append((f"{ref.group(1)}.{num.group(1)}", red,
                         fx + px * math.cos(rot) + py * math.sin(rot),
                         fy - px * math.sin(rot) + py * math.cos(rot)))

    segs = []
    for sb in bloques(t, "segment"):
        ini, fin = xy(sb, "start"), xy(sb, "end")
        ancho = campo(sb, "width", r"([\d.]+)")
        capa, red = campo(sb, "layer"), campo(sb, "net")
        if ini and fin and ancho and capa is not None:
            segs.append((ini[0], ini[1], fin[0], fin[1], float(ancho), capa, red or ""))

    vias = []
    for vb in bloques(t, "via"):
        p = xy(vb, "at")
        taladro = campo(vb, "drill", r"([\d.]+)")
        red = campo(vb, "net")
        if p:
            vias.append((p[0], p[1], float(taladro or 0), red or ""))

    return pads, segs, vias, len(re.findall(r"\(zone[\s(]", t))


def nodo(x, y, capa):
    return (round(x / TOL), round(y / TOL), capa)


def main():
    pads, segs, vias, zonas = leer()
    print(f"{len(pads)} pads · {len(segs)} segmentos · {len(vias)} vias "
          f"· {zonas} relleno(s)\n")

    por_red = {}
    for nombre, red, x, y in pads:
        if red:
            por_red.setdefault(red, []).append((nombre, x, y))

    pendientes = []
    for red, lista in sorted(por_red.items()):
        if len(lista) < 2:
            continue
        u = Union()
        for nombre, x, y in lista:
            u.une(("pad", nombre), nodo(x, y, "*"))
        for x1, y1, x2, y2, _w, capa, r in segs:
            if r != red:
                continue
            u.une(nodo(x1, y1, capa), nodo(x2, y2, capa))
            for nombre, px, py in lista:
                for ex, ey in ((x1, y1), (x2, y2)):
                    if abs(ex - px) < 0.06 and abs(ey - py) < 0.06:
                        u.une(nodo(ex, ey, capa), ("pad", nombre))
        for x, y, _d, r in vias:
            if r != red:
                continue
            for capa in ("B.Cu", "F.Cu"):
                u.une(nodo(x, y, capa), nodo(x, y, "*"))

        grupos = {}
        for nombre, _x, _y in lista:
            grupos.setdefault(u.find(("pad", nombre)), []).append(nombre)
        if len(grupos) > 1:
            pendientes.append((red, list(grupos.values())))

    if pendientes:
        print(f"REDES INCOMPLETAS ({len(pendientes)}):\n")
        for red, grupos in pendientes:
            print(f"  {red:14} {len(grupos) - 1} conexion(es) pendiente(s)")
            for g in grupos:
                print(f"       {', '.join(sorted(g))}")
        print()
    else:
        print("Todas las redes estan completas.\n")

    puentes = [s for s in segs if s[5] == "F.Cu"]
    if puentes:
        print(f"PUENTES DE ALAMBRE ({len(puentes)} tramos en F.Cu):\n")
        total = 0.0
        for x1, y1, x2, y2, _w, _c, r in puentes:
            largo = math.hypot(x2 - x1, y2 - y1)
            total += largo
            print(f"  {r or '(sin red)':12} ({x1:6.1f},{y1:5.1f}) -> "
                  f"({x2:6.1f},{y2:5.1f})   {largo:5.1f} mm")
        print(f"\n  alambre total: {total:.0f} mm\n")

    # --- se puede fabricar en casa? ---
    print("FABRICACION CASERA")
    avisos = []

    finas = [s for s in segs
             if s[4] < (ANCHO_MIN_POTENCIA if s[6] in REDES_POTENCIA
                        else ANCHO_MIN_SENAL)]
    if finas:
        anchos = sorted({s[4] for s in finas})
        avisos.append(
            f"{len(finas)} de {len(segs)} pistas por debajo del minimo "
            f"(anchos usados: {', '.join(str(a) for a in anchos)} mm).\n"
            f"       Minimos: {ANCHO_MIN_SENAL} mm senal, "
            f"{ANCHO_MIN_POTENCIA} mm alimentacion.")

    chicas = [v for v in vias if v[2] < TALADRO_VIA_MIN]
    if chicas:
        avisos.append(
            f"{len(chicas)} de {len(vias)} vias con taladro menor a "
            f"{TALADRO_VIA_MIN} mm (la mas chica: {min(v[2] for v in chicas)} mm).\n"
            f"       No se perforan ni se sueldan a mano.")

    sin_red = [s for s in segs if not s[6]]
    if sin_red:
        avisos.append(f"{len(sin_red)} segmento(s) sin red asignada: "
                      f"pistas sueltas que no conectan nada.")

    if zonas == 0:
        avisos.append("Sin relleno de masa. GND ruteado a mano.")

    if avisos:
        for a in avisos:
            print(f"  !  {a}")
    else:
        print("  Todo dentro de los minimos.")

    sys.exit(1 if pendientes else 0)


if __name__ == "__main__":
    main()
