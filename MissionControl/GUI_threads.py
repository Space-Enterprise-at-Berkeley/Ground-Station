import select
import random
import sys
import traceback
import time
import serial.tools.list_ports
import serial
import sensorParsing
import csv
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import matplotlib
matplotlib.use('Qt5Agg')


'''this is NOT finalized - just a placehold for actual values'''
id_to_sensor = {
    1: "Propane Tank",
    1: "LOX Tank",
    3: "Injector"
}

initHighPressure()


class SerialThread(QRunnable):
    '''
    Main Serial Thread

    Args:
    graphs -

    sensor_nums - a dictionary of the format
        sensor_type:# in use

    valve_signals -  is a dictionary that is kinda acting like a queue...
    should replace it with an actual queue. Right now it has all values set to 0, and will send the
    value as a message if it is non-zero

    filename - the name of the file to write the data to

    '''

    running = True

    def __init__(self, graphs, sensor_nums, valve_signals, filename):
        super(SerialThread, self).__init__()
        self.signals = SerialSignals()
        self.name = "Serial Thread"

        # ---------- Serial Config ----------------------------------

        self.sensor_nums = sensor_nums
        self.graph_titles = {'low_pt': [
            'Lox Tank', 'Propane Tank', 'Lox Injector', 'Propane Injector'], 'high_pt': ['Pressurant Tank']}
        self.sensor_types = ['low_pt', 'high_pt']  # 'high_pt', 'temp']

        self.ser = None

        self.valve_signals = valve_signals

        # ---------- Recording Config ----------------------------------

        self.raw_filename = filename
        self.filename = None
        self.save_waterflow = False
        self.headers = None

        # ---------- Display Config ---------------------------------

        # generate data to set base line on eacg graph
        n_data = 400
        xdata = list(range(n_data))
        # [random.randint(0, 10) for i in range(n_data)]
        ydata = [0 for i in range(n_data)]

        # Initialize Plot
        # plot_refs = self.canvas.axes.plot(self.xdata, self.ydata, 'b')
        # self._plot_ref = plot_refs[0]

        # Create canvases based on the number of sensors that are actually in use
        self.plot_ref_dict = {}  # [self._plot_ref]
        self.canvas_dict = {}

        for sensor in self.sensor_types:
            self.canvas_dict[sensor] = []
            self.plot_ref_dict[sensor] = []
            for i in range(len(graphs[sensor])):
                canvas = graphs[sensor][i]
                self.canvas_dict[sensor].append(canvas)
                # Get plot reference that can be used to update graph later
                plot_refs = canvas.axes.plot(xdata, ydata, 'b')
                self.plot_ref_dict[sensor].append(plot_refs[0])
                canvas.axes.set_title(self.graph_titles[sensor][i])

    @pyqtSlot()
    def run(self):
        '''
        Initialize the independent thread
        '''

        # while SerialThread.running:
        #     result = random.randint(0, 10)
        #     self.update_plot(result)
        #     time.sleep(0.01)

        NUMDATAPOINTS = 400
        fail_num = 15
        should_print = True

        print("Starting")

        chosenCom = ""
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            print(p)
            if "Arduino" in p.description or "ACM" in p.description or "cu.usbmodem" in p[0]:
                chosenCom = p[0]
                print("Chosen COM: {}".format(p))
        if not chosenCom:
            self.stop_thread("No Valid Com Found")
            return
        print("Chosen COM {}".format(chosenCom))
        baudrate = 9600
        print("Baud Rate {}".format(baudrate))
        try:
            ser = serial.Serial(chosenCom, baudrate, timeout=3)
            self.ser = ser
        except Exception as e:
            self.stop_thread("Invalid Serial Connection")
            return
        ser.flushInput()

        display = True
        display_all = False
        repeat = 1

        # filename = input("Which file should the data be written to?\n")
        print("Writing raw data to: {}".format(self.raw_filename))

        fails = 0
        currLine = str(ser.readline())
        start = time.time()
        while ("low pressure sensors" not in currLine and "low pt" not in currLine):
            currLine = str(ser.readline())
            if (currLine != "b''"):
                print(currLine)
                if time.time() - start > 1.5:
                    start = time.time()
                    print("looking for low pressure input")
            else:
                fails += 1
            if (fails == fail_num):
                self.stop_thread("Connection Lost")
                return
        numLowSensors = self.sensor_nums['low_pt']
        byteNum = (str(numLowSensors) + "\r\n").encode('utf-8')
        print("write low sensor nums: {}".format(ser.write(byteNum)))

        currLine = str(ser.readline())
        start = time.time()
        while ("high pressure sensors" not in currLine):
            currLine = str(ser.readline())
            if time.time() - start > 1.5:
                start = time.time()
                print("looking for high pressure input")
        numHighSensors = self.sensor_nums['high_pt']
        byteNum = (str(numHighSensors) + "\r\n").encode('utf-8')
        print("write high sensor nums: {}".format(ser.write(byteNum)))

        total_sensors = numLowSensors + numHighSensors  # TODO: add in temp sensor
        # sensors = int(input("How many sensors are connected?\n")) #set to how many sensors are connected
        # There are x low PTs and x high PTs.
        print(ser.readline().decode("utf-8"))
        # low1, low2, low3, high1.....
        self.headers = ser.read_until().decode("utf-8")
        headerList = self.headers.split(",")
        print(headerList)

        print("num sensors: {}".format(total_sensors))
        data_dict = {}
        toDisplay_dict = {}
        for sensor in self.sensor_types:
            data_dict[sensor] = [[] for i in range(self.sensor_nums[sensor])]
            toDisplay_dict[sensor] = [[] for i in range(total_sensors)]

        with open(self.raw_filename, "a") as f:
            self.headers = "time elapsed, " + self.headers
            f.write(self.headers + "\n")

        ser.write("0\r\n".encode('utf-8'))

        # TODO: Figure out why this is crashing on close

        def getLatestSerialInput():
            if ser:
                line = ser.readline()
                start = time.time()
                while(ser.in_waiting > 0):
                    if ser:
                        line = ser.readline()
                        if time.time() - start > 1.5:
                            start = time.time()
                            print("looking for low pressure input")
                return line.decode('utf-8').strip()

        last_first_value = 0
        last_values = [0] * 5

        start = time.time()
        print("starting loop")
        while SerialThread.running:
            # try:
            line = getLatestSerialInput()
            if ',' in line:
                values = line.strip().split(',')

                if values[0] == '':
                    values[0] = str(last_first_value)
                if len(values) < total_sensors:
                    print("not enough data, continuing")
                    continue
                last_values = values
                values = [val.strip() for val in values]
                values = [lowPressureConversion(val) if i != 0 else highPressureConversion(
                    val) for val, ind in enumerate(values)]
                last_first_value = values[0]

                if should_print:
                    print("values: {}".format(values))

                with open(self.raw_filename, "a") as fe:
                    toWrite = str(time.time() - start) + \
                        "," + ",".join(values) + "\n"
                    fe.write(toWrite)
                    writer = csv.writer(fe, delimiter=",")
                if self.save_waterflow:
                    with open(self.filename, "a") as fe:
                        toWrite = str(
                            time.time() - self.waterflow_start) + "," + ",".join(values) + "\n"
                        fe.write(toWrite)
                        writer = csv.writer(fe, delimiter=",")

                # iterate through values of incoming data and add to appropriate graps datasets
                sensor = ''
                for i in range(len(values)):
                    # At the start of each series of sensor values, change sensor type & reset j
                    if i == 0:
                        sensor = 'high_pt'
                        j = 0
                    elif i == 1:
                        sensor = 'low_pt'
                        j = 0
                    # elif: i == 5:
                    #     pass #TODO: add in for temperature sensors

                    # if the value is -1, that means there is no data for that sensor
                    # if j >= self.sensor_nums[sensor], that means not all sensor are being used
                    if values[i] != -1 and j < self.sensor_nums[sensor]:
                        data = data_dict[sensor]
                        toDisplay = toDisplay_dict[sensor]
                        plots = self.plot_ref_dict[sensor]

                        data[j].append(float(values[i]))
                        toDisplay[j] = data[j][-NUMDATAPOINTS:]
                        if should_print:
                            print(len(data[j]))
                            print(len(toDisplay[j]))
                            print("Sensor: {} Index: {}".format(sensor, j))

                        if display_all:
                            plots[j].set_ydata(data[j])
                            plots[j].set_xdata(range(len(data[j])))
                        else:
                            plots[j].set_ydata(toDisplay[j])
                            plots[j].set_xdata(range(len(toDisplay[j])))

                    j += 1

                if should_print:
                    should_print = False

                # update graph display & rescale based off data
                if display and repeat % 2 == 0:
                    for sensor in self.sensor_types:
                        canvas_list = self.canvas_dict[sensor]
                        for i in range(len(canvas_list)):

                            canvas_list[i].axes.relim()
                            canvas_list[i].axes.autoscale_view()

                        # for num in range(numHighSensors):
                        #     ax[1,num].relim()
                        #     ax[1,num].autoscale_view()

                            canvas_list[i].draw()
                        # self.canvas.flush_events()
                    repeat = 1
                else:
                    repeat += 1

                # valve stuff
                for name in self.valve_signals.keys():
                    if (self.valve_signals[name] != 0):
                        print(self.valve_signals[name])
                        byteNum = (
                            str(self.valve_signals[name]) + "\r\n").encode('utf-8')
                        ser.write(byteNum)
                        self.valve_signals[name] = 0

                # data_in = select.select([sys.stdin], [], [], 0.1)[0]
                # if data_in:
                #     c = sys.stdin.readline().rstrip()
                #     if (c == "q"):
                #         print("Exiting")
                #         sys.exit(0)
                #     elif c == '0':
                #         display = not display
                #         print("toggling display")
                #     elif c == 't':
                #         display = True
                #     elif c == 'f':
                #         display = False
                #     elif c == 'd':
                #         display_all = not display_all
                #         print("toggle display all data")
                #     elif c == "c":
                #         data = [[] for i in range(sensors)]
                #         toDisplay = [[] for i in range(sensors)]
                #     else:
                #         print("You entered: %s" % c)
            else:
                print(line)

            # except Exception as e:
            #     # self.stop_thread("Error in reading loop\nCrash: {}".format(e))
            #     print("Error in reading loop\nCrash: {}")#.format(e))
            #
            #     exception_type, exception_object, exception_traceback = sys.exc_info()
            #     filename = exception_traceback.tb_frame.f_code.co_filename
            #     line_number = exception_traceback.tb_lineno
            #
            #     print("Exception type: ", exception_type)
            #     print("File name: ", filename)
            #     print("Line number: ", line_number)
            #
            #     ser.close()
            #     break

        self.stop_thread("Thread Stopped")

    def stop_thread(self, msg=''):
        SerialThread.running = False
        if self.ser:
            self.ser.close()
        if msg:
            print("{}: ".format(self.name), msg)
        self.signals.finished.emit()

    def update_plot(self):

        self._plot_ref.set_ydata(self.ydata)
        self._plot_ref.set_xdata(self.xdata)

        self.canvas.draw()

    def start_saving_waterflow(self, filename, metadata):
        if self.headers:
            self.filename = "data/" + filename
            self.waterflow_start = time.time()
            print("Writing data to: {}".format(filename))
            with open(self.filename, "a") as f:
                f.write(metadata + "\n")
                f.write(self.headers + "\n")
            self.save_waterflow = True
        else:
            print("Error: data collection has not started")

    def stop_saving_waterflow(self):
        self.save_waterflow = False


class SerialSignals(QObject):
    '''
    Defines the signals available from a running worker thread

    Suported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    data = pyqtSignal(object)
