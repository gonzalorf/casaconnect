"""Busca candidatos de numero LCSC para los componentes que faltan.

Consulta la API comunitaria jlcsearch (https://jlcsearch.tscircuit.com),
que no pide clave. Imprime candidatos con su C-number para que elijas y
los copies a PARTS en generar-netlist.py.

    python tools/buscar-lcsc.py            # solo los que faltan
    python tools/buscar-lcsc.py HDRM16     # uno en particular

LIMITACION IMPORTANTE
---------------------
jlcsearch indexa el catalogo de ENSAMBLADO de JLCPCB, que es un subconjunto
de LCSC y esta sesgado a SMD. Varios conectores pasantes no estan ahi y hay
que buscarlos igual en lcsc.com. El script te dice cuales.

Pistas para leer las descripciones, que vienen en chino:
    插件  = pasante (through hole)   <- lo que queremos
    贴片  = montaje superficial (SMD)
    直针  = pin recto
    弯插  = pin acodado (90 grados)
"""

import json
import sys
import urllib.parse
import urllib.request

API = "https://jlcsearch.tscircuit.com/api/search"

# La API rechaza el user-agent por defecto de urllib. Nos identificamos con
# el nombre real de la herramienta: no es disfrazarse de navegador.
UA = "CasaConnect-netlist/1.0 (+herramienta de inventario, uso personal)"

# La consola de Windows es cp1252 y las descripciones vienen con chino.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Que buscar y como filtrar. La busqueda de jlcsearch es difusa: pedir
# "1x16P" devuelve tambien "2x8P", que tiene la misma cantidad de pines
# pero es de DOBLE FILA y no nos sirve. Por eso cada entrada lleva
# subcadenas obligatorias y prohibidas que se aplican sobre la descripcion.
BUSQUEDAS = {
    "RJ12":   {"q": ["RJ12", "6P6C", "modular jack"],
               "si": [], "no": []},
    "HDRF19": {"q": ["1x20P 2.54 female", "2.54 female header 1x20P"],
               "si": ["1x20P", "Female"], "no": ["2x", "Right Angle"]},
    "HDRM2":  {"q": ["1x2P 2.54 pin header"],
               "si": ["1x2P", "Pin Header"], "no": ["2x", "Right Angle"]},
    "HDRM4":  {"q": ["1x4P 2.54 pin header"],
               "si": ["1x4P", "Pin Header"], "no": ["2x", "Right Angle"]},
    "HDRM10": {"q": ["1x10P 2.54 pin header"],
               "si": ["1x10P", "Pin Header"], "no": ["2x", "Right Angle"]},
    "HDRM12": {"q": ["1x12P 2.54 pin header"],
               "si": ["1x12P", "Pin Header"], "no": ["2x", "Right Angle"]},
    "HDRM16": {"q": ["1x16P 2.54 pin header"],
               "si": ["1x16P", "Pin Header"], "no": ["2x", "Right Angle"]},
}


def consultar(termino, limite=6):
    url = API + "?" + urllib.parse.urlencode({"q": termino, "limit": limite})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except Exception as e:
        return None, str(e)
    items = d.get("components", []) if isinstance(d, dict) else d
    return items, None


def tipo_montaje(texto):
    t = texto or ""
    if "插件" in t or "Through" in t or "THT" in t:
        return "PASANTE"
    if "贴片" in t or "SMD" in t:
        return "smd"
    return "?"


def mostrar(clave, cfg):
    print(f"\n{'=' * 72}")
    print(f"  {clave}")
    print("=" * 72)

    terminos = cfg["q"]
    for termino in terminos:
        items, err = consultar(termino, limite=40)
        if err:
            print(f"  [{termino}] error de red: {err}")
            continue
        if not items:
            print(f"  [{termino}] sin resultados")
            continue

        # Filtrar: la busqueda difusa trae mucho que no sirve
        utiles = []
        for c in items:
            d = str(c.get("description") or "") + " " + str(c.get("mfr") or "")
            if any(x.lower() not in d.lower() for x in cfg["si"]):
                continue
            if any(x.lower() in d.lower() for x in cfg["no"]):
                continue
            utiles.append(c)
        if not utiles:
            print(f"  [{termino}] {len(items)} resultados, ninguno pasa el filtro")
            continue

        print(f"  [{termino}]  ({len(utiles)} de {len(items)} pasan el filtro)")
        for c in utiles[:6]:
            desc = str(c.get("description") or "")
            mont = tipo_montaje(desc + str(c.get("package") or ""))
            marca = "  <<<" if mont == "PASANTE" else ""
            print(f"    C{c.get('lcsc'):<10} {str(c.get('mfr'))[:26]:26} "
                  f"{mont:8} stock={str(c.get('stock') or '?'):>9}{marca}")
            if desc:
                print(f"       {desc[:88]}")
        return True   # con que un termino de resultados, alcanza
    return False


def main():
    # Que falta, leido de generar-netlist.py. Se lee como texto porque el
    # nombre del modulo tiene guion y no se puede importar.
    import re
    from pathlib import Path
    src = (Path(__file__).parent / "generar-netlist.py").read_text(encoding="utf-8")
    pendientes = set(re.findall(r'"(\w+)":\s*\{"lcsc": PENDIENTE', src))

    pedidos = [a.upper() for a in sys.argv[1:]]
    claves = pedidos if pedidos else [k for k in BUSQUEDAS if k in pendientes]

    if not claves:
        print("No queda ningun componente pendiente.")
        return

    print(f"Buscando {len(claves)} componente(s) en jlcsearch...")
    print("Las lineas marcadas <<< son PASANTES, que es lo que necesitamos.")

    sin_resultados = []
    for clave in claves:
        if clave not in BUSQUEDAS:
            print(f"\n  {clave}: no hay terminos de busqueda definidos")
            continue
        if not mostrar(clave, BUSQUEDAS[clave]):
            sin_resultados.append(clave)

    if sin_resultados:
        print(f"\n{'=' * 72}")
        print("  SIN RESULTADOS - buscar a mano en lcsc.com")
        print("=" * 72)
        for k in sin_resultados:
            print(f"    {k}")
        print("\n  jlcsearch solo indexa el catalogo de ensamblado de JLCPCB,")
        print("  que no cubre todos los conectores pasantes de LCSC.")


if __name__ == "__main__":
    main()
