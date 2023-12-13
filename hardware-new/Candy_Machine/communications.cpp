#include "config.h"
#include <Arduino.h>
#include "hardware_operations.h"
#include "communications.h"
// -------------------------------------------------------------------------------------------- //
// ID10T is a custom API created to ensure reliable commmunicaiton betwen a candy machine and python game
// More info can be found here: https://docs.google.com/document/d/1ca_Wcartc7HCcUCTFjyDuHfJEx4QGji220VcJuBd3wo/edit

// ID10T TRANS Types
#define TRANS_TYPE_COMMAND 0x7E // The command trans type is denoted by a Tilde '~'
#define TRANS_TYPE_ACKNOWLEDGE 0x40 // The acknowledge trans type is denoted by an "AT" symbol '@'
#define TRANS_TYPE_EVENT 0x25 // The event trans type is denoted by a percentage '%'

//Used to keep track of what trans type is currently being processed
bool TransTypeCommand = false; 
bool TransTypeAcknowledge = false; 
bool TransTypeEvent = false;

// ID10T Host Commands
#define ESTABLISH_CONNECTION 0x45 // Used to signal the start of comms ('~E[B/S])
#define DISPENSE_CANDY 0x49 // Used to signal for the arduino to dispense candy ('~ID')
#define WATCHDOG_HEARTBEAT 0x72 // Used to determine if a proper connection still exists ('~HD')
// #define RESET 0x51 // This command is denoted by a capital 'Q' Indev reset function (req. hardware mod)

//ID10T Command Parameters
#define CONNECTION_TYPE_BLUETOOTH 0x42 // Used to indicate that bluetooth is being used ('~EB')
#define CONNECTION_TYPE_SERIAL 0X53 // Used to indicate that Serial (USB) is being used ('~ES')

// ID10T Host Acknowledgements
char ESTABLISH_CONNECTION_SERIAL_RESPONSE[3] = {0x40,0x65,0x73}; // Ack sent to python to begin serial ('@es')
char ESTABLISH_CONNECTION_BLUETOOTH_RESPONSE[3] = {0x40,0x65,0x62}; // Ack sent to python to begin bluetooth ('@eB')
char WATCHDOG_HEARTBEAT_ACKNOWLEDGEMENT[3] = {0x40,0x68,0x44};
char MOTOR_ROTATE_RESPONSE[3] = {0x40,0x69,0x79}; // Ack sent upon attempted dispense ('@i[y/z]')

//ID10T Events

// ID10T Incoming Buffer Variables -- used to maintain the incoming buffer
char SerialIncomingQueue[SERIAL_INCOMING_BUFFER_SIZE];
int SerialIncomingQueueFillAmt = 0; // How much is available to read
int SerialIncomingReadPointer = 0; // Index in queue to start read (circular buffer)
int SerialIncomingWritePointer = 0; // Index where to write next byte
// bool ResetToggle = false; //INDEV
bool IsConnectionEstablished = false;
 
#define CHECK_IF_ENOUGH_BYTES_TO_WRITE_TO_QUEUE 3

// ID10T Outgoing Buffer Variables -- used to maintain the outgoing buffer
char SerialOutgoingQueue[SERIAL_OUTGOING_BUFFER_SIZE];
int SerialOutgoingQueueFillAmt = 0; // How much is available to read
int SerialOutgoingReadPointer = 0; // Index in queue to start read (circular buffer)
int SerialOutgoingWritePointer = 0; // Index where to write next byte
bool WatchForCandyDispensed = false;
bool WatchForCandyTaken = false;

// ID10T Error handling -- indev 
bool IsErrorRaised = false;

// -------------------------------------------------------------------------------------------- //
void setWatchForCandyDispensed (bool newValue) {
  WatchForCandyDispensed = newValue;
}
// -------------------------------------------------------------------------------------------- //
bool getWatchForCandyDispensed () {
  return WatchForCandyDispensed;
}
// -------------------------------------------------------------------------------------------- //
void setWatchForCandyTaken (bool newValue) {
  WatchForCandyTaken = newValue;
}
// -------------------------------------------------------------------------------------------- //
bool getWatchForCandyTaken () {
  return WatchForCandyTaken;
}
// -------------------------------------------------------------------------------------------- //
void SetUpCommunications() {
  // Set up Serial at predefined baudrate
  Serial.begin(SERIAL_BAUD_RATE);

  // Wait for Serial
  SetFailLed(true);           
  while (!Serial);
}
// -------------------------------------------------------------------------------------------- //
void WriteArrayOnSerial (char* SendOnSerialArray, int length) {   // Output to the Serial BUS
  Serial.write(SendOnSerialArray, length);
  }
// -------------------------------------------------------------------------------------------- //
void ReadSerial () { // Generat a circular buffer to store incoming comamnds for later interpretation
  int BytesToRead = Serial.available();
  if (BytesToRead > 0) {
    // Dump each b{0x25,0x54,0x    SetFailLed(true);52}yte to queue
    for (int i = 0; i < BytesToRead; i++) {
      // Check to be sure room still exists in buffer
      if (SerialIncomingQueueFillAmt < SERIAL_INCOMING_BUFFER_SIZE) {
        // int SerialReadByte = Serial.read();
        // if (SerialReadByte ==XON)

        SerialIncomingQueue[SerialIncomingWritePointer] = Serial.read();
        // Serial.println(SerialIncomingQueue[SerialIncomingWritePointer], HEX); // For debug only
        // Increase count of what is in buffer
        SerialIncomingQueueFillAmt++;

        // Move where to write next byte (may need to loop back to start of array if end is full).
        // Note that end is based on a start index of 0 so 64 size would have index range is 0-63
        if (SerialIncomingWritePointer == SERIAL_INCOMING_BUFFER_SIZE - 1) {
          // Loop back to first index
          SerialIncomingWritePointer = 0;
        } else {
          SerialIncomingWritePointer++;
        }
      }
    }
  }
  }
// -------------------------------------------------------------------------------------------- //
char PullByteOffIncomingQueue () {   // read the bytes stored in the incoming buffer
  // Note that this function is not verifying bytes exist before pulling so you MUST be sure there is a usable byte BEFORE calling this function
  char returnValue = SerialIncomingQueue[SerialIncomingReadPointer];
  // consume up the byte read by moving the read pointer and decreasing fill amount
  if (SerialIncomingReadPointer == SERIAL_INCOMING_BUFFER_SIZE - 1) {
    // Loop back to first index
    SerialIncomingReadPointer = 0;
  } else {
    SerialIncomingReadPointer++;
  }
  SerialIncomingQueueFillAmt--;
  return returnValue;
  }
// -------------------------------------------------------------------------------------------- //
void ProcessIncomingQueue () {   //interpret the byte pulled from the cue and execute the command
  // Pull off a single command from the queue if command has enough bytes.
  // For simplicity sake, all commands will be a total of 3 bytes (indicating command type, command id, command parameter)
  if (SerialIncomingQueueFillAmt > 2) { // Having anything more than 2 means we have enough to pull a 3 byte command.
    // Check if first byte in queue indicates a command type (if not, throw it out and yell at the python dev)
    char ByteRead = PullByteOffIncomingQueue(); // save the byte from the que for later (now)
     // determine the nature of the proceeding byte (CMD)
    switch(ByteRead) { // Determine transtye from the first byte (one of two [three] types)
      case TRANS_TYPE_COMMAND:
        TransTypeCommand = true;
        TransTypeAcknowledge = false;
        //Serial.write('1');
        break;
      case TRANS_TYPE_ACKNOWLEDGE:
        TransTypeAcknowledge = true;
        TransTypeCommand = false;
        break;
    }
    if ((TransTypeCommand == false) and (TransTypeAcknowledge == false)) { //
      ByteRead = 0; // Zero out ByteRead to reset it for the next execution
      return; // cease execution of the function as a valid trans type was not passed
    }
    if (TransTypeCommand) {
      ByteRead = PullByteOffIncomingQueue();
      switch (ByteRead) {
        case ESTABLISH_CONNECTION:
          ByteRead = PullByteOffIncomingQueue();
          switch (ByteRead) {
            case CONNECTION_TYPE_BLUETOOTH:
              IsConnectionEstablished = true;
              WriteOutgoingBuffer (ESTABLISH_CONNECTION_BLUETOOTH_RESPONSE, sizeof(ESTABLISH_CONNECTION_BLUETOOTH_RESPONSE));
              break; //bluetooth is grossly indev
            case CONNECTION_TYPE_SERIAL:
              IsConnectionEstablished = true;
              WriteOutgoingBuffer (ESTABLISH_CONNECTION_SERIAL_RESPONSE, sizeof(ESTABLISH_CONNECTION_SERIAL_RESPONSE));
              break;
          }
          break;
        //case WATCHDOG_HEARTBEAT:
          //DidgetHeartbeat = true;  
        case DISPENSE_CANDY:
          ByteRead = PullByteOffIncomingQueue();
          ControlMotor(ByteRead);
          WatchForCandyDispensed = true;
          WriteOutgoingBuffer(MOTOR_ROTATE_RESPONSE, sizeof(MOTOR_ROTATE_RESPONSE)); 
          break;
          }
      
    } 
    TransTypeAcknowledge = false;
    TransTypeCommand = false;
  }
}  
// -------------------------------------------------------------------------------------------- //
void WriteOutgoingBuffer (char* ByteArray, int length) {
  //Serial.write('1');
  if (length >= CHECK_IF_ENOUGH_BYTES_TO_WRITE_TO_QUEUE) { 
    //Serial.write('2');
    for (int i = 0; i < length; i++) {
      // Check to be sure room still exists in buffer
      if (SerialOutgoingQueueFillAmt < SERIAL_OUTGOING_BUFFER_SIZE) {
        //Serial.write('3');
        // int SerialReadByte = Serial.read();
        // if (SerialReadByte ==XON)
        SerialOutgoingQueue[SerialOutgoingWritePointer] = ByteArray[i];
        // Serial.println(SerialIncomingQueue[SerialIncomingWritePointer], HEX); // For debug only
        // Increase count of what is in buffer
        SerialOutgoingQueueFillAmt++;
        // Move where to write next byte (may need to loop back to start of array if end is full).
        // Note that end is based on a start index of 0 so 64 size would have index range is 0-63
        if (SerialOutgoingWritePointer == SERIAL_OUTGOING_BUFFER_SIZE - 1) {
          //Serial.write('4');
          // Loop back to first index
          SerialOutgoingWritePointer = 0;
        } else {
          //Serial.write('5');
          SerialOutgoingWritePointer++;
        }
      }
    }
  }
  //WriteArrayOnSerial (SerialOutgoingQueue, 3);
}
// -------------------------------------------------------------------------------------------- //
char PullByteOffOutgoingQueue () {   // read the bytes on the buffer
  // Note that this function is not verifying bytes exist before pulling so you MUST be sure there is a usable byte BEFORE calling this function
  char returnValue = SerialOutgoingQueue[SerialOutgoingReadPointer];

  // consume up the byte read by moving the read pointer and decreasing fill amount
  if (SerialOutgoingReadPointer == SERIAL_OUTGOING_BUFFER_SIZE - 1) {
    // Loop back to first index
    SerialOutgoingReadPointer = 0;
  } else {
    SerialOutgoingReadPointer++;
  }
  SerialOutgoingQueueFillAmt--;
  return returnValue;
}
// -------------------------------------------------------------------------------------------- //
void ProcessOutgoingQueue () { // pull the bytes off of the outgoing buffer, analyze them, reconstruct them, then send the array over serial
  if (SerialOutgoingQueueFillAmt >= CHECK_IF_ENOUGH_BYTES_TO_WRITE_TO_QUEUE) {
    char ByteToWrite1 = PullByteOffOutgoingQueue();
    char ByteToWrite2 = PullByteOffOutgoingQueue();
    char ByteToWrite3 = PullByteOffOutgoingQueue();
    char BytesToSend[3] = {ByteToWrite1,ByteToWrite2,ByteToWrite3};
    WriteArrayOnSerial(BytesToSend, sizeof(BytesToSend));
  }
}

// -------------------------------------------------------------------------------------------- //
void CommsOperation () {
  ReadSerial();
  ProcessIncomingQueue();
  ProcessOutgoingQueue ();
}
// -------------------------------------------------------------------------------------------- //
void EstablishConnectionToSoftware () { 
  // set up communications
  SetUpCommunications();

  // Watch for initilization command
  while (!IsConnectionEstablished) {
    CommsOperation();
  }
  SetFailLed(false);
}
// -------------------------------------------------------------------------------------------- //
void DetermineWatchdogResponse () {
  if (IsErrorRaised == false) { 
    WriteOutgoingBuffer (WATCHDOG_HEARTBEAT_ACKNOWLEDGEMENT, sizeof(WATCHDOG_HEARTBEAT_ACKNOWLEDGEMENT));
  } else {
    // WriteOutgoingBuffer (/*error conditionn raised*/, sizeof(/*error condition*/))
  }
}