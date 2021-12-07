import math
import requests
import numpy as np
from datetime import datetime
import math


windowSize = 20
step_length = 0.7

def numpy_ewma_vectorized_v2(data, window):

    alpha = 2 /(window + 1.0)
    alpha_rev = 1-alpha
    n = data.shape[0]

    pows = alpha_rev**(np.arange(n+1))

    scale_arr = 1/pows[:-1]
    offset = data[0]*pows[1:]
    pw0 = alpha*alpha_rev**(n-1)

    mult = data*pw0*scale_arr
    cumsums = mult.cumsum()
    out = offset + cumsums*scale_arr[::-1]
    return out


def addNotDup(data, timestamps):
    
    temp_ts = [i[0] for i in data]
    temp_y = [i[1][0] for i in data]
    temp_z = [i[1][1] for i in data]
    temp_a = [i[1][2] for i in data]
    ts = []
    y = []
    z = []
    a = []
    
    for tiempo, elem_y, elem_z, elem_a in zip(temp_ts, temp_y, temp_z, temp_a):
        found = False
        stop_looking = False
        if not stop_looking:
            for j in reversed(timestamps):
                if tiempo == j:
                    found = True
                    break
                
        if not found:
            stop_looking = True
            ts.append(tiempo)
            y.append(elem_y)
            z.append(elem_z)
            a.append(elem_a)
    
    return ts, y, z, a


def calcMovAvg(amount, data):
    return sum(data[-amount:])/amount


def calculateSteps(length, stepData, ewma):
    steps = 0
    
    below = stepData[-length] < ewma[-length]
    
    for i, step in enumerate(stepData[-length:], start=0):
        if below:
            if(calcMovAvg(2, stepData[:-length + i]) > (ewma[-length + i] + ewma[-length + i] * 0.2)):
                steps += 1
                below = False
        
        else:
            if(calcMovAvg(2, stepData[:-length + i]) < (ewma[-length + i] - ewma[-length + i] * 0.2)):
                steps += 1
                below = True

    return steps

timestamps = []
steps_data = []
ewma = []
num_steps = 0

startTime = datetime.now()

while True:

    res = requests.get('http://192.168.1.27:8080/sensors.json')
    data = res.json().get('accel').get('data')

    ts_add, acc_y_add, acc_z_add, acc_a_add = addNotDup(data, timestamps)

    steps_new = [math.sqrt(y*y + z*z + a*a) for y,z,a in zip(acc_y_add, acc_z_add, acc_a_add)]

    steps_data += steps_new
    steps_data = steps_data[-1000:]

    ewma = numpy_ewma_vectorized_v2(np.array(steps_data), windowSize)
    ewma = ewma[-1000:]

    a = calculateSteps(len(steps_new), steps_data, ewma)
    num_steps += math.floor(a/2)
    
    timestamps += ts_add
    timestamps = timestamps[-1000:]

    currTime = datetime.now()
    totalSecs = (currTime - startTime).total_seconds()
    #Rounds to tens of units
    bpm = round(60*(num_steps/totalSecs), -1)


    distance = round((step_length * num_steps) / 1000, 3)
    pace = round((totalSecs / 60) / (distance + 0.01), 2)
    
    print("Total distance: ", '{:<8}'.format(str(distance) + " Km"), " |||  Pace: ", '{:<13}'.format(str(pace) + " min/km"), " |||  BPM",  '{:<5}'.format(str(bpm)), " ||| NUM STEPS: ",  '{:<5}'.format(str(num_steps)), " ||| Total time: ", str(datetime.now() - startTime).split('.')[0])