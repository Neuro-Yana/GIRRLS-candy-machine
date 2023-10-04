import os
import socket
import math
from PST_functions import *
from psychopy import core, data, event, gui, misc, sound, visual

CWD = os.getcwd()
RESOURCE_PATH = (CWD + r"\Resources")
DATA_PATH = os.path.join(CWD, "Datapath")
HOST_NAME = socket.gethostname()
TEST_MONITOR = "testMonitor"

default_values = {
    "Participant": "ParticipantName",
    "Date": data.getDateStr(),
    "Computer": HOST_NAME,
    "Com Port": "COM3",
    "Fullscreen": True,
    "Bluetooth": False,
    #"Test": False,
}

# Variables from the original project, need to figure out what everything actually does
num_disdaqs = 5 # Not sure what this is yet
TR = 3 # Shouldn't need not scanning
refresh = 16.7
initial_waittime = 5
stim_dur = 3
fdbk_dur = 5
disdaq_time = int(math.floor((num_disdaqs*3000)/refresh)) # 15s (5TRs) math.floor rounds to nearest int
num_trials = 60 # Per block.
trial_dur = 8 # On average.
lastHRF = 15 # Time in sec, adjusted on-fly to account for timing errors.
end_time = (TR * num_disdaqs) + (num_trials * trial_dur) + lastHRF
baud = 9600
# These variables seem to relate to the choices
b0 = '0'
b1 = '1'
b2 = '2'
b3 = '3'
b4 = '4'


def settingsGUI():
    print("Showing GUI")
    # Create a dictionary with default values for all the settings

    # Create the GUI dialog
    dialog = gui.DlgFromDict(
        dictionary=default_values,
        title="Settings",
        order=["Participant", "Date", "Computer", "Com Port", "Fullscreen", "Bluetooth"],
        tip={
            "Name": "Enter the participant's name",
            "Com Port": "Enter the communication port",
            "Computer": "Enter the computer name",
            "Date": "Enter the date",
            "Test": "Enter the test name",
            "Participant": "Enter the participant ID",
            "Fullscreen": "Enable/disable fullscreen mode",
            "Bluetooth": "Enable/disable Bluetooth",
            #"Test?": "Enable/disable test mode",
        },
    )
    if dialog.OK:
        #print("User entered:", default_values)
        misc.toFile('lastParams.pickle', default_values)
        return default_values

    else:
        print("User cancelled the dialog")
        closeApplication()    

#Window.
wintype='pyglet'
def set_visuals(color, text, align, ht, wWidth, textcolor, radius, default):
    win = visual.Window([800,600], fullscr=default_values['Fullscreen'], monitor=TEST_MONITOR, allowGUI = False, color = 'black', winType=wintype)
    instruct = visual.TextStim(win, text=text, alignHoriz = align, height = ht, wrapWidth = wWidth, color = textcolor)
    fix = visual.TextStim(win, text = '+')
    left_choice = visual.Circle(win, radius = radius, lineColor = textcolor, lineWidth = 2.0, pos = [-0.4,0])
    right_choice = visual.Circle(win, radius = radius, lineColor = textcolor, lineWidth = 2.0, pos = [0.4,0])
    reward = visual.ImageStim(win, units = 'norm', size = [1,1], pos = [0,0], image = os.path.join(RESOURCE_PATH,'reward.png'))
    zero = visual.ImageStim(win, units = 'norm', size = [1,1], pos = [0,0], image = os.path.join(RESOURCE_PATH,'zero.png'))
    no_resp = visual.TextStim(win, text='No Response Detected!', height = 0.15, wrapWidth = 35, color = 'red')
    parameters = {'win':win, 'instruct':instruct, 'fix':fix, 'left_choice':left_choice, 'right_choice':right_choice, 'reward':reward, 'zero':zero, 'no_resp':no_resp}
    return(parameters)


# Control keys
LEFT_KEY = '1'
RIGHT_KEY = '4'
QUIT_KEY = 'q'
# Test Keys
SIMULATE_CORRECT = "c"
SIMULATE_INCORRECT = "v"
START_MOTOR = "b"
STOP_MOTOR = "n"
# Timestamp Variables
dispense_time = None
taken_time = None
