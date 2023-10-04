#!/usr/bin/python

#PST training script.
#Last Updated: Jun 13, 2023
#Original Author: Dan Dillon
#Updated by: G Shearrer and Y Akmadjonova
#for the serial library, download pyserial (not serial)
#ports differ on different pc-s

import os
import math
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
from psychopy import sound
#import psychopy_sounddevice
import SerialHandler
import keyboard as keebee # need to do this to prevent overlap with psychopy keyboard
import serial
from PST_functions import *
from PST_setup import *
from pathlib import Path

# don't forget to check the port in device manager (associated with cp210 driver)
# ser = serial.Serial('COM4', 9800)

wintype='pyglet' 
HOST_NAME = socket.gethostname()


#Screen refresh duration. Not needed, but good fyi
refresh = 16.7

# Note
'''
Wait for candy to be dispensed
Beam break trigger + 5
'''

##GUI to get subject number, date.
info = settingsGUI()

# Dictionary for pickle file
pk = {}
pk.update({info['participant']:{
        'date': info['Date'],
        'fullscr':info['Fullscreen'], 
        'test?':info['test?']
}})
# Paths
stimpath = './Stims/'
datapath = os.path.join('.','Datapath')
adillyofapickle(datapath, pk, info['participant'])


#setting up recording of beam break events 
#to csv and a dic 
#csv is needed to work with a SerialHandler, which tracks time of BBevents)
#dic is needed to put data to pickle
beambreakevents_file = os.path.join(datapath,  info['participant'],'%s_%s_beam_break_events.csv'%(info['participant'], info['Date']))
beambreakevents_file = open(beambreakevents_file, 'w')
beambreakevents_file.write('BBtime,CandyDispensed,CandyTaken\n')

beambreakevents_dic = {}
#dict.fromkeys(["BBtime", "Candy_Dispensed", "Candy_Taken"])


# Global_variables
## Define response keys.
left_key = '1'
right_key = '4'
quit_key = 'q' # WHY DUPLICATE (second in PST_setup)
fdbk_dur = 5
baud = 9600

if info['Bluetooth'] == False:    
    SerialHandler.connect_serial(info['Com Port'],baud,beambreakevents_file, beambreakevents_dic)
    ready = SerialHandler.command_to_send(SerialHandler.establishConnection)    

if ready == True:
    print('ready to start')
else:
    pk.update({'error':'could not establish connection'})
    clean_quit(datapath, pk, info['participant'], block_clock,beambreakevents_file, beambreakevents_dic)
# set visual parameters

parameters = set_visuals([600,400], False, 'black', wintype, 'Text', 'center', 0.12, 350, 'white', 0.3, stimpath)
pk.update({'experiment_parameters':{}})


win = parameters['win']
instruct = parameters['instruct']
left_choice = parameters['left_choice']
right_choice = parameters['right_choice']
reward = parameters['reward']
zero = parameters['zero']
no_resp = parameters['no_resp']
fix = parameters['fix']

#set number of blocks, stimuli, and trials
num_blocks = 1 #4
num_stims = 6
trials_per_stim = 10 #10 # Number times stim on left out of 20 trials.
total_trials = trials_per_stim*num_stims 

#set start time for blocks and trial
#block_start_time = SerialHandler.what_time_is_now()
#trial_start_time = SerialHandler.what_time_is_now()


pk['experiment_parameters'].update({'settings': ['600','400','False','MacAir','black','pyglet','Text','center','0.12','350','white','0.3']})
pk['experiment_parameters'].update({'num_blocks': num_blocks})
pk['experiment_parameters'].update({'num_stims': num_stims})
pk['experiment_parameters'].update({'trials_per_stim': trials_per_stim})

# List of paths to images
pic_list = [os.path.join(stimpath,'1.bmp'), 
            os.path.join(stimpath,'2.bmp'), 
            os.path.join(stimpath,'3.bmp'), 
            os.path.join(stimpath,'4.bmp'), 
            os.path.join(stimpath,'5.bmp'), 
            os.path.join(stimpath,'6.bmp')]

#Make master list of stim lists.
stim_names = stimulating(num_stims, trials_per_stim)
AB_trialList, CD_trialList, EF_trialList = make_it(stim_names)
small_blocks = block_it(AB_trialList, CD_trialList, EF_trialList, trials_per_stim)

#Shuffle bitmaps so images used as stims A, B, C, etc. vary across subjects.
stim_rand = stim_mapping(pic_list, datapath, info['participant'])

# Text
inst_text = [
'This is a new game, with\nchances to win more money.\n\nPress button 1 to advance.', 
'Two figures will appear\non the computer screen.\n\nOne figure will pay you more often\nthan the other, but at first you won\'t\nknow which figure is the good one.\n\nPress 1 to advance.', 
'Try to pick the figure that pays\nyou most often.\n\nWhen you see the REWARD screen,\nthat means you won bonus money!\n\nWhen you see the ZERO screen,\nyou did not win.\n\nPress 1 to advance.', 
'Keep in mind that no figure\npays you every time you pick it.\n\nJust try to pick the one\nthat pays most often.\n\nPress 1 to select the figure\non the left. Press 4 to select\nthe figure on the right.\n\nPress 1 to advance.', 
'At first you may be confused,\nbut don\'t worry.\n\nYou\'ll get plenty of chances.\n\nPress 1 to advance.', 
'There are 4 blocks of trials.\nEach one lasts about 8 minutes.\n\nMake sure to try all the figures\nso you can learn which ones\nare better and worse.\n\nPress button 1 to advance.']

allKeys = []
#list that stores all keys that have been pressed
adillyofapickle(datapath, pk, info['participant'])

# Introduction    
intro(inst_text, instruct, win, allKeys, left_key, quit_key)
stim_matrix = starter(small_blocks, stim_rand, win, trials_per_stim)
#stim_matrix has all the stims,outcomes for the game
last_text = ['Ready to begin, press o when you are comfortable']
advance = 'false'
#why not boolean?
k = ['']

#Run experimental trials.
for block_num, block in enumerate(range(num_blocks)):    
    while advance == 'false':
        pk.update({'data':{'%i'%block_num:{}}})
        instruct.setText(text=last_text[0])
        instruct.draw()
        win.flip()
        k = event.waitKeys()

        if k[0] == 'o':
            RT = core.Clock() # begin the reaction time clock
            block_clock = core.Clock() #begin the task clock
            advance = 'true'

        elif k[0] == 'q':            
            core.quit()
    fix.draw()
    win.flip()
    #need win.flip between screens to change the screen (ckean the screen between different events displayed)
    
    
    SerialHandler.reset_time(block_clock)
    #to reset block time between the blocks

    #Run through the trials
    for i in range(total_trials):


        trial_num = i + 1
        pk['data']['%i'%block_num].update({'%i'%trial_num:{}})
        pk['data']['%i'%block_num]['%i'%trial_num].update({trial_start_time:[]})

        #Prep the stims.

        left_stim = stim_matrix[trial_num-1][0]
        left_stim_name = stim_matrix[trial_num-1][1]
        left_stim_num = stim_matrix[trial_num-1][2]
        right_stim = stim_matrix[trial_num-1][3]
        right_stim_name = stim_matrix[trial_num-1][4]
        right_stim_num = stim_matrix[trial_num-1][5]hh
        scheduled_outcome = stim_matrix[trial_num-1][6]
        for x in [left_stim_name, left_stim_num, right_stim_name, right_stim_num, scheduled_outcome]:
            pk['data']['%i'%block_num]['%i'%trial_num].append(x)
        
        #Reset the RT clock and clear events
        RT.reset()
        event.clearEvents(eventType='keyboard')
        #record trial start time
        pk['data']['%i'%block_num]['%i'%trial_num][trial_start_time].append(SerialHandler.what_time_is_now())
        # present the stimuli and wait for key press
        key_press, stim_onset = present_stims(fix, left_stim, right_stim, win, left_key,right_key, quit_key, RT, block_clock, scheduled_outcome)
        ## log events in dict for pickle
        pk['data']['%i'%block_num]['%i'%trial_num].append(stim_onset) # stimulus onset
        pk['data']['%i'%block_num]['%i'%trial_num].append(key_press[0][0]) # keypress
        pk['data']['%i'%block_num]['%i'%trial_num].append(key_press[0][1]) # RT
          
        # Check accuracy
        acc = accuracy(left_stim_num, right_stim_num, key_press[0][0])
        pk['data']['%i'%block_num]['%i'%trial_num].append(acc) # accuracy
        # show response for 2 seconds   
        if key_press[0][0] == 'q': 
            clean_quit(datapath, pk, info['participant'], block_clock, beambreakevents_file, beambreakevents_dic)     
        response_update(key_press[0][0], win, left_stim, right_stim, left_choice, right_choice, block_clock)
        core.wait(2.0)
        # show feedback and dispense candy here, right now it is waiting 3 sec 
        #fixed that
        Response, fdbk_onset = show_fdbk(acc, scheduled_outcome, block_clock, zero, win, reward, info['test?'])

        
        #output = SerialHandler.read_from_port() #not sure what the output of this looks like, once I know then I can add it to the core wait time
        
        pk['data']['%i'%block_num]['%i'%trial_num].append(Response) # reward or not
        pk['data']['%i'%block_num]['%i'%trial_num].append(fdbk_onset) # feedback onset

        # pickle dump
        adillyofapickle(datapath, pk, info['participant'])


        # wait 3 seconds, update with dispense time when we have it
        if Response == 'correct_reward' or Response == 'probabalistic_reward': 
            SerialHandler.dispense_event.wait()
            SerialHandler.dispense_event.clear()
        else:
            core.wait(3.0)

        
        # check what trial it is
        if trial_num == total_trials:
            adillyofapickle(datapath, pk, info['participant'])

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
                    allKeys = []

                elif resp == quit_key:
                    clean_quit(datapath, pk, info['participant'], block_clock,beambreakevents_file, beambreakevents_dic)

                    

# create a dataframe and save   
data_df = make_df_data(pk)
savepath_data = os.path.join(datapath,'%s'%info['participant'],'%s.csv'%info['participant'])
data_df.to_csv(savepath_data, index=False)

# create an experiment parameters dataframe and save   
experiment_parameters_df = make_df_experiment_parameters(pk)
experiment_parameters_output_file = str('%s' %info['participant'] + '_experiment_parameters' + '.csv')
experiment_parameters_savepath = Path(os.path.join(datapath, '%s'%info['participant']))
experiment_parameters_df.to_csv(experiment_parameters_savepath/experiment_parameters_output_file, index=False)
    #saving info
info_df = make_df_info(pk, info['participant'])
info_output_file = str('%s' %info['participant'] + '_info' + '.csv')
info_savepath = Path(os.path.join(datapath, '%s'%info['participant']))
info_df.to_csv(info_savepath/info_output_file, index=False)

