"""Verifica nombres de huella contra la instalacion real de KiCad.

Los nombres cambian entre versiones: el de la bornera que usamos al
principio (TerminalBlock_bornier-2_P5.08mm) existia en versiones viejas
y no en la 10. Esto lo detecta ANTES de importar, en vez de descubrirlo
con la mitad de los componentes afuera.

Lo usa generar-netlist-kicad.py, pero tambien corre solo:

    python tools/verificar-huellas-kicad.py
"""

import glob
import os
import re
from pathlib import Path


def dir_huellas():
    """Ubica la carpeta de huellas de KiCad. Devuelve None si no esta."""
    patrones = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\KiCad\*\share\kicad\footprints"),
        r"C:\Program Files\KiCad\*\share\kicad\footprints",
        "/usr/share/kicad/footprints",
        os.path.expanduser("~/.local/share/kicad/*/footprints"),
    ]
    for patron in patrones:
        hits = sorted(glob.glob(patron))
        if hits:
            return Path(hits[-1])
    return None


def pads_de(base, huella):
    """Pads con nombre de una huella. None si la huella no existe.

    Los agujeros de montaje son np_thru_hole y vienen con nombre vacio,
    asi que quedan descartados por el filtro.
    """
    lib, nombre = huella.split(":", 1)
    ruta = base / (lib + ".pretty") / (nombre + ".kicad_mod")
    if not ruta.exists():
        return None
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    return {p for p in re.findall(r'\(pad\s+"([^"]+)"', texto) if p}


def verificar(netlists, huellas):
    """netlists: lista de objetos con .orden · huellas: clave -> (sym, fp, _)

    Devuelve True si todo esta bien. Imprime el detalle.
    """
    base = dir_huellas()
    if base is None:
        print("KiCad no esta instalado aca: no se pueden verificar las huellas.")
        print("Los nombres quedan sin chequear; verificalos al importar.")
        return True

    print("Verificando huellas contra:")
    print("  " + str(base))
    print()

    problemas = []
    for nl in netlists:
        for designador, clave, pins in nl.orden:
            huella = huellas[clave][1]
            pads = pads_de(base, huella)
            if pads is None:
                problemas.append(
                    "{:6} huella inexistente: {}".format(designador, huella))
                continue
            faltan = sorted(set(pins) - pads)
            if faltan:
                problemas.append(
                    "{:6} la huella {} no tiene el/los pad(s) {}".format(
                        designador, huella.split(":", 1)[1], ", ".join(faltan)))

    vistos = set()
    unicos = [p for p in problemas if not (p in vistos or vistos.add(p))]

    if unicos:
        print("  {} problema(s) distinto(s):".format(len(unicos)))
        print()
        for p in unicos:
            print("    " + p)
        print()
        print("  Corregir los nombres en HUELLAS antes de importar.")
        print("  Para encontrar el correcto, mirar el contenido de:")
        print("    " + str(base))
        return False

    print("  Todas las huellas existen y tienen los pads que usa el netlist.")
    return True


if __name__ == "__main__":
    base = dir_huellas()
    if base is None:
        print("No se encontro la instalacion de KiCad.")
    else:
        libs = sorted(p.stem for p in base.glob("*.pretty"))
        print("KiCad encontrado en:\n  {}\n".format(base))
        print("{} bibliotecas de huellas disponibles.".format(len(libs)))
