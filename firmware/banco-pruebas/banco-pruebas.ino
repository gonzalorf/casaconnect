/*
 * CasaConnect - Banco de pruebas (Fase 1)
 *
 * Valida las suposiciones del diseno antes de etchar las placas.
 * No usa ninguna libreria externa: solo Wire y Preferences, que vienen
 * con el core esp32.
 *
 * Placa:  NodeMCU ESP-32S  (ESP32 Dev Module)
 * Serie:  115200
 *
 * CABLEADO
 *   ESP32 3V3  -> VCC del modulo de reles (lado opto)   <- NO 5 V
 *   ESP32 GND  -> GND comun
 *   Fuente 5V  -> JD-VCC del modulo (bobinas)           <- jumper JD-VCC QUITADO
 *   GPIO 13,16,17,18,19,23,25,26 -> IN1..IN8
 *   Cada linea de rele con pull-up de 10 kOhm a 3V3
 */

#include <Wire.h>
#include <Preferences.h>

// ---------------------------------------------------------------- pines
// Salidas de rele, en orden R1..R8. Los modulos son ACTIVO-LOW.
const int RELES[] = { 13, 16, 17, 18, 19, 23, 25, 26 };
const int N_RELES = sizeof(RELES) / sizeof(RELES[0]);

// Entradas digitales con pull-up interno (lineas L1 y L2 de cada pareja)
const int ENTRADAS_DIG[] = { 2, 4, 5, 14, 15, 27 };
const int N_ENTRADAS_DIG = sizeof(ENTRADAS_DIG) / sizeof(ENTRADAS_DIG[0]);

// Entradas analogicas: ADC1, las unicas que funcionan con WiFi activo
const int ENTRADAS_ADC[] = { 32, 33, 34, 35, 36, 39 };
const int N_ENTRADAS_ADC = sizeof(ENTRADAS_ADC) / sizeof(ENTRADAS_ADC[0]);

const int SDA_PIN = 21;
const int SCL_PIN = 22;

// Activo-LOW: nombrarlo asi evita confundirse al leer el codigo
const int RELE_ON  = LOW;
const int RELE_OFF = HIGH;

Preferences prefs;
uint32_t arranques = 0;

// ------------------------------------------------------------- utilidades
void apagarTodos() {
  for (int i = 0; i < N_RELES; i++) digitalWrite(RELES[i], RELE_OFF);
}

bool esperarEnter(uint32_t ms) {
  // Devuelve true si llego algo por serie antes del timeout.
  uint32_t t0 = millis();
  while (millis() - t0 < ms) {
    if (Serial.available()) { while (Serial.available()) Serial.read(); return true; }
    delay(10);
  }
  return false;
}

// ---------------------------------------------------------------- pruebas

// TEST 1.1 - cada rele por separado
void testRelesUnoPorUno() {
  Serial.println(F("\n--- Reles uno por uno ---"));
  Serial.println(F("Mira y escucha: cada clic tiene que ser seco, sin zumbido."));
  for (int i = 0; i < N_RELES; i++) {
    Serial.printf("  R%d  (GPIO %2d)  ON ", i + 1, RELES[i]);
    digitalWrite(RELES[i], RELE_ON);
    delay(600);
    Serial.println(F("-> OFF"));
    digitalWrite(RELES[i], RELE_OFF);
    delay(400);
  }
  Serial.println(F("Listo. Si alguno quedo pegado o zumbo, anotalo: el opto no"));
  Serial.println(F("apaga bien con 3.3 V y hay que revisar el jumper JD-VCC."));
}

// TEST 1.6 - los 8 a la vez, con y sin el capacitor de 1000 uF
void testTodosALaVez() {
  Serial.println(F("\n--- Los 8 reles a la vez (test del reservorio) ---"));
  Serial.println(F("Pico esperado: 8 x 70 mA = 560 mA de golpe."));
  Serial.println();
  Serial.println(F("IMPORTANTE: este test SOLO vale si el ESP32 y las bobinas"));
  Serial.println(F("comparten el riel de 5 V (USB desconectado, todo desde la"));
  Serial.println(F("fuente). Con el ESP32 en el USB son rieles distintos, el pico"));
  Serial.println(F("no lo alcanza y el test pasa siempre sin significar nada."));
  Serial.println();
  Serial.printf("Arranques registrados hasta ahora: %u\n", arranques);
  Serial.println(F("Si al terminar el numero subio, hubo reset."));
  Serial.println(F("\n10 ciclos..."));

  for (int c = 1; c <= 10; c++) {
    Serial.printf("  ciclo %2d  ON...", c);
    Serial.flush();
    for (int i = 0; i < N_RELES; i++) digitalWrite(RELES[i], RELE_ON);
    delay(500);
    apagarTodos();
    Serial.println(F(" OFF"));
    delay(500);
  }
  Serial.printf("\nTerminado sin reset. Arranques: %u\n", arranques);
  Serial.println(F("Para la prueba de verdad: desconecta el USB, alimenta todo"));
  Serial.println(F("desde la fuente, deja correr, y volve a conectar el USB para"));
  Serial.println(F("leer el contador con la opcion 6."));
}

// TEST 1.3 - bus I2C
void testI2C() {
  Serial.println(F("\n--- Escaneo del bus I2C ---"));
  Wire.begin(SDA_PIN, SCL_PIN);
  int encontrados = 0;
  for (uint8_t dir = 1; dir < 127; dir++) {
    Wire.beginTransmission(dir);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  0x%02X", dir);
      if (dir == 0x3C || dir == 0x3D) Serial.print(F("  <- OLED SSD1306"));
      if (dir >= 0x20 && dir <= 0x27)  Serial.print(F("  <- MCP23017?"));
      Serial.println();
      encontrados++;
    }
  }
  if (encontrados == 0) {
    Serial.println(F("  Nada. Revisa SDA=21, SCL=22, alimentacion a 3.3 V"));
    Serial.println(F("  y los pull-ups (el modulo OLED suele traerlos)."));
  } else {
    Serial.printf("  %d dispositivo(s).\n", encontrados);
  }
}

// TEST 1.4 - monitor de entradas, para ver rebotes y ruido
void testEntradas() {
  Serial.println(F("\n--- Monitor de entradas (Enter para salir) ---"));
  Serial.println(F("Aprieta un boton y mira las transiciones."));
  Serial.println(F("Normal: 1 a 5 transiciones en menos de 10 ms."));
  Serial.println(F("Ruido:  transiciones sueltas sin que toques nada.\n"));

  int previo[N_ENTRADAS_DIG];
  uint32_t ultimo[N_ENTRADAS_DIG];
  for (int i = 0; i < N_ENTRADAS_DIG; i++) {
    previo[i] = digitalRead(ENTRADAS_DIG[i]);
    ultimo[i] = 0;
  }

  while (!Serial.available()) {
    for (int i = 0; i < N_ENTRADAS_DIG; i++) {
      int v = digitalRead(ENTRADAS_DIG[i]);
      if (v != previo[i]) {
        uint32_t ahora = millis();
        uint32_t delta = ultimo[i] ? ahora - ultimo[i] : 0;
        Serial.printf("  %7u ms  GPIO %2d  ->  %s", ahora, ENTRADAS_DIG[i],
                      v ? "ALTO " : "BAJO ");
        if (delta && delta < 50) Serial.printf("  (+%u ms, rebote)", delta);
        Serial.println();
        previo[i] = v;
        ultimo[i] = ahora;
      }
    }
    delay(1);
  }
  while (Serial.available()) Serial.read();
}

// TEST 1.5 - lectura de los pines analogicos
void testADC() {
  Serial.println(F("\n--- Lectura de ADC1 (Enter para salir) ---"));
  Serial.println(F("Tapa y destapa el LDR para ver el rango util.\n"));
  while (!Serial.available()) {
    Serial.print(F("  "));
    for (int i = 0; i < N_ENTRADAS_ADC; i++) {
      int crudo = analogRead(ENTRADAS_ADC[i]);
      Serial.printf("G%-2d:%4d (%4d mV)  ", ENTRADAS_ADC[i], crudo,
                    analogReadMilliVolts(ENTRADAS_ADC[i]));
    }
    Serial.println();
    delay(400);
  }
  while (Serial.available()) Serial.read();
}

// TEST 1.2 - contador de arranques
void testArranques() {
  Serial.println(F("\n--- Contador de arranques ---"));
  Serial.printf("  Arranques desde el ultimo borrado: %u\n", arranques);
  Serial.println();
  Serial.println(F("USO (test 1.2): resetea con el boton EN unas 20 veces y"));
  Serial.println(F("escucha si algun rele hace clic durante el arranque."));
  Serial.println(F("  - Nunca suena     -> el pull-up de 10 kOhm alcanza"));
  Serial.println(F("  - Suena a veces   -> bajar a 4.7 kOhm"));
  Serial.println();
  Serial.println(F("Enter para borrar el contador, o espera 5 s para volver."));
  if (esperarEnter(5000)) {
    arranques = 0;
    prefs.begin("banco", false);
    prefs.putUInt("arranques", 0);
    prefs.end();
    Serial.println(F("  Contador en cero."));
  }
}

// ------------------------------------------------------------------ menu
void menu() {
  Serial.println(F("\n================ CasaConnect - banco ================"));
  Serial.printf(  " arranques: %-4u          reles: todos apagados\n", arranques);
  Serial.println(F("-----------------------------------------------------"));
  Serial.println(F("  1  Reles uno por uno            (test 1.1)"));
  Serial.println(F("  2  Los 8 reles a la vez         (test 1.6)"));
  Serial.println(F("  3  Escanear bus I2C             (test 1.3)"));
  Serial.println(F("  4  Monitor de entradas          (test 1.4)"));
  Serial.println(F("  5  Lectura de ADC               (test 1.5)"));
  Serial.println(F("  6  Contador de arranques        (test 1.2)"));
  Serial.println(F("  0  Apagar todos los reles"));
  Serial.println(F("=====================================================\n> "));
}

void setup() {
  // LO PRIMERO DE TODO: dejar los reles apagados.
  // Entre el encendido y esta linea los GPIO estan en alta impedancia;
  // ese hueco lo cubren los pull-ups de 10 kOhm, no el firmware.
  for (int i = 0; i < N_RELES; i++) {
    pinMode(RELES[i], OUTPUT);
    digitalWrite(RELES[i], RELE_OFF);
  }

  Serial.begin(115200);
  delay(300);

  for (int i = 0; i < N_ENTRADAS_DIG; i++) pinMode(ENTRADAS_DIG[i], INPUT_PULLUP);
  // Los ADC no se configuran: 34/35/36/39 son solo-entrada y sin pull-up interno.

  prefs.begin("banco", false);
  arranques = prefs.getUInt("arranques", 0) + 1;
  prefs.putUInt("arranques", arranques);
  prefs.end();

  menu();
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  while (Serial.available()) Serial.read();

  switch (c) {
    case '1': testRelesUnoPorUno(); break;
    case '2': testTodosALaVez();    break;
    case '3': testI2C();            break;
    case '4': testEntradas();       break;
    case '5': testADC();            break;
    case '6': testArranques();      break;
    case '0': apagarTodos(); Serial.println(F("\nTodos apagados.")); break;
    default:  return;   // ignorar saltos de linea
  }
  apagarTodos();
  menu();
}
