# CasaConnect v1 — Plan de trabajo

> Plan por fases para llegar del diseño en papel al módulo funcionando en la pared.
> Diseño: [`configuracion-v1.md`](configuracion-v1.md) ·
> [`circuito-v1.md`](circuito-v1.md) · [`comparticion-rj12.md`](comparticion-rj12.md)

## La idea de fondo: no serializar

El instinto es hacer **placas → componentes → software**, en ese orden. Conviene no
hacerlo, por dos razones:

1. **Comprar tiene el tiempo muerto más largo.** Si los componentes vienen de afuera
   pueden ser semanas. Ese pedido tiene que salir **primero**, antes de dibujar
   ninguna pista, porque nada físico avanza sin él.
2. **El software no necesita la PCB.** El DevKit, el módulo de relés, los sensores y
   los cables Dupont **ya están en el inventario**. Todo el firmware se puede escribir
   y probar en protoboard mientras llegan las compras y se etchan las placas.

Entonces el plan corre en **dos carriles paralelos** que se juntan al final:

```
  CARRIL FÍSICO     F0 compras ──> F3 Placa A ──> F4 Placa B ──> F5 cables
                         │                                          │
                         │                                          v
  CARRIL LÓGICO     F1 protoboard ──> F2 firmware ──────────> F6 integración
```

El carril lógico arranca **hoy**, sin esperar nada.

---

## Fase 0 — Desbloqueo y compras

**Arranca ya. Bloquea todo el carril físico.**

| # | Tarea | Notas |
|---|---|---|
| 0.1 | **Buscar los 17 números LCSC** | Editar `PARTS` en [`../tools/generar-netlist.py`](../tools/generar-netlist.py). Hace doble función: habilita el netlist **y** es la lista de compras |
| 0.2 | **Decidir dónde comprar** | Local vs. importación. Define si la Fase 3 arranca en una semana o en dos meses |
| 0.3 | **Hacer el pedido** | Lista completa en [`lista-de-compras.md`](lista-de-compras.md). Pedir **repuestos** de lo barato |
| 0.3b | **Identificar PRO-003 y PRO-004** | El género de la tira de pines y de los Dupont define si hay que comprar el zócalo del ESP32 y cables hembra-hembra. **Antes del pedido** |
| 0.4 | **Medir el ancho de los dos DevKit** | Con calibre. 22.86 mm u 25.4 mm — y pueden diferir entre MCU-001 y MCU-002. Sin esto no se puede dibujar el zócalo |
| 0.5 | **Verificar el amperaje de la fuente de 5 V** | Mínimo 2 A, ideal 3 A |
| ~~0.6~~ | ~~Regenerar los netlists~~ | ✅ **Hecho.** Esquema de parejas, sin campo de patch. Placa A: 22 componentes · Placa B: **71** (eran 87) |

> ⚠️ **0.1 es el cuello de botella real.** Un número LCSC equivocado carga un
> componente incorrecto en EasyEDA que no se puede corregir después de importar.
> Verificá los 15 con calma; es el único paso del proyecto sin vuelta atrás.

---

## Fase 1 — Prototipo en protoboard

**Arranca ya, en paralelo con la Fase 0. No necesita comprar nada.**

Todo sale del inventario: DevKit, módulo de 8 relés, 2 PIR, LDR, OLED, Dupont.

| # | Tarea | Qué valida |
|---|---|---|
| 1.1 | Alimentar el módulo de relés con el jumper JD-VCC quitado, `VCC` a 3.3 V | Que los 3.3 V conmuten los relés de forma confiable |
| 1.2 | Pull-up de 10 kΩ en una línea de relé, resetear el ESP32 varias veces | **Que el relé no se active durante el boot** |
| 1.3 | OLED por I²C, detectar `0x3C` | Dirección y bus |
| 1.4 | Leer un PIR y un botón con 10 m de cable telefónico real | Ruido, rebotes, si hace falta el RC |
| 1.5 | Leer el LDR por `AO` alimentado a 3.3 V | Rango útil del ADC |
| 1.6 | **Conmutar los 8 relés a la vez**, con y sin el capacitor de 1000 µF | Si el pico de 560 mA resetea el ESP32, y si el reservorio lo resuelve |

### Kit de banco — lo único que hay que tener a mano

| Componente | Cantidad |
|---|---:|
| R 10 kΩ | 1 (8 si querés probar los 8 canales) |
| R 1 kΩ | 1 |
| C 100 nF | **2** |
| C 1000 µF | 1 *(para el test 1.6)* |
| R 4.7 kΩ | 2 *(solo si el OLED no trae pull-ups de I²C)* |

**Dos capacitores de 100 nF, no doce.** Y están ahí para poder confirmar la solución:
el test 1.4 existe justamente para averiguar si el filtro RC hace falta. Sin ningún
capacitor podés ver el problema pero no verificar que se arregla.

### Resultados

| Test | Estado | Resultado |
|---|---|---|
| 1.1 Conmutación con 3.3 V | ✅ | Clic seco en ambos sentidos. Sin zumbido ni pegado |
| 1.2 Arranque sin disparo | ✅ | **20+ resets, ningún relé se activó.** El pull-up de 10 kΩ queda confirmado |
| 1.3 Bus I²C | ⏳ | |
| 1.4 Entradas — cable corto | ✅ | `GPIO2` lee bien con pull-up interno (**el LED de a bordo no interfiere**). Rebote: 4-5 transiciones en **menos de 10 ms**. Sin transiciones espurias en huecos de varios segundos |
| 1.4b Entradas — **10 m de cable real** | ⏳ | Lo que de verdad decide si el RC de 1 kΩ + 100 nF es obligatorio |
| 1.5 Lectura de ADC | ⏳ | |
| 1.6 Los 8 relés a la vez | ⏳ | Requiere los 8 canales cableados |

**Hallazgo lateral — el ESP32 ya trae pull-up interno en `GPIO13`:** sin la resistencia
externa, 10 encendidos en frío (cortando la alimentación por completo, con la potencia
de los relés conectada) **no dispararon el relé**. El AVR del sistema viejo sí lo hace,
porque arranca con los pines en alta impedancia real y el pull-up interno desactivado;
el ESP32 tiene pull-up activo en ese pad desde el reset.

**La resistencia externa se mantiene en el diseño.** Tres razones:

1. Los estados por defecto al reset son **distintos pin por pin**. Está verificado en
   `GPIO13`; los otros siete (`16 17 18 19 23 25 26`) podrían flotar.
2. Es un comportamiento que podría cambiar con una actualización del core.
3. Cuesta ocho resistencias. El riesgo de sacarlas no es cero; el de dejarlas, sí.

En `GPIO13` el resultado es que hay **doble protección**: el pull-up interno y el
externo. Margen de sobra.

> Nota sobre los "~33 kΩ equivalentes" calculados del divisor: es una **linealización
> válida solo en ese punto de trabajo**. La carga real es el LED del opto, que es no
> lineal, así que ese número no predice el comportamiento con otro valor de pull-up.

**Antirrebote:** con rebotes que se apagan en <10 ms, una ventana de **25 ms** por
software los filtra entera sin que la tecla deje de sentirse instantánea.

**Mediciones de referencia** (1 canal conectado, `VCC` del módulo a 3.3 V):

| Condición | `IN1` respecto de GND |
|---|---|
| Sin firmware — solo el pull-up, GPIO en alta impedancia | **2.54 V** |
| Firmware corriendo, relé apagado — GPIO manejando el pin | **3.3 V** |

Los 2.54 V implican una carga equivalente de ~33 kΩ dentro del módulo, y dejan
0.76 V sobre el camino del opto: por debajo del umbral de ~1.1 V del LED, con
0.34 V de margen. Sobre el papel es ajustado; los 20 resets confirman que alcanza.

> Probado sobre **1 canal de 8**. Los ocho circuitos son idénticos y cada pull-up es
> independiente, así que es una muestra sólida. Conviene repetirlo con los 8 cableados
> como verificación final, pero el valor de 10 kΩ ya se puede dar por decidido.

### Dos configuraciones de banco

La fuente definitiva es **switching de 5 V / 2 A**. Alcanza: el pico de la v1 es
~1.2 A (560 mA de bobinas + ~500 mA del ESP32 en ráfaga de TX + ~125 mA de sensores).

⚠️ **Nunca el USB y la fuente a la vez** en el pin `5V`: en muchos DevKit ese pin va
directo al VBUS del USB y tendrías dos fuentes enfrentadas. No hace falta, porque los
tests se parten solos en dos grupos.

**Configuración A — desarrollo** (tests 1.1 a 1.5 y toda la Fase 2)

```
  USB ──────────> ESP32            ← alimenta y da el monitor serie
                    └─ 3V3 ──────> VCC del módulo (opto) · OLED · LDR
  Fuente 5V ────> JD-VCC · PIR
            └───> GND común ─────> GND del ESP32
```

**Configuración B — test 1.6** (y validación final)

```
  USB DESCONECTADO
  Fuente 5V ──┬──> ESP32 pin 5V   ┐
              ├──> JD-VCC          ├─ mismo riel, como en producción
              └──> PIR             ┘
```

> ⚠️ **El test 1.6 solo vale en la configuración B.** Si el ESP32 está en el USB y las
> bobinas en la fuente, son rieles distintos: el pico no puede alcanzar al ESP32 y el
> test **pasa siempre, sin significar nada**. La pregunta es si 560 mA tirados del
> *mismo* riel lo resetean — y para eso tienen que compartirlo.

**Cómo leer el resultado sin monitor serie:** con el USB desconectado no hay consola.
El sketch de banco guarda un **contador de arranques en NVS** y lo muestra en el OLED.
Si después de conmutar los relés el número subió, hubo reset.

### Prerrequisitos que no son obvios

- **Soldarle los pines macho a un DevKit.** Vienen sin soldar. No es trabajo perdido:
  el diseño final usa zócalo, así que el ESP32 lleva pines macho igual.
- **Protoboard.** No figura en el inventario. Los tests 1.1, 1.3 y 1.5 se pueden hacer
  con Dupont de módulo a módulo, pero el 1.2, 1.4 y 1.6 tienen componentes sueltos.

**Por qué esta fase importa más de lo que parece:** cada una de esas seis cosas es una
**suposición** del diseño, no un hecho verificado. Si alguna falla, es mucho más
barato enterarse ahora que después de etchar dos placas. Dos en particular pueden
cambiar el circuito: el **1.2** (si los pull-ups de 10 kΩ no alcanzan, hay que bajar
a 4.7 kΩ) y el **1.6** (si el reservorio no alcanza, hay que agrandarlo o repensar
la distribución de la alimentación).

> **Punto de control:** si 1.1 o 1.2 fallan, parar y rediseñar antes de seguir.

---

## Fase 2 — Firmware

**Sobre el protoboard de la Fase 1. En paralelo con todo el carril físico.**

| # | Tarea | Por qué en este orden |
|---|---|---|
| 2.1 | **Tabla de particiones + OTA andando** | **Va primero.** Cambiarla después obliga a reflashear por USB, que es justo lo que OTA evita |
| 2.2 | WiFi + NTP | Hora real sin RTC, para los timestamps |
| 2.3 | Lógica botón → relé, **local y sin red** | El corazón. Tiene que andar con el WiFi caído |
| 2.4 | Antirrebote y pulsación larga | La larga es el gesto de "mostrar estado" en el OLED |
| 2.5 | OLED guiado por eventos | Enciende con cada evento, se apaga a los 10 s |
| 2.6 | PIR con **supresión del primer minuto** | El HC-SR501 da falsos positivos ~60 s al arrancar |
| 2.7 | Sensor de luz con umbral configurable | Por software, no por trimpot |
| 2.8 | Persistir el estado de los relés | Que un corte de luz no deje la casa a oscuras o encendida |

> **2.1 primero no es un capricho.** Una vez que hay OTA, cada iteración siguiente son
> segundos en vez de desarmar y enchufar el USB. Es la tarea que acelera todas las
> demás.

---

## Fase 3 — Placa A (Control)

**Depende de:** 0.1, 0.4, 0.6 y que hayan llegado los componentes.

22 componentes. Chica y simple — **se hace primero a propósito**, para aprender el
proceso de etching con la placa barata antes de jugarse la complicada.

| # | Tarea |
|---|---|
| 3.1 | Importar el netlist en EasyEDA Pro, revisar el esquemático |
| 3.2 | Rutear a 1 capa con los anchos de la §9 de `circuito-v1.md`, resolver lo que falte con puentes |
| 3.3 | Imprimir 1:1, transferir, etchar, perforar |
| 3.4 | Soldar por bloques y probar según el orden de la §9: alimentación → ESP32 → OLED → relés |

> **Punto de control:** con la Placa A funcionando, el firmware de la Fase 2 ya corre
> sobre hardware definitivo. El sistema queda **utilizable** aunque la Placa B no
> exista: 8 relés comandados por MQTT o por horario. Es un primer hito real.

---

## Fase 4 — Placa B (Entradas)

**Depende de:** Fase 3 terminada (por la experiencia, no por el hardware).

71 componentes, pero el ruteo es **repetitivo**: 12 redes de protección idénticas en
fila, que es lo más fácil de hacer a una cara.

| # | Tarea |
|---|---|
| 4.1 | Importar el netlist, revisar |
| 4.2 | Rutear. Los jacks en **una sola fila**, con los compañeros pegados: `P1 P4 · P2 P5 · P3 P6` |
| 4.3 | Etchar, perforar, soldar |
| 4.4 | Probar **una entrada** completa antes de soldar las 12 |
| 4.5 | Dejar puesto el header de 12 pines sin poblar (salida de emergencia) |

> ⚠️ **4.4 no se saltea.** Si la red de protección tiene un error de diseño, soldar
> las 12 primero significa desoldar 48 componentes.

---

## Fase 5 — Cables y puertos

**Depende de:** Fase 4.

| # | Tarea | Notas |
|---|---|---|
| 5.1 | Armar los cables RJ12 **derechos** (pin a pin) | Los telefónicos comunes son **cruzados** |
| 5.2 | Verificar continuidad de **cada** cable antes de instalarlo | Un cable cruzado pone 5 V contra GND |
| 5.3 | Etiquetar los dos extremos | Puerto y línea: `P1.L2` |
| 5.4 | Instalar en las cajas según el plan de parejas | Respetar la regla de 4 líneas por pareja |
| 5.5 | Pegar la tabla de parejas dentro de la tapa del tablero | Dentro de dos años, esto vale oro |

> El PTC de cada puerto convierte un cable cruzado en "ese puerto no anda" en lugar de
> un cortocircuito. Pero **verificá igual**: el PTC es la red, no el plan.

---

## Fase 6 — Integración y puesta en marcha

**Depende de:** Fases 2, 4 y 5.

| # | Tarea |
|---|---|
| 6.1 | Montar todo en el gabinete, cableado definitivo de 220 V a los relés |
| 6.2 | Prueba completa: los 6 botones, los 2 PIR, el sensor de luz, los 8 relés |
| 6.3 | Prueba de corte: desconectar el WiFi y confirmar que los botones **siguen andando** |
| 6.4 | Prueba de reinicio: cortar la alimentación y confirmar que ningún relé se activa al arrancar |
| 6.5 | Migración desde el sistema viejo de Arduino |

> ⚠️ **6.1 es la única fase con 220 V.** Cortar la llave térmica antes de tocar nada.
> Y hasta acá nada del proyecto tuvo tensión de red: fue a propósito.

---

## Qué se puede hacer en paralelo

| Semana (relativa) | Carril físico | Carril lógico |
|---|---|---|
| 1 | F0: LCSC, medir, pedir | F1: protoboard |
| 2 → llegada | *esperando el pedido* | F2: firmware (2.1 a 2.5) |
| llegada + 1 | F3: Placa A | F2: firmware (2.6 a 2.8) |
| +2 | F4: Placa B | pruebas sobre Placa A |
| +3 | F5: cables | ajustes |
| +4 | F6: integración | |

La columna del medio tiene un hueco de espera que **el carril lógico llena por
completo**. Si en cambio se hiciera todo en serie, ese hueco sería tiempo perdido y el
firmware recién empezaría al final.

---

## Decisiones todavía abiertas

| # | Pregunta | Bloquea |
|---|---|---|
| D1 | **¿Dónde comprás los componentes?** Local o importado | Define la escala de tiempo de todo el carril físico |
| D2 | **¿El sistema viejo de Arduino convive o se reemplaza?** | Fase 6.5. Si conviven, hay que decidir qué circuitos pasa cada uno |
| D3 | ¿Alguna caja va a usar las 4 líneas? | Ya respondido: **sí, y se acepta anular el puerto compañero**. Contemplado |

> **D1 es la que más cambia el plan.** Si comprás local, el carril físico arranca esta
> semana y el proyecto puede estar andando en un mes. Si importás, el carril lógico va
> a terminar mucho antes que el físico — y conviene aprovecharlo para dejar el firmware
> completo y probado.

---

## Riesgos y qué hacer con cada uno

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Un número LCSC equivocado | Media | Verificar los 15 en 0.1. Es irreversible después de importar |
| Los 3.3 V no conmutan los relés | Baja | Se detecta en **1.1**, antes de etchar nada |
| Los relés se activan al bootear | Media | Se detecta en **1.2**. Si los pull-ups no alcanzan, bajar a 4.7 kΩ |
| Ruido en los 10 m de cable | Media | Se detecta en **1.4**. El RC ya está previsto en el diseño |
| Error en la red de protección | Baja | Se detecta en **4.4**, con 1 entrada en vez de 12 |
| Etching fallido | **Alta** (es casero) | Por eso la Placa A va primero: es la barata para aprender |
| Cable RJ12 cruzado | Media | PTC por puerto + verificación en 5.2 |

Fijate que **cinco de los siete riesgos se detectan en la Fase 1 o en pruebas
parciales**, antes de haber invertido trabajo significativo. Esa es toda la razón por
la que el protoboard va primero y por la que la Placa A se prueba por bloques.
