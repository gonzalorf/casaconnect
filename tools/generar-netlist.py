"""Genera los netlists JSON para importar en EasyEDA Pro.

Produce dos archivos, uno por placa:
    netlist/placa-a-control.json
    netlist/placa-b-entradas.json

USO
---
1. Completar los numeros LCSC en el diccionario PARTS de abajo.
   Buscarlos en https://www.lcsc.com  (el "C-number", ej: C25804)
2. Correr:  python tools/generar-netlist.py
3. En EasyEDA Pro: instalar la extension "eext-generate-schematic-from-netlist"
   desde el marketplace e importar cada JSON.

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
# Reemplazar cada PENDIENTE por el numero LCSC correspondiente.
# "que_buscar" es el texto sugerido para la busqueda en lcsc.com.

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
               "que_buscar": "BAT85 schottky diode DO-35"},
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
    "HDRM16": {"lcsc": PENDIENTE, "device": "connector", "value": "header macho 1x16",
               "que_buscar": "male pin header 1x16 2.54mm"},
    "TB2":    {"lcsc": PENDIENTE, "device": "connector", "value": "bornera 2 vias",
               "que_buscar": "screw terminal block 2 position 5.08mm PCB"},
}

# ---------------------------------------------------------------------------
# MAPA DE PINES DEL DEVKIT ESP32 38 PINES
# ---------------------------------------------------------------------------
# Indice = numero de pin del header (1..19), de arriba hacia abajo.
# "NC" = pin no conectado en este diseno.

SOCKET_IZQ = [
    "+3V3",  # 1  3V3
    "NC",    # 2  EN
    "IN11",  # 3  GPIO36 (SP)
    "IN12",  # 4  GPIO39 (SN)
    "IN9",   # 5  GPIO34
    "IN10",  # 6  GPIO35
    "IN7",   # 7  GPIO32
    "IN8",   # 8  GPIO33
    "RLY7",  # 9  GPIO25
    "RLY8",  # 10 GPIO26
    "IN6",   # 11 GPIO27
    "IN4",   # 12 GPIO14
    "NC",    # 13 GPIO12  <-- strapping critico, NO USAR
    "GND",   # 14 GND
    "RLY1",  # 15 GPIO13
    "NC",    # 16 SD2
    "NC",    # 17 SD3
    "NC",    # 18 CMD
    "+5V",   # 19 5V
]

SOCKET_DER = [
    "GND",   # 1  GND
    "RLY6",  # 2  GPIO23
    "SCL",   # 3  GPIO22
    "NC",    # 4  TXD (GPIO1) - UART0, reservado
    "NC",    # 5  RXD (GPIO3) - UART0, reservado
    "SDA",   # 6  GPIO21
    "GND",   # 7  GND
    "RLY5",  # 8  GPIO19
    "RLY4",  # 9  GPIO18
    "IN3",   # 10 GPIO5
    "RLY3",  # 11 GPIO17
    "RLY2",  # 12 GPIO16
    "IN2",   # 13 GPIO4
    "NC",    # 14 GPIO0  <-- boton BOOT
    "IN1",   # 15 GPIO2
    "IN5",   # 16 GPIO15
    "NC",    # 17 SD1
    "NC",    # 18 SD0
    "NC",    # 19 CLK
]

# Enlace entre placas: header 1x16
LINK = ["+5V", "GND", "+3V3", "GND"] + [f"IN{n}" for n in range(1, 13)]

# Entradas que llevan pull-up conmutable (GPIO 34/35/36/39 no tienen interno)
INPUTS_SIN_PULLUP_INTERNO = [9, 10, 11, 12]


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
    nl.add("J1", "TB2", {"1": "+5V_IN", "2": "GND"})
    nl.add("F1", "FUSE2A", {"1": "+5V_IN", "2": "+5V"})
    nl.add("C1", "C1000U", {"1": "+5V", "2": "GND"})
    nl.add("C2", "C100N", {"1": "+5V", "2": "GND"})
    nl.add("C3", "C100N", {"1": "+3V3", "2": "GND"})

    # --- Zocalo del DevKit ESP32 (dos tiras hembra de 19) ---
    nl.add("J2", "HDRF19", {str(i + 1): net for i, net in enumerate(SOCKET_IZQ)})
    nl.add("J3", "HDRF19", {str(i + 1): net for i, net in enumerate(SOCKET_DER)})

    # --- Pull-ups de rele: mantienen el rele APAGADO durante el boot ---
    for i in range(1, 9):
        nl.add(f"R{i}", "R10K", {"1": "+3V3", "2": f"RLY{i}"})

    # --- Header al modulo de 8 reles ---
    pines_rele = {"1": "+3V3"}
    for i in range(1, 9):
        pines_rele[str(i + 1)] = f"RLY{i}"
    pines_rele["10"] = "GND"
    nl.add("J4", "HDRM10", pines_rele)

    # --- Alimentacion de bobinas (JD-VCC del modulo de reles) ---
    nl.add("J5", "TB2", {"1": "+5V", "2": "GND"})

    # --- OLED I2C ---
    nl.add("J6", "HDRM4", {"1": "GND", "2": "+3V3", "3": "SCL", "4": "SDA"})
    nl.add("R9", "R4K7", {"1": "+3V3", "2": "SDA"})
    nl.add("R10", "R4K7", {"1": "+3V3", "2": "SCL"})

    # --- I2C de expansion (futuro MCP23017, sensores) ---
    nl.add("J7", "HDRM4", {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL"})

    # --- Enlace a la Placa B ---
    nl.add("J8", "HDRM16", {str(i + 1): net for i, net in enumerate(LINK)})

    return nl


def placa_b():
    """Entradas: jacks RJ12, PTCs, campo de patch y 12 redes de proteccion."""
    nl = Netlist("Placa B - Entradas")

    # --- Enlace a la Placa A ---
    nl.add("J1", "HDRM16", {str(i + 1): net for i, net in enumerate(LINK)})

    # --- 6 jacks RJ12, cada uno con su PTC en la linea de +5V ---
    for k in range(1, 7):
        nl.add(f"F{k}", "PTC500", {"1": "+5V", "2": f"P{k}_5V"})
        nl.add(
            f"J{k + 1}",
            "RJ12",
            {
                "1": "GND",
                "2": f"P{k}_1",
                "3": f"P{k}_2",
                "4": f"P{k}_3",
                "5": f"P{k}_4",
                "6": f"P{k}_5V",
            },
        )

    # --- Campo de patch, BLOQUE A: las 24 lineas de datos de los jacks ---
    lineas = [f"P{k}_{d}" for k in range(1, 7) for d in range(1, 5)]
    for i in range(0, 24, 2):
        nl.add(f"TB{i // 2 + 1}", "TB2", {"1": lineas[i], "2": lineas[i + 1]})

    # --- Campo de patch, BLOQUE B: las 12 entradas protegidas ---
    for i in range(0, 12, 2):
        nl.add(
            f"TB{13 + i // 2}",
            "TB2",
            {"1": f"INA{i + 1}", "2": f"INA{i + 2}"},
        )

    # --- Red de proteccion por entrada ---
    #
    #                        +3V3
    #                          |
    #                         [10k]  (solo IN9..IN12)
    #                          |
    #                        o-+ JP
    #                        o-+
    #                          |
    #   INAn --[1k]-- INn -----+-----> al GPIO (via enlace)
    #                  |       |
    #                [100n]  [BAT85 x2]  recorte a +3V3 y a GND
    #                  |       |
    #                 GND     GND
    #
    for n in range(1, 13):
        nl.add(f"R{n + 10}", "R1K", {"1": f"INA{n}", "2": f"IN{n}"})
        nl.add(f"C{n}", "C100N", {"1": f"IN{n}", "2": "GND"})
        # Recorte: anodo a la senal, catodo a +3V3 (conduce si sube de 3.6 V)
        nl.add(f"D{n}A", "BAT85", {"1": f"IN{n}", "2": "+3V3"})
        # Recorte: anodo a GND, catodo a la senal (conduce si baja de -0.3 V)
        nl.add(f"D{n}B", "BAT85", {"1": "GND", "2": f"IN{n}"})

    # --- Pull-ups conmutables para las entradas sin pull-up interno ---
    for idx, n in enumerate(INPUTS_SIN_PULLUP_INTERNO, start=1):
        nl.add(f"R{idx + 30}", "R10K", {"1": "+3V3", "2": f"PU{n}"})
        nl.add(f"JP{idx}", "HDRM2", {"1": f"PU{n}", "2": f"IN{n}"})

    return nl


def main():
    destino = Path(__file__).parent / "netlist"
    destino.mkdir(exist_ok=True)

    faltantes = [k for k, v in PARTS.items() if v["lcsc"] == PENDIENTE]

    for nl, archivo in [
        (placa_a(), "placa-a-control.json"),
        (placa_b(), "placa-b-entradas.json"),
    ]:
        ruta = destino / archivo
        cantidad = nl.dump(ruta)
        print(f"{nl.nombre:24}  {cantidad:3} componentes  ->  {ruta}")

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
