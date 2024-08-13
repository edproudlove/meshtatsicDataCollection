#Code for sending Messsages and Data over the serial Stream
import sys

sys.path.append('/Users/ethan/Desktop/Summer_Internship_2024/Rssi_and_snr_tests/MLDataScraping/pythonmatser')

import meshtastic.mesh_pb2 as mesh_pb2
import meshtastic.portnums_pb2 as portnums_pb2
import serial
import time
import logging
import random
import termios 
import os

START1 = 0x94
START2 = 0xc3

def generateRadnomPacketID():
    #Limits here are the semi arbitrary: latest packet I had recived -> the largest 4 byte unsigned value (0xFFFFFFFF) 
    return random.randrange(3170588179, 4294967295)

def send_packet_to_radio(
    serial_obj, 
    protobuf_message):

    # Convert protobuf message to bytes
    b = protobuf_message.SerializeToString()
    bufLen = len(b)

    print(f'Length: {bufLen}')

    if bufLen > 512:
        raise ValueError("Protobuf length must be <= 512")

    # Construct the header
    MSB_length = (bufLen >> 8) & 0xFF  # Extract the Most Significant Byte
    LSB_length = bufLen & 0xFF         # Extract the Least Significant Byte

    header = bytes([START1, START2, MSB_length, LSB_length])

    serial_obj.write(header + b)
    serial_obj.flush()

    time.sleep(0.1)

    print(f"sending header:{header} b:{b}")
    # print(f"Header sent: {[hex(byte) for byte in header]}")
    # print(f"Protobuf message sent: {b}")


def send_message_to_radio(
    serial_obj, 
    text, 
    toIdNum,
    channel, 
    want_response,
    want_ack,
    hop_lim):

    meshpacket = mesh_pb2.MeshPacket()
    meshpacket.decoded.payload = text.encode('utf-8') 
    meshpacket.to = toIdNum
    meshpacket.id = generateRadnomPacketID()
    meshpacket.channel = channel
    meshpacket.decoded.portnum = portnums_pb2.PortNum.TEXT_MESSAGE_APP
    meshpacket.decoded.want_response = want_response
    meshpacket.want_ack = want_ack
    meshpacket.hop_limit = hop_lim

    toRadio = mesh_pb2.ToRadio()
    toRadio.packet.CopyFrom(meshpacket)

    send_packet_to_radio(serial_obj=serial_obj, protobuf_message=toRadio)

def send_traceroute(
    serial_obj, 
    toIdNum,
    meshpacketID,
    channel, 
    want_ack,
    hop_lim):

    data = mesh_pb2.RouteDiscovery()
    if getattr(data, "SerializeToString", None):
        print('SERIALISE NEEDED')
        logging.debug(f"Serializing protobuf as data: {stripnl(data)}")
    data = data.SerializeToString()

    meshpacket = mesh_pb2.MeshPacket()
    meshPacket.decoded.payload = data
    meshPacket.to = toIdNum
    meshPacket.id = generateRadnomPacketID()
    meshpacket.channel = channel
    meshPacket.decoded.portnum = portnums_pb2.PortNum.TRACEROUTE_APP
    meshpacket.decoded.want_response = True
    meshpacket.want_ack = want_ack
    meshpacket.hop_limit = hop_lim

    toRadio = mesh_pb2.ToRadio()
    toRadio.packet.CopyFrom(meshpacket)

    send_packet_to_radio(serial_obj=serial_obj, protobuf_message=toRadio)

    #Wait for responce and need a response handler ....

def connect(serial_obj):
    p = bytearray([START2] * 32)
    print(f"Connecting: {p} \n")
    serial_obj.write(p)
    serial_obj.flush()
    time.sleep(0.1)

def startConfig(serial_obj):
    print("Start Config \n")

    startConfig = mesh_pb2.ToRadio()
    configId = random.randint(0, 0xFFFFFFFF)
    startConfig.want_config_id = 69420
    
    #Dosent Have a packet so just gets sent

    send_packet_to_radio(serial_obj, startConfig)






if __name__ == '__main__':
    print('Testing Message Sending')

    logging.basicConfig(
        level=logging.DEBUG,
        filename='StreamUtils.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
    )

    INTERVAL = 15
    portList = serial.tools.list_ports.comports()

    for i in range(len(portList)):
        port = portList[i]
        if port.vid is not None:
            print(port.device) #Not Name
            port_dev = port.device


    #Code from the python lib
    with open(port_dev, 'r', encoding='utf8') as f:
        attrs = termios.tcgetattr(f)
        attrs[2] = attrs[2] & ~termios.HUPCL
        termios.tcsetattr(f, termios.TCSAFLUSH, attrs)
    time.sleep(0.1)


    ser = serial.Serial(port=port_dev, baudrate=9600, exclusive=True, timeout=0.5, write_timeout=0) 
    ser.flush()
    time.sleep(0.1)

    connect(ser)

    startConfig(ser)

    try:
        counter = 0
        while True:
            out = ''
            time.sleep(1)
            counter += 1

            print(ser.inWaiting())
            print(ser.in_waiting)
            print(ser.out_waiting)

            while ser.inWaiting() > 0:
                out += ser.read(1).decode("latin-1")
            
            if out != '':
                print('\n' + out)

            if counter % INTERVAL == 0:
                #COuld try flushing the input buffer etc...
                print(f'Sending Message: {counter}')
                send_message_to_radio(
                    serial_obj=ser, 
                    text = f"Hello From Ethan .... {counter}",
                    toIdNum = 1978533556,
                    channel = 0, 
                    want_response = 0,
                    want_ack = 0, 
                    hop_lim = 3)
    
    except KeyboardInterrupt:
        print("\n Shutting down connection ...")
        ser.close()


#This workes at the momment -> but as soon as i write to the serial, I cannot read anythingß
#The Reading Problem is not solved yet tho .... still breaks everytime ...

#Idea at the moment: Have a buffer that reads and writes into the serial for you: Also look at the que functionality of the python cli
#IT DOSENT need to work after the restart if the traceroute is working correctly -> you just scrape for however many seconds
#But i still think this will have an effect


#Possible haky workaround: you can set the from param of a mesh packet: could use a second node to send the packets with the from of
#Node being scraped

#Maybe we need to start the connection first connect() .....





