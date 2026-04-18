#include <Adafruit_NeoPixel.h>

#define MIC_PIN 1
#define LED_PIN 48        // Onboard NeoPixel
#define RED_LED_PIN 42     // NEW: External Red LED pin
#define NUM_LEDS 1
#define SENSITIVITY 10    // ADJUST THIS: How far from baseline triggers the Green LED

Adafruit_NeoPixel rgb(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int baseline = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize NeoPixel
  rgb.begin();
  rgb.setBrightness(50);
  rgb.show(); 

  // NEW: Initialize the external Red LED
  pinMode(RED_LED_PIN, OUTPUT);
  digitalWrite(RED_LED_PIN, LOW);

  // --- Auto-Calibration Phase ---
  Serial.println("Calibrating baseline... Keep quiet for 1 second.");
  long sum = 0;
  int samples = 100;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(MIC_PIN);
    delay(10);
  }
  baseline = sum / samples;
  Serial.print("Calibration complete. Baseline set to: ");
  Serial.println(baseline);
  
  // Flash Blue to indicate calibration is done
  rgb.setPixelColor(0, rgb.Color(0, 0, 255)); 
  rgb.show();
  delay(500);
  rgb.setPixelColor(0, rgb.Color(0, 0, 0));
  rgb.show();
}

void loop() {
  int value = analogRead(MIC_PIN);
  
  // Calculate absolute distance from the established baseline
  int deviation = abs(value - baseline);

  // Send BOTH the raw value and the baseline for your Python plot
  Serial.print(value);
  Serial.print(",");
  Serial.println(baseline);

  if (deviation > SENSITIVITY) {
    // Loud sound detected — blink green, turn OFF red
    digitalWrite(RED_LED_PIN, LOW);
    rgb.setPixelColor(0, rgb.Color(0, 255, 0));  
    rgb.show();
    delay(100);                                  
    rgb.setPixelColor(0, rgb.Color(0, 0, 0));    
    rgb.show();
  } else {
    // Sound is too low — turn ON red
    digitalWrite(RED_LED_PIN, HIGH);
  }

  delay(10);
}