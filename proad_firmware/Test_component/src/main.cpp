#include "MAX30105.h"
#include <Wire.h>
#include <Arduino.h>

// ---------- AD8232 ECG (analog leads) ----------
// OUTPUT -> GPIO2 (D0, analog)
// LO-    -> GPIO3 (D1, digital in)
// LO+    -> GPIO4 (D2, digital in)
#define AD8232_OUTPUT_PIN 2
#define AD8232_LO_MINUS_PIN 3
#define AD8232_LO_PLUS_PIN 4

// ---------- MAX30102 (I2C) ----------
// SDA -> GPIO6 (D4)
// SCL -> GPIO7 (D5)
#define I2C_SDA_PIN 6
#define I2C_SCL_PIN 7

MAX30105 particleSensor;
bool max30102Found = false;

unsigned long lastEcgPrint = 0;
const unsigned long ecgIntervalMs = 10; // ~100Hz

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {
    ; // wait for serial monitor on native USB boards
  }

  // AD8232 setup
  pinMode(AD8232_LO_MINUS_PIN, INPUT);
  pinMode(AD8232_LO_PLUS_PIN, INPUT);

  // MAX30102 setup
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  if (particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    max30102Found = true;
    // brightness, avg samples, LED mode, sample rate, pulse width, ADC range
    particleSensor.setup(0x1F, 4, 2, 400, 411, 4096);
    Serial.println("MAX30102 initialized.");
  } else {
    Serial.println("MAX30102 not found. Check wiring (SDA=GPIO6, SCL=GPIO7).");
  }

  Serial.println("Starting AD8232 + MAX30102 test...");
}

void loop() {
  unsigned long now = millis();

  // ---- AD8232 ECG reading ----
  if (now - lastEcgPrint >= ecgIntervalMs) {
    lastEcgPrint = now;

    bool leadsOff = (digitalRead(AD8232_LO_PLUS_PIN) == HIGH) ||
                     (digitalRead(AD8232_LO_MINUS_PIN) == HIGH);

    Serial.print("ECG:");
    if (leadsOff) {
      Serial.print("LEADS_OFF");
    } else {
      Serial.print(analogRead(AD8232_OUTPUT_PIN));
    }

    // ---- MAX30102 reading ----
    Serial.print("\tIR:");
    if (max30102Found) {
      Serial.print(particleSensor.getIR());
      Serial.print("\tRED:");
      Serial.print(particleSensor.getRed());
    } else {
      Serial.print("N/A\tRED:N/A");
    }

    Serial.println();
  }
}
