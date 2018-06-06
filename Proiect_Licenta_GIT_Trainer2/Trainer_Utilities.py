from mido import MidiFile, MidiTrack, Message
from mido.midifiles import MetaMessage
import mido
import sys
from keras.callbacks import Callback
import numpy as np
import time
import csv
import glob
import shutil

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
     return time_sig, list_dir, nr_files        

def getNoteRangeAndTicks(files_dir,list_dir,nr_training, res_factor=1 ):
    print(getNoteRangeAndTicks)
    print(getNoteRangeAndTicks)
    ticks = []
    notes = []
    counter = 0
    for file_dir in files_dir:
        file_path = "%s" %(file_dir)
        if file_path in list_dir and counter<nr_training:
            print(file_path)
            counter = counter+1
            mid = MidiFile(file_path)                  
            for track in mid.tracks:
                if(track.name=='Piano right'):
                    num_ticks = 0          
                    for message in track:
                        if not isinstance(message, MetaMessage):
                           if(message.type=='note_on'):
                                notes.append(message.note)
                                num_ticks += int(message.time/res_factor)
                        ticks.append(num_ticks)
         
    return max(ticks)
 
def fromMidiCreatePianoRoll(files_dir, ticks, list_dir, nr_training, res_factor=1):
    print(fromMidiCreatePianoRoll)
    print(fromMidiCreatePianoRoll)
    num_files = len(files_dir)        
    piano_roll = np.zeros((num_files,ticks, 48), dtype=np.int)
    counter = 0
    for i, file_dir in enumerate(files_dir):
        if file_dir in list_dir and counter<nr_training:
            shutil.copy(file_dir,'./')
            counter = counter + 1
            file_path = "%s" %(file_dir)
            mid = MidiFile(file_path)
            print(file_path)
            note_time_onoff = getNoteTimeOnOffArray(mid, res_factor)
            note_on_length = getNoteOnLengthArray(note_time_onoff)
           
            for message in note_on_length:
                if(message[0]<52):
                    while(message[0]<52):
                        message[0] = message[0] + 12
                    piano_roll[i,message[1]:(message[1]+int(message[2]/2)), message[0]-52] = 1
                elif(message[0]>88):
                    ct = 0
                    while(message[0]>88):
                        message[0] = message[0] - 12
                    piano_roll[i,message[1]:(message[1]+int(message[2]/2)),message[0]-52] = 1
                else:
                    piano_roll[i,message[1]:(message[1]+int(message[2]/2)), message[0]-52] =  1
               
    return piano_roll

def removeChords(note_time_onoff_array):
    print(removeChords)
    piano_roll  = np.zeros((note_time_onoff_array.shape[0],note_time_onoff_array.shape[1],48),dtype=np.int)
    aux = []
    #note_time_onoff_array = np.matrix(note_time_onoff_array)
    for i,songs in enumerate(note_time_onoff_array):
        aux.clear()
        for j,timestep in enumerate(songs):
                pos = 0
                ct  = 0
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
                aux.append(timestep)
        piano_roll[i]=aux
           

    #piano_roll = np.array(piano_roll)

    return piano_roll

def getNoteTimeOnOffArray(mid, res_factor):
    print(getNoteTimeOnOffArray)
    note_time_onoff_array = []
    for track in mid.tracks:
        if(track.name=='Piano right'):
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
    print(getNoteOnLengthArray)
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


def createNetInputs(roll, target, seq_length):
    print(createNetInputs)
    print(createNetInputs)
    X = []
    y = []
    for i, song in enumerate(roll):
        pos = 0
        while pos+seq_length < song.shape[0]:
            sequence = np.array(song[pos:pos+seq_length])
            X.append(sequence)
            y.append(target[i, pos+seq_length])
            pos += 1
    return np.array(X), np.array(y)

class LossHistory(Callback):
	def on_train_begin(self, logs={}):
		self.losses = []

	def on_batch_end(self, batch, logs={}):
		self.losses.append(logs.get('loss'))