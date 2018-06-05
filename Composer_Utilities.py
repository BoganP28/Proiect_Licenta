


from mido import MidiFile, MidiTrack, Message
from mido.midifiles import MetaMessage
import mido
import sys

import numpy as np
import time
import csv
import glob

def timeSignature(files_dir, resolution_factor, numerator, denominator):
     print(timeSignature)
     num_files = len(files_dir)
     time_sig = np.zeros((num_files), dtype=np.int)
     list_dir = []
     nr_files = 0
     for i,file_dir in enumerate(files_dir):
       # print(file_dir)
        file_path = "%s" %(file_dir)
        mid = MidiFile(file_path)                  
        for track in mid.tracks:
            for message in track:
                if(message.type == 'time_signature'):
                    if(message.numerator == numerator and message.denominator == denominator):
                        print('%s         ' % (file_dir),end='')
                        print('%d %d %d' % (message.numerator, message.denominator, mid.ticks_per_beat))
                        tpb = mid.ticks_per_beat
                        if message.denominator == 8:
                            tpb = mid.ticks_per_beat/2
                        if message.denominator == 16:
                            tpb = mid.ticks_per_beat/4
                        fac = tpb * message.numerator
                        fac = int(fac/resolution_factor)
                        time_sig=fac
                        list_dir.append(file_dir)
                        nr_files = nr_files+1
     return time_sig, tpb

def getNoteRangeAndTicks(files_dir, res_factor=1):
    ticks = []
    notes = []
    for file_dir in files_dir:
        file_path = "%s" %(file_dir)
        mid = MidiFile(file_path)                  
        for track in mid.tracks: #preprocessing: Checking range of notes and total number of ticks
            if(track.name=='Piano left'):
                num_ticks = 0          
                for message in track:
                    if not isinstance(message, MetaMessage):
                       if(message.type=='note_on'):
                            #notes.append(message.note)
                            num_ticks += int(message.time/res_factor)
                    ticks.append(num_ticks)
 
                   
    return  max(ticks)
 
def fromMidiCreatePianoRoll(files_dir, ticks, res_factor=1):
    num_files = len(files_dir)        
    piano_roll = np.zeros((ticks, 48), dtype=np.int)
    #piano_roll = np.zeros(( ticks, highest_note-lowest_note+1), dtype=np.int)
    for i, file_dir in enumerate(files_dir):
        file_path = "%s" %(file_dir)
        mid = MidiFile(file_path)
        print(file_path)
        note_time_onoff = getNoteTimeOnOffArray(mid, res_factor)
        note_on_length = getNoteOnLengthArray(note_time_onoff)
       
        for message in note_on_length:
            if(message[0]<52):
                while(message[0]<52):
                    message[0] = message[0] + 12
                piano_roll[message[1]:(message[1]+int(message[2]/2)), message[0]-52] = 1
            elif(message[0]>88):
                ct = 0
                while(message[0]>88):
                    message[0] = message[0] - 12
                piano_roll[message[1]:(message[1]+int(message[2]/2)),message[0]-52] = 1
            else:
                piano_roll[message[1]:(message[1]+int(message[2]/2)), message[0]-52] =  1
               
    return piano_roll
 
 
def removeChords(network_output):
    piano_roll = []
    for i, timestep in enumerate(network_output):
            ct = 0
            pos = 0
            for k in timestep:
                if(k>0):
                    pos = ct
                ct = ct+1
            if(pos==0 and timestep[pos]==0):
                timestep[:] = np.zeros(timestep.shape)
                timestep[pos] = 0
            if((pos == 0 and timestep[pos]!=0) or pos!=0):
                timestep[:] = np.zeros(timestep.shape)
                timestep[pos] = 1
 
 
            piano_roll.append(timestep)
       
    return np.array(piano_roll)
 
 
def getNoteTimeOnOffArray(mid, res_factor):
 
    note_time_onoff_array = []
    for track in mid.tracks:
        if(track.name=='Piano left'):
            current_time = 0
            for message in track:
                    if not isinstance(message, MetaMessage):
                        current_time += int(message.time/res_factor)
                        bol = False
                        if (message.type == 'note_on'):
                            if(message.velocity!=0):
                                note_onoff = 1
                                bol = True
                            else:
                                note_onoff = 0
                                bol = True
                        if (message.type == 'note_off'):
                            note_onoff = 0
                            bol = True
                 
                        if(bol==True):
                            note_time_onoff_array.append([message.note, current_time, note_onoff])
     
    return note_time_onoff_array
 
def getNoteOnLengthArray(note_time_onoff_array):
 
    note_on_length_array = []
    first_time = False
    aux = 0
    a = note_time_onoff_array[0:1:1]
    b = [x[1] for x in note_time_onoff_array]
    aux = b[0]
    if aux != 0:
        first_time = True
 
    for i, message in enumerate(note_time_onoff_array):
        if message[2] == 1: #if note type is 'note_on'
            start_time = message[1]
            for event in note_time_onoff_array[i:]: #go through array and look for, when the current note is getting turned off
                if event[0] == message[0] and event[2] == 0:
                    length = event[1] - start_time
                    break
               
            note_on_length_array.append([message[0], start_time, length])
 
    if first_time == True:
        i = 0
        for note,timer,length in note_on_length_array:
            timer = timer - aux
            note_on_length_array[i]=[note, timer, length]
            i = i+1
 
           
    return note_on_length_array
 
def createMidiFromPianoRoll(n,piano_roll, directory, mel_test_file, threshold, res_factor=1):
    ticks_per_beat = int(n)
    mid = MidiFile(type=0, ticks_per_beat=ticks_per_beat)
    track = MidiTrack()
    mid.tracks.append(track)
    mid_files = []
    delta_times = [0]
    for k in range(piano_roll.shape[1]):#initial starting values
        if piano_roll[0, k].any() == 1:
            track.append(Message('note_on', note=k+52, velocity=100, time=0))
            delta_times.append(0)
            aux = k
    counter = 0  
    for j in range(piano_roll.shape[0]-1):#all values between first and last one
        #set_note = 0 #Check, if for the current timestep a note has already been changed (set to note_on or note_off)
       
        for k in range(piano_roll.shape[1]):
            if (piano_roll[j+1, k] == 1 and piano_roll[j, k] == 0) or (piano_roll[j+1, k] == 0 and piano_roll[j, k] == 1):#only do something if note_on or note_off are to be set
                #if set_note == 0:
                time = j+1 - sum(delta_times)          
                delta_times.append(time)
                counter = counter + 1
                #else:
                    #time = 0
                #print(piano_roll[j,k])
                if piano_roll[j+1, k] == 1 and piano_roll[j, k] == 0:
                    set_note = 1
                    track.append(Message('note_on', note=k+52, velocity=100, time=time))
 
                if piano_roll[j+1, k] == 0 and piano_roll[j, k] == 1:
                    set_note=1
                    track.append(Message('note_off', note=k+52, velocity=0, time=time))
           
                           
    mid.save('%s%s_th%s2.mid' %(directory, mel_test_file, threshold))
    mid_files.append('%s.mid' %(mel_test_file))
       
    return
 
def createNetInputs(song, seq_length=3072):
    #roll: 3-dim array with Midi Files as piano roll. Size: (num_samples=num Midi Files, num_timesteps, num_notes)
    #seq_length: Sequence Length. Length of previous played notes in regard of the current note that is being trained on
    #seq_length in Midi Ticks. Default is 96 ticks per beat --> 3072 ticks = 8 Bars
    pos = 0
    X = []
    while pos+seq_length < song.shape[0]:
        sequence = np.array(song[pos:pos+seq_length])
        X.append(sequence)
        pos += 1
        
   # testData.append(np.array(X))

    
    return np.array(X)
 
def NetOutToPianoRoll(network_output, threshold=0.1):
    piano_roll = []
    for i, timestep in enumerate(network_output):
        if np.amax(timestep) > threshold:
            pos = 0
            pos = np.argmax(timestep)
            timestep[:] = np.zeros(timestep.shape)
            timestep[pos] = 1
        else:
            timestep[:] = np.zeros(timestep.shape)
        piano_roll.append(timestep)
       
    return np.array(piano_roll)


    
