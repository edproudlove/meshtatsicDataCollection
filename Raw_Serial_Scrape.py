# Code that prints the raw output of the serial port of the device

import time 
import serial 
from serial.tools import list_ports

# Cannot handle more than one serial port connected at once
for port in list_ports.comports():
    if port.vid is not None:
        print(port.device) 
        port_dev = port.device

ser = serial.Serial(port=port_dev, baudrate=115200)

try:
    while True:
        out = ''
        time.sleep(1)
        while ser.inWaiting() > 0:
            out += ser.read(1).decode("latin-1")
            
        if out != '':
            print('\n' + out)
        
except KeyboardInterrupt:
    print("\n Shutting down connection ...")
    ser.close()

