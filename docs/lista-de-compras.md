# CasaConnect v1 — Lista de componentes

> Lista completa para construir el módulo. Refleja el diseño **final**: dos placas,
> todo THT, con compartición de GPIO (sin campo de patch).
> Fases: [`plan.md`](plan.md) · Circuito: [`circuito-v1.md`](circuito-v1.md)

## Dos versiones

La PCB lleva **todos** los footprints. Lo que no se puebla en la v1 se suelda
después sin rehacer nada — ver §12 de [`circuito-v1.md`](circuito-v1.md).

| | **Mínima** ⭐ | Completa |
|---|---:|---:|
| Unidades a comprar | **~65** | ~130 |
| Tipos distintos | **12** | 17 |
| BAT85 | 0 | 30 |
| PTC | 2 | 8 |

**Comprá la mínima.** La diferencia es protección contra transitorios rápidos, y
tu sistema actual lleva años sin nada de eso en las mismas condiciones. Si algún
día aparece un problema, los pads ya están.

> ⚠️ Al soldar: un footprint vacío **en serie** necesita puente; uno **en paralelo**
> se deja pelado. Puentear un paralelo cortocircuita el riel. La tabla completa está
> en §12 de `circuito-v1.md`.

## Resumen

| | Ítems | Estado |
|---|---:|---|
| Ya tenés en el inventario | 7 | ✅ |
| Hay que verificar antes de comprar | 2 | ⚠️ **bloquean parte del pedido** |
| Hay que comprar (versión mínima) | 12 | 🛒 |
| Diferido — footprint sí, componente no | 5 | ⏸ |
| Tenías pero **ya no hacen falta** | 5 | — |

---

## ⚠️ Verificá esto primero — cambia el pedido

Dos ítems del inventario quedaron sin identificar y ahora importan.

### 1. La tira de pines alta (PRO-003) — ¿macho o hembra?

**Si es hembra 1×40:** cubre el zócalo del ESP32 (dos tiras de 19) y **no comprás
nada**.
**Si es macho:** hay que comprar **2 tiras hembra 1×19** (o una de 1×40 y cortarla).

> Mirala de perfil: si los pines salen de un cuerpo plástico grueso y hay agujeros
> arriba, es hembra. Si son pines desnudos que atraviesan una barra fina, es macho.

### 2. Los cables Dupont (PRO-004) — ¿qué género?

Sirven para unir la Placa A con el módulo de relés (header macho de 10 pines contra
los pines del módulo).

**Si tenés hembra-hembra:** listo.
**Si son todos macho-hembra:** comprá ~12 hembra-hembra.

---

## ✅ Ya lo tenés

| ID | Componente | Necesario | Tenés |
|---|---|---:|---:|
| MCU-001/002 | DevKit ESP32 38 pines | 1 | **2** |
| ACT-001 | Módulo relé 8 canales | 1 | 1 |
| SEN-003 | PIR HC-SR501 | 2 | 2 |
| SEN-001 | Módulo sensor de luz (LDR + LM393) | 1 | 1 |
| DSP-001 | OLED 0.96" SSD1306 I²C | 1 | 1 |
| PRO-001 | Bornera KF301 2 vías | **2** | ~22 |
| PRO-002 | Tira de pines macho 1×40 | 2 | 1-2 |

> **Las borneras pasaron de 18 a 2.** Al eliminar el campo de patch solo quedan la
> entrada de alimentación y la salida de 5 V al `JD-VCC`. Te sobran ~20.

> **Pines macho necesarios:** Placa A usa 34 (1×10 + 1×4 + 1×4 + 1×16) y Placa B usa
> 36 (1×16 + 4×2 + 1×12). Son **70 pines**, o sea **dos tiras de 40**. Si PRO-003
> resulta ser macho, estás cubierto; si es hembra, comprá una tira macho más.

---

## 🛒 Hay que comprar

### Semiconductores y pasivos

| # | Componente | Necesario | Pedir | Dónde va |
|---|---|---:|---:|---|
| 1 | **BAT85** Schottky DO-35 | 24 | **30** | Recorte, 2 por entrada |
| 2 | **R 10 kΩ** 1/4 W | 12 | **25** | 8 pull-up de relé + 4 pull-up conmutable |
| 3 | **R 1 kΩ** 1/4 W | 12 | **25** | Serie de cada entrada |
| 4 | **R 4.7 kΩ** 1/4 W | 2 | **10** | Pull-ups I²C |
| 5 | **C 100 nF** cerámico | 14 | **25** | 12 filtro de entrada + 2 desacople |
| 6 | **C 1000 µF / 16 V** electrolítico | 1 | **2** | Reservorio de la alimentación |

> ⚠️ **No sustituyas el BAT85 por 1N4148.** El de silicio cae 0.7 V y recortaría en
> 4.0 V, por encima del máximo del ESP32 (3.6 V). Tiene que ser **Schottky**.
> Alternativa válida: **BAT43** o **1N5819** (este último es más grande, DO-41).

> Las cantidades a pedir incluyen repuestos a propósito: una resistencia de más cuesta
> centavos; esperar tres semanas por una, no.

### Conectores

| # | Componente | Necesario | Pedir | Nota |
|---|---|---:|---:|---|
| 7 | **Jack RJ12 6P6C** montaje PCB | 6 | **8** | El componente más caro de la lista |
| 8 | **Fichas RJ12 6P6C** para crimpear | 12+ | **25** | 2 por cable |
| 9 | **PTC rearmable 500 mA** radial | 6 | **8** | Uno por puerto |
| 10 | **Portafusible PCB + fusible 2 A** | 1 | 1 + 3 | Entrada general |
| 11 | **Jumper shunt 2.54 mm** | 4 | **10** | Pull-ups conmutables |
| 12 | **Header hembra 1×19** | 2 | 2 | **Solo si PRO-003 es macho** — ver arriba |
| 13 | **Cable plano 16 vías** + 2 IDC hembra 16 | 1 | 1 | Enlace entre placas |
| 14 | Dupont **hembra-hembra** | ~12 | 20 | **Solo si PRO-004 no los incluye** |

### Para fabricar las placas

| # | Componente | Cantidad | Nota |
|---|---|---:|---|
| 15 | **Placa virgen de cobre** simple faz | 2-3 | Una de repuesto: el etching casero falla seguido |
| 16 | **Percloruro férrico** | 1 | Para atacar el cobre |
| 17 | **Gabinete** | 1 | Con espacio para 2 placas + módulo de relés + fuente |

### Verificar, no comprar

| Componente | Requisito | Tenés |
|---|---|---|
| **Fuente 5 V** | **Mínimo 2 A, ideal 3 A** | Decís que sí — **verificá el amperaje** |
| **Cable telefónico 6 hilos** | Lo que falte para las cajas nuevas | Ya hay tendido |
| **Crimpadora RJ12** | Para armar los cables | Suponemos que sí |

---

## Lo que tenés y **no** se usa en la v1

No es que sobren: quedan para la v2 o para otros proyectos.

| ID | Componente | Por qué queda afuera |
|---|---|---|
| MCU-003 | Arduino Pro Mini | Con 1 sola entrada analógica no hace falta front-end |
| ACT-002 | Módulo relé 4 canales | La v1 usa 8 relés y el de 8 ya los cubre |
| SEN-002 | Sensor MQ-7 (CO) | Decidido: fuera de la v1 |
| PWR-001 | LM2596 step-down | Se eligió fuente de 5 V directa |
| PWR-002 | MT3608 step-up | Sin rol: en este diseño todo baja de tensión |
| PRO-006 | Conversor TXS0108E | Ninguna interfaz lo necesita |

> **MCU-002** queda como repuesto del ESP32. Con cables de 10 m entrando a la casa,
> tener la segunda placa es buena noticia — y por eso el zócalo en lugar de soldar.

> **PRO-005 (FTDI)** no va montado en nada, pero guardalo: es la única forma de
> programar el Pro Mini, y sirve de segundo puerto serie para depurar.

---

## ⏸ Diferido — footprint en la placa, componente después

No comprar ahora. Si aparecen disparos fantasma o se daña una entrada, se sueldan
**solo en la entrada afectada**: 2 diodos y 1 capacitor.

| Componente | Cant. | Topología | Si no se puebla |
|---|---:|---|---|
| BAT85 | 24 | Paralelo | **Dejar vacío** |
| C 100 nF de entrada | 12 | Paralelo | **Dejar vacío** |
| R 10 kΩ pull-up conmutable | 4 | Paralelo | **Dejar vacío** |
| Jumper shunt | 4 | — | — |
| R 4.7 kΩ I²C | 2 | Paralelo | **Dejar vacío** — verificar si el OLED ya los trae |
| PTC por puerto | 6 | **Serie** | **Puentear con alambre** |

> Los pull-ups conmutables **hoy no hacen falta ninguno**: los 6 botones caen en
> L1/L2, que tienen pull-up interno. Solo harían falta si ponés un botón en una L4.

---

## Resumen para llevar al negocio — versión mínima

```
RESISTENCIAS 1/4 W
  25  10 kΩ      ← 8 pull-up de relé (NO son opcionales: sin ellos
                    los 8 reles se activan en cada arranque)
  25  1 kΩ       ← 12 en serie de entrada, la proteccion que mas rinde

CAPACITORES
  10  100 nF ceramico
   2  1000 uF 16 V electrolitico   ← sin esto el ESP32 se resetea al
                                     conmutar varios reles juntos
CONECTORES
   8  Jack RJ12 6P6C montaje PCB     ← lo mas caro de la lista
  25  Ficha RJ12 6P6C para crimpear
   2  PTC rearmable 1 A              ← uno en el riel comun
   1  Portafusible PCB + 3 fusibles 2 A
   1  Cable plano 16 vias + 2 IDC hembra 16
  (2) Header hembra 1x19        <- solo si PRO-003 es macho
 (20) Dupont hembra-hembra      <- solo si PRO-004 no los trae
  (1) Tira de pines macho 1x40  <- solo si PRO-003 es hembra

FABRICACION
   3  Placa virgen de cobre simple faz
   1  Percloruro ferrico
   1  Gabinete
```

Las resistencias y los cerámicos van con repuestos a propósito: un pack cuesta
centavos y recortar ahí no ahorra nada real.
