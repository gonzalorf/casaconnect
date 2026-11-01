# CasaConnect v1 — Diseño del circuito

> Esquemático y guía de construcción para PCB casera.
> Configuración de pines: [`configuracion-v1.md`](configuracion-v1.md).
>
> **Decidido:** dos placas · **todo THT** (montaje pasante) · EasyEDA Pro.
> Los netlists se generan con [`../tools/generar-netlist.py`](../tools/generar-netlist.py).

## Qué es esta placa

**No lleva relés ni microcontrolador montados.** El módulo de relés (ACT-001) y el
DevKit ESP32 son placas que ya existen y se conectan por conectores. Esta PCB es una
**placa portadora**: zócalo, protecciones, conectores y campo de patch.

Eso simplifica mucho el ruteo — no hay que manejar corrientes de bobina ni pistas de
220 V en el PCB.

```
                    ┌──────────────────────────────┐
   Fuente 5 V ─────>│  Bloque de alimentación      │
                    │  fusible · bulk · desacople  │
                    └───────┬──────────────┬───────┘
                         5V │           5V │
                    ┌───────▼──────┐  ┌────▼────────────────┐
                    │ Zócalo       │  │ Riel +5 V a los     │
                    │ ESP32 DevKit │  │ 6 puertos RJ12      │
                    │              │  │ (1 PTC por puerto)  │
                    └──┬────┬────┬─┘  └────┬────────────────┘
                 3V3 │  │I²C │GPIO         │ 24 líneas de datos
          ┌──────────┘  │    │             │
          │    ┌────────▼─┐  │       ┌─────▼──────────────┐
          │    │ Header   │  │       │ BLOQUE A           │
          │    │ OLED     │  │       │ patch (24 puntos)  │
          │    └──────────┘  │       └─────┬──────────────┘
          │                  │             │
          │   ┌──────────────▼───┐   ┌─────▼──────────────┐
          └──>│ 8 pull-ups 10 k  │   │ BLOQUE B           │
              │ Header a relés   │   │ 12 entradas        │
              └──────────────────┘   │ protegidas         │
                                     └────────────────────┘
```

---

## 1. Bloque de alimentación

```
          F1 2 A
  +5V ───/\/\/───┬──────────┬──────────┬────────> riel +5V
 (fuente)        │          │          │
                ═╪═ C1     ═╪═ C2     ═╪═ C3
                 │ 1000µF   │ 100nF    │ 100nF
                 │ 16V      │          │
  GND ───────────┴──────────┴──────────┴────────> riel GND
```

| Ref | Valor | Función |
|---|---|---|
| F1 | Fusible 2 A (portafusible o PTC) | Protección general |
| C1 | 1000 µF / 16 V electrolítico | **Reservorio**. Absorbe el golpe de corriente cuando varios relés conmutan a la vez. Sin esto el ESP32 se resetea |
| C2, C3 | 100 nF cerámico | Desacople de alta frecuencia |

> ⚠️ **Sin diodo en serie para protección de polaridad inversa.** Un Schottky tiraría
> ~0.4 V y las bobinas de los relés necesitan sus 5 V completos. En su lugar: **bornera
> de entrada claramente serigrafiada** `+5V` / `GND`, y el fusible. Si querés
> protección real, va un MOSFET de canal P (IRF4905 o similar) que casi no cae tensión,
> pero para una fuente fija bien etiquetada es overkill.

### Riel de 3.3 V

Sale del pin `3V3` del DevKit (regulador AMS1117 a bordo). Presupuesto:

| Consumidor | Corriente |
|---|---:|
| 8 optoacopladores de los relés (~2 mA c/u) | ~17 mA |
| OLED SSD1306 | ~20 mA |
| Módulo LDR (SEN-001) | ~5 mA |
| Pull-ups varios | ~5 mA |
| **Total** | **~47 mA** |

Entra sin problemas. El AMS1117 ya alimenta el ESP32 (picos de ~500 mA) y 47 mA más
no lo mueven. **No hace falta un regulador adicional.**

### Masa en estrella — obligatorio con GND común

En la instalación final hay **una sola fuente**, así que el GND es común para todo: el
ESP32, el lado lógico del módulo, las bobinas y los puertos RJ12. Está bien que así
sea, pero obliga a cuidar **por dónde vuelve cada corriente**.

El problema: las 8 bobinas pueden tirar **560 mA de golpe**. Si ese retorno comparte
una pista fina con el GND del ESP32, la caída sobre esa pista aparece como un
**desplazamiento de masa** que el ESP32 ve como ruido — y las entradas analógicas, que
miden contra GND, se corren.

```
   MAL — en cadena                 BIEN — en estrella

   Fuente(−)                       Fuente(−)
      │                               │
      ├── bobinas  ← 560 mA           ├────────── bobinas   ← pista GRUESA, directa
      │                               │
      ├── ESP32    ← ve el ruido      ├────────── ESP32 + lógica
      │   de las bobinas              │
      └── sensores                    └────────── sensores / RJ12
```

**Regla:** el retorno de las bobinas vuelve **directo al borne de entrada de la
fuente**, por pista gruesa y por su propio camino. La masa del ESP32 y la de las
entradas salen del mismo punto, pero cada una por su lado — nunca colgadas de la pista
por donde pasan los 560 mA.

Con el plano de masa de la §9 esto sale casi solo, **siempre que la bornera de entrada
quede cerca del header de relés** y no en la punta opuesta de la placa. Es una decisión
de ubicación de componentes más que de ruteo, así que conviene tenerla en cuenta al
acomodar la placa, no después.

### Programar por USB con la fuente conectada

Una vez instalado, si alguna vez necesitás el USB (por ejemplo si se rompe el OTA),
**desconectá primero la fuente de 5 V**. En muchos DevKit el pin `5V` está unido
directamente al 5 V del puerto USB, y tendrías la fuente y la PC empujando una contra
la otra.

Para flashear alcanza con el USB solo: los relés no van a funcionar por falta de
corriente, pero eso no afecta la carga del firmware.

---

## 2. Zócalo del ESP32

⚠️ **Zocalar, no soldar.** Dos tiras de 1×19 hembra. Si el ESP32 se daña (y con
cables de 10 m entrando a la casa, puede pasar), lo cambiás en 30 segundos en vez de
desoldar 38 pines.

> ⚠️ **Las dos placas miden distinto.** Verificado contando agujeros de protoboard
> (más exacto que una regla, porque el patrón es de 2.54 mm clavados):
>
> | Placa | Separación entre filas |
> |---|---|
> | **MCU-001** (la elegida) | **0.9" = 22.86 mm** |
> | MCU-002 | 1.0" = 25.4 mm |
>
> **El zócalo se diseña para 0.9".** MCU-002 no entra, y no hay forma de contemplar
> las dos: quedarían a 1.27 mm entre tiras y los cuerpos plásticos se chocan.
>
> **Perforá igual el segundo juego de agujeros a 1.0".** En una placa casera no cuesta
> nada y te deja la salida de mover las tiras si algún día solo tenés la otra placa.
> Serigrafiá cuál juego está en uso.
>
> Como MCU-002 no sirve de repuesto directo, conviene **sumar un DevKit de 0.9" al
> pedido de componentes**.

---

## 3. Salidas de relé (×8)

Una por cada uno de: `13` `16` `17` `18` `19` `23` `25` `26`.

```
            +3V3
              │
             ┌┴┐
             │ │ 10 kΩ      ← mantiene el relé APAGADO durante el boot
             └┬┘
  GPIO ───────┴──────────────> IN(n) del módulo de relés
```

Eso es todo: **una resistencia por canal**. El optoacoplador del módulo ya trae su
resistencia limitadora.

### Conexión al módulo de relés

Header macho de 10 pines:

| Pin del header | Va a | Notas |
|---|---|---|
| 1 | `VCC` del módulo | **+3.3 V** ← no 5 V |
| 2-9 | `IN1`..`IN8` | Desde los GPIO con su pull-up |
| 10 | `GND` | Común |

Más un cable aparte de **+5 V al borne `JD-VCC`** del módulo de relés.

> ⚠️ **Quitar el jumper JD-VCC del módulo de relés.** Si queda puesto, `VCC` y
> `JD-VCC` están unidos y los 3.3 V no alcanzan para alimentar las bobinas. Con el
> jumper fuera: lado lógico a 3.3 V (conmuta limpio con el ESP32) y bobinas a 5 V.

---

## 4. Entradas protegidas (×12)

Las 12 redes viven en la **Placa B**, **después** del campo de patch. Al estar del
lado del GPIO y no del lado del jack, son **12 juegos de componentes en vez de 24**.
El cable plano entre placas lleva señales ya filtradas.

```
                                    +3V3
                                      │
                                     ┌┴┐
                                     │ │ 10 kΩ   ┐
                                     └┬┘         │ solo IN9-IN12
                                    o─┤          │ (jumper JP)
                                    o─┘          ┘
                                      │
  Bloque B ──[ 1 kΩ ]──┬──────────────┴──────────> GPIO
   (patch)             │              │
                      ─┴─ BAT85 ×2  ═╪═ 100 nF
                       ▽  (clamp)     │
                       │              │
                      GND            GND
```

| Componente | Valor | Función |
|---|---|---|
| R serie | **1 kΩ** | Limita corriente de falla y forma el filtro RC |
| C | **100 nF** | Antirrebote y filtro de ruido (τ = 100 µs). También estabiliza la lectura del ADC |
| D | **2× BAT85** (Schottky DO-35) | Recorta a `3V3` y a `GND`. Baja fuga: **no afecta las lecturas analógicas**. Son 24 en total (2 por entrada) |
| R pull-up | **10 kΩ** + jumper | Solo en IN9-IN12 (`34` `35` `36` `39`), que no tienen pull-up interno |

> **Por qué Schottky y no un zener de 3.3 V:** el zener tiene fuga apreciable y falsea
> las lecturas del ADC en las entradas analógicas. El Schottky no conduce nada
> mientras la señal esté en rango.
>
> ⚠️ **Y no sirve un 1N4148.** Al ser de silicio cae 0.7 V, así que recortaría recién
> en 4.0 V — por encima del máximo absoluto del ESP32 (3.6 V). El Schottky cae 0.3 V
> y recorta en 3.6 V. **Tiene que ser Schottky.**

> **El pull-up con jumper (IN9-IN12):** puesto = botón · sacado = sensor analógico.
> En la v1, IN9 (`34`) lleva el sensor de luz, así que **ese jumper va SACADO**.

---

## 5. Puertos RJ12 (×6)

Jack **6P6C de montaje en PCB**, uno por puerto.

| Pin | Señal |
|---:|---|
| 1 | **GND** |
| 2 | Dato 1 |
| 3 | Dato 2 |
| 4 | Dato 3 |
| 5 | Dato 4 |
| 6 | **+5 V** |

```
  riel +5V ──[ PTC 500 mA ]──> pin 6 del jack    (uno por puerto)
  riel GND ──────────────────> pin 1 del jack
  pines 2-5 ─────────────────> Bloque A del patch
```

> ⚠️ **El PTC por puerto no es opcional.** Los cables telefónicos RJ12 suelen ser
> **cruzados** (pin 1 ↔ pin 6). Con un cable así, los pines de GND y +5 V se invierten
> y **cortocircuitás la fuente**. El PTC convierte eso en "ese puerto no anda" en vez
> de en un incendio. Usá cables derechos y verificá cada uno con continuidad, pero
> poné el PTC igual.

---

## 6. Campo de patch

| Bloque | Puntos | Contenido |
|---|---:|---|
| **A** | 24 | `P1.1`..`P6.4` — las 4 líneas de datos de cada jack |
| **B** | 12 | `IN1`..`IN12` — entrada de cada red de protección |

Conectar con puentes cortos. Máximo 12 activos a la vez.

**Serigrafía del Bloque B — esto es lo que te va a salvar en dos años:**

```
 IN1  GPIO2   dig
 IN2  GPIO4   dig
 IN3  GPIO5   dig
 IN4  GPIO14  dig
 IN5  GPIO15  dig
 IN6  GPIO27  dig
 IN7  GPIO32  dig+ADC
 IN8  GPIO33  dig+ADC
 IN9  GPIO34  ADC  solo-ent
 IN10 GPIO35  ADC  solo-ent
 IN11 GPIO36  ADC  solo-ent
 IN12 GPIO39  ADC  solo-ent
```

---

## 7. Header del OLED

4 pines: `GND` `+3V3` `SCL(22)` `SDA(21)`.

Agregar **2 resistencias de 4.7 kΩ a 3.3 V** en SDA y SCL. Muchos módulos OLED ya las
traen, pero los pull-ups internos del ESP32 son débiles y poco confiables para I²C.
Si el módulo ya tiene, dejá los footprints sin poblar.

> Dejá **2 pines más del bus I²C accesibles** en un header aparte. Es la vía de
> crecimiento: el día que quieras más relés o entradas, un MCP23017 entra ahí sin
> tocar la placa.

---

## 8. Lista de materiales

### Para comprar

| Cant. | Componente | Nota |
|---:|---|---|
| 6 | Jack RJ12 6P6C montaje PCB | |
| 6 | PTC rearmable 500 mA | Uno por puerto |
| 24 | BAT85 (DO-35) | Clamp de entradas, 2 por entrada |
| 1 | Fusible 2 A + portafusible | |
| 1 | Capacitor 1000 µF / 16 V | **El más importante de la lista** |
| ~8 | Capacitor 100 nF cerámico | Desacople |
| 12 | Capacitor 100 nF cerámico | Filtro de entradas |
| 20 | Resistencia 10 kΩ | 8 relés + 4 jumper + repuestos |
| 12 | Resistencia 1 kΩ | Serie de entradas |
| 2 | Resistencia 4.7 kΩ | Pull-ups I²C (si el OLED no los trae) |
| 4 | Jumper 2 pines + shunt | Pull-ups conmutables IN9-IN12 |
| 2 | Tira header hembra 1×19 | Zócalo del ESP32 |
| 1 | Bornera 2 vías | Entrada de alimentación |
| 1 | Fuente 5 V / 2-3 A | **Verificar amperaje de la que tenés** |

### Ya en inventario

| Cant. | Componente | ID |
|---:|---|---|
| 1 | DevKit ESP32 38 pines | MCU-001 o MCU-002 |
| 1 | Módulo relé 8 canales | ACT-001 |
| 1 | OLED SSD1306 | DSP-001 |
| 2 | PIR HC-SR501 | SEN-003 |
| 1 | Módulo LDR | SEN-001 |
| ~18 | Bornera KF301 | PRO-001 — para el campo de patch |
| 1-2 | Tira de pines macho | PRO-002 / PRO-003 |

---

## 9. Notas para hacerla a mano

### Dos placas (decidido)

| Placa | Contenido | Componentes |
|---|---|---:|
| **A — Control** | Zócalo ESP32 · alimentación · pull-ups de relé · header a relés · OLED · I²C de expansión | 22 |
| **B — Entradas** | 6 jacks RJ12 · PTCs · 12 redes de protección · header de emergencia | 71 |

Se unen con un **cable plano de 16 vías**: `+5V` `GND` `+3V3` `GND` + `IN1`..`IN12`.

La Placa B parece la pesada por el conteo, pero su ruteo es **casi todo paralelo y
repetitivo** (12 redes idénticas en fila), que es lo más fácil de hacer a una cara.
La Placa A es chica pero tiene el ruteo más irregular.

Aun así, contá con **puentes de alambre** por el lado de componentes: a una sola capa
son inevitables. Es normal en placas caseras.

### Reglas de dibujo para etching casero

| Parámetro | Valor |
|---|---|
| Ancho de pista, señales | **≥ 0.6 mm** (24 mil) |
| Ancho de pista, 5 V y GND | **≥ 1.5 mm** (60 mil) |
| Separación entre pistas | **≥ 0.5 mm** (20 mil) |
| Anillo de pad | **≥ 0.6 mm** |
| Diámetro de agujero | 0.8-1.0 mm según componente |

Más grueso de lo que sugiere el autorouter por defecto: el método casero no tiene la
precisión de una fábrica, y una pista fina que queda sobre-atacada es una falla
intermitente que vas a tardar horas en encontrar.

**Plano de masa:** llenar todo el cobre libre con GND (*copper pour*). Reduce el
atacado químico, mejora el ruido y ahorra reactivo.

### Orden de armado y prueba

Armala y probala por etapas. Si enchufás todo junto y algo está mal, no vas a saber
qué.

1. **Alimentación sola.** Conectar la fuente. Medir **5.0 V** y, con el ESP32 puesto,
   **3.3 V**. Verificar que nada se caliente.
2. **ESP32 + OLED.** Cargar un sketch mínimo que escanee el bus I²C. Debe aparecer
   `0x3C`.
3. **Relés.** Conectar el módulo (jumper JD-VCC **fuera**, `VCC` a 3.3 V). Probar los
   8 canales uno por uno. **Resetear el ESP32 y confirmar que ningún relé se activa
   durante el arranque** — es la prueba de que los pull-ups están bien.
4. **Una entrada.** Patchear un solo botón, verificar lectura y antirrebote.
5. **El resto de las entradas**, de a una.
6. **Los puertos RJ12**, midiendo continuidad de cada cable **antes** de enchufarlo.

> Antes del paso 3, con el multímetro: confirmá que en el borne `VCC` del módulo de
> relés hay **3.3 V** y en `JD-VCC` hay **5 V**. Si están al revés o unidos, el jumper
> no se quitó.

---

## 10. Firmware — OTA desde el principio

Decidido: **sin protocolo de comunicación en la v1**, pero **con OTA**.

El ESP32 va dentro de un tablero: sin OTA, cada cambio significa abrir la caja y
enchufar el USB.

**Tabla de particiones.** Con 4 MB de flash y OTA, el esquema por defecto
(`default_4MB` en Arduino, "Minimal SPIFFS" u otros) deja **~1.3 MB por slot de
aplicación**. Alcanza de sobra para esto, pero **elegila antes de empezar a programar**:
cambiarla después implica reflashear por USB, que es justo lo que OTA viene a evitar.

Con WiFi conectada solo para OTA, aprovechá también **NTP** para tener hora real sin
hardware adicional (nada de RTC). Útil para registrar eventos con timestamp en el
OLED.

> Dejá la WiFi configurada pero sin ningún servicio de control. Cuando en la etapa 2
> definas MQTT o HTTP, el transporte ya va a estar probado y funcionando.

---

## 11. Generar el esquemático en EasyEDA

No hace falta colocar los 93 componentes a mano. EasyEDA **Pro** tiene una extensión
que arma el esquemático completo desde un netlist en JSON.

### Pasos

1. **Completar los números LCSC.** Abrir
   [`tools/generar-netlist.py`](../tools/generar-netlist.py) y reemplazar cada
   `PENDIENTE` del diccionario `PARTS` por el C-number correspondiente, buscándolo en
   [lcsc.com](https://www.lcsc.com). Son **17 búsquedas**; cada componente se repite
   muchas veces pero se define una sola.

2. **Generar:**

   ```
   python tools/generar-netlist.py
   ```

   Avisa si queda algún `PENDIENTE` y produce:

   ```
   tools/netlist/placa-a-control.json     22 componentes
   tools/netlist/placa-b-entradas.json    71 componentes
   ```

3. **En EasyEDA Pro:** marketplace → instalar
   `eext-generate-schematic-from-netlist` → importar cada JSON por separado, en
   proyectos distintos.

4. **Rutear** con el autorouter, configurado a **1 capa** y con los anchos de pista de
   la sección 9.

### La advertencia importante

> ⚠️ EasyEDA resuelve los componentes **únicamente** por el número LCSC. El fabricante
> y el footprint no intervienen en la búsqueda.
>
> - **Número faltante** → la importación falla (molesto pero inofensivo)
> - **Número equivocado** → carga un componente incorrecto, **y no se puede corregir
>   después de importar**
>
> Verificá los 17 antes de generar. Es el único paso del proceso sin vuelta atrás.

### Si la importación falla

La documentación de la extensión es ambigua sobre si los campos van en minúscula
(`device_name`, `value`) o en mayúscula (`DeviceName`, `Value`). El script genera
**minúscula**. Si EasyEDA rechaza el archivo, cambiar esas dos claves en el método
`Netlist.add()` y volver a generar.

---

## 12. Poblado opcional — qué se puentea y qué se deja vacío

El diseño lleva **todos** los footprints, pero en la primera versión se pueblan solo
los imprescindibles. Lo que falte se suelda después sin rehacer la placa.

> ⚠️ **La regla crítica:** un footprint sin poblar se puentea **solo si el componente
> iba en serie**. Si iba en paralelo (a GND o a 3V3), un puente lo **cortocircuita**.

| Componente | Topología | Si no se puebla |
|---|---|---|
| **R 1 kΩ** serie de entrada | **Serie** | Necesita puente — sin él la señal no pasa |
| **PTC** de puerto | **Serie** | Necesita puente — sin él el puerto se queda sin 5 V |
| **C 100 nF** de entrada | Paralelo a GND | **Dejar vacío.** Un puente pone la señal a masa |
| **BAT85** ×2 de recorte | Paralelo a 3V3 / GND | **Dejar vacío.** Un puente cortocircuita el riel |
| **R 10 kΩ** pull-up conmutable | Paralelo a 3V3 | **Dejar vacío.** Un puente fija la entrada en alto |
| **R 4.7 kΩ** pull-up I²C | Paralelo a 3V3 | **Dejar vacío** |

De todo lo que se difiere en la v1, **solo el PTC va en serie**. Los demás se dejan con
los pads pelados y listo.

### Convención de serigrafía

Para no tener que recordar esta tabla con el soldador en la mano:

**Dibujar una línea fina de serigrafía entre los dos pads de cada footprint en serie.**

```
   SERIE                        PARALELO
   ┌───┐                        ┌───┐
   │ o─┼──── o │                │ o │   o
   └───┘   línea                └───┘
                                  sin línea
   Si está vacío: PUENTEAR       Si está vacío: DEJAR ASÍ
```

Si ves la línea, ese hueco tiene que quedar cerrado sí o sí — con el componente o con
un puente. Si no hay línea, vacío está bien.

### Qué se puebla en la v1

| Bloque | Se puebla | Se difiere |
|---|---|---|
| Alimentación | Fusible · 1000 µF · 2× 100 nF | — |
| Relés | 8× 10 kΩ pull-up | — |
| Entradas | 12× 1 kΩ serie | 12× 100 nF · 24× BAT85 |
| Pull-ups conmutables | — | 4× 10 kΩ · 4× jumper |
| I²C | — | 2× 4.7 kΩ *(verificar si el OLED ya los trae)* |
| Puertos RJ12 | 1× PTC en el riel común · 6 puentes | 6× PTC por puerto |

> **Los 8 pull-up de relé no son opcionales.** No son protección sino función: sin
> ellos los relés se activan durante el arranque.

### El PTC: protección base ahora, por puerto después

Se dejan **las dos cosas**: un PTC de 1 A en el riel común (poblado) y los 6 footprints
por puerto (puenteados con alambre).

- **Hoy:** el PTC común protege contra un cable cruzado. Un corto apaga los 5 V de los
  6 puertos — molesto, pero diagnosticable, y evita el cortocircuito franco contra una
  fuente de 3 A, que es lo que realmente importa.
- **Mañana:** cambiás el puente de un puerto por un PTC y ese puerto queda aislado.

> No dejes los 6 puertos sin ningún PTC. Un corto sostenido con 3 A disponibles
> calienta el cable telefónico dentro de la pared.

