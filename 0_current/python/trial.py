#!/usr/bin/python
#Make sure to activate the virtual environment with .\env\scripts\activate
# Requires Python 3.8.10
import os
from math import floor
import numpy as np
import pandas as pd
import serial
import sys
import socket
from psychopy import core, data, event, gui, misc, visual, prefs, monitors
from itertools import count, takewhile
from typing import Iterator
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
# Set the audio preferences to use PTB first and then import psychopy.sound
prefs.hardware['audioLib'] = ['PTB','pyo','pygame','sounddevice']
import SerialHandler
from PST_functions import *
from PST_setup import *


# Set variables for paths we will be using, as well as other useful default_valuesrmation
CWD = os.getcwd()
RESOURCE_PATH = (CWD + r"\Resources")
DATA_PATH = os.path.join(CWD, "Datapath")
HOST_NAME = socket.gethostname()
TEST_MONITOR = "testMonitor"

default_values = settingsGUI();

# Creates the Datapath folder if it does not exist
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

beambreakevents_file = os.path.join(DATA_PATH, '%s_%s_beam_break_events.csv'%(default_values['Participant'], default_values['Date']))
beambreakevents_file = open(beambreakevents_file, 'w')
beambreakevents_file.write('BBtime,CandyDispensed,CandyTaken\n')

left_key = '1'
right_key = '4'
quit_key = 'q'
fdbk_dur = 5

#if default_values['Bluetooth'] == False:    
SerialHandler.connect_serial(default_values['Com Port'], baud, beambreakevents_file)
SerialHandler.command_to_send(SerialHandler.establishConnection)    
    

parameters = set_visuals('black', 'Text', 'center', 0.12, 350, 'white', 0.3, default_values)
win = parameters['win']
instruct = parameters['instruct']
left_choice = parameters['left_choice']
right_choice = parameters['right_choice']
reward = parameters['reward']
zero = parameters['zero']
no_resp = parameters['no_resp']
fix = parameters['fix']
num_blocks = 4
num_stims = 6
trials_per_stim = 10 # Number times stim on left out of 20 trials.
total_trials = trials_per_stim*num_stims

pk=default_values


pic_list = [os.path.join(RESOURCE_PATH,'1.bmp'), os.path.join(RESOURCE_PATH,'2.bmp'), 
    os.path.join(RESOURCE_PATH,'3.bmp'), os.path.join(RESOURCE_PATH,'4.bmp'),
    os.path.join(RESOURCE_PATH,'5.bmp'), os.path.join(RESOURCE_PATH,'6.bmp')]

#Make master list of stim lists.
stim_names = stimulating(num_stims, trials_per_stim)
AB_trialList, CD_trialList, EF_trialList = make_it(stim_names)
small_blocks = block_it(AB_trialList, CD_trialList, EF_trialList)

#Write out stim randomization for use in test.

stim_rand = stim_mapping(pic_list, DATA_PATH, default_values['Participant'])

df = pd.DataFrame(stim_rand.items())
df.to_csv(os.path.join(DATA_PATH,'%s_PST_stim_rand.csv'%(default_values['Participant'])), header=False, index=False)
#df.to_csv(default_values['participant']+'_PST_stim_rand.csv', header=False, index=False)

parameters.update({'num_blocks':num_blocks,'num_stims':num_stims, 'trials_per_stim':trials_per_stim, 'stim_names':stim_names, 'small_blocks':small_blocks, 'stim_rand':stim_rand})
pk.update({'experiment_parameters':parameters})

#Clocks.

RT = core.Clock()
task_clock = core.Clock()
block_time = core.Clock()

#File to collect training data. 

#train_file = default_values['participant'] + '_' + default_values['Date']
train_file = os.path.join(DATA_PATH, '%s_%s_PST_fMRI_train.csv'%(default_values['Participant'], default_values['Date']))
trainFile = open(train_file, 'w')
trainFile.write('block,trial_num,left_stim,left_stim_number,right_stim,right_stim_number,object_onset,'+
                'object_duration,response,response_onset,trial_RT,accuracy,scheduled_outcome,\n')



##Start the study.
#Instructions.

inst_text = [
'This is a new game, with\nchances to win more money.\n\nPress button 1 to advance.', 
'Two figures will appear\non the computer screen.\n\nOne figure will pay you more often\nthan the other, but at first you won\'t\nknow which figure is the good one.\n\nPress 1 to advance.', 
'Try to pick the figure that pays\nyou most often.\n\nWhen you see the REWARD screen,\nthat means you won bonus money!\n\nWhen you see the ZERO screen,\nyou did not win.\n\nPress 1 to advance.', 
'Keep in mind that no figure\npays you every time you pick it.\n\nJust try to pick the one\nthat pays most often.\n\nPress 1 to select the figure\non the left. Press 4 to select\nthe figure on the right.\n\nPress 1 to advance.', 
'At first you may be confused,\nbut don\'t worry.\n\nYou\'ll get plenty of chances.\n\nPress 1 to advance.', 
'There are 4 blocks of trials.\nEach one lasts about 8 minutes.\n\nMake sure to try all the figures\nso you can learn which ones\nare better and worse.\n\nPress button 1 to advance.']
allKeys = []

intro(inst_text, instruct, win, allKeys, left_key, quit_key)

#Run experimental trials.

for block_num, block in enumerate(range(num_blocks)): 
    #Check-in 
    stim_matrix = starter(small_blocks, stim_rand, win)
    last_text = ['Ready to begin, press o when you are comfortable']
    fix.draw()
    win.flip()
    block_time.reset()
    SerialHandler.reset_time(block_time)

    for i in range(total_trials):
    #Clear buffers.

        trial_num = i + 1 
        


        event.clearEvents()
        allKeys=[]
        resp=[]
        trial_RT=[]

        #Prep the stims.
        object_onset = block_time.getTime()

        left_stim = stim_matrix[trial_num-1][0]
        left_stim_name = stim_matrix[trial_num-1][1]
        left_stim_num = stim_matrix[trial_num-1][2]
        right_stim = stim_matrix[trial_num-1][3]
        right_stim_name = stim_matrix[trial_num-1][4]
        right_stim_num = stim_matrix[trial_num-1][5]
        scheduled_outcome = stim_matrix[trial_num-1][6]


        #Reset the RT clock.
        check_key = event.getKeys(keyList=[quit_key],  timeStamped=task_clock)
        print(check_key)
        check_quit(check_key, DATA_PATH, pk, default_values['Participant'])
        RT.reset()
        event.clearEvents(eventType='keyboard')
        
        key_press = present_stims(fix, left_stim, right_stim, win, left_key,right_key, quit_key, RT, task_clock, scheduled_outcome)

        if key_press[0][0] == 'q':
            closeApplication()

        if key_press[0][0] == '1' or key_press[0][0] == '4':
            acc = accuracy(left_stim_num, right_stim_num, key_press[0][0])
        else: 
            acc = 999
        


        response_update(key_press[0][0], win, left_stim, right_stim, left_choice, right_choice, task_clock)
        core.wait(2.0)
        object_dur = RT.getTime()
        response = show_fdbk(acc, scheduled_outcome, task_clock, zero, win, reward, False)
        core.wait(3.0)
        #Write out the data.
        trainFile.write('%i,%i,%s,%i,%s,%i,%0.3f,%0.3f,%s,%0.3f,%i,%0.3f,%i\n' 
            %(block_num, trial_num, left_stim_name.split('\\')[-1], left_stim_num, right_stim_name.split('\\')[-1], right_stim_num, object_onset, object_dur, response[0], response[1], 0, acc, scheduled_outcome))


        #Fade out with lastHRF fixation cross after 60 trials.        
        if trial_num == 60: 
            elapsed_time = task_clock.getTime()
            time_left = end_time - elapsed_time
            for i in range(int(round((time_left*1000)/refresh))):
                fix.draw()
                win.flip()

    #Present a screen between blocks.

    if block_num < num_blocks:
        pause_text = ['Great job!\n\nYou are done with that block.\n\nTake a few seconds to relax.\n\nWhen you are ready to continue,\npress button 1.']        
        allKeys = []
        for i in range(len(pause_text)):
            advance = 'false'
            instruct.setText(text = pause_text[i])             
            while advance == 'false':
                instruct.draw()
                win.flip()
                allKeys = event.waitKeys(keyList = [left_key,quit_key])
                resp = allKeys[0][0]

                if resp == left_key:
                    advance = 'true'
                    #advance_sound.play()
                    allKeys = []

                elif resp == quit_key:
                    closeApplication()

#Now that we've looped over all the blocks, close the training file.

trainFile.close()
beambreakevents_file.close()
