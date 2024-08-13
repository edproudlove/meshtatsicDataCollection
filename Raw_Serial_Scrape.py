# Code that can read the serial port of the device - in RAW form
# Need to understand what the code means, read the docs to find where theese debug messages are being outputted and what is causing them
# Consider writing this to a file aswell: 
# And the pub sub stuff: 

import time 
import serial 
from serial.tools import list_ports
import sys
import logging 

sys.path.append('/Users/ethan/Desktop/Summer_Internship_2024/Rssi_and_snr_tests/MLDataScraping/pythonmatser')

import meshtastic.mesh_pb2 as mesh_pb2
import meshtastic.portnums_pb2 as portnums_pb2

portList = list_ports.comports()

for i in range(len(portList)):
    port = portList[i]
    if port.vid is not None:
        print(port.device) #Not Name3
        port_dev = port.device


ser = serial.Serial(port=port_dev, baudrate=115200) #If you only have one serial - works

#Using these instructions: https://meshtastic.org/docs/development/device/client-api/
#And: https://github.com/meshtastic/firmware/blob/bcdda4de8ab81fec6a35be52cc2a3a0fa3fa5332/src/mesh/StreamAPI.cpp#L82
#And: https://github.com/meshtastic/python/blob/master/meshtastic/mesh_interface.py

def send_packet_to_radio(serial_obj, protobuf_message):

    # Convert protobuf message to bytes
    protobuf_bytes = protobuf_message.SerializeToString()
    protobuf_length = len(protobuf_bytes)

    print(f'Length: {protobuf_length}')

    if protobuf_length > 512:
        raise ValueError("Protobuf length must be <= 512")

    # Construct the header
    START1 = 0x94
    START2 = 0xc3
    MSB_length = (protobuf_length >> 8) & 0xFF  # Extract the Most Significant Byte
    LSB_length = protobuf_length & 0xFF         # Extract the Least Significant Byte

    header = bytes([START1, START2, MSB_length, LSB_length])

    serial_obj.write(header + protobuf_bytes)
    serial_obj.flush()

    print(f"Header sent: {[hex(byte) for byte in header]}")
    print(f"Protobuf message sent: {protobuf_bytes}")

try:
    counter = 0
    while True:
        out = ''
        # let's wait one second before reading output (let's give device time to answer)
        time.sleep(1)
        counter += 1 
        while ser.inWaiting() > 0:
            out += ser.read(1).decode("latin-1")
            
        if out != '':
            # print('-------- NEW MESSAGE --------- \n' + out)
            print('\n' + out)
        
        if counter % 300 == 0:
            if not ser.isOpen():
                print('NOT OPEN')
                ser.open()
            print(f' {counter}: TEST SEND NOW')

            meshpacket = mesh_pb2.MeshPacket()

            meshpacket.decoded.payload = f' {counter} => HelloWorldFromSerial'.encode('utf-8') 
            meshpacket.to = 1978533556
            meshpacket.id = 0x75905e22
            meshpacket.channel = 0
            meshpacket.decoded.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
            meshpacket.decoded.want_response = 0
            meshpacket.want_ack = 0

            toRadio = mesh_pb2.ToRadio()
            toRadio.packet.CopyFrom(meshpacket)

            #this does work - sometimes and still breaks the serial scraper .... Not sure why but this is progress
            # send_packet_to_radio(serial_obj=ser, protobuf_message=toRadio)


except KeyboardInterrupt:
    print("\n Shutting down connection ...")
    ser.close()

