# Compartir GPIO entre puertos RJ12 — esquemas ensayados

> Propuesta: eliminar el campo de patch cableando de fábrica cada GPIO a **dos líneas
> de puertos distintos**, aprovechando que nunca se pueden usar las 24 líneas a la vez.
> Se gana simplicidad; se paga con una regla que hay que respetar al armar los cables.

## Lo que se gana y lo que se pierde

| | Campo de patch | Compartición cableada |
|---|---|---|
| Borneras KF301 | **18** | 0 |
| Cables internos | hasta 12 | **0** |
| Área de PCB | Grande | Mucho menor |
| Reconfigurar | Destornillador | **Cortar pista** |
| Reglas a recordar | Ninguna | Una tabla |

Para una placa casera, sacar 18 borneras y los cables internos es un ahorro grande de
trabajo y de puntos de falla.

---

## La restricción que no cambia con ningún esquema

**12 GPIO de entrada. 24 líneas posibles. Se usan 9.**

Ningún esquema crea capacidad: en todos sobran exactamente **3 líneas**. Lo único que
cambia entre esquemas es **dónde** se pueden gastar esas 3 y **qué tan difícil es la
regla**.

## Por qué "contiguos" falla

Emparejando vecinos directos — (P1,P2), (P3,P4), (P5,P6) — cada pareja dispone de
4 GPIO para sus 8 líneas. Con tu carga real:

| Pareja | Necesita | Disponible | |
|---|---:|---:|---|
| P1 (3 líneas) + P2 (3 líneas) | **6** | 4 | ❌ **No entra** |
| P3 (2) + P4 (1) | 3 | 4 | ✓ |
| P5 (0) + P6 (0) | 0 | 4 | ✓ desperdiciadas |

P1 y P2 son los dos puertos cargados (2 botones + 1 PIR cada uno) y quedarían
compitiendo por los mismos 4 pines, mientras la pareja P5-P6 desperdicia los suyos.

**El criterio correcto es emparejar por carga complementaria:** un puerto cargado con
uno liviano. Y eso se puede hacer *sin perder* la contigüidad física, simplemente
eligiendo la disposición de los jacks.

```
   ┌────┐ ┌────┐ ┌────┐
   │ P1 │ │ P2 │ │ P3 │   ← fila superior: puertos cargados
   └─┬──┘ └─┬──┘ └─┬──┘
     │      │      │       cada uno comparte con el de abajo
   ┌─┴──┐ ┌─┴──┐ ┌─┴──┐
   │ P4 │ │ P5 │ │ P6 │   ← fila inferior: puertos livianos / reserva
   └────┘ └────┘ └────┘
```

Las parejas quedan **verticalmente contiguas**, que es lo más corto de rutear.

---

## Esquema 1 — Parejas complementarias ⭐

Tres parejas fijas: **(P1,P4) · (P2,P5) · (P3,P6)**.

**La regla, en una frase:** *cada puerto tiene un compañero; entre los dos pueden usar
4 líneas, y nunca la misma línea en ambos.*

### Mapa de GPIO

Los pines se reparten para que **cada pareja tenga 2 digitales y 2 analógicas**:

| Línea | Pareja (P1,P4) | Pareja (P2,P5) | Pareja (P3,P6) | Tipo |
|---|---|---|---|---|
| **L1** | `GPIO2` | `GPIO5` | `GPIO15` | Digital, pull-up interno |
| **L2** | `GPIO4` | `GPIO14` | `GPIO27` | Digital, pull-up interno |
| **L3** | `GPIO32` | `GPIO33` | `GPIO36` | **ADC** (36 es solo-entrada) |
| **L4** | `GPIO34` | `GPIO35` | `GPIO39` | **ADC**, solo-entrada |

**Regla mnemotécnica que vale para los 6 puertos:**

- **L1 y L2 → digitales.** Botones, PIR, reed switches. Pull-up interno, nada que hacer.
- **L3 y L4 → analógicas.** Sensores con salida de tensión.
- **L4 siempre es solo-entrada** → si ahí va un botón, hay que **poner el jumper de
  pull-up**. Si va un sensor analógico, **sacarlo**.

### Dónde conviene poner el sensor de luz

Acá aparece algo que no es obvio. Si el sensor de luz va en **P4.L4** (`GPIO34`), la
pareja (P1,P4) queda **completamente llena**: P1 usa L1, L2, L3 y P4 usa L4. Los
4 GPIO consumidos, cero margen. Y las 3 líneas libres se concentran en las otras dos
parejas.

Si en cambio va en **P6.L3** (`GPIO36`), queda **exactamente 1 línea libre en cada
pareja**:

| Sensor de luz en... | Libre en (P1,P4) | Libre en (P2,P5) | Libre en (P3,P6) |
|---|---:|---:|---:|
| P4.L4 | **0** ❌ | 1 | 2 |
| **P6.L3** ⭐ | **1** | **1** | **1** |

Mismo total de 3, repartido de forma pareja en vez de dejar una pareja sin aire. Como
el sensor de luz es el único elemento que podés ubicar libremente (los botones y los
PIR dependen de dónde estén las cajas), conviene usarlo justamente para equilibrar.

### Cómo queda tu configuración

| Puerto | Línea | Señal | GPIO | Jumper PU |
|---|---|---|---|---|
| **P1** | L1 | Botón 1 | `GPIO2` | — |
| | L2 | Botón 2 | `GPIO4` | — |
| | L3 | PIR 1 | `GPIO32` | — |
| | L4 | *libre* | `GPIO34` | |
| **P2** | L1 | Botón 3 | `GPIO5` | — |
| | L2 | Botón 4 | `GPIO14` | — |
| | L3 | PIR 2 | `GPIO33` | — |
| | L4 | *libre* | `GPIO35` | |
| **P3** | L1 | Botón 5 | `GPIO15` | — |
| | L2 | Botón 6 | `GPIO27` | — |
| | L3 | *(bloqueada: la usa P6)* | | |
| | L4 | *libre* | `GPIO39` | |
| **P4** | L1-L3 | *(bloqueadas: las usa P1)* | | |
| | L4 | *libre* — comparte con P1.L4 | `GPIO34` | |
| **P5** | L4 | *libre* — comparte con P2.L4 | `GPIO35` | |
| **P6** | **L3** | **Sensor de luz (`AO`)** | `GPIO36` | **SACADO** |
| | L4 | *libre* — comparte con P3.L4 | `GPIO39` | |

**Capacidad libre: 3 líneas, una por pareja** — y las tres son analógicas, así que
sirven tanto para un sensor como para un botón (poniendo el jumper de pull-up).

| Pareja | GPIO libre | Se puede usar en |
|---|---|---|
| (P1,P4) | `GPIO34` | P1.L4 **o** P4.L4 |
| (P2,P5) | `GPIO35` | P2.L4 **o** P5.L4 |
| (P3,P6) | `GPIO39` | P3.L4 **o** P6.L4 |

> Notá que P4 y P5 quedan sin ninguna línea digital disponible, porque P1 y P2 ya se
> llevaron las suyas. Si lo que vas a sumar en el futuro son **botones**, van a tener
> que ir en una L4 con el jumper de pull-up puesto — funciona igual, pero conviene
> saberlo al armar el cable.

### Ventajas y límites

- ✅ Una sola regla, fácil de recordar y de poner en una etiqueta dentro de la tapa
- ✅ Ruteo cortísimo: cada pareja son dos jacks pegados
- ✅ Cada pareja tiene mezcla de digitales y analógicas
- ❌ La capacidad queda **encerrada en cada pareja**: si P1 y P4 necesitaran 5 líneas
  entre los dos, no se puede, aunque sobren líneas en otra pareja

---

## Esquema 2 — Compañero cruzado por grupo de líneas

Igual que el 1, pero **el compañero cambia según la línea**:

- **L1 y L2** → parejas (P1,P4) · (P2,P5) · (P3,P6)
- **L3 y L4** → parejas (P1,P2) · (P3,P4) · (P5,P6)

| GPIO | Comparten | | GPIO | Comparten |
|---|---|---|---|---|
| `GPIO2` | P1.L1 / P4.L1 | | `GPIO32` | P1.L3 / P2.L3 |
| `GPIO4` | P1.L2 / P4.L2 | | `GPIO34` | P1.L4 / P2.L4 |
| `GPIO5` | P2.L1 / P5.L1 | | `GPIO33` | P3.L3 / P4.L3 |
| `GPIO14` | P2.L2 / P5.L2 | | `GPIO35` | P3.L4 / P4.L4 |
| `GPIO15` | P3.L1 / P6.L1 | | `GPIO36` | P5.L3 / P6.L3 |
| `GPIO27` | P3.L2 / P6.L2 | | `GPIO39` | P5.L4 / P6.L4 |

Con tu carga:

| Puerto | Usa | GPIO |
|---|---|---|
| P1 | L1, L2, L3 | `2` `4` `32` |
| P2 | L1, L2, **L4** | `5` `14` `34` ← L3 bloqueada por P1 |
| P3 | L1, L2 | `15` `27` |
| P4 | L3 | `33` ← sensor de luz |
| **Libres** | P3/P4.L4 · P5/P6.L3 · P5/P6.L4 | `35` `36` `39` |

- ✅ Cada puerto tiene **dos compañeros distintos** → más combinaciones posibles
- ✅ **2 de las 3** líneas libres caen en P5/P6, que son justo las reservas (la tercera
  queda repartible entre P3 y P4)
- ❌ La regla es el doble de difícil: hay que mirar la tabla cada vez
- ❌ Las líneas analógicas de P1 y P2 compiten entre sí (los dos puertos cargados)

---

## Esquema 3 — Sin compartir, asignación graduada

Nada compartido. Cada puerto tiene su cupo fijo de líneas cableadas.

| Puerto | Líneas | GPIO | Pensado para |
|---|---:|---|---|
| **P1** | 3 | `GPIO2` `GPIO4` `GPIO32` | 2 botones + 1 PIR |
| **P2** | 3 | `GPIO5` `GPIO14` `GPIO33` | 2 botones + 1 PIR |
| **P3** | 2 | `GPIO15` `GPIO27` | 2 botones |
| **P4** | 2 | `GPIO34` `GPIO35` | Sensores analógicos |
| **P5** | 1 | `GPIO36` | Reserva |
| **P6** | 1 | `GPIO39` | Reserva |

- ✅ **Cero reglas.** Lo que dice la serigrafía del jack es lo que hay. Imposible
  equivocarse
- ✅ El ruteo más simple de los tres
- ✅ Todo puerto tiene al menos 1 línea garantizada
- ❌ Cupos **rígidos**: si P5 algún día necesita 3 líneas, no hay forma
- ❌ Las 2 líneas libres (P4.L2 y una de P3) no se pueden mover a otro puerto

---

## Comparación

| | Esq. 1 — Parejas | Esq. 2 — Cruzado | Esq. 3 — Graduado |
|---|---|---|---|
| Dificultad de la regla | **Baja** | Media | **Ninguna** |
| Flexibilidad | Media | **Alta** | Baja |
| Dónde quedan las 3 libres | 1 por pareja | **Concentradas en P5/P6** | Dispersas y fijas |
| Largo de pistas | **Corto** | Medio | **Corto** |
| Riesgo de error al cablear | Bajo | Medio | **Nulo** |

### Recomendación

**Esquema 1.** El 2 es más flexible pero la regla doble es justo el tipo de cosa que
dentro de dos años, con el tablero abierto y un sensor en la mano, se recuerda mal. El
3 es a prueba de errores pero demasiado rígido para algo que explícitamente querés que
crezca.

El 1 tiene una regla que entra en una frase, y la mnemotecnia de
**L1-L2 digitales / L3-L4 analógicas** hace casi imposible conectar algo en el pin
equivocado.

---

## Salida de emergencia, por si acaso

Cualquiera sea el esquema, la contra es que reconfigurar implica cortar una pista.
Por centavos se puede dejar una vía de escape:

**Un header de 12 pines con los GPIO de entrada, sin poblar.** Si algún día hay que
romper el esquema, se corta la pista compartida y se tira un cable desde ahí. También
sirve como punto de medición para diagnosticar con el osciloscopio o el multímetro.

Dejar los pads previstos cuesta nada. No tenerlos, el día que haga falta, significa
rehacer la placa.

---

## Lo que esto le cambia al diseño

Si se adopta, la Placa B pierde el campo de patch entero:

| | Antes | Después |
|---|---:|---:|
| Borneras KF301 | 18 | **0** |
| Componentes Placa B | 87 | **69** |
| Cables internos | hasta 12 | **0** |

Las 12 redes de protección **no cambian** — siguen una por GPIO, del lado del enlace a
la Placa A.

> ⚠️ Hay que regenerar los netlists: [`../tools/generar-netlist.py`](../tools/generar-netlist.py)
> todavía produce la versión con campo de patch.
