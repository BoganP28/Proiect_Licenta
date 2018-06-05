import Trainer as trainer
import Composer as composer
import Trainer_Utilities as train_util
import Composer_Utilities as comp_util
import numpy as np
import time
import csv
import glob

from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.callbacks import ModelCheckpoint

if __name__ == "__main__":
 
    print("Enter option:")
    print("1 - Train Network")
    print("2 - Compose melody")
    print("3 - Exit")
    option=int(input('Option: '))
    while option!= 3:
        if option == 1:

            mel_train_dir = './trainData/melody/'
            mel_train_files = glob.glob("%s*.mid" %(mel_train_dir))

            resolution_factor = int(input('Resolution Factor (recommended=12):')) #24: 1/8 Resolution, 12: 1/16 Resolution, 6: 1/32 Resolution
            print('Choose time signature to train: 3/4 4/4 6/8')
            numerator = int(input('Numerator = '))
            denominator = int(input('Denominator = '))
            seq_length, list_dir, nr_files = train_util.timeSignature(mel_train_files,resolution_factor,numerator,denominator)
            
            print("Choose a resolution factor. (e.g. Resolution_Factor=24: 1/8 Resolution, 12: 1/16 Resolution, 6: 1/32 Resolution, etc...)")
            print("There are %d files in %d/%d time signatures" % (nr_files, numerator, denominator))
            print("Number of training files")
            nr_training = int(input('Number = '))
            
            mel_ticks = train_util.getNoteRangeAndTicks(mel_train_files, list_dir, nr_training, res_factor=resolution_factor)
            mel_roll = train_util.fromMidiCreatePianoRoll(mel_train_files, mel_ticks, list_dir, nr_training, res_factor=resolution_factor)
            mel_roll = train_util.removeChords(mel_roll)
            
            #Get Time Signature
            
            #Create Network Inputs:
            #Input_data Shape: (num of training samples, num of timesteps=sequence length, note range)
            #Target_data Shape: (num of training samples, note range)
            input_data, target_data = train_util.createNetInputs(mel_roll, mel_roll, seq_length)
            input_data = input_data.astype(np.bool)
            target_data = target_data.astype(np.bool)
            
            
            input_dim = input_data.shape[2]
            output_dim = target_data.shape[1]
 
            print()
            print("For how many epochs do you wanna train?")
            num_epochs = int(input('Num of Epochs:'))
            print()
           
            print()
            print("Choose a batch size:")
            print("(Batch size determines how many training samples per gradient-update are used. --> Number of gradient-updates per epoch: Num of samples / batch size)")
            batch_size = int(input('Batch Size (recommended=128):'))
            print()
           
            print()
            print("Network Input Dimension:", input_dim)
            print("Network Output Dimension:", output_dim)
            print("How many layers should the network have?")
            num_layers = int(input('Number of Layers:'))
            print()

            model = Sequential()
            model = trainer.BuildNetwork(model,input_dim, output_dim, num_layers)
            model = trainer.CompileNetwork(model,num_epochs, batch_size,input_data, target_data ,num_layers)
            trainer.SaveModelAndWeights(model,num_layers,num_epochs)
 
            print("Done Training")
            option=int(input('Option: '))
        elif option == 2:

            chord_train_files = './trainData/Chords/'
            chord_files = glob.glob("%s*.mid" %(chord_train_files))

            print("Choose a resolution factor. (e.g. Resolution_Factor=24: 1/8 Resolution, 12: 1/16 Resolution, 6: 1/32 Resolution, etc...)")
            resolution_factor = int(input('Resolution Factor (recommended=12):')) #24: 1/8 Resolution, 12: 1/16 Resolution, 6: 1/32 Resolution
            numerator = 4
            denominator = 4
            seq_length, tpb = comp_util.timeSignature(chord_files, resolution_factor, numerator, denominator)

            chord_ticks = comp_util.getNoteRangeAndTicks(chord_files, res_factor=resolution_factor)
            chord_roll = comp_util.fromMidiCreatePianoRoll(chord_files, chord_ticks,  res_factor=resolution_factor)
            chord_roll = comp_util.removeChords(chord_roll)                                                                                                     
            
            test_data = comp_util.createNetInputs(chord_roll,seq_length)
            
            batch_size = 128
            class_mode = "binary"
            
            print()
            print()
            print("Enter the threshold (threshold is used for creating a Piano Roll Matrix out of the Network Output)")
            #thresh = float(input('Threshold (recommended ~ 0.1):'))
            fac = tpb/resolution_factor
            model = composer.LoadModelAndWeights()
            composer.Compose(model,test_data,fac)

            print("Done composing")
            option=int(input('Option: '))
        else:
            break

 