#include "esphome.h"
using namespace esphome;

class Sonoff4CHFanOutput : public Component, public FloatOutput {
  public:
    void write_state(float state) override {
      if (state < 0.3) {
        // OFF
        digitalWrite(12, LOW);
        digitalWrite(5, LOW);
        digitalWrite(4, LOW);
      } else if (state < 0.6) {
        // low speed
        digitalWrite(4, HIGH);
        digitalWrite(12, LOW);
        digitalWrite(5, LOW);
      } else if (state < 0.9) {
        // medium speed
        digitalWrite(5, HIGH);
        digitalWrite(12, LOW);
        digitalWrite(4, LOW);
      } else {
        // high speed
        digitalWrite(12, HIGH);
        digitalWrite(5, LOW);
        digitalWrite(4, LOW);
      }
    }
};