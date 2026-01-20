#include <Servo.h>
#include "HX711.h"

// ==============================
// SERVO CONFIG (YOUR WORKING SETUP)
// ==============================
Servo wasteServo;

const int SERVO_PIN = 9;

const int CENTER_ANGLE =35;   // Neutral position
const int DRY_ANGLE    = 140;  // Dry side
const int WET_ANGLE    = 0;    // Wet side

const unsigned long OPEN_TIME = 10000; // 10 seconds

// ==============================
// HX711 CONFIG
// ==============================
#define DOUT 3
#define SCK  2

HX711 scale;

// 🔴 Your verified calibration factor
float calibration_factor = 104.2;

// ==============================
// VARIABLES
// ==============================
float base_weight = 0;

// ==============================
// FUNCTION: READ WEIGHT
// ==============================
float readWeight() {
  float w = scale.get_units(10);   // average 10 readings
  if (abs(w) < 20) w = 0;          // noise filter (ignore <20g)
  return w;
}

// ==============================
// SETUP
// ==============================
void setup() {
  Serial.begin(9600);
  delay(1000);

  // Servo setup
  wasteServo.attach(SERVO_PIN);
  wasteServo.write(CENTER_ANGLE);
  delay(1000);

  // HX711 setup
  scale.begin(DOUT, SCK);
  scale.set_scale(calibration_factor);
  scale.tare();   // ZERO with empty bin

  Serial.println("ARDUINO READY");
}

// ==============================
// LOOP
// ==============================
void loop() {

  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  // ==============================
  // BASE WEIGHT (BEFORE ITEM)
  // ==============================
  if (cmd == "BASE") {
    base_weight = readWeight();

    Serial.print("BASE_WEIGHT:");
    Serial.println(base_weight, 1);
    Serial.flush();
  }

  // ==============================
  // DRY WASTE
  // ==============================
  else if (cmd == "DRY") {
    wasteServo.write(DRY_ANGLE);
    delay(OPEN_TIME);

    wasteServo.write(CENTER_ANGLE);
    delay(1500);

    float final_weight = readWeight();
    float item_weight = final_weight - base_weight;
    if (item_weight < 0) item_weight = 0;

    Serial.print("ITEM_WEIGHT:");
    Serial.println(item_weight, 1);
    Serial.flush();
  }

  // ==============================
  // WET WASTE
  // ==============================
  else if (cmd == "WET") {
    wasteServo.write(WET_ANGLE);
    delay(OPEN_TIME);

    wasteServo.write(CENTER_ANGLE);
    delay(1500);

    float final_weight = readWeight();
    float item_weight = final_weight - base_weight;
    if (item_weight < 0) item_weight = 0;

    Serial.print("ITEM_WEIGHT:");
    Serial.println(item_weight, 1);
    Serial.flush();
  }

  // ==============================
  // RESET SERVO
  // ==============================
  else if (cmd == "NONE") {
    wasteServo.write(CENTER_ANGLE);
  }
}
