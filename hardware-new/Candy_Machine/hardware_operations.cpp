#include "config.h"
#include "communications.h"
#include <Arduino.h> 
#include <Adafruit_MotorShield.h> // Need to get appropriate library if new arduino install
#include "hardware_operations.h"

char EVENT_CANDY_DISPENSED[3] = {0x25,0x4d,0x43};
char EVENT_CANDY_TAKEN[3] = {0x25,0x54,0x52};


// Setup instance of motor stepper
Adafruit_MotorShield AFMS = Adafruit_MotorShield(); // Create the motor shield object with the default I2C address
Adafruit_StepperMotor *MotorPrimaryDispense = AFMS.getStepper(516, 2); // Connect a stepper motor with 516 steps per revolution to motor port #2 (M3 and M4)

bool RunTheMotor = false;
int TimesDispensed = 0;

// -------------------------------------------------------------------------------------------- //
void setRunTheMotor (bool newValue) {
  RunTheMotor = newValue;
}
// -------------------------------------------------------------------------------------------- //
bool getRunTheMotor () {
  return RunTheMotor;
}
// -------------------------------------------------------------------------------------------- //
void SetFailLed(bool setLedOn) {
  if (setLedOn) {
    digitalWrite(PIN_LED_FAIL, HIGH);
  } else {
    digitalWrite(PIN_LED_FAIL, LOW);
  }
}
// -------------------------------------------------------------------------------------------- //
void SetUpHardware () {
  //configure the led
  pinMode(PIN_LED_FAIL, OUTPUT);

  //configure reset
  pinMode(PIN_RESET, OUTPUT);
  digitalWrite(PIN_RESET, LOW);

  // Configuring the motor
  if (!AFMS.begin()) {         // create with the default frequency 1.6KHz
    bool setLedOn = false;
    while (1) {
      setLedOn = !setLedOn;
      SetFailLed(setLedOn);
      delay(1000);
    }
  }
  MotorPrimaryDispense->setSpeed(MOTOR_PRIMARY_DISPENSE_SPEED); // configure speed
  
  // configuring beam breakers
  pinMode(PIN_CANDY_DISPENSE_DETECT, INPUT_PULLUP);  // define beambreaker port mode
  pinMode(PIN_USER_EXTRACTION_DETECT, INPUT_PULLUP);  // define beambreaker port mode
}
// -------------------------------------------------------------------------------------------- //
void MotorMovePrimaryDispense (int StepsToMove) { // 512 == full rotation //old geizer command

  MotorPrimaryDispense->step(StepsToMove, FORWARD, DOUBLE);
  MotorPrimaryDispense->release();
}
// ------#include "config.h"-------------------------------------------------------------------------------------- //
void ControlMotor (char parameter) {
 if (parameter == 0x44) {
 setRunTheMotor(true);
 MotorMovePrimaryDispense(MOTOR_ROTATION_PER_DISPENSE);
 setRunTheMotor(false);
 
 }
}
// -------------------------------------------------------------------------------------------- //
bool IsCandyDispensed () {
    if (digitalRead(PIN_CANDY_DISPENSE_DETECT) == LOW) { 
      return true;
    } else {
      return false;
    }
}
// -------------------------------------------------------------------------------------------- //
bool IsCandyTaken () {
    if (digitalRead(PIN_USER_EXTRACTION_DETECT) == LOW) { 
      return true;
    } else {
      return false;
    }
}
// -------------------------------------------------------------------------------------------- //
void Restart () {
    digitalWrite(PIN_RESET, HIGH);
}
// -------------------------------------------------------------------------------------------- //
void WatchBeamBreakers () {
  // Candy Dispensed
  if (getWatchForCandyDispensed() && IsCandyDispensed ()) {
    setWatchForCandyDispensed(false);
    setWatchForCandyTaken(true);
    TimesDispensed++;
    WriteOutgoingBuffer (EVENT_CANDY_DISPENSED, sizeof(EVENT_CANDY_DISPENSED));
    setRunTheMotor(false);
  }

  // Candy Taken
  if (TimesDispensed > 0 && getWatchForCandyTaken() && IsCandyTaken()) {
    TimesDispensed--;
    WriteOutgoingBuffer (EVENT_CANDY_TAKEN, sizeof(EVENT_CANDY_TAKEN));
  } else {
    setWatchForCandyTaken(false);
    }
}
// -------------------------------------------------------------------------------------------- //