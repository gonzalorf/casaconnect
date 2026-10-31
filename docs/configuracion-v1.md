# CasaConnect — Configuración v1 (definida)

> Especificación de construcción del primer módulo. Decidida el 2026-10-31.
> El análisis que respalda estas decisiones está en
> [`diseno-modulo-esp32.md`](diseno-modulo-esp32.md).
> El esquemático y la guía de construcción, en [`circuito-v1.md`](circuito-v1.md).

## Resumen de la decisión

- **8 relés** (Alternativa A) — sin expansor I²C
- **Todo el resto de los pines va a entradas**: 12 disponibles
- **6 jacks RJ12**, con solo algunas líneas conectadas inicialmente
- **Display OLED** en el bus I²C — no consume pines ni botones
- **Sin sensor de gas** en esta versión (el MQ-7 queda para una v2)
- **Alimentación: fuente de 5 V directa** (ya disponible)

---

## 1. Mapa de pines completo

Los 22 pines utilizables, sin dejar ninguno sin asignar.

### Salidas — 8 relés

| Relé | GPIO | | Relé | GPIO |
|---|---|---|---|---|
| R1 | `13` | | R5 | `19` |
| R2 | `16` | | R6 | `23` |
| R3 | `17` | | R7 | `25` |
| R4 | `18` | | R8 | `26` |

Todos son pines **limpios**: sin función de strapping y sin glitch en el arranque.
Cada uno lleva **pull-up de 10 kΩ a 3.3 V** para que el relé quede apagado mientras el
ESP32 bootea.

### Bus I²C — 2 pines

| Función | GPIO | Dispositivos |
|---|---|---|
| SDA | `21` | OLED SSD1306 (`0x3C`) |
| SCL | `22` | *(libre para crecer)* |

> **Este bus es la vía de crecimiento del módulo.** Si algún día necesitás más relés o
> más entradas, un MCP23017 entra acá sin tocar el resto del diseño. Por eso no se
> sacrifica aunque hoy solo lleve la pantalla.

### Entradas — 12 pines

Los pines **no son equivalentes**. Esta tabla es la que importa al momento de patchear:

| # | GPIO | Analógico | Pull-up interno | Notas |
|---:|---|:---:|:---:|---|
| IN1 | `2` | ❌ | ✅ | LED on-board en muchas placas; glitch breve al bootear |
| IN2 | `4` | ❌ | ✅ | Limpio |
| IN3 | `5` | ❌ | ✅ | Glitch breve al bootear |
| IN4 | `14` | ❌ | ✅ | Glitch breve al bootear |
| IN5 | `15` | ❌ | ✅ | Glitch breve al bootear |
| IN6 | `27` | ❌ | ✅ | Limpio |
| IN7 | `32` | ✅ **ADC1** | ✅ | Limpio. Digital o analógico |
| IN8 | `33` | ✅ **ADC1** | ✅ | Limpio. Digital o analógico |
| IN9 | `34` | ✅ **ADC1** | ❌ **externo** | **Solo entrada** |
| IN10 | `35` | ✅ **ADC1** | ❌ **externo** | **Solo entrada** |
| IN11 | `36` (SP) | ✅ **ADC1** | ❌ **externo** | **Solo entrada** |
| IN12 | `39` (SN) | ✅ **ADC1** | ❌ **externo** | **Solo entrada** |

El glitch de arranque de IN1/IN3/IN4/IN5 **no molesta en entradas** — solo sería un
problema si fueran salidas de relé.

### Pull-ups con jumper en IN9-IN12

`34` `35` `36` `39` no tienen pull-up interno, y lo que necesitan depende de qué se
conecte:

- **Un botón** necesita pull-up → sin él, el pin queda flotando y lee basura
- **Un sensor analógico** se arruina con el pull-up → falsea la lectura

Solución: **una resistencia de 10 kΩ a 3.3 V con un jumper de 2 pines** en cada uno de
esos cuatro. Jumper puesto = botón. Jumper sacado = analógico. Cuatro jumpers, dos
centavos, y el problema desaparece para siempre.

---

## 2. Plan de puertos RJ12

6 jacks. Cada uno lleva **GND** y **+5 V** (rieles compartidos, no consumen GPIO) más
4 líneas de datos.

| Puerto | Uso inicial | Líneas en uso | Libres |
|---|---|---:|---:|
| **P1** | Botón 1 · Botón 2 · PIR 1 | 3 | 1 |
| **P2** | Botón 3 · Botón 4 · PIR 2 | 3 | 1 |
| **P3** | Botón 5 · Botón 6 | 2 | 2 |
| **P4** | Sensor de luz (LDR, salida `AO`) | 1 | 3 |
| **P5** | *reserva* | 0 | 4 |
| **P6** | *reserva* | 0 | 4 |
| | **Total** | **9** | **15** |

### El límite a tener presente

6 puertos × 4 líneas = **24 líneas posibles**, pero hay **12 pines de entrada**.
Nunca van a poder estar activas más de 12 líneas a la vez. Hoy usás 9, así que te
quedan **3 ampliaciones** antes de tener que agregar un MCP23017 al bus I²C.

### Asignación inicial concreta

| Señal | Puerto · línea | GPIO | Configuración |
|---|---|---|---|
| Botón 1 | P1.1 | `2` | `INPUT_PULLUP` |
| Botón 2 | P1.2 | `4` | `INPUT_PULLUP` |
| PIR 1 | P1.3 | `32` | `INPUT` (el HC-SR501 excita activamente) |
| Botón 3 | P2.1 | `5` | `INPUT_PULLUP` |
| Botón 4 | P2.2 | `14` | `INPUT_PULLUP` |
| PIR 2 | P2.3 | `33` | `INPUT` |
| Botón 5 | P3.1 | `15` | `INPUT_PULLUP` |
| Botón 6 | P3.2 | `27` | `INPUT_PULLUP` |
| Sensor de luz (`AO`) | P4.1 | `34` | `analogRead` · **jumper de pull-up SACADO** |
| *(reserva)* | — | `35` `36` `39` | 3 entradas analógicas libres |

> **El MQ-7 queda fuera de la v1.** Las 3 entradas analógicas de reserva siguen
> libres. Si en una v2 querés sumarlo, consume 1 de esas 3 — y si además se
> implementa el ciclado del calefactor, hace falta un pin PWM que hoy no sobra.
> Preverlo ahora en el PCB (una pista hasta un header sin poblar) cuesta nada y
> evita rehacerlo después.

> **Por qué el sensor de luz va por `AO` y no por `DO`:** el módulo tiene las dos
> salidas, pero por el RJ12 llega una sola línea y hay que elegir. Con `AO` el umbral
> se define por software y se puede cambiar sin ir hasta el sensor con un
> destornillador. Con `DO` quedás atado al trimpot. Para algo que va a estar montado en
> un lugar incómodo, `AO` es claramente mejor.

> **Por qué los PIR van en `32`/`33` y no en los solo-entrada:** así dejás los cuatro
> pines analógicos puros (`34`-`39`) libres para sensores futuros, que es donde más
> falta van a hacer. Los PIR son digitales y no necesitan ADC.

---

## 3. Campo de patch

Para poder agregar conexiones en el futuro sin rehacer la placa.

**Estructura:** dos bloques enfrentados, unidos por jumpers cortos.

```
  BLOQUE A — líneas RJ12 (24 puntos)        BLOQUE B — entradas ESP32 (12 puntos)

  P1.1 P1.2 P1.3 P1.4                        IN1  (GPIO2)   digital
  P2.1 P2.2 P2.3 P2.4                        IN2  (GPIO4)   digital
  P3.1 P3.2 P3.3 P3.4        <--jumper-->    ...
  P4.1 P4.2 P4.3 P4.4                        IN7  (GPIO32)  digital + ADC
  P5.1 P5.2 P5.3 P5.4                        IN9  (GPIO34)  ADC, solo entrada
  P6.1 P6.2 P6.3 P6.4                        IN12 (GPIO39)  ADC, solo entrada
```

**Serigrafiar el Bloque B con la capacidad de cada pin** (`digital` / `ADC` /
`solo-entrada`). Dentro de dos años, parado frente al tablero con un sensor en la mano,
esa etiqueta es la diferencia entre resolverlo en un minuto o tener que abrir este
documento.

### Qué conector usar

| Opción | Puntos | Ventaja | Desventaja |
|---|---:|---|---|
| **Bornera KF301** (ya tenés ~22) | 36 = 18 bloques | Muy fiable, destornillador y listo | Placa más grande |
| **Header 2.54 + jumper** | 36 | Compacto, barato | Sin traba; hay que asegurar los cables |

Con 36 puntos entran justo en las borneras que ya tenés. Si el tamaño de la caja no es
problema, **andá por KF301**: es la opción que no vas a tener que revisar nunca.

---

## 4. Protecciones obligatorias

| Dónde | Qué | Por qué |
|---|---|---|
| Cada línea de relé | Pull-up 10 kΩ a 3.3 V | Evita que los 8 relés se activen durante el boot |
| Cada línea de entrada | 1 kΩ en serie + 100 nF a GND | Antirrebote y filtro para los 10 m de cable |
| Cada línea de entrada | TVS o zener 3.3 V a GND | Recorte de sobretensión |
| IN9-IN12 | 10 kΩ a 3.3 V **con jumper** | Pull-up conmutable: botón vs. analógico |
| Línea +5 V de **cada** puerto | PTC rearmable 500 mA | Protege ante un cable RJ12 cruzado |
| Módulos de relé | Quitar jumper JD-VCC · `VCC`=3.3 V · `JD-VCC`=5 V | Conmutación confiable con lógica de 3.3 V |


---

## 4.bis Alimentación

**Decidido: fuente conmutada de 5 V directa.** El LM2596 y el MT3608 quedan de
repuesto, fuera de este diseño.

Consumo con la configuración v1 (8 relés, no 12):

| Consumidor | Corriente |
|---|---:|
| 8 bobinas SRD-05VDC (~70 mA c/u, todas activas) | 560 mA |
| ESP32 con WiFi (picos de transmisión) | ~500 mA |
| 2 × PIR HC-SR501 | ~100 mA |
| Módulo LDR | ~10 mA |
| OLED SSD1306 | ~20 mA |
| **Total pico** | **~1.2 A** |

⚠️ **Verificá el amperaje de tu fuente.** Hace falta **2 A como mínimo**; con **3 A**
quedás cómodo. Una fuente de 1 A va a andar bien hasta el día que se activen varios
relés a la vez mientras el WiFi transmite — y ahí la caída de tensión resetea el
ESP32. Es una falla intermitente desagradable de diagnosticar, así que conviene
descartarla ahora.

Distribución:

```
Fuente 5 V ─┬─> JD-VCC de los módulos de relé   (bobinas)
            ├─> pin 5V del DevKit ESP32          (alimenta el AMS1117)
            └─> riel +5 V de los 6 puertos RJ12  (cada uno con su PTC de 500 mA)

ESP32 3V3 ──┬─> VCC de los módulos de relé       (lado optoacoplador)
            ├─> OLED SSD1306
            ├─> módulo LDR
            └─> pull-ups de entradas y de líneas de relé
```

---

## 4.ter Comportamiento del OLED

**Sin botón dedicado.** El display se maneja solo, guiado por eventos.

### Lógica

| Disparador | Qué hace |
|---|---|
| Cualquier evento del módulo | Enciende, muestra el evento |
| Pasan **N segundos** sin eventos nuevos (sugerido: 10 s) | Se apaga solo |
| Evento nuevo mientras está encendido | Reinicia el contador y muestra el nuevo |
| Arranque del sistema | Muestra versión, SSID, **IP** y RSSI durante ~20 s |

Que esté apagado la mayor parte del tiempo **resuelve el burn-in sin hacer nada más**.
No hace falta atenuar ni rotar contenido.

### Qué mostrar en cada evento

Sirve de registro de diagnóstico en el tablero, sin necesitar un celular:

```
 14:32:05
 BOTON 3  ->  RELE 2
 ENCENDIDO
 ───────────────────
 WiFi OK    MQTT OK
```

La última línea fija con el estado de conectividad es lo que más va a servir el día
que algo no funcione: de un vistazo sabés si el problema es de red o del módulo.

### Dos detalles de implementación

**1. Actualizá el display DESPUÉS de accionar el relé, nunca antes.** Un refresco
completo del SSD1306 por I²C a 400 kHz son 1024 bytes, unos **25 ms**. Si lo hacés
antes de mover el relé, le agregás ese retardo a cada pulsación de tecla — poco, pero
perceptible, y sin ninguna razón. El orden correcto es: leer botón → accionar relé →
publicar por MQTT → actualizar pantalla.

**2. Pulsación larga como gesto de estado, gratis.** No hace falta un botón dedicado:
mantener apretado **cualquier botón de pared** 2 segundos puede mostrar una pantalla
de estado general (IP, uptime, relés activos, RSSI). Cuesta solo código y te da la
función de diagnóstico sin agregar hardware.

---

## 5. Lo que queda por decidir

- [x] ~~Sensor de gas MQ-7~~ → **fuera de la v1**
- [x] ~~Arquitectura de alimentación~~ → **fuente de 5 V directa**
- [x] ~~Qué muestra el OLED~~ → **registro de eventos con apagado automático**
- [ ] **Confirmar el amperaje de la fuente de 5 V** (mínimo 2 A, ideal 3 A)
- [x] ~~Protocolo~~ → **ninguno en la v1**. WiFi solo para **OTA** y NTP.
      MQTT/HTTP quedan para la etapa 2
- [ ] Si el sistema viejo de Arduino convive o se reemplaza de una
