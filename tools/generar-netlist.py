"""Genera los netlists JSON para importar en EasyEDA Pro.

Produce dos archivos, uno por placa:
    netlist/placa-a-control.json
    netlist/placa-b-entradas.json

Refleja el diseno v1 con COMPARTICION DE GPIO entre parejas de puertos
(sin campo de patch). Ver docs/comparticion-rj12.md.

USO
---
1. Completar los numeros LCSC en el diccionario PARTS de abajo.
   Buscarlos en https://www.lcsc.com  (el "C-number", ej: C25804)
2. Correr:  python tools/generar-netlist.py
3. En EasyEDA Pro: instalar la extension "eext-generate-schematic-from-netlist"
   desde el marketplace e importar cada JSON en un proyecto separado.

ADVERTENCIA
-----------
EasyEDA resuelve los componentes UNICAMENTE por el numero LCSC. Un numero
equivocado carga un componente incorrecto y no se puede corregir despues de
importar. Verificar cada uno antes de generar.
"""

import json
from pathlib import Path

PENDIENTE = "PENDIENTE"

# ---------------------------------------------------------------------------
# CATALOGO DE COMPONENTES  <-- EDITAR SOLO ESTO
# ---------------------------------------------------------------------------

PARTS = {
    "R10K":   {"lcsc": PENDIENTE, "device": "resistor",  "value": "10k",
               "que_buscar": "resistor 10k 1/4W axial through hole"},
    "R1K":    {"lcsc": PENDIENTE, "device": "resistor",  "value": "1k",
               "que_buscar": "resistor 1k 1/4W axial through hole"},
    "R4K7":   {"lcsc": PENDIENTE, "device": "resistor",  "value": "4.7k",
               "que_buscar": "resistor 4.7k 1/4W axial through hole"},
    "C100N":  {"lcsc": PENDIENTE, "device": "capacitor", "value": "100nF",
               "que_buscar": "capacitor 100nF 50V ceramic through hole 2.54mm"},
    "C1000U": {"lcsc": PENDIENTE, "device": "capacitor", "value": "1000uF 16V",
               "que_buscar": "electrolytic capacitor 1000uF 16V radial"},
    "BAT85":  {"lcsc": PENDIENTE, "device": "diode",     "value": "BAT85",
               "que_buscar": "BAT85 schottky diode DO-35 (o BAT43 / 1N5819)"},
    "PTC1A":  {"lcsc": PENDIENTE, "device": "fuse",      "value": "PTC 1A",
               "que_buscar": "resettable fuse PTC 1A 30V radial"},
    "PTC500": {"lcsc": PENDIENTE, "device": "fuse",      "value": "PTC 500mA",
               "que_buscar": "resettable fuse PTC 500mA 30V radial"},
    "FUSE2A": {"lcsc": PENDIENTE, "device": "fuse",      "value": "2A",
               "que_buscar": "fuse holder 5x20mm PCB mount + fuse 2A"},
    "RJ12":   {"lcsc": PENDIENTE, "device": "connector", "value": "RJ12 6P6C",
               "que_buscar": "RJ12 6P6C jack PCB mount through hole"},
    "HDRF19": {"lcsc": PENDIENTE, "device": "connector", "value": "header hembra 1x19",
               "que_buscar": "female header 1x20 2.54mm (cortar a 19)"},
    "HDRM2":  {"lcsc": PENDIENTE, "device": "connector", "value": "header macho 1x2",
               "que_buscar": "male pin header 1x2 2.54mm"},
    "HDRM4":  {"lcsc": PENDIENTE, "device": "connector", "value": "header macho 1x4",
               "que_buscar": "male pin header 1x4 2.54mm"},
    "HDRM10": {"lcsc": PENDIENTE, "device": "connector", "value": "header macho 1x10",
               "que_buscar": "male pin header 1x10 2.54mm"},
    "HDRM12": {"lcsc": PENDIENTE, "device": "connector", "value": "header macho 1x12",
               "que_buscar": "male pin header 1x12 2.54mm"},
    "HDRM16": {"lcsc": PENDIENTE, "device": "connector", "value": "header macho 1x16",
               "que_buscar": "male pin header 1x16 2.54mm"},
    "TB2":    {"lcsc": PENDIENTE, "device": "connector", "value": "bornera 2 vias",
               "que_buscar": "screw terminal block 2 position 5.08mm PCB"},
}

# ---------------------------------------------------------------------------
# ESQUEMA DE COMPARTICION
# ---------------------------------------------------------------------------
# Los 6 jacks van en UNA SOLA FILA, con los companeros contiguos:
#     P1 P4  ·  P2 P5  ·  P3 P6
# Cada GPIO se cablea a la MISMA linea de los dos puertos de su pareja.

PAREJAS = [
    {"tag": "A", "puertos": ("P1", "P4"), "gpios": (2,  4,  32, 34)},
    {"tag": "B", "puertos": ("P2", "P5"), "gpios": (5,  14, 33, 35)},
    {"tag": "C", "puertos": ("P3", "P6"), "gpios": (15, 27, 36, 39)},
]

# Sin pull-up interno: llevan uno externo de 10k conmutable por jumper.
SIN_PULLUP_INTERNO = (34, 35, 36, 39)

# Orden fisico de los jacks en la placa, de izquierda a derecha.
ORDEN_JACKS = ["P1", "P4", "P2", "P5", "P3", "P6"]

# Los 12 GPIO de entrada, en el orden en que viajan por el cable plano.
GPIOS_ENTRADA = [g for p in PAREJAS for g in p["gpios"]]

# Nombres de red
def net_crudo(gpio):     return f"RJ_{gpio}"   # del jack, antes de proteger
def net_limpio(gpio):    return f"IN_{gpio}"   # ya protegido, al ESP32

# Enlace entre placas: header 1x16
LINK = ["+5V", "GND", "+3V3", "GND"] + [net_limpio(g) for g in GPIOS_ENTRADA]

# ---------------------------------------------------------------------------
# MAPA DE PINES DEL DEVKIT ESP32 38 PINES
# ---------------------------------------------------------------------------
# Indice = numero de pin del header (1..19), de arriba hacia abajo.

SOCKET_IZQ = [
    "+3V3",            # 1  3V3
    "NC",              # 2  EN
    net_limpio(36),    # 3  GPIO36 (SVP)
    net_limpio(39),    # 4  GPIO39 (SVN)
    net_limpio(34),    # 5  GPIO34
    net_limpio(35),    # 6  GPIO35
    net_limpio(32),    # 7  GPIO32
    net_limpio(33),    # 8  GPIO33
    "RLY7",            # 9  GPIO25
    "RLY8",            # 10 GPIO26
    net_limpio(27),    # 11 GPIO27
    net_limpio(14),    # 12 GPIO14
    "NC",              # 13 GPIO12  <-- strapping critico, NO USAR
    "GND",             # 14 GND
    "RLY1",            # 15 GPIO13
    "NC",              # 16 SD2
    "NC",              # 17 SD3
    "NC",              # 18 CMD
    "+5V",             # 19 5V
]

SOCKET_DER = [
    "GND",             # 1  GND
    "RLY6",            # 2  GPIO23
    "SCL",             # 3  GPIO22
    "NC",              # 4  TXD (GPIO1) - UART0, reservado
    "NC",              # 5  RXD (GPIO3) - UART0, reservado
    "SDA",             # 6  GPIO21
    "GND",             # 7  GND
    "RLY5",            # 8  GPIO19
    "RLY4",            # 9  GPIO18
    net_limpio(5),     # 10 GPIO5
    "RLY3",            # 11 GPIO17
    "RLY2",            # 12 GPIO16
    net_limpio(4),     # 13 GPIO4
    "NC",              # 14 GPIO0  <-- boton BOOT
    net_limpio(2),     # 15 GPIO2
    net_limpio(15),    # 16 GPIO15
    "NC",              # 17 SD1
    "NC",              # 18 SD0
    "NC",              # 19 CLK
]


class Netlist:
    """Acumula componentes y los emite con claves gge# secuenciales."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.items = {}
        self.n = 0

    def add(self, designator, part_key, pins):
        """pins: dict {numero_de_pin(str): nombre_de_net}. 'NC' se omite."""
        part = PARTS[part_key]
        self.n += 1
        self.items[f"gge{self.n}"] = {
            "props": {
                "Designator": designator,
                "device_name": part["device"],
                "value": part["value"],
                "Supplier Part": part["lcsc"],
            },
            "pins": {p: net for p, net in pins.items() if net != "NC"},
        }

    def dump(self, destino):
        destino.write_text(
            json.dumps(self.items, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return self.n


def placa_a():
    """Control: zocalo ESP32, alimentacion, pull-ups de rele, OLED, enlace."""
    nl = Netlist("Placa A - Control")

    # --- Alimentacion ---
    nl.add("J1", "TB2",    {"1": "+5V_IN", "2": "GND"})
    nl.add("F1", "FUSE2A", {"1": "+5V_IN", "2": "+5V"})
    nl.add("C1", "C1000U", {"1": "+5V",    "2": "GND"})
    nl.add("C2", "C100N",  {"1": "+5V",    "2": "GND"})
    nl.add("C3", "C100N",  {"1": "+3V3",   "2": "GND"})

    # --- Zocalo del DevKit ESP32 ---
    #
    # TRES tiras hembra de 19, no dos. Las dos placas que tenemos miden
    # distinto entre filas: MCU-001 = 0.9" (22.86 mm) y MCU-002 = 1.0"
    # (25.4 mm). Con la fila izquierda fija, las dos opciones de la derecha
    # quedan a 2.54 mm una de otra -- justo el ancho del cuerpo de una tira,
    # asi que entran pegadas.
    #
    # J3 y J3B van cableadas en paralelo pin a pin: entra cualquiera de las
    # dos placas. La tira que queda libre sirve de fila de puntos de prueba.
    #
    #        J2            J3 (0.9")  J3B (1.0")
    #         |                 |  |
    #         o---- 22.86 mm ---o  o
    #         o------- 25.4 mm ----o
    #
    nl.add("J2",  "HDRF19", {str(i + 1): n for i, n in enumerate(SOCKET_IZQ)})
    nl.add("J3",  "HDRF19", {str(i + 1): n for i, n in enumerate(SOCKET_DER)})
    nl.add("J3B", "HDRF19", {str(i + 1): n for i, n in enumerate(SOCKET_DER)})

    # --- Pull-ups de rele: mantienen el rele APAGADO durante el boot ---
    for i in range(1, 9):
        nl.add(f"R{i}", "R10K", {"1": "+3V3", "2": f"RLY{i}"})

    # --- Header al modulo de 8 reles ---
    pines = {"1": "+3V3"}
    for i in range(1, 9):
        pines[str(i + 1)] = f"RLY{i}"
    pines["10"] = "GND"
    nl.add("J4", "HDRM10", pines)

    # --- Alimentacion de bobinas (JD-VCC del modulo de reles) ---
    nl.add("J5", "TB2", {"1": "+5V", "2": "GND"})

    # --- OLED I2C ---
    nl.add("J6",  "HDRM4", {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"})
    nl.add("R9",  "R4K7",  {"1": "+3V3", "2": "SDA"})
    nl.add("R10", "R4K7",  {"1": "+3V3", "2": "SCL"})

    # --- I2C de expansion (futuro MCP23017, sensores) ---
    nl.add("J7", "HDRM4", {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL"})

    # --- Enlace a la Placa B ---
    nl.add("J8", "HDRM16", {str(i + 1): n for i, n in enumerate(LINK)})

    return nl


def placa_b():
    """Entradas: jacks RJ12 con GPIO compartidos y 12 redes de proteccion."""
    nl = Netlist("Placa B - Entradas")

    # --- Enlace a la Placa A ---
    nl.add("J1", "HDRM16", {str(i + 1): n for i, n in enumerate(LINK)})

    # --- PTC comun del riel de 5 V de los puertos (poblado en la v1) ---
    nl.add("F0", "PTC1A", {"1": "+5V", "2": "+5V_PUERTOS"})

    # --- 6 jacks RJ12 ---
    #
    #   Cada pareja comparte sus 4 GPIO: la linea L(n) de los DOS puertos
    #   va a la misma red. Esa es toda la compartición, no hay nada mas.
    #
    #   pin 1 = GND · pines 2-5 = lineas L1..L4 · pin 6 = +5V (via PTC)
    #
    ref_jack, ref_ptc = 2, 1
    for nombre in ORDEN_JACKS:
        pareja = next(p for p in PAREJAS if nombre in p["puertos"])

        # PTC por puerto: footprint presente, puenteado con alambre en la v1
        nl.add(f"F{ref_ptc}", "PTC500",
               {"1": "+5V_PUERTOS", "2": f"{nombre}_5V"})

        pines = {"1": "GND", "6": f"{nombre}_5V"}
        for linea in range(1, 5):
            pines[str(linea + 1)] = net_crudo(pareja["gpios"][linea - 1])
        nl.add(f"J{ref_jack}", "RJ12", pines)

        ref_jack += 1
        ref_ptc += 1

    # --- Red de proteccion, una por GPIO de entrada ---
    #
    #                        +3V3
    #                          |
    #                         [10k]   (solo los sin pull-up interno)
    #                          |
    #                        o-+ JP
    #                        o-+
    #                          |
    #   RJ_n --[1k]-- IN_n ----+----> al enlace con la Placa A
    #                  |       |
    #                [100n]  [BAT85 x2]  recorte a +3V3 y a GND
    #                  |       |
    #                 GND     GND
    #
    ref_pu = 1
    for i, gpio in enumerate(GPIOS_ENTRADA, start=1):
        crudo, limpio = net_crudo(gpio), net_limpio(gpio)
        nl.add(f"R{i}",   "R1K",   {"1": crudo,  "2": limpio})
        nl.add(f"C{i}",   "C100N", {"1": limpio, "2": "GND"})
        # Recorte: anodo a la senal, catodo a +3V3 (conduce si sube de 3.6 V)
        nl.add(f"D{i}A",  "BAT85", {"1": limpio, "2": "+3V3"})
        # Recorte: anodo a GND, catodo a la senal (conduce si baja de -0.3 V)
        nl.add(f"D{i}B",  "BAT85", {"1": "GND",  "2": limpio})

        if gpio in SIN_PULLUP_INTERNO:
            nl.add(f"R{30 + ref_pu}", "R10K",  {"1": "+3V3", "2": f"PU_{gpio}"})
            nl.add(f"JP{ref_pu}",     "HDRM2", {"1": f"PU_{gpio}", "2": limpio})
            ref_pu += 1

    # --- Salida de emergencia: los 12 GPIO accesibles, sin poblar ---
    nl.add("J8", "HDRM12",
           {str(i + 1): net_limpio(g) for i, g in enumerate(GPIOS_ENTRADA)})

    return nl


def main():
    destino = Path(__file__).parent / "netlist"
    destino.mkdir(exist_ok=True)

    for nl, archivo in [
        (placa_a(), "placa-a-control.json"),
        (placa_b(), "placa-b-entradas.json"),
    ]:
        ruta = destino / archivo
        print(f"{nl.nombre:24}  {nl.dump(ruta):3} componentes  ->  {ruta}")

    faltantes = [k for k, v in PARTS.items() if v["lcsc"] == PENDIENTE]
    if faltantes:
        print(f"\n!!  Faltan {len(faltantes)} numeros LCSC. NO importar todavia:\n")
        ancho = max(len(k) for k in faltantes)
        for k in faltantes:
            print(f"    {k:<{ancho}}  buscar: {PARTS[k]['que_buscar']}")
        print("\n    Completalos en PARTS y volve a correr este script.")
    else:
        print("\nOK: todos los componentes tienen numero LCSC.")


if __name__ == "__main__":
    main()
