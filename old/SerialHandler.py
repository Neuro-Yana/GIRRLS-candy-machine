import serial
import time
import threading
import time
#Command Types
TRANS_TYPE_COMMAND = 0x7E
TRANS_TYPE_ACKNOWLEDGE = 0x40
TRANS_TYPE_EVENT = 0x25

#Host Parameters
ESTABLISH_CONNECTION_SERIAL = 0x53

#Host Commands
ESTABLISH_CONNECTION = 0x45
DISPENSE_CANDY = 0x49
RESET = 0x51

#Client Events
JAM_OR_EMPTY = 0xa
DISPENSE_DETECTED = 0x4d
CANDY_TAKEN = 0x54

#Host Acknowledgements
CONNECTION_ESTABLISHED = 0x65
DISPENSING_CANDY = 0x69
RESETTING = 0x71

#Client Acknowledgements
PAUSED_FOR_ASSISTANCE = 0x65
DISPENSE_NOTED = 0x6d
CANDY_TAKEN_NOTED = 0x74

#Hardware Events
MOTOR_ROTATE = 0x44
reading_serial = True

establishConnection = [TRANS_TYPE_COMMAND,ESTABLISH_CONNECTION,ESTABLISH_CONNECTION_SERIAL]
moveMotor = [TRANS_TYPE_COMMAND,DISPENSE_CANDY,MOTOR_ROTATE]



def connect_serial(comport,baudrate, beambreakevents, beambreakevents_dic):
    global ser
    global reading_serial
    global thread
    global start_time
    global beambreakevents_var
    beambreakevents_var = beambreakevents
    #defining that the variable should com as a function param 
    #which is set in trial.py
    beambreakevents_dic = beambreakevents_dic
    #fill the dic with keys
    # beambreakevents_dic.update({'BBtime': [None],
    #                         'CandyDispensed': [None],
    #                         'CandyTaken': [None]})
    ser = serial.Serial(comport, baudrate, xonxoff = True)
    time.sleep(3)
    thread = threading.Thread(target=read_from_port)
    thread.start()
    print("Connected to serial")
    reading_serial = True
    return ser, reading_serial

def close_serial():
    global reading_serial
    # Join thread back in
    print("Thread Join")
    reading_serial = False; # Needs to happen before join
    thread.join()
    print("Serial Closing...")
    ser.close()
    print("Serial Closed")
    return reading_serial

def command_to_send(command):
    #print("Running Command to Send")
    ser.reset_input_buffer()
    ser.write(command)
    return True

def reset_time(timer):
    global start_time
    start_time = timer
#def reset_time()
 #   start_time = time.time()

def read_from_port():
    print("Read from port thread started")
    while reading_serial:
        if ser.in_waiting >= 3:
            bytes_read = ser.read(3)
            if bytes_read == b"@es":
                print("Connection Established")
            elif bytes_read == b"@iy":
                print("Motor Moved")
                #print(datetime.datetime.now())
            elif bytes_read == b"%MC":
                print("Candy Dispensed")
                dispense_time = time.time()
                beambreakevents_var.write('%s,%i,%i\n' %(str(dispense_time-start_time), 1, 0))
                beambreakevents_dic.update({'BBtime':str(dispense_time-start_time)})
                beambreakevents_dic.update({'CandyDispensed':1})
                beambreakevents_dic.update({'CandyTaken':0})
                print(dispense_time)
                #return dispense_time
            elif bytes_read == b"%TR":
                print("Candy Taken")
                #taken_time = time.time()
                taken_time = start_time.getTime()
                beambreakevents_var.write('%0.3f,%i,%i\n' %(taken_time, 0, 1))
                #beambreakevents_var.write('%s,%i,%i\n' %(str(taken_time-start_time), 0, 1))
                beambreakevents_dic.update({'BBtime':taken_time})
                beambreakevents_dic.update({'CandyDispensed':0})
                beambreakevents_dic.update({'CandyTaken':1})
                print(taken_time)
                #return taken_time
            else:
                print(bytes_read)