from keras.models import model_from_json
from keras.models import Sequential
from keras.layers.recurrent import LSTM
import numpy as np
import time
import csv
import glob
import Composer_Utilities as comp_util
from os import listdir

def LoadModelAndWeights():
    #Load model file
    model_dir = './saved_model/'
    model_files = listdir(model_dir)
    print("Choose a file for the model:")
    print("---------------------------------------")
    for i, file in enumerate(model_files):
        print(str(i) + " : " + file)
    print("---------------------------------------")
    print()
    file_number_model = int(input('Type in the number in front of the file you want to choose:')) 
    model_file = model_files[file_number_model]
    model_path = '%s%s' %(model_dir, model_file)
    
    #Load weights file
    weights_dir = './weights/'
    weights_files = listdir(weights_dir)
    print()
    print()
    print("Choose a file for the weights (Model and Weights MUST correspond!):")
    print("---------------------------------------")
    for i, file in enumerate(weights_files):
        print(str(i) + " : " + file)
    print("---------------------------------------")
    print()
    file_number_weights = int(input('Type in the number in front of the file you want to choose:')) 
    weights_file = weights_files[file_number_weights]
    weights_path = '%s%s' %(weights_dir, weights_file)
    
    class_mode = 'binary'
    print()
    print("loading model...")
    model = model_from_json(open(model_path).read())
    print()
    print("loading weights...")
    model.load_weights(weights_path)
    print()
    print("Compiling model...")
    model.compile(loss='binary_crossentropy', optimizer='adam', class_mode=class_mode)
    
    print()

    return model


def Compose(model,song,fac):
    print("Compose...")
    composition_dir = './Generated_Melodies/'
    net_output = model.predict(song)
    #print("net_output:", net_output)
    net_roll = comp_util.NetOutToPianoRoll(net_output, threshold=0.0)
    print("net_roll.shape", net_roll.shape)
    comp_util.createMidiFromPianoRoll(fac,net_roll, composition_dir,
                                               './Song_chpn_14_leftRez4.mi', 0.0, res_factor=1)
    
    #print("Finished composing song %d." %(1))
    
    print()    
    print("Dope!")