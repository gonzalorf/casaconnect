"""Identifica una placa ESP32 conectada por USB y guarda el reporte.

Uso:  python tools/identificar-esp32.py [etiqueta]

Detecta el puerto COM automaticamente. Si hay mas de uno, los lista y sale.
El reporte queda en tools/reportes/<etiqueta>.txt para volcarlo al inventario.
"""
import subprocess
import sys
from pathlib import Path

try:
    from serial.tools import list_ports
except ImportError:
    sys.exit("Falta pyserial. Instalalo con: python -m pip install pyserial")

REPORTES = Path(__file__).parent / "reportes"


def detectar_puerto():
    puertos = list(list_ports.comports())
    if not puertos:
        sys.exit(
            "No se detecto ningun puerto COM.\n"
            "  - Revisa que el cable USB sea de datos, no solo de carga.\n"
            "  - Si no aparece, falta el driver CP210x de Silicon Labs."
        )
    if len(puertos) > 1:
        print("Hay varios puertos conectados:")
        for p in puertos:
            print(f"  {p.device}  {p.description}")
        sys.exit("Deja conectada una sola placa y volve a correr el script.")
    return puertos[0]


def main():
    etiqueta = sys.argv[1] if len(sys.argv) > 1 else "placa"
    puerto = detectar_puerto()
    print(f"Puerto detectado: {puerto.device}  ({puerto.description})\n")

    resultado = subprocess.run(
        [sys.executable, "-m", "esptool", "--port", puerto.device, "flash-id"],
        capture_output=True,
        text=True,
    )
    salida = resultado.stdout + resultado.stderr
    print(salida)

    if resultado.returncode != 0:
        sys.exit(
            "esptool no pudo comunicarse con la placa.\n"
            "  Probá manteniendo apretado BOOT mientras arranca la conexion."
        )

    REPORTES.mkdir(exist_ok=True)
    destino = REPORTES / f"{etiqueta}.txt"
    destino.write_text(
        f"Puerto: {puerto.device} ({puerto.description})\n\n{salida}",
        encoding="utf-8",
    )
    print(f"Reporte guardado en: {destino}")


if __name__ == "__main__":
    main()
