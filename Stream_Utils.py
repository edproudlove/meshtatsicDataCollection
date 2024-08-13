# Code for sending Messsages and Data over the serial Stream
# send_packet_to_radio sends a protobuf message over the serial connection to the device 

# Code adapted from: 
# - https://github.com/meshtastic/python/blob/master/meshtastic/mesh_interface.py
# - https://meshtastic.org/docs/development/device/client-api/
# - https://github.com/meshtastic/firmware/blob/bcdda4de8ab81fec6a35be52cc2a3a0fa3fa5332/src/mesh/StreamAPI.cpp#L82

# Meshtastic cli version 2.3.13 changed theese imports:
try:
    import meshtastic.mesh_pb2 as mesh_pb2
    import meshtastic.portnums_pb2 as portnums_pb2
except ImportError:
    from meshtastic.protobuf import mesh_pb2, portnums_pb2

import serial
import time
import random
import termios 

START1 = 0x94
START2 = 0xc3

def generateRadnomPacketID():
    # Limits here are semi-arbitrary 
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
    # Not working yet.
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

    # if a message has the same packetID as one we have already seen it wount send
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
    
    # No packet so just gets sent
    send_packet_to_radio(serial_obj, startConfig)


if __name__ == '__main__':
    print('Testing Message Sending')

    # If running as main, the serial port will be scraped and every n seconds 
    # a message will be send using send_message_to_radio()

    logging.basicConfig(
        level=logging.DEBUG,
        filename='StreamUtils.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
    )

    INTERVAL = 15
    portList = serial.tools.list_ports.comports()

    # Cannot handle more than one serial port connected at once
    for port in list_ports.comports():
        if port.vid is not None:
            print(port.device) 
            port_dev = port.device

    # Code from the meshtastic python lib
    with open(port_dev, 'r', encoding='utf8') as f:
        attrs = termios.tcgetattr(f)
        attrs[2] = attrs[2] & ~termios.HUPCL
        termios.tcsetattr(f, termios.TCSAFLUSH, attrs)
    time.sleep(0.1)


    ser = serial.Serial(port=port_dev, baudrate=115200, exclusive=True, timeout=0.5, write_timeout=0) 
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

            # print(ser.inWaiting())
            # print(ser.in_waiting)
            # print(ser.out_waiting)

            while ser.inWaiting() > 0:
                out += ser.read(1).decode("latin-1")
            
            if out != '':
                print('\n' + out)

            if counter % INTERVAL == 0:
                print(f'Sending Message: {counter}')
                send_message_to_radio(
                    serial_obj=ser, 
                    text = f" Hello, Counter: {counter}",
                    toIdNum = 1978533556,
                    channel = 0, 
                    want_response = 0,
                    want_ack = 0, 
                    hop_lim = 3)
    
    except KeyboardInterrupt:
        print("\n Shutting down connection ...")
        ser.close()