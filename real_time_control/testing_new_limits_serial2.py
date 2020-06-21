import serial
import time
import csv
import matplotlib
matplotlib.use("tkAgg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

#ser = serial.Serial('/dev/tty/COM3')
ser = serial.Serial('COM7', 9600)
ser.flushInput()

plot_window = 1000
display = True

sensors = 4 #set to how many sensors are connected 
all_sensor_data = []

for i in range(sensors):
    all_sensor_data.append([]) #store y_first, y_second, etc. in 2D array

plt.ion()
fig, ax = plt.subplots(2,3)

all_plots = []

if sensors <= 1:
    plot1, = ax[0,0].plot(all_sensor_data[0])
    all_plots.append(plot1)
if sensors <= 2:
    plot2, = ax[0,1].plot(all_sensor_data[1])
    all_plots.append(plot2)
if sensors <= 3:
    plot3, = ax[0,2].plot(all_sensor_data[2])
    all_plots.append(plot3)
if sensors <= 4:
    plot4, = ax[1,0].plot(all_sensor_data[3])
    all_plots.append(plot4)
if sensors <=5:
    plot5, = ax[1,1].plot(all_sensor_data[4])
    all_plots.append(plot5)
if sensors <= 6:
    plot6, = ax[1,2].plot(all_sensor_data[5])
    all_plots.append(plot6)

last_first_value = 0
last_values = [0] * 5

while True:
    try:
        line = ser.readline().strip()
        print(line[2:len(line)])
        values = line[2:len(line)].decode('ascii').split(',')
        print(values)

        if values[0] == '':
            values[0] = str(last_first_value);
        if len(values) < 5:
            values = last_values
        last_values = values
        values = [float(s) for s in values]
        last_first_value = values[0]

        with open("test_4_data.csv","a") as f:
            writer = csv.writer(f,delimiter=",")
            writer.writerow([time.time(),values])

        for i in range(sensors):
            all_sensor_data[i] = np.append(all_sensor_data[i],values[i])
            all_plots[i].set_ydata(all_sensor_data[i])
            all_plots[i].set_xdata(range(len(all_sensor_data[i])))

        # x.set_xlim(0, len(y_var))
        c = sys.stdin.read(1)
        if c == ' ':
            display = not display
        if display:
            ax[0,0].relim()
            ax[0,0].autoscale_view()
            ax[0,1].relim()
            ax[0,1].autoscale_view()
            ax[0,2].relim()
            ax[0,2].autoscale_view()
            ax[1,0].relim()
            ax[1,0].autoscale_view()
            ax[1,1].relim()
            ax[1,1].autoscale_view()
            fig.canvas.draw()
            fig.canvas.flush_events()
    except:
        print("Crash")
        ser.close()
        break



ser.close()
