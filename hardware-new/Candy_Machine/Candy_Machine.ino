#include "config.h"
#include "hardware_operations.h" 
#include "communications.h"



// -------------------------------------------------------------------------------------------- //
void setup() {
  //Determine if the python program is present
  EstablishConnectionToSoftware ();
  // set up hardware:
  SetUpHardware();
}
// -------------------------------------------------------------------------------------------- //

void loop() {
  CommsOperation();
  WatchBeamBreakers();
  if (getRunTheMotor()) { 
    MotorMovePrimaryDispense(MOTOR_ROTATION_PER_DISPENSE);}
}
// -------------------------------------------------------------------------------------------- //
