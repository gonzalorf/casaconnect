"""Genera los netlists en formato KiCad (.net) para importar en Pcbnew.

A diferencia de la version para EasyEDA, esta NO depende de ninguna
libreria externa ni de numeros de proveedor: usa los simbolos y huellas
que vienen con KiCad.

    python tools/generar-netlist-kicad.py

Produce:
    netlist/placa-a-control.net
    netlist/placa-b-entradas.net

COMO IMPORTARLO
---------------
No hace falta dibujar el esquematico. En KiCad:

    1. Abrir el editor de PCB (Pcbnew) con un archivo .kicad_pcb nuevo
    2. File > Import > Netlist...
    3. Elegir el .net, dejar "Update PCB" y aceptar

Los componentes aparecen apilados con sus huellas y el ratsnest (las
lineas finas) mostrando todas las conexiones. De ahi se acomodan y se
rutea.

SOBRE LAS HUELLAS
-----------------
Todos los nombres estan verificados contra la instalacion real de KiCad.
Al generar, el script los vuelve a chequear uno por uno y aborta si
alguno no existe o le falta un pad que el netlist usa. Los nombres
cambian entre versiones, asi que la verificacion corre siempre.
"""

import datetime
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verificar_huellas import verificar  # noqa: E402

AQUI = Path(__file__).parent


def cargar_diseno():
    """Importa generar-netlist.py, cuyo nombre tiene guion."""
    spec = importlib.util.spec_from_file_location("diseno", AQUI / "generar-netlist.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# MAPEO A LA LIBRERIA DE KICAD
# ---------------------------------------------------------------------------
# (simbolo, huella, hay_que_verificar)
#
# Para los conectores uso Connector_Generic:Conn_01xNN en vez de simbolos
# especificos: existen siempre, tienen la cantidad de pines correcta y
# numerados 1..N, que es justo lo que necesita el netlist.

HUELLAS = {
    "R10K":   ("Device:R", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", False),
    "R1K":    ("Device:R", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", False),
    "R4K7":   ("Device:R", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", False),
    "C100N":  ("Device:C", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm", False),
    "C1000U": ("Device:C_Polarized", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", False),
    "BAT85":  ("Device:D_Schottky", "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal", False),

    # El PTC radial no tiene huella dedicada en KiCad. Un disco de 2 patas
    # con paso 5 mm es geometricamente lo mismo.
    "PTC1A":  ("Device:Polyfuse", "Capacitor_THT:C_Disc_D7.5mm_W2.5mm_P5.00mm", False),
    "PTC500": ("Device:Polyfuse", "Capacitor_THT:C_Disc_D7.5mm_W2.5mm_P5.00mm", False),
    "FUSE2A": ("Device:Fuse", "Fuse:Fuseholder_Cylinder-5x20mm_Bulgin_FX0457"
               "_Horizontal_Closed", False),
    "RJ12":   ("Connector_Generic:Conn_01x06", "Connector_RJ:RJ12_Amphenol_54601-x06_Horizontal", False),

    "HDRF19": ("Connector_Generic:Conn_01x19",
               "Connector_PinSocket_2.54mm:PinSocket_1x19_P2.54mm_Vertical", False),
    "HDRM2":  ("Connector_Generic:Conn_01x02",
               "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", False),
    "HDRM4":  ("Connector_Generic:Conn_01x04",
               "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", False),
    "HDRM10": ("Connector_Generic:Conn_01x10",
               "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical", False),
    "HDRM12": ("Connector_Generic:Conn_01x12",
               "Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical", False),
    "HDRM20": ("Connector_Generic:Conn_01x20",
               "Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical", False),
    "TB2":    ("Connector_Generic:Conn_01x02",
               "TerminalBlock_Phoenix:TerminalBlock_Phoenix"
               "_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", False),
}


def esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def generar(nl, diseno, destino):
    """Escribe el .net en formato S-expression de KiCad."""
    fecha = datetime.date.today().isoformat()
    out = [
        '(export (version "E")',
        "  (design",
        f'    (source "{esc(nl.nombre)}")',
        f'    (date "{fecha}")',
        '    (tool "CasaConnect generar-netlist-kicad.py"))',
        "  (components",
    ]

    for i, (desig, clave, _pins) in enumerate(nl.orden, start=1):
        simbolo, huella, _ = HUELLAS[clave]
        lib, parte = simbolo.split(":", 1)
        valor = diseno.PARTS[clave]["value"]
        lcsc = diseno.PARTS[clave]["lcsc"]
        out += [
            f'    (comp (ref "{esc(desig)}")',
            f'      (value "{esc(valor)}")',
            f'      (footprint "{esc(huella)}")',
            f'      (libsource (lib "{esc(lib)}") (part "{esc(parte)}") (description ""))',
            f'      (property (name "LCSC") (value "{esc(lcsc)}"))',
            '      (sheetpath (names "/") (tstamps "/"))',
            f'      (tstamps "{i:08d}-0000-0000-0000-000000000000"))',
        ]
    out.append("  )")

    # Reunir las redes
    redes = {}
    for desig, _clave, pins in nl.orden:
        for pin, net in pins.items():
            redes.setdefault(net, []).append((desig, pin))

    out.append("  (nets")
    for codigo, net in enumerate(sorted(redes), start=1):
        out.append(f'    (net (code "{codigo}") (name "{esc(net)}")')
        for desig, pin in sorted(redes[net]):
            out.append(f'      (node (ref "{esc(desig)}") (pin "{esc(pin)}"))')
        out.append("    )")
    out += ["  )", ")"]

    destino.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(nl.orden), len(redes)


def main():
    diseno = cargar_diseno()
    destino = AQUI / "netlist"
    destino.mkdir(exist_ok=True)

    hechos = []
    for constructor, archivo in [
        (diseno.placa_a, "placa-a-control.net"),
        (diseno.placa_b, "placa-b-entradas.net"),
    ]:
        nl = constructor()
        ruta = destino / archivo
        comp, nets = generar(nl, diseno, ruta)
        print(f"{nl.nombre:24}  {comp:3} componentes · {nets:2} redes  ->  {ruta}")
        hechos.append(nl)

    print()
    if not verificar(hechos, HUELLAS):
        sys.exit(1)


if __name__ == "__main__":
    main()
