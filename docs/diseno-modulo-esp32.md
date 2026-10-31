# Diseño del módulo CasaConnect — relevamiento de pines y alternativas

> ✅ **Configuración v1 ya decidida** — ver [`configuracion-v1.md`](configuracion-v1.md).
> Este documento es el análisis que la respalda.
>
> Basado en el hardware real verificado: **ESP32-D0WD-V3 rev v3.1, 4 MB flash, sin
> PSRAM** (ver `inventario.md`). Que no tengan PSRAM es relevante: libera GPIO16 y
> GPIO17, que en los módulos WROVER están ocupados.

---

## 1. Relevamiento de pines

El DevKit expone 38 pines, pero la cantidad **realmente utilizable es mucho menor**.
Desglose completo:

### 1.1 Pines descartados de entrada

| Pines | Motivo | ¿Recuperable? |
|---|---|---|
| `SD0` `SD1` `SD2` `SD3` `CMD` `CLK` (GPIO 6-11) | Conectados a la flash SPI interna | **No, nunca** |
| `GPIO1` (TXD) · `GPIO3` (RXD) | UART0 — programación y monitor serie | Técnicamente sí, pero perdés debug. No conviene |
| `GPIO0` | Botón BOOT en la placa; strapping de arranque | Como salida después del boot, pero es riesgoso |
| `GPIO12` (MTDI) | **Strapping crítico**: si está en HIGH al arrancar, configura la flash a 1.8 V y **la placa no bootea** | No. Dejarlo libre |
| `3V3` `5V` `GND` `EN` | Alimentación y reset | No son GPIO |

**12 de los 38 pines se van acá.**

### 1.2 Pines utilizables — 22 en total

| Grupo | Pines | Cant. | Características |
|---|---|---:|---|
| **Limpios** (sin caveats) | `4` `13` `16` `17` `18` `19` `21` `22` `23` `25` `26` `27` | 12 | Entrada o salida, sin sorpresas en el arranque |
| **ADC1** | `32` `33` | 2 | Limpios **+** lectura analógica que funciona con WiFi |
| **ADC1 solo-entrada** | `34` `35` `36`(SP) `39`(SN) | 4 | **No pueden ser salidas.** Sin pull-up/pull-down interno |
| **Con glitch de arranque** | `2` `5` `14` `15` | 4 | Emiten un pulso breve al bootear. Sirven de entrada; como salida hacen "clic" el relé al encender |

### 1.3 Las tres restricciones que mandan en el diseño

**a) ADC2 no sirve con WiFi.** El ESP32 tiene dos conversores. `ADC2` (GPIO 0, 2, 4, 12,
13, 14, 15, 25, 26, 27) queda inutilizable cuando el WiFi está activo — y el WiFi va a
estar siempre activo. Entonces **las únicas 6 entradas analógicas reales son `32` `33`
`34` `35` `36` `39`**.

Esto importa mucho para tu caso: los **sensores de gas (MQ-2, MQ-135) y los LDR son
analógicos**. Cada uno consume uno de esos 6 pines. Gastarlos en relés sería un error
que después no se deshace sin rediseñar.

> Dato bueno: ambas placas tienen **Vref calibrada en eFuse**, así que el ADC va a dar
> lecturas razonables sin calibración manual. Igual conviene hacer oversampling: el ADC
> del ESP32 es ruidoso y no del todo lineal.

**b) Los 4 pines solo-entrada no tienen pull-up interno.** `34` `35` `36` `39` sirven
perfecto para botones... pero **necesitan una resistencia de pull-up externa de 10 kΩ
sí o sí**. Tu sistema actual con Arduino funciona sin resistencias porque usás el
pull-up interno; en estos cuatro pines eso no existe. Es un cambio obligatorio.

**c) Los relés son activo-LOW.** Durante el arranque los GPIO del ESP32 quedan en alta
impedancia hasta que el firmware los configura. Con módulos activo-LOW eso significa
**todos los relés encendidos durante ~300 ms en cada reset** — todas las luces de la
casa prendiéndose en cada reinicio. Se resuelve con **pull-up de 10 kΩ en cada línea de
control**, que mantiene el relé apagado hasta que el firmware toma el control. No es
opcional en una instalación real.

---

## 2. El problema de presupuesto

22 pines utilizables, de los cuales 6 deberían quedar para analógico y 2 para I²C.
Quedan **14 pines** para repartir entre relés y entradas digitales.

Tu pregunta era si se puede llegar a 12 relés sin sacrificar demasiado las entradas.
**La respuesta honesta es que en conexión directa, no.** 12 relés dejan 2 entradas
digitales. Para un sistema que querés que acepte PIR, gas, luz y botones, eso no
alcanza.

Pero hay una salida limpia, que es la Alternativa C.

---

## 3. Alternativas de asignación

### Alternativa A — 8 relés directos, máxima entrada

Sin chips adicionales. La más simple de construir y depurar.

| Función | Pines | Cant. |
|---|---|---:|
| **Relés 1-8** | `13` `16` `17` `18` `19` `23` `25` `26` | 8 |
| I²C reservado (SDA/SCL) | `21` `22` | 2 |
| Entradas digitales | `2` `4` `5` `14` `15` `27` | 6 |
| Entradas analógicas | `32` `33` `34` `35` `36` `39` | 6 |
| **Total entradas** | | **12** |

**Capacidad RJ12:** 3 puertos de 4 líneas · o 6 puertos de 2 líneas · o 12 de 1 línea.

- ✅ Simple, barata, sin dependencias de software extra
- ✅ Deja I²C libre para pantalla OLED, RTC o expansión futura
- ❌ Tope duro de 8 relés

---

### Alternativa B — 12 relés directos

Exprime el chip al máximo. Sacrifica el bus I²C.

| Función | Pines | Cant. |
|---|---|---:|
| **Relés 1-12** | `4` `13` `16` `17` `18` `19` `21` `22` `23` `25` `26` `27` | 12 |
| Entradas digitales | `2` `5` `14` `15` | 4 |
| Entradas analógicas | `32` `33` `34` `35` `36` `39` | 6 |
| **Total entradas** | | **10** |

**Capacidad RJ12:** 2 puertos de 4 líneas + 1 de 2 · o 5 puertos de 2 líneas.

- ✅ Llega a 12 relés sin hardware extra
- ❌ **Sin I²C**: no hay pantalla, ni RTC, ni expansión posterior. El módulo queda cerrado
- ❌ Las 4 entradas digitales son todas pines con glitch de arranque
- ❌ Si mañana querés un relé más, hay que rediseñar

---

### Alternativa C — Relés por expansor I²C ⭐ recomendada

Un **MCP23017** (~USD 2) da 16 salidas usando solo 2 pines del ESP32. Los relés no
tienen requisitos de temporización — conmutan en milisegundos y se accionan unas pocas
veces por hora — así que pasarlos por I²C no cuesta nada en la práctica.

| Función | Pines ESP32 | Cant. |
|---|---|---:|
| I²C (SDA/SCL) → MCP23017 | `21` `22` | 2 |
| **Relés 1-16** | *(vía expansor, 0 pines del ESP32)* | 0 |
| Entradas digitales | `2` `4` `5` `13` `14` `15` `16` `17` `18` `19` `23` `25` `26` `27` | 14 |
| Entradas analógicas | `32` `33` `34` `35` `36` `39` | 6 |
| **Total entradas** | | **20** |

**Capacidad RJ12:** 5 puertos de 4 líneas · o 10 puertos de 2 líneas.

- ✅ **12 relés y 20 entradas** — más del doble que la Alternativa B
- ✅ 4 salidas de relé de sobra para crecer
- ✅ Un segundo MCP23017 (dirección `0x21`) suma **16 entradas más** sin gastar un solo
  pin adicional — tiene salida de interrupción, así que no hay que hacer polling
- ✅ El expansor es sacrificable: si una línea de 10 m mete una sobretensión, se quema
  un chip de dos dólares y no el ESP32
- ❌ Una dependencia de software más (librería del MCP23017, trivial)
- ❌ Un chip más que soldar

> **Por qué la recomiendo:** el costo es un chip de dos dólares y resuelve de una vez el
> techo de pines. Las alternativas A y B te dejan contra el límite el día uno; la C te
> deja margen para los próximos años, que es justo lo que pedís cuando decís
> "configurarlo de la forma más versátil posible".

---

## 3.bis ¿Y usar el Arduino Pro Mini como expansor?

Tenemos un **Arduino Pro Mini (ATmega328P)** y un adaptador **FTDI FT232RL** para
programarlo (MCU-003 y PRO-005 en el inventario). Evaluación honesta de si conviene
meterlo en el diseño.

### Para expansión digital: no conviene

| | MCP23017 | Pro Mini como esclavo I²C |
|---|---|---|
| Firmware a mantener | Ninguno | Un segundo proyecto con su build y su debug |
| Fiabilidad | Determinística | El esclavo TWI de `Wire` corre en contexto de ISR; es **frágil** y fuente clásica de cuelgues intermitentes |
| Interrupción al host | Integrada (INTA/INTB) | Hay que implementarla a mano |
| Latencia | Predecible | Depende de qué esté haciendo el AVR |
| Costo | ~USD 2 | Ya está comprado, pero cuesta horas |

En un sistema que controla la iluminación de una casa, un cuelgue intermitente de I²C
a las 2 de la mañana es justamente lo que hay que evitar. **Para digital, MCP23017.**

### Para entradas analógicas: acá sí tiene sentido

Es su ventaja real sobre el ESP32:

| | ESP32 (ADC1) | Pro Mini |
|---|---:|---:|
| Canales analógicos | 6 | **8** (A0-A7) |
| Resolución | 12 bit | 10 bit |
| Linealidad / ruido | Mediocre, necesita oversampling | **Bastante mejor** |
| Tolerancia a 5 V | No — se daña | **Sí** (variante 5 V) |
| Pull-up interno | No en 34/35/36/39 | **Sí en todos** |

Y hay un argumento que no es técnico sino de riesgo: el Pro Mini de 5 V puede recibir
directo los 10 m de cable telefónico y los sensores de 5 V, haciendo de **parachoques
sacrificable**. Si una sobretensión lo mata, se pierden USD 3 y no el cerebro del
sistema.

### Recomendación

| Si necesitás... | Hacé esto |
|---|---|
| **≤ 6 entradas analógicas** | No lo uses. El ADC1 del ESP32 alcanza. Guardá el Pro Mini como repuesto y herramienta de banco |
| **> 6 entradas analógicas** | Pro Mini como **front-end analógico** dedicado sobre el bus I²C ya existente: 0 pines extra del ESP32 |
| **Más salidas digitales** | MCP23017, no el Pro Mini |
| **Más entradas digitales** | Segundo MCP23017 (dirección `0x21`), no el Pro Mini |

### Si se usa: el tema de los niveles de tensión

El Pro Mini es de **5 V** y el ESP32 de **3.3 V**. No se pueden conectar sin pensarlo.

- **I²C (recomendado si ya hay bus):** cuesta 0 pines adicionales. Con los pull-ups a
  3.3 V el ESP32 nunca ve más de 3.3 V, así que está protegido. El problema es el otro
  lado: el ATmega a 5 V tiene `VIH = 0.6 × VCC = 3.0 V`, y 3.3 V deja apenas **0.3 V de
  margen**. Funciona —es un truco conocido— pero es ajustado para una instalación
  permanente con variación térmica. **Usar un level shifter bidireccional BSS138
  (~USD 1)** y sacarse el tema de encima.
- **UART (alternativa más robusta):** protocolo simple, fácil de depurar, sin la
  fragilidad del esclavo TWI. Solo necesita un divisor resistivo en el RX del ESP32.
  Cuesta 2 pines (ej. UART2 en `16`/`17`), mientras que por I²C no cuesta ninguno.

> **No** bajar el Pro Mini a 3.3 V para evitar el level shifter: el ATmega328P a 3.3 V
> está especificado hasta ~13 MHz y esta placa tiene resonador de 16 MHz. Suele andar,
> pero fuera de especificación no es aceptable para algo que queda en la pared años.

### Lo que NO hace falta que haga

Una idea tentadora es usar el Pro Mini como **respaldo local** por si el ESP32 se
cuelga o se cae el WiFi. **No hace falta.** La lógica botón → relé corre entera dentro
del ESP32 y no necesita red para nada: si el WiFi se cae, las teclas de la pared
siguen funcionando igual. Agregar un segundo microcontrolador como respaldo
introduciría arbitraje sobre el bus de relés, que es mucha complejidad para resolver
un problema que no existe.

---

## 3.ter Asignación concreta para la carga declarada

**Carga definida (2026-10-31):** 6 botones de pared · 2 sensores PIR · 1 sensor de luz
de día. **Total: 9 líneas de entrada.**

> Nota que cambia el cálculo: los 6 pines de ADC1 (`32` `33` `34` `35` `36` `39`)
> **también funcionan como entradas digitales**, no solo analógicas. El presupuesto de
> entradas es por lo tanto mayor de lo que sugiere la tabla de la sección 7.

| Alternativa | Entradas disponibles | Necesarias | Margen |
|---|---:|---:|---:|
| **A** — 8 relés | 12 | 9 | **+3** ✅ |
| **B** — 12 relés | 10 | 9 | **+1** ⚠️ |
| **C** — 12 relés + MCP23017 | 20 | 9 | **+11** ✅ |

**Entra en las tres.** La B entra matemáticamente pero deja una sola entrada de
reserva, que para un sistema pensado para crecer es prácticamente cero.

### Asignación A — si 8 relés alcanzan

| Función | Pin | Notas |
|---|---|---|
| Relés 1-8 | `13` `16` `17` `18` `19` `23` `25` `26` | Pull-up 10 kΩ en cada uno |
| I²C (SDA/SCL) | `21` `22` | Libre para BH1750, OLED, RTC |
| Botones 1-6 | `2` `4` `5` `14` `15` `27` | Pull-up interno + RC de protección |
| PIR 1-2 | `32` `33` | Digitales; el HC-SR501 saca 3.3 V |
| Sensor de luz (LDR) | `34` | Analógico. Pull-down externo obligatorio |
| **Reserva** | `35` `36` `39` | 3 entradas analógicas libres |

### Asignación C — si querés los 12 relés ⭐

| Función | Pin | Notas |
|---|---|---|
| I²C (SDA/SCL) | `21` `22` | MCP23017 + sensores I²C + OLED |
| Relés 1-16 | *(vía MCP23017)* | 12 usados, 4 de reserva |
| Botones 1-6 | `13` `16` `17` `18` `19` `23` | Pines limpios, sin glitch de arranque |
| PIR 1-2 | `25` `26` | |
| Sensor de luz | `32` | Analógico, o por I²C y este pin queda libre |
| **Reserva** | `2` `4` `5` `14` `15` `27` `33` `34` `35` `36` `39` | **11 entradas libres** |

### Sobre el sensor de luz de día

El módulo LDR ya está comprado (SEN-001), así que **usalo**. Tiene salida analógica
(`AO`) y digital con umbral por trimpot (`DO`). Alimentado a 3.3 V ambas son seguras
para el ESP32.

Si con el tiempo el umbral resulta molesto de mantener, el camino de mejora es un
**BH1750** (~USD 2, I²C):

| | LDR + LM393 (lo que tenés) | BH1750 (mejora opcional) |
|---|---|---|
| Pines consumidos | 1 | **0** (comparte el bus I²C) |
| Salida | Valor crudo, varía con temperatura y envejecimiento | **Lux reales**, calibrados |
| Umbrales | A prueba y error; se corren con las estaciones | Directos: "menos de 50 lux = de noche" |

No es motivo para comprar nada ahora. Es la carta a jugar si el LDR te hace renegar.

---

## 3.quater Compatibilidad eléctrica de los sensores que tenemos

Revisión de los tres sensores del inventario contra los 3.3 V del ESP32. **Dos de los
tres necesitan atención.**

| Sensor | Alimentación | Salida | ¿Directo al ESP32? |
|---|---|---|---|
| **SEN-003** PIR HC-SR501 | 4.5-20 V (usar 5 V) | **3.3 V** por diseño | ✅ **Sí, directo** |
| **SEN-001** LDR + LM393 | 3.3 V ó 5 V | Sigue a VCC | ✅ **Sí, alimentándolo a 3.3 V** |
| **SEN-002** MQ-7 (CO) | **5 V obligatorio** | **~5 V** | ❌ **No. Divisor resistivo + ciclado del calefactor** |

### SEN-001 (luz): alimentarlo a 3.3 V, no a 5 V

El LM393 de estos módulos tiene salida en colector abierto con pull-up a VCC. Con
VCC = 5 V, el `DO` saca 5 V y **daña el pin del ESP32**. Y el `AO` es un divisor
resistivo alimentado por VCC, así que también escala a 5 V.

La solución es gratis: **alimentar el módulo con los 3.3 V del ESP32**. El LDR es una
resistencia y el LM393 funciona desde 2 V, así que a 3.3 V anda igual y ambas salidas
quedan dentro de rango. Un cable, cero componentes.

### SEN-002 (MQ-7, monóxido de carbono): el que da trabajo

**a) No se puede bajar a 3.3 V.** El calefactor de los MQ está especificado a 5 V. A
3.3 V no alcanza la temperatura de trabajo y las lecturas no significan nada.

**b) AO y DO salen a ~5 V** y hay que bajarlos antes del ESP32.

> ⚠️ **El conversor de nivel (PRO-006) sirve para `DO`, no para `AO`.** Los conversores
> bidireccionales tipo BSS138 son para señales **lógicas**: conmutan entre dos estados.
> La salida `AO` es **analógica** y un conversor lógico la destroza. Para `AO` va un
> **divisor resistivo** y nada más:

```
AO del MQ-7 ──[ 10 kΩ ]──┬── GPIO ESP32 (ADC1)
                         │
                      [ 20 kΩ ]
                         │
                        GND
```

Relación 2:1 → 5 V se convierten en 3.33 V. Ajustado; con 10 k / 15 k quedan 3.0 V y
más margen. **Verificar con el multímetro antes de conectar el pin.**

**c) El ciclado del calefactor — lo que casi nadie implementa**

Esto es específico del MQ-7 y es la diferencia entre medir CO y no medir nada. El
datasheet exige un **ciclo de dos fases**:

| Fase | Tensión del calefactor | Duración | Para qué |
|---|---|---|---|
| Alta | **5.0 V** | 60 s | Quema contaminantes adheridos al sensor (limpieza) |
| Baja | **1.4 V** | 90 s | **Medición** — la lectura válida se toma al final de esta fase |

Los módulos baratos como este **no implementan el ciclado**: dejan el calefactor a 5 V
fijo y sacan el `AO` de ahí. Esa lectura responde a gases combustibles en general, pero
**no es una medición de CO**. Si lo conectás tal cual, vas a tener un número que se
mueve y parece funcionar, sin que signifique lo que creés.

Para hacerlo bien hay que controlar la tensión del calefactor por **PWM desde el
ESP32** a través de un transistor (un MOSFET lógico tipo IRLZ44N o un 2N7000 para esta
corriente), con ~28 % de ciclo de trabajo para promediar 1.4 V. Es un circuito extra y
una máquina de estados de 150 s en el firmware.

**Decisión a tomar:** ¿vale la pena? Si lo que querés es *tendencia y alerta* de CO,
implementá el ciclado. Si no, el MQ-7 sin ciclar es poco más que un detector genérico
de "hay algo raro en el aire" — útil igual, pero hay que llamarlo por su nombre y no
confiar en el número como si fueran ppm de CO.

**d) Suma al presupuesto de energía:** ~150 mA en la fase alta, menos en la baja.

**e) No lo pongas al final de un cable RJ12 largo.** Por 10 m de cable telefónico de
28 AWG (ida y vuelta, ~4.3 Ω) los 150 mA producen **~0.64 V de caída**: el sensor
recibiría 4.4 V en vez de 5 V, y con un sensor cuyo funcionamiento depende de
tensiones precisas del calefactor, eso invalida la medición. Montalo cerca del módulo
o alimentalo localmente.

> ### ⚠️ El MQ-7 no reemplaza a un detector de CO homologado
>
> Esto merece decirse con claridad porque el monóxido de carbono mata sin olor ni
> aviso. Los MQ son componentes de hobby: derivan con el tiempo, necesitan 24-48 h de
> *burn-in*, son sensibles a humedad y temperatura, y no tienen certificación de
> seguridad ni autotest.
>
> Usalo para **automatización y tendencia** — registrar niveles, mandarte una alerta,
> encender un extractor. Para **protección de vida**, poné además un **detector de CO
> homologado** con alarma sonora propia, que funcione aunque este proyecto esté
> apagado, desprogramado o a medio armar. Cuesta poco y es independiente del sistema.

### SEN-003 (PIR): sin problemas

El HC-SR501 saca **3.3 V** aunque se lo alimente con 5 V — está pensado para eso. Es el
único de los tres que se conecta directo. Aun así, el RC de protección de la sección 6
sigue correspondiendo por los 10 m de cable.

Dos cosas a tener en cuenta al instalarlo:

- **Jumper H/L:** en `H` (disparo repetible) el pin se mantiene alto mientras haya
  movimiento. Es lo que querés para encender luces. En `L` dispara una sola vez y
  espera a que termine el retardo.
- **~60 segundos de calentamiento** al energizar, durante los cuales da falsos
  positivos. El firmware debería **ignorar los PIR durante el primer minuto** después
  de un arranque, o cada reset va a prender luces solo.

---

## 4. Alimentación

Cuenta rápida con 12 relés:

| Consumidor | Corriente |
|---|---:|
| 12 bobinas SRD-05VDC (~70 mA c/u, todas activas) | 840 mA |
| ESP32 con WiFi (picos de transmisión) | ~500 mA |
| 2 × PIR HC-SR501 (~50 mA c/u) | ~100 mA |
| 1 × MQ-7 (calefactor, fase alta) | ~150 mA |
| 1 × módulo LDR | ~10 mA |
| **Total pico** | **~1.6 A** |

El regulador AMS1117 de la DevKit **no puede** alimentar los módulos de relé — es solo
para el ESP32. Hace falta una fuente externa.

### Dos arquitecturas posibles

Tenemos un **LM2596S** (PWR-001) en el inventario, así que hay dos caminos:

| | **Opción 1 — Fuente de 5 V directa** | **Opción 2 — Fuente de 12 V + LM2596** |
|---|---|---|
| Qué comprar | Fuente conmutada **5 V / 3 A** | Fuente **12 V / 2 A** (si no tenés una) |
| Componentes | Ninguno más | LM2596S (ya lo tenés) |
| Puntos de falla | 1 | 2 |
| Margen de corriente | Holgado | **Ajustado** — ver abajo |
| Veredicto | ✅ **Recomendada si comprás nueva** | ✅ Buena **si ya tenés una fuente de 12 V dando vueltas** |

⚠️ **El límite real del LM2596:** el módulo se vende como "3 A", pero eso es el pico
absoluto del chip. **Sin disipador hace ~2 A continuos** antes de entrar en protección
térmica. Nuestro pico calculado es ~1.6 A, así que entra — pero con poco margen y el
módulo va a trabajar caliente. Si vas por la Opción 2, **ponele un disipador**; cuesta
centavos y le saca el tema de encima.

> ⚠️ **Ajustá la salida ANTES de conectar nada.** El LM2596 sale de fábrica con el
> trimpot en cualquier posición: puede estar en 30 V. Conectalo a la entrada, medí la
> salida con el multímetro, girá el trimpot hasta leer **5.0 V exactos**, y recién ahí
> conectá el resto. Al revés, te llevás puesto todo el módulo de una.

### El MT3608 no tiene rol acá

El **MT3608** (PWR-002) es un elevador: solo sube tensión. En este diseño todo baja de
la fuente hacia 5 V y 3.3 V, así que no hay dónde usarlo. Queda de repuesto para otro
proyecto. Lo menciono para que no quede dando vueltas la duda de si falta integrarlo.

### ¿Dónde hace falta el conversor de niveles TXS0108E?

Tenemos uno (PRO-006), pero conviene revisar si el diseño realmente lo necesita. La
respuesta corta es que **probablemente no**:

| Interfaz | ¿Necesita conversor? | Por qué |
|---|---|---|
| ESP32 ↔ MCP23017 | ❌ No | El MCP23017 funciona a **3.3 V**. Mismo nivel, conexión directa |
| ESP32 ↔ módulos de relé | ❌ No | Se resuelve con el jumper JD-VCC: lado opto a 3.3 V |
| ESP32 ↔ LDR (SEN-001) | ❌ No | Se alimenta a 3.3 V y sus salidas quedan en rango |
| ESP32 ↔ PIR (SEN-003) | ❌ No | El HC-SR501 ya saca 3.3 V |
| ESP32 ↔ **`AO` del MQ-7** | ❌ **No sirve** | Es **analógica**. Un conversor lógico la destroza. Va **divisor resistivo** |
| ESP32 ↔ `DO` del MQ-7 | ⚠️ Opcional | Es la única línea de 5 V. Un divisor resistivo de dos resistencias también alcanza |

**Conclusión:** si usás la salida analógica del MQ-7 (que es la que sirve para medir),
**no necesitás el conversor en ninguna parte**. Guardalo: el día que agregues algo de
5 V con varias líneas digitales, es la herramienta correcta.

> Un detalle si algún día lo usás en I²C: el TXS0108E tiene mala fama en ese bus. Sus
> aceleradores *one-shot* chocan con los pull-ups de I²C y generan fallas difíciles de
> diagnosticar. Para I²C conviene un conversor discreto a BSS138.

### Nivel lógico: usar el jumper JD-VCC

Los módulos de relé son de 5 V y el ESP32 saca 3.3 V. Un HIGH de 3.3 V contra un riel
de 5 V deja solo 1.7 V sobre el optoacoplador — **puede no apagar el relé de forma
confiable**. Es una falla intermitente clásica y molesta de diagnosticar.

La solución está en los módulos que ya tenés:

1. **Quitar el jumper JD-VCC**
2. Alimentar `VCC` (lado lógico/opto) con **3.3 V** del ESP32
3. Alimentar `JD-VCC` (bobinas) con **5 V** de la fuente

Así el opto ve 3.3 V contra 3.3 V y conmuta limpio, mientras las bobinas reciben sus
5 V. Verificar con el multímetro antes de energizar: los módulos clones a veces traen
la serigrafía cambiada.

---

## 5. Conectores

### 5.1 Pinout RJ12 — y una trampa importante

⚠️ **Los cables telefónicos RJ12 estándar son cruzados** (*rollover*): el pin 1 de un
extremo llega al pin 6 del otro. Los cables de red son derechos; los telefónicos no.

Esto no es un detalle menor: si tu pinout pone **+5 V en el pin 1 y GND en el pin 6**,
un cable cruzado **cortocircuita la fuente**. Con cables de 10 m ya tendidos en la casa,
el riesgo es concreto.

**Tres medidas, las tres recomendadas:**

1. Usar **solo cable derecho** (pin a pin) y verificar cada uno con continuidad antes de
   instalarlo. Etiquetarlos.
2. Poner un **fusible rearmable PTC (polyfuse) de 500 mA en la línea de 5 V de cada
   puerto**. Cuesta centavos y convierte un cortocircuito en una molestia.
3. Elegir un pinout **tolerante a inversión**:

| Pin | Señal | Al revés queda |
|---:|---|---|
| 1 | GND | +5 V ❌ |
| 2 | D1 | D4 |
| 3 | D2 | D3 |
| 4 | D3 | D2 |
| 5 | D4 | D1 |
| 6 | +5 V | GND ❌ |

Las líneas de datos se permutan (recuperable: se repatcha). La alimentación se invierte
(destructivo). **Con el PTC, lo peor que pasa es que el puerto se apague.**

### 5.2 Conectores para el patch interno

Sobre tu duda con los Dupont: **tenés razón en desconfiar.** No tienen traba, los
crimpados se aflojan con vibración y ciclos térmicos, y es fácil correrse un pin. Para
un prototipo sobre la mesa están bien; para una instalación fija en la casa que querés
olvidar durante años, no.

| Opción | Fiabilidad | Reconfigurar | Veredicto |
|---|---|---|---|
| **Dupont 2.54** | Baja — sin traba | Instantáneo | Solo para el prototipo |
| **JST-XH 2.54** | Alta — con traba y polarizado | Requiere crimpadora | Bueno para lo que no se toca |
| **Bornera a tornillo KF301** | Muy alta | Destornillador, 10 s | **Ideal para el patch** — y ya tenés ~22 |
| **Jumper shunt sobre headers** | Media | Instantáneo | Solo entre pines contiguos; no sirve para ruteo arbitrario |
| **Cable plano IDC** | Alta | Nada | Para tramos fijos en bloque |

### 5.3 La recomendación de fondo: no hagas un crossbar

Con 5 puertos RJ12 × 4 líneas tenés 20 puntos de patch. Una matriz donde cualquier línea
pueda ir a cualquier pin son 20 cables sueltos adentro de la caja: imposible de
documentar, imposible de diagnosticar a los dos años, y cada cable es un punto de falla.

**Propuesta alternativa — puertos tipificados.** En vez de que todo sea patcheable,
definir 3 tipos de puerto con ruteo fijo en el PCB:

| Tipo | Líneas | Ruteo fijo a | Para |
|---|---|---|---|
| **Tipo B** (botón) | 4 × digital con pull-up | Pines digitales | Botones de pared, finales de carrera, reed switches |
| **Tipo S** (sensor) | 2 × analógico + 2 × digital | ADC1 + digitales | Gas, LDR, temperatura, PIR |
| **Tipo X** (libre) | 4 × patcheable por bornera | Campo de patch | Lo que no entre en B ni en S |

Con, digamos, 3 puertos B + 2 puertos S + 1 puerto X cubrís prácticamente todo, y
quedan **4 cables de patch** en la caja en vez de 20. Un puerto Tipo X alcanza para los
casos raros, que son pocos.

Si después hace falta otro puerto especial, se cambia un Tipo B por un Tipo X y listo.

---

## 6. Protección de entradas — no la saltees

Tu sistema actual anda "sin capacitores ni resistencias" y es cierto que funciona. Pero
hay dos diferencias que cambian el cálculo:

- El Arduino es de **5 V y tolerante**; el ESP32 es de **3.3 V** y sus GPIO son bastante
  más frágiles ante ESD y transitorios.
- Si el RJ12 lleva **5 V** y un sensor devuelve una señal de 5 V a un pin del ESP32, **lo
  destruís**. Los PIR HC-SR501 alimentados a 5 V sacan 3.3 V en la salida y están bien,
  pero no todos los sensores se portan igual. Hay que verificar uno por uno.

**Por cada línea de entrada (son centavos):**

```
Pin RJ12 ──[ 1 kΩ ]──┬──[ 100 nF ]── GND     (antirrebote + filtro de ruido)
                     ├──[ 10 kΩ  ]── 3.3 V   (pull-up; OBLIGATORIO en 34/35/36/39)
                     └──[ TVS 3.3 V o zener ]── GND   (recorte de sobretensión)
                                │
                             GPIO ESP32
```

Con 10 metros de cable telefónico sin blindar corriendo al lado de la instalación
eléctrica de 220 V, el acoplamiento capacitivo mete ruido. En 5 V con Arduino se diluye;
en 3.3 V puede generar disparos fantasma. El RC de 1 kΩ + 100 nF (constante ~100 µs) lo
limpia sin afectar la pulsación de un botón.

---

## 7. Comparación final

| | Alt. A | Alt. B | **Alt. C** ⭐ |
|---|---:|---:|---:|
| Relés | 8 | 12 | **12** (hasta 16) |
| Entradas digitales | 6 | 4 | **14** |
| Entradas analógicas | 6 | 6 | **6** |
| **Entradas totales** | 12 | 10 | **20** |
| Puertos RJ12 de 4 líneas | 3 | 2 | **5** |
| I²C libre (OLED, RTC) | ✅ | ❌ | ✅ |
| Margen de crecimiento | ❌ | ❌ | ✅ |
| Chips extra | 0 | 0 | 1 |

---

## 8. Pendientes de definir

- [x] ~~Cuántos puntos de entrada~~ → **9** (6 botones + 2 PIR + 1 luz). Ver 3.ter
- [ ] **Cuántos circuitos de iluminación necesitás comandar** → define si es Alt. A o Alt. C
- [ ] Cómo se agrupan los 6 botones físicamente (define cuántos jacks RJ12 hacen falta)
- [x] ~~Qué modelo de MQ es SEN-002~~ → **MQ-7 (monóxido de carbono)**
- [x] ~~Conseguir un segundo HC-SR501~~ → **ya lo tiene**
- [ ] **¿Implementamos el ciclado del calefactor del MQ-7?** Define si hace falta un
      MOSFET y un pin PWM, o si el sensor queda como detector genérico
- [ ] **Arquitectura de alimentación:** fuente de 5 V directa, o 12 V + LM2596
      (¿tenés alguna fuente de 12 V ya disponible?)
- [ ] Si el sistema viejo de Arduino convive o se reemplaza de una
- [ ] Si se reutiliza el cableado telefónico ya tendido (verificar si es cruzado)
- [x] ~~Más de 6 entradas analógicas~~ → **no**. El Pro Mini queda como repuesto
- [ ] Protocolo de comunicación: MQTT, HTTP, o ambos
- [ ] Si querés que el módulo siga funcionando con WiFi caído (lógica local de respaldo)
