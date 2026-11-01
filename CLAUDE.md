# CasaConnect

Módulo de domótica para controlar la iluminación de una casa: **ESP32 + 8 relés +
6 puertos RJ12 de entrada**. Reemplaza un sistema anterior hecho con Arduinos viejos.

El hardware se construye a mano (PCB casera, etching, todo THT). **El diseño v1 ya
está decidido** — no hay que re-abrirlo salvo que algo falle en las pruebas.

## Convenciones

- **Todo en español**: documentación, comentarios de código y mensajes de commit.
- Los documentos de `docs/` son la fuente de verdad del diseño. Este archivo es el
  resumen; ante una discrepancia, **gana `docs/`**.
- Al proponer cambios de diseño, verificar primero contra las restricciones de abajo.

## Documentos

| Archivo | Qué contiene |
|---|---|
| [`inventario.md`](inventario.md) | 18 ítems de hardware, verificados por foto y por lectura de chip |
| [`docs/plan.md`](docs/plan.md) | **Plan de trabajo en 7 fases.** Empezar por acá |
| [`docs/configuracion-v1.md`](docs/configuracion-v1.md) | La configuración elegida |
| [`docs/circuito-v1.md`](docs/circuito-v1.md) | Esquemático, BOM y guía de construcción |
| [`docs/comparticion-rj12.md`](docs/comparticion-rj12.md) | Esquema de GPIO compartidos entre puertos |
| [`docs/lista-de-compras.md`](docs/lista-de-compras.md) | Qué hay y qué falta comprar |
| [`docs/diseno-modulo-esp32.md`](docs/diseno-modulo-esp32.md) | El análisis que respalda las decisiones |
| [`docs/placa-rj12.html`](docs/placa-rj12.html) | Vista de la placa + planificador de líneas |

## Herramientas

| Script | Para qué |
|---|---|
| `tools/identificar-esp32.py` | Lee chip, revisión, flash y MAC de una placa conectada |
| `tools/generar-netlist.py` | Genera los netlists JSON para EasyEDA Pro |
| `tools/reportes/` | Salida cruda de esptool de cada DevKit |

---

## Hardware

**Microcontrolador (elegido: MCU-001).** NodeMCU ESP-32S v1.1 ·
**ESP32-D0WD-V3 rev v3.1** · 4 MB flash · **sin PSRAM** · MAC `84:1f:e8:2b:24:5c`.
MCU-002 es idéntica y queda de repuesto.

> **La serigrafía usa otros nombres:** `GPIO27` aparece como **`P27`**, `GPIO36` como
> **`SVP`** y `GPIO39` como **`SVN`**.

**Otros:** módulo relé 8 canales (SRD-05VDC-SL-C, optoacoplado, activo-LOW) ·
2× PIR HC-SR501 · módulo LDR con LM393 · OLED SSD1306 128×64 I²C ·
fuente switching 5 V / 2 A.

**Fuera de la v1:** Arduino Pro Mini · relé 4 canales · MQ-7 (CO) · LM2596 · MT3608 ·
TXS0108E · 2× CD74HC4051E.

---

## Mapa de pines — decidido, no cambiar sin motivo

### Salidas: 8 relés

```
R1=13   R2=16   R3=17   R4=18   R5=19   R6=23   R7=25   R8=26
```

Cada uno con **pull-up de 10 kΩ a 3.3 V** (ver restricciones).

### Bus I²C

`GPIO21` = SDA · `GPIO22` = SCL → OLED (`0x3C`). **Es la vía de crecimiento del
módulo**: un MCP23017 entra ahí sin tocar nada más. No sacrificarlo.

### Entradas: 12 GPIO para 24 líneas RJ12

Los 6 puertos van en **una sola fila**, agrupados en parejas contiguas:
`P1 P4 · P2 P5 · P3 P6`. Cada GPIO se cablea a la **misma línea** de los dos puertos
de su pareja.

| Línea | Pareja A (P1,P4) | Pareja B (P2,P5) | Pareja C (P3,P6) | Tipo |
|---|---|---|---|---|
| **L1** | `GPIO2` | `GPIO5` | `GPIO15` | Digital, pull-up interno |
| **L2** | `GPIO4` | `GPIO14` | `GPIO27` | Digital, pull-up interno |
| **L3** | `GPIO32` | `GPIO33` | `GPIO36` | ADC (36 es solo-entrada) |
| **L4** | `GPIO34` | `GPIO35` | `GPIO39` | ADC, **solo-entrada** |

**Regla de uso:** dentro de una pareja se pueden usar **4 líneas en total**, y nunca
la misma línea en ambos puertos. Un puerto puede quedarse con las 4; su compañero
queda entonces en cero.

### Asignación actual (9 de 12 en uso)

| Señal | Puerto · línea | GPIO |
|---|---|---|
| Botón 1 · Botón 2 · PIR 1 | P1 · L1 L2 L3 | `2` `4` `32` |
| Botón 3 · Botón 4 · PIR 2 | P2 · L1 L2 L3 | `5` `14` `33` |
| Botón 5 · Botón 6 | P3 · L1 L2 | `15` `27` |
| Sensor de luz (`AO`) | P6 · L3 | `36` |
| **Libres** | una por pareja | `34` `35` `39` |

---

## Restricciones — violarlas produce fallas reales

| # | Regla | Si se viola |
|---|---|---|
| 1 | **Nunca** usar GPIO 6-11 (`SD0` `SD1` `SD2` `SD3` `CMD` `CLK`) | Están en la flash SPI interna |
| 2 | **Nunca** usar GPIO 12 | Strapping: en HIGH al arrancar, la placa **no bootea** |
| 3 | Analógico **solo** en ADC1 (`32` `33` `34` `35` `36` `39`) | ADC2 no funciona con WiFi activo, y el WiFi está siempre activo |
| 4 | GPIO `34` `35` `36` `39` **no tienen pull-up interno** | Un botón ahí lee basura sin resistencia externa |
| 5 | Pull-up de 10 kΩ en **cada** línea de relé | Los módulos son activo-LOW: sin pull-up los 8 relés se activan ~300 ms en **cada** reset |
| 6 | Módulo de relés: jumper JD-VCC **fuera**, `VCC`=3.3 V, `JD-VCC`=5 V | 3.3 V contra un riel de 5 V puede no apagar el relé de forma confiable |
| 7 | Recorte de entradas: **Schottky** (BAT85/BAT43/1N5819), nunca 1N4148 | El de silicio recorta en 4.0 V, por encima del máximo del ESP32 (3.6 V) — y después del diodo interno, así que no haría nada |
| 8 | Cables RJ12 **derechos**, verificados con continuidad, + PTC en el 5 V | Los telefónicos comunes son cruzados: ponen 5 V contra GND |
| 9 | Masa **en estrella**: el retorno de las bobinas va directo a la fuente | 560 mA compartiendo pista con el GND del ESP32 corren las lecturas del ADC |
| 10 | Nunca USB y fuente externa a la vez en el pin `5V` | En muchos DevKit ese pin va directo al VBUS del USB |
| 11 | Footprint sin poblar: **en serie** → puentear · **en paralelo** → dejar vacío | Puentear un paralelo cortocircuita el riel |

---

## Firmware

**Sin protocolo de comunicación en la v1.** WiFi solo para **OTA** y **NTP**.
MQTT/HTTP quedan para la etapa 2.

Orden de implementación (ver `docs/plan.md` §Fase 2):

1. **Tabla de particiones + OTA** — va primero. Cambiarla después obliga a reflashear
   por USB, que es justo lo que OTA evita. Con 4 MB quedan ~1.3 MB por slot.
2. WiFi + NTP
3. Lógica botón → relé, **local y sin red** (tiene que andar con el WiFi caído)
4. Antirrebote + pulsación larga (gesto de "mostrar estado")
5. OLED guiado por eventos
6. PIR con **supresión del primer minuto** (el HC-SR501 da falsos positivos al arrancar)
7. Sensor de luz con umbral por software
8. Persistir el estado de los relés

**Reglas de firmware:**

- **Actualizar el OLED después de accionar el relé, nunca antes.** Un refresco completo
  del SSD1306 son ~25 ms y se los sumarías a cada pulsación.
- El OLED se enciende con cada evento y se apaga solo a los 10 s. Eso resuelve el
  *burn-in* sin hacer nada más.
- La lógica botón → relé no debe depender de la red en ningún punto.

Entorno: **Arduino IDE** con core **esp32 3.3.11** ya instalado.
`esptool 5.6.0` y `pyserial` instalados. Driver CP210x 11.6.0.420 instalado; el DevKit
enumera en **COM7**.

---

## Estado actual

**Fase 1 en curso** — prototipo en protoboard. Los pines macho ya están soldados a
MCU-001.

**Tests 1.1 y 1.2 pasados** (1 canal cableado): el relé conmuta limpio con 3.3 V y
**el pull-up de 10 kΩ evita el disparo en el arranque** — 20+ resets sin activación.
Ese valor queda decidido.

Queda un test que puede cambiar el circuito:

- **Test 1.6** — si el capacitor de 1000 µF no evita el reset al conmutar los 8 relés
  a la vez, hay que repensar la distribución de alimentación. Requiere los 8 canales
  cableados, y **solo vale si el ESP32 y las bobinas comparten el riel de 5 V**
  (USB desconectado); si no, pasa siempre sin significar nada.

Tareas de desbloqueo abiertas (ver `docs/plan.md` §Fase 0):

- [ ] Buscar los 15 números LCSC para el netlist (**irreversible**: un número
      equivocado carga un componente incorrecto que no se puede corregir)
- [ ] Medir con calibre la separación entre filas del DevKit (22.86 mm vs 25.4 mm)
- [ ] Identificar el género de PRO-003 (tira de pines) y PRO-004 (Dupont)
- [ ] Regenerar los netlists con el esquema de parejas (el script todavía produce la
      versión con campo de patch)
- [ ] Decidir: ¿el sistema viejo de Arduino convive o se reemplaza?
