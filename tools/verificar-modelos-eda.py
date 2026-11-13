"""Verifica que cada numero LCSC de PARTS tenga modelo EDA en EasyEDA.

La extension de importacion busca los componentes en la libreria de EasyEDA,
no en el catalogo de LCSC. Muchos articulos de LCSC NO tienen simbolo ni
huella cargados, y para esos la importacion falla con:

    Supplier part not found: Cxxxxxxx

Este script consulta la API publica de EasyEDA y dice cuales sirven.

    python tools/verificar-modelos-eda.py

OJO - LIMITACION IMPORTANTE
---------------------------
Esta API es la de EasyEDA STANDARD (v6). EasyEDA PRO tiene una libreria
SEPARADA, y la extension de importacion busca en la de Pro. Que un
componente aparezca OK aca NO garantiza que Pro lo tenga.

Para verificar en Pro hay que buscar el C-number en el panel Library de
la propia aplicacion.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = "https://easyeda.com/api/products/{}/components?version=6.4.19.5"
UA = "CasaConnect-netlist/1.0 (+herramienta de inventario, uso personal)"


def modelo(lcsc):
    """Devuelve (ok, detalle) para un C-number."""
    try:
        req = urllib.request.Request(API.format(lcsc), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except Exception as e:
        return False, f"error de red: {e}"

    if not d.get("success") or not d.get("result"):
        return False, "sin modelo EDA"

    r = d["result"]
    shape = (r.get("dataStr") or {}).get("shape") or []
    pines = len([s for s in shape if s.startswith("P~")])
    pk = ((r.get("packageDetail") or {}).get("dataStr") or {}).get("shape") or []
    pads = len([s for s in pk if s.startswith("PAD~")])

    if pines == 0 or pads == 0:
        return False, f"modelo incompleto (pines={pines}, pads={pads})"
    return True, f"{pines} pines / {pads} pads · {r.get('title') or '?'}"


def main():
    src = (Path(__file__).parent / "generar-netlist.py").read_text(encoding="utf-8")
    partes = re.findall(r'"(\w+)":\s*\{"lcsc": "(C\d+)"', src)
    if not partes:
        sys.exit("No se encontraron numeros LCSC en generar-netlist.py")

    print(f"Verificando {len(partes)} componentes contra la libreria de EasyEDA...\n")
    malos = []
    for clave, lcsc in partes:
        ok, detalle = modelo(lcsc)
        print(f"  {'OK ' if ok else 'NO '} {clave:8} {lcsc:12} {detalle}")
        if not ok:
            malos.append((clave, lcsc))

    print()
    if malos:
        print(f"{len(malos)} componente(s) SIN modelo EDA: la extension no los va a")
        print("encontrar. Hay que elegir otro articulo de LCSC que si lo tenga.")
        print("En la ficha del producto tiene que figurar 'EDA Models: EasyEDA'.\n")
        for clave, lcsc in malos:
            print(f"    {clave:8} {lcsc}")
    else:
        print("Todos tienen modelo EDA. La importacion deberia funcionar.")


if __name__ == "__main__":
    main()
