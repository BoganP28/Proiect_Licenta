from keras.models import Sequential
from keras.layers.recurrent import LSTM
from keras.callbacks import ModelCheckpoint
import numpy as np
import time
import csv
import glob
import Trainer_Utilities as train_util

def BuildNetwork(model,input_dim, output_dim, num_layers):
   
 
    if num_layers == 1:
        print("Your Network:")
        model.add(LSTM(input_dim=input_dim, output_dim=output_dim, activation='sigmoid', return_sequences=False))
        print("add(LSTM(input_dim=%d, output_dim=%d, activation='sigmoid', return_sequences=False))" %(input_dim, output_dim))
    elif num_layers > 1:
        print("Enter the number of units for each layer:")
        num_units = []
        for i in range(num_layers-1):
            units = int(input('Number of Units in Layer %d:' %(i+1)))
            num_units.append(units)
        print()
        print("Your Network:")
        model.add(LSTM(input_dim=input_dim, output_dim=num_units[0], activation='sigmoid', return_sequences=True))
        print("add(LSTM(input_dim=%d, output_dim=%d, activation='sigmoid', return_sequences=True))" %(input_dim, num_units[0]))
        for i in range(num_layers-2):
            model.add(LSTM(output_dim=num_units[i+1], activation='sigmoid', return_sequences=True))
            print("add(LSTM(output_dim=%d, activation='sigmoid', return_sequences=True))" %(num_units[i+1]))
        model.add(LSTM(output_dim=output_dim, activation='sigmoid', return_sequences=False))
    print("add(LSTM(output_dim=%d, activation='sigmoid', return_sequences=False))" %(output_dim))

    return model
 
 
def CompileNetwork(model,num_epochs, batch_size, input_data, target_data, num_layers):

    print()
    print()
    print("Compiling your network with the following properties:")
    loss_function = 'binary_crossentropy'
    optimizer = 'adam'
    class_mode = 'binary'
    print("Loss function: ", loss_function)
    print("Optimizer: ", optimizer)
    print("Class Mode: ", class_mode)
    print("Number of Epochs: ", num_epochs)
    print("Batch Size: ", batch_size)
    model.compile(loss=loss_function, optimizer=optimizer, class_mode=class_mode)
    print()
    print("Training...")
    history = train_util.LossHistory()
    model.fit(input_data, target_data, batch_size=batch_size, nb_epoch=num_epochs, callbacks=[history])
    w = csv.writer(open("./history_csv/%dlayer_%sepochs_%s.csv" %(num_layers, num_epochs, time.strftime("%Y%m%d_%H_%M")), "w"))
    for loss in history.losses:
        w.writerow([loss])

    return model
 
def SaveModelAndWeights(model,num_layers, num_epochs):
    print()
    print("Saving model and weights...")
    print("Saving weights...")
    weights_dir = './weights/'
    weights_file = '%dlayer_%sepochs_%s' %(num_layers, num_epochs, time.strftime("%Y%m%d_%H_%M.h5"))
    weights_path = '%s%s' %(weights_dir, weights_file)
    print("Weights Path:", weights_path)
    model.save_weights(weights_path)
   
    print("Saving model...")
    json_string = model.to_json()
    model_file = '%dlayer_%sepochs_%s' %(num_layers, num_epochs, time.strftime("%Y%m%d_%H_%M.json"))
    model_dir = './saved_model/'
    model_path = '%s%s' %(model_dir, model_file)
    print("Model Path:", model_path)
    open(model_path, 'w').write(json_string)
   
    print()
 