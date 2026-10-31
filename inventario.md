# Inventario de Componentes Electrónicos — CasaConnect

> Catálogo de componentes disponibles para el proyecto.
> Última actualización: 2026-10-31

## Resumen

| Categoría | Ítems distintos | Unidades totales |
|---|---:|---:|
| Microcontroladores y SBC | 3 | 3 |
| Sensores | 3 | 4 |
| Alimentación | 2 | 2 |
| Pantallas e Interfaz | 1 | 1 |
| Actuadores y Salidas | 2 | 2 |
| Prototipado, Cables y Herramientas | 6 | ~106 |
| **Total** | **17** | **~118** |

---

## Microcontroladores y SBC

| ID | Componente | Modelo / Chip | Cant. | Detalles clave | Notas |
|---|---|---|---:|---|---|
| MCU-001 | **NodeMCU ESP-32S v1.1** (serigrafía `ESP-32S V1.1 101010`) | **ESP32-D0WD-V3 rev v3.1** · 4 MB flash · sin PSRAM · MAC `84:1f:e8:2b:24:5c` | 1 | Dual core + LP core 240 MHz · WiFi + BT · cristal 40 MHz · Vref calibrada en eFuse | USB-UART **Silabs CP2102** (FPC03X 2433+) · micro-USB · botones **EN** y **BOOT**. ✅ **Pines macho ya soldados** (2026-10-31). Pinout serigrafiado en la cara inferior, verificado — idéntico a MCU-002. **Elegida para la v1.** |
| MCU-002 | DevKit ESP32 38 pines | **ESP32-D0WD-V3 rev v3.1** · 4 MB flash · sin PSRAM · MAC `d4:e9:f4:64:c5:54` | 1 | Dual core + LP core 240 MHz · WiFi + BT · cristal 40 MHz · Vref calibrada en eFuse | Variante de serigrafía: botones **RST** y **BOOT**, 4 agujeros de montaje en esquinas. Regulador **AMS1117-3.3** (`1117 33 e447`) · CP2102 (FPC03X 2433+) · Q1/Q2 **J3Y (S8050)** para auto-reset · cap. 10 µF 16 V. **Pinout completo verificado — ver apéndice.** |

| MCU-003 | Arduino Pro Mini | **ATmega328P-AU** (date code `1437`) | 1 | 8-bit AVR 16 MHz · 32 KB flash · 2 KB SRAM · 1 KB EEPROM | Regulador marcado `LG50` → **variante 5 V / 16 MHz** (*a confirmar midiendo VCC*). **Sin USB**: se programa con el adaptador FTDI (PRO-005). 14 I/O digitales + **8 entradas analógicas** (A0-A7). Todos los digitales con pull-up interno. |

> ✅ **Confirmado por el usuario (2026-10-31):** las dos ESP32 son **placas físicas distintas**, no la misma fotografiada dos veces.
>
> ✅ **Ambas identificadas por hardware** (ver Apéndice C). Son **funcionalmente idénticas** e intercambiables; solo difieren en serigrafía y MAC.

## Sensores

| ID | Componente | Modelo | Cant. | Salidas / Interfaz | Notas |
|---|---|---|---:|---|---|
| SEN-001 | Módulo sensor de luz (LDR) | LDR + comparador **LM393** | 1 | `VCC` `GND` `DO` `AO` | Doble salida: **AO** analógica y **DO** digital con umbral por trimpot (`3362`). LEDs de power y de disparo. ✅ **Alimentar a 3.3 V** y ambas salidas quedan seguras para el ESP32 |
| SEN-002 | Sensor de **monóxido de carbono** | **MQ-7**, placa `Flying-Fish` | 1 | `VCC` `GND` `DO` `AO` | ⚠️ Requiere **ciclado del calefactor** (60 s @ 5 V / 90 s @ 1.4 V) para dar lecturas válidas — ver diseño §3.quinquies. AO y DO salen a ~5 V: **divisor resistivo obligatorio**. ~150 mA |
| SEN-003 | Sensor de movimiento PIR | **HC-SR501** (lote `082025-1456`) | 2 | `VCC` `GND` `OUT` | Alimentación 4.5-20 V · **salida 3.3 V → conexión directa al ESP32, segura** ✅ · 2 trimpots (sensibilidad 3-7 m, retardo 5 s-300 s) · jumper H/L (disparo repetible/único) · ~60 s de calentamiento al encender |

## Actuadores y Salidas

| ID | Componente | Modelo | Cant. | Especificaciones | Notas |
|---|---|---|---:|---|---|
| ACT-001 | Módulo relé 8 canales | PCB `HL-58S v1.2`, relés SONGLE **SRD-05VDC-SL-C** | 1 | Bobina 5 V DC · Contactos 10 A @ 250 VAC / 10 A @ 30 VDC · SPDT (NO/NC/COM) | **Optoacoplado**. Jumper **JD-VCC** presente → permite alimentar bobinas con fuente separada. Entradas activas en **LOW**. Borneras de tornillo por canal. Consumo ~70 mA por bobina activa. |
| ACT-002 | Módulo relé 4 canales | Relés SONGLE **SRD-05VDC-SL-C** | 1 | Bobina 5 V DC · Contactos 10 A @ 250 VAC / 10 A @ 30 VDC · SPDT | **Optoacoplado**. Jumper JD-VCC presente. Pines: `VCC / IN1 / IN2 / IN3 / IN4 / GND`. Entradas activas en LOW. |

## Pantallas e Interfaz

| ID | Componente | Modelo | Cant. | Resolución / Interfaz | Notas |
|---|---|---|---:|---|---|
| DSP-001 | Display OLED 0.96" | **SSD1306**, 128×64 monocromo | 1 | **I²C** · pines `GND` `VCC` `SCK`(SCL) `SDA` | Dirección típica `0x3C` (algunos `0x3D`). Alimentar a **3.3 V**. ✅ **No consume pines extra**: comparte el bus I²C ya reservado. ⚠️ Los OLED sufren *burn-in* con contenido estático permanente — conviene atenuar, rotar el contenido o apagar la pantalla tras unos minutos |

## Alimentación

| ID | Componente | Modelo | Cant. | Entrada / Salida | Notas |
|---|---|---|---:|---|---|
| PWR-001 | Regulador **step-down** (buck) | **LM2596S-ADJ** | 1 | In **4.5-40 V** → Out **1.25-37 V** ajustable | 3 A pico, **~2 A continuos sin disipador**. Eficiencia ~90 %. Conmuta a 150 kHz. Requiere `Vin ≥ Vout + 1.5 V`. Caps 100 µF/50 V (in) y 220 µF/35 V (out), bobina 330 µH. ⚠️ **Ajustar la salida a 5.0 V con el trimpot ANTES de conectar nada** |
| PWR-002 | Regulador **step-up** (boost) | **MT3608** | 1 | In **2-24 V** → Out **5-28 V** ajustable | 2 A de corriente de conmutación (no de salida). Eficiencia ~93 %, 1.2 MHz. Solo eleva: la salida debe ser **mayor** que la entrada. ⏳ **Sin rol asignado en el diseño actual** — queda de repuesto |

## Prototipado, Cables y Herramientas

| ID | Componente | Tipo | Cant. | Detalles | Notas |
|---|---|---|---:|---|---|
| PRO-001 | Bornera de tornillo 2 vías | KF301 / KF128 (clon), azul | ~22 | Paso 5.08 mm · 2 posiciones · montaje PCB THT | Conteo **aproximado** desde la foto. Encastrables entre sí para formar tiras de N vías. |
| PRO-002 | Tira de pines macho | Header macho 1×40, paso 2.54 mm | 1 tira (40 pines) | Pines cortos estándar | Cortable a medida. Sirve para soldar a MCU-001/002. |
| PRO-003 | Tira de pines macho (pin largo) | Header 1×40, paso 2.54 mm, cuerpo alto | 1 tira (40 pines) | Cuerpo plástico más grueso y pines más largos que PRO-002 | *A confirmar*: header macho de pin largo ("stackable") o header hembra de perfil. |
| PRO-006 | Conversor de niveles lógicos 8 canales | **TXS0108E** (marcado `YF08E`), placa CJMCU | 1 | `VA` 1.4-3.6 V ↔ `VB` 1.65-5.5 V · 8 canales bidireccionales con detección automática de sentido · pin `OE` | Pull-ups internos ~10 kΩ en ambos lados. `OE` debe estar en alto para habilitar. ⚠️ **Solo señales digitales** — no sirve para la `AO` analógica del MQ-7. ⚠️ Baja capacidad de corriente: no puede excitar LEDs ni relés directo. ⚠️ El TXS0108E es conocido por dar problemas en I²C (sus aceleradores *one-shot* chocan con los pull-ups del bus) |
| PRO-005 | Adaptador USB-Serie | **FTDI FT232RL** (`1412-G B890B572`) | 1 | Mini-USB · jumper selector **3.3 V / 5 V** · pines DTR RXI TXO VCC CTS GND | Necesario para programar MCU-003 (el Pro Mini no tiene USB). El DTR habilita el auto-reset. También sirve como segundo puerto serie para depurar la UART2 del ESP32. ⚠️ Poner el jumper en **5 V** si MCU-003 es la variante de 5 V. |
| PRO-004 | Cables Dupont | Jumpers 2.54 mm, cinta multicolor | ~2 mazos (~40 unid.) | Largo aparente ~20 cm | *A confirmar* el género (M-H / H-H / M-M). |

---

## Por identificar

| # | Descripción de lo observado | Hipótesis | Qué falta para confirmar |
|---:|---|---|---|
| ~~1~~ | ~~¿MCU-001 y MCU-002 son dos placas o una sola?~~ | — | ✅ **Resuelto: son dos placas distintas** |
| ~~6~~ | ~~Variante de chip, rev. de silicio, flash, PSRAM y MAC~~ | — | ✅ **Resuelto por lectura de hardware: ambas ESP32-D0WD-V3 rev v3.1, 4 MB, sin PSRAM** |
| 2 | Tira de pines de cuerpo alto (foto 2) | Header macho de pin largo o header hembra | Foto de perfil / de punta |
| 3 | Dos mazos de cables Dupont, extremos opuestos no visibles | M-H o H-H | Foto mostrando ambos extremos |
| 4 | Cantidad exacta de borneras KF301 | ~22 unidades | Conteo manual |
| 7 | Variante del Pro Mini (MCU-003): ¿5 V/16 MHz o 3.3 V/8 MHz? | **5 V / 16 MHz** — el regulador dice `LG50` (`LG33` sería el de 3.3 V) | Medir VCC con el multímetro, o leer el marcado del resonador |
| ~~9~~ | ~~Modelo del sensor de gas~~ | — | ✅ **Resuelto: MQ-7 (monóxido de carbono)** |
| ~~10~~ | ~~Modelo del conversor de nivel~~ | — | ✅ **Resuelto: TXS0108E, 8 canales** |
| 8 | ¿El FT232RL (PRO-005) es FTDI genuino o clon? | Indeterminado — los clones son muy comunes y reportan el mismo VID/PID | Conectarlo: si enumera y transmite bien, es funcional (genuino o clon aceptable) |
| ~~5~~ | ~~Cantidad de pines del DevKit ESP32~~ | — | ✅ **Resuelto: 38 pines (19/lado)** |

---

## Apéndice A — Pinout DevKit ESP32 38 pines

Verificado sobre la serigrafía de MCU-002.

| Fila izquierda (arriba→abajo) | Fila derecha (arriba→abajo) |
|---|---|
| `3V3` · `EN` · `SP` (GPIO36) · `SN` (GPIO39) · `G34` · `G35` · `G32` · `G33` · `G25` · `G26` · `G27` · `G14` · `G12` · `GND` · `G13` · `SD2` · `SD3` · `CMD` · `5V` | `GND` · `G23` · `G22` · `TXD` (GPIO1) · `RXD` (GPIO3) · `G21` · `GND` · `G19` · `G18` · `G5` · `G17` · `G16` · `G4` · `G0` · `G2` · `G15` · `SD1` · `SD0` · `CLK` |

### Equivalencia con la serigrafía de la placa

La placa **no usa los mismos nombres** que la documentación de Espressif. Al cablear,
buscar la columna de la derecha:

| En estos documentos | En la serigrafía |
|---|---|
| `GPIO36` | **`SVP`** |
| `GPIO39` | **`SVN`** |
| `GPIO2`, `GPIO4`, `GPIO15`… | **`P2`**, **`P4`**, **`P15`**… (prefijo `P`) |
| `SD0` `SD1` `SD2` `SD3` `CMD` `CLK` | iguales |

> El pinout está serigrafiado en la **cara inferior**, así que las columnas aparecen
> espejadas respecto de la vista superior. Verificado en MCU-001 y MCU-002: **las dos
> placas son idénticas en pinout**.

**Restricciones a tener en cuenta al asignar pines:**

- **No usar:** `SD0`, `SD1`, `SD2`, `SD3`, `CMD`, `CLK` → conectados a la flash SPI interna.
- **Solo entrada (sin pull-up/pull-down interno):** `SP`/GPIO36, `SN`/GPIO39, `G34`, `G35`. No sirven para manejar relés.
- **Strapping pins** (condicionan el arranque, evitar o usar con cuidado): `G0`, `G2`, `G12`, `G15`.
- **UART0:** `TXD`/`RXD` ocupados por el CP2102 durante la programación y el monitor serie.
- **ADC2** (`G0`,`G2`,`G4`,`G12`–`G15`,`G25`–`G27`) **no funciona con WiFi activo** → para lecturas analógicas usar ADC1 (`G32`–`G39`).
- **GPIO libres y cómodos para salidas digitales:** `G13`, `G14`, `G16`, `G17`, `G18`, `G19`, `G21`, `G22`, `G23`, `G25`, `G26`, `G27`, `G32`, `G33` → **14 pines**, suficientes para los 12 canales de relé (ACT-001 + ACT-002).
- **Alimentación:** `5V` acepta la entrada de la fuente; `3V3` es salida del AMS1117 (máx. ~500 mA, pero en la práctica dejar margen).

---

## Apéndice B — Cómo identificar una placa por hardware

Las fotos no revelan variante de chip, revisión de silicio, tamaño de flash ni PSRAM.
Esos datos se leen del propio chip:

```
python tools/identificar-esp32.py MCU-001
```

El script detecta el puerto COM solo, corre `esptool flash-id` y guarda el reporte en
`tools/reportes/<etiqueta>.txt`.

**Procedimiento:** conectar **una sola placa por vez** (el script aborta si detecta
varias, para no confundir cuál es cuál), correr el comando con la etiqueta
correspondiente, desconectar y repetir con la otra.

**Requisitos ya instalados:** `esptool 5.6.0`, `pyserial`.

### Estado del entorno (verificado 2026-10-31)

| Check | Resultado |
|---|---|
| Hardware ID del puente USB | `VID_10C4&PID_EA60` → **CP2102 genuino de Silicon Labs** (ambas placas) |
| Driver CP210x en el driver store | ❌ **Ausente** — `pnputil /enum-drivers` no devuelve nada |
| Puertos COM disponibles | Ninguno (consecuencia directa de lo anterior) |
| `esptool` / `pyserial` | ✅ Instalados (esptool 5.6.0) |
| Python | ✅ 3.11.0 y 3.13.0 |
| Arduino IDE + core ESP32 | ✅ Instalados (core **esp32 v3.3.11**) |

El dispositivo aparece en el Administrador de dispositivos bajo **"Other devices"** con
ícono de advertencia: Windows detecta el chip pero no tiene driver, así que no crea el
puerto COM. **No es un defecto de las placas.**

### Instalación del driver CP210x

⚠️ **"Buscar controladores automáticamente" desde el Administrador de dispositivos
NO funciona** — en Windows 11 esa opción ya no consulta Windows Update, y responde
que el mejor driver ya está instalado. Es un callejón sin salida.

El driver **sí está en Windows Update**, pero como *actualización opcional*.
Verificado por consulta directa al servicio (2026-10-31):

```
Silicon Laboratories Inc. - Ports - 11.2.0.167
```

**Ruta correcta:**

```
Configuración → Windows Update → Opciones avanzadas
  → Actualizaciones opcionales → Actualizaciones de controladores
```

Marcar la entrada de Silicon Laboratories → *Descargar e instalar*. Conviene tener
una placa conectada para que Windows la asocie de inmediato. Al terminar, el
dispositivo pasa de "Other devices" a **"Ports (COM & LPT)"**.

**Vías descartadas** (para no repetir el intento):

| Vía | Resultado |
|---|---|
| Device Manager → Buscar automáticamente | ❌ No consulta Windows Update |
| Descarga directa de `silabs.com/documents/public/software/` | ❌ HTTP 403, protección anti-bot |
| `winget search CP210x` | ❌ No existe el paquete |
| Driver incluido en Arduino IDE | ❌ Arduino no lo trae (solo headers de tinyusb) |
| **Windows Update → Actualizaciones opcionales** | ✅ **Driver disponible** |

**Otros problemas posibles, una vez instalado el driver:**

1. Si el puerto sigue sin aparecer: verificar que el cable micro-USB sea **de datos**,
   no solo de carga — es la causa más frecuente y la más fácil de pasar por alto.
2. Si el puerto aparece pero `esptool` no sincroniza: mantener apretado **BOOT**
   mientras arranca la conexión, soltarlo al ver `Connecting...`.

**Lo que devuelve:** tipo de chip y variante · revisión de silicio · features
(cores, WiFi/BT, flash embebida, PSRAM) · frecuencia del cristal · MAC address ·
fabricante y tamaño real de la flash.

---

## Apéndice C — Identificación por hardware (resultados)

### MCU-002 — leída en COM7 el 2026-10-31

> ✅ Asignada a **MCU-002** (botón `RST`, etiqueta "WIFI+BT SoC Inside").
> Confirmado por doble lectura: la MAC se repitió, probando que era la misma placa física.

| Dato | Valor |
|---|---|
| Chip | **ESP32-D0WD-V3** |
| Revisión de silicio | **v3.1** — la más nueva; sin las erratas de PSRAM ni de deep-sleep del rev1 |
| Núcleos | Dual core + LP core, 240 MHz |
| Radio | Wi-Fi + Bluetooth |
| Cristal | 40 MHz |
| Calibración ADC | **Vref calibrada en eFuse** → lecturas analógicas razonablemente precisas sin calibrar a mano |
| Flash | **4 MB** · fabricante `0x68` · device `4016` · 3.3 V por strapping pin |
| PSRAM | **No** |
| MAC | `d4:e9:f4:64:c5:54` |

**Implicancias para el proyecto:**

- **4 MB de flash sin PSRAM** es la configuración estándar del WROOM-32. Alcanza de
  sobra para firmware con WiFi + MQTT + servidor web, pero el esquema de particiones
  por defecto deja **~1.3 MB por slot de aplicación** con OTA habilitado. Si el
  firmware se acerca a ese límite, hay que pasar a una tabla de particiones custom.
- **Sin PSRAM:** descartar buffers grandes (framebuffers de pantallas a color
  grandes, cámara). Para sensores y relés es irrelevante.
- **Rev v3.1** permite usar deep-sleep sin workarounds — relevante si alguna parte
  del sistema va a batería.

> El fabricante de flash `0x68` (Boya) es un proveedor de terceros, no el que suele
> traer el módulo original de Espressif. Es un **indicio** de que el módulo sería un
> clon de WROOM-32, no una prueba. En la práctica funciona igual; solo importaría si
> el proyecto necesitara certificación formal.

### MCU-001 — leída en COM7 el 2026-10-31

> ✅ Asignada a **MCU-001** (botón `EN`, etiqueta con QR y FCC ID, lote `XXSR69`).
> MAC distinta de la de MCU-002, lo que prueba que es otra placa física.

Specs **idénticas a MCU-002** en todo salvo la MAC:

| Dato | Valor |
|---|---|
| Chip | **ESP32-D0WD-V3** |
| Revisión de silicio | **v3.1** |
| Núcleos | Dual core + LP core, 240 MHz |
| Radio | Wi-Fi + Bluetooth |
| Cristal | 40 MHz |
| Calibración ADC | Vref calibrada en eFuse |
| Flash | **4 MB** · fabricante `0x68` · device `4016` |
| PSRAM | **No** |
| MAC | `84:1f:e8:2b:24:5c` |

### Comparación

| | MCU-001 | MCU-002 |
|---|---|---|
| Serigrafía botón reset | `EN` | `RST` |
| Etiqueta del módulo | QR + FCC ID (lote XXSR69) | "WIFI+BT SoC Inside" |
| Chip / revisión | ESP32-D0WD-V3 v3.1 | ESP32-D0WD-V3 v3.1 |
| Flash / PSRAM | 4 MB / no | 4 MB / no |
| MAC | `84:1f:e8:2b:24:5c` | `d4:e9:f4:64:c5:54` |

**Conclusión: intercambiables.** Cualquier firmware corre igual en las dos; la MAC
es lo único que las distingue en runtime (útil para identificar nodos en red).

---

## Registro de fotos procesadas

| # | Fecha | Contenido | Ítems catalogados |
|---:|---|---|---:|
| 1 | 2026-10-31 | DevKit ESP32 con CP2102, vista del módulo con FCC ID | 1 |
| 2 | 2026-10-31 | Módulos relé 8ch y 4ch, borneras, headers, cables Dupont | 6 |
| 3 | 2026-10-31 | DevKit ESP32, vista con serigrafía de pinout completa | 1 + pinout |
| 4 | 2026-10-31 | Arduino Pro Mini (ATmega328P) y adaptador FTDI FT232RL | 2 |
| 5 | 2026-10-31 | Sensores: luz (LDR+LM393), gas (MQ-7) y PIR HC-SR501 | 3 |
| 6 | 2026-10-31 | LM2596S (buck), TXS0108E (niveles), MT3608 (boost) | 3 |
| 7 | 2026-10-31 | Display OLED 0.96" SSD1306 I²C | 1 |
| 8 | 2026-10-31 | MCU-001 cara inferior, pines soldados y pinout serigrafiado | — |
