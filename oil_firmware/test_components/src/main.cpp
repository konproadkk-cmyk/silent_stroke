#include <Arduino.h>
#include <Wire.h>
#include "MAX30105.h"

// ---- AD8232 Heart Monitor wiring (per schematic) ----
// OUTPUT -> GPIO2 (A0)
// LO-    -> GPIO3 (A1)
// LO+    -> GPIO4 (A2)
// GND    -> GND
// +3V    -> 3V3
const int AD8232_OUTPUT_PIN = 2;
const int AD8232_LO_MINUS_PIN = 3;
const int AD8232_LO_PLUS_PIN = 4;

// ---- MAX30102 wiring (I2C) ----
// SDA -> GPIO6 (D4)
// SCL -> GPIO7 (D5)
const int I2C_SDA_PIN = 6;
const int I2C_SCL_PIN = 7;

MAX30105 max30102;
bool max30102Found = false;

unsigned long lastPrintMs = 0;
const unsigned long PRINT_INTERVAL_MS = 20; // ~50 Hz

void setup() {
  Serial.begin(115200);
  delay(1500); // give USB serial time to enumerate

  pinMode(AD8232_LO_MINUS_PIN, INPUT);
  pinMode(AD8232_LO_PLUS_PIN, INPUT);

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

  Serial.println("Initializing MAX30102...");
  if (max30102.begin(Wire, I2C_SPEED_FAST)) {
    max30102Found = true;
    max30102.setup(); // default settings: 50Hz, IR+Red, 15-bit, etc.
    max30102.setPulseAmplitudeRed(0x0A);
    max30102.setPulseAmplitudeGreen(0);
    Serial.println("MAX30102 found and configured.");
  } else {
    Serial.println("MAX30102 NOT found. Check wiring (SDA=D4, SCL=D5, 3V3, GND).");
  }

  Serial.println("ad8232_raw,leads_off,max_ir,max_red");
}

void loop() {
  bool leadsOff = digitalRead(AD8232_LO_MINUS_PIN) || digitalRead(AD8232_LO_PLUS_PIN);
  int ecgRaw = leadsOff ? 0 : analogRead(AD8232_OUTPUT_PIN);

  long irValue = 0;
  long redValue = 0;
  if (max30102Found) {
    irValue = max30102.getIR();
    redValue = max30102.getRed();
  }

  if (millis() - lastPrintMs >= PRINT_INTERVAL_MS) {
    lastPrintMs = millis();
    Serial.print(ecgRaw);
    Serial.print(",");
    Serial.print(leadsOff ? "1" : "0");
    Serial.print(",");
    Serial.print(irValue);
    Serial.print(",");
    Serial.println(redValue);
  }
}
