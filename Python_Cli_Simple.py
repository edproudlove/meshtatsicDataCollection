#Testing Setting Up a Meshtastic Python CLI Connection and printing raw packets:

import sys 
import logging

from meshtastic.serial_interface import SerialInterface
from serial.tools import list_ports
from pubsub import pub

logging.basicConfig(
    level=logging.DEBUG,
    filename='SimpleMesh.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
)

def main():
    interface = SerialInterface()
    
    def packet_recive(packet):
        print(packet)

    def onReceive(packet, interface):
        """called when a packet arrives"""
        packet_recive(packet)

    def onConnection(interface, topic=pub.AUTO_TOPIC):
        """called when we (re)connect to the radio"""
        print('Connection Established')

    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    try:
        while True:
            pass

    except KeyboardInterrupt:
        print("\n Shutting down the server...")
        interface.close()

if __name__ == "__main__":
    main()
