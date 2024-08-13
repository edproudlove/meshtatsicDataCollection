# Setting Up a Meshtastic Python CLI Connection and collecting data
# Code adapted from: https://github.com/pdxlocations/Meshtastic-Python-Examples/blob/main/print-packets.py

import csv
import numpy as np
import time
import meshtastic
import datetime

from meshtastic.serial_interface import SerialInterface
from time import strftime, localtime
from pubsub import pub

BROADCAST_ADDR = "!75ee06b4" # Other taget node addresses 1978524388 #1978533556  #'!75ee06b4' #'!75ee06b4'  #'!75ee06dc' #'!75edee94' #'75ede2e4'
KNOWN_NUMERICAL_ID_ARR = [1978533556, 1978524388, 1978527380]
ARR_TITLES = ['TIMESTAMP', 'DISTANCE', 'RECEIVER LAT', 'RECIVER LONG', 'RECIVER ALT', 'BASE LAT', 'BASE LONG', 'RSSI', 'SNR', 'HOP_LIM', 'BAND', 'TX_POWER', 'ORIENTATION']

INTERVAL = 30
RECIVER_TX_POWER = 27 #dB
ORIENTATION_INTERVAL = 200

with open('output.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(ARR_TITLES)

def distance(lat1, lon1, lat2, lon2):  # generally used geo measurement function
    R = 6378.137 #Earth R in Km
    PI = 3.14159265359
    dLat = (lat2 * PI / 180) - (lat1 * PI / 180)
    dLon = (lon2 * PI / 180) - (lon1 * PI / 180)
    a = np.sin(dLat/2) * np.sin(dLat/2) + np.cos(lat1 * PI / 180) * np.cos(lat2 * PI / 180) * np.sin(dLon/2) * np.sin(dLon/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    d = R * c
    return d * 1000

def main():
    print('Beginning Test .....')
    ori = 0 
    interface = SerialInterface()

    BaseNodeInfo = interface.getMyNodeInfo()
    print(f'Basestation Node ID: {BaseNodeInfo['user']['id']}, Long Name: {BaseNodeInfo['user']['longName']}, Short Name: {BaseNodeInfo['user']['shortName']}')

    localNode = interface.getNode('^local')
    band = ('868 MHz' if localNode.localConfig.lora.region == 3 else '433 MHz')
    local_transmit_power = RECIVER_TX_POWER 

    try:
        Base_lat = interface.nodes[BaseNodeInfo['user']['id']]['position']['latitude']
        Base_lon = interface.nodes[BaseNodeInfo['user']['id']]['position']['longitude'] 

    except:
        Base_lat = -1
        Base_lon = -1
        print('BaseStation Position Not Yet Avalible')

    
    print('Reciving Base Location')
    print(f"    Base Latitude: {Base_lat}")
    print(f"    Base Longitude: {Base_lon} \n")

    
    def packet_recive_raw(packet):
        print(f"Received: {packet} \n")

    #Code adapted from: https://github.com/pdxlocations/Meshtastic-Python-Examples/blob/main/print-packets.py
    def packet_recive(packet):
        print(f"    Band: {band}")
        print(f"    Transmission Power: {local_transmit_power} mdB")

        try:
            Base_lat = interface.nodes[BaseNodeInfo['user']['id']]['position']['latitude'] #THis one - This is the other Node:
            Base_lon = interface.nodes[BaseNodeInfo['user']['id']]['position']['longitude'] 

        except:
            Base_lat = -1
            Base_lon = -1
            print('BaseStation Position Not Avalible')

        print(f"    Base Latitude: {Base_lat}")
        print(f"    Base Longitude: {Base_lon}")

        if 'hopLimit' in packet:
            hop_lim = packet['hopLimit']
            print(f"    Hop Limit: {hop_lim}")
        else:
            hop_lim = -1
        
        if 'rxSnr' in packet:
            snr = packet['rxSnr']
            print(f"    SNR: {snr}")
        else:
            snr = -1

        if 'rxRssi' in packet:
            rssi = packet['rxRssi']
            print(f"    RSSI: {rssi}")
        else: 
            rssi = -1 

        if 'rxTime' in packet:
            pos_time = strftime('%Y-%m-%d %H:%M:%S', localtime(packet['rxTime']))
            print(f'    rxTime: {pos_time}')
        else: 
            print('Not rxTime - Using Local Time ...')
            pos_time = strftime('%Y-%m-%d %H:%M:%S', localtime(time.time()))
            print(f'    rxTime: {pos_time}')
            
        if 'decoded' in packet:
            if packet['decoded'].get('portnum') == 'POSITION_APP':
                position = packet['decoded']['position']
                lat = position.get('latitude', 'N/A')
                lon = position.get('longitude', 'N/A')
                alt = position.get('altitude', 'N/A')
                dist = distance(Base_lat, Base_lon, lat, lon)

                print(f"    Latitude: {lat}")
                print(f"    Longitude: {lon}")
                print(f"    Altitude: {alt}")
                print(f"    Distance: {dist} m")
            else:
                lat = -1
                lon = -1
                alt = -1
                dist = -1
            
        else:
            lat = -1
            lon = -1
            alt = -1
            dist = -1
        
        data = [pos_time, dist, lat, lon, alt, Base_lat, Base_lon, rssi, snr, hop_lim, band, local_transmit_power, ori]

        if packet['from'] in KNOWN_NUMERICAL_ID_ARR:
            with open('output.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(data)

        print('\n')

        print(data)

        print('\n')

    def onReceive(packet, interface):
        """called when a packet arrives"""
        packet_recive_raw(packet)

    def onConnection(interface, topic=pub.AUTO_TOPIC):
        """called when we (re)connect to the radio"""
        
        interface.sendText("Init Connection") #Send a message on public network

    pub.subscribe(onReceive, "meshtastic.receive")
    pub.subscribe(onConnection, "meshtastic.connection.established")

    try:
        counter = 0
        while True:
            time.sleep(1)
            counter += 1

            if counter % INTERVAL == 0:
                print(f'Counter: {counter}: Sending Text to {BROADCAST_ADDR}')

                # Send position and ask for a response every n seconds, 
                # Write the position, RSSI, SNR, etc. into a CSV
                # Use a PC to running this script (basestation) and move around with the target node
                try: 
                    interface.sendPosition(
                        destinationId = BROADCAST_ADDR,
                        wantAck = True,
                        wantResponse = True)

                    # interface.sendTraceRoute(
                    #     dest = node["user"]["id"],
                    #     hopLimit=5
                    #     )

                    # interface.sendText(
                    #     text='Hello World Test 1',
                    #     destinationId = BROADCAST_ADDR,)



                except meshtastic.mesh_interface.MeshInterface.MeshInterfaceError:
                    print('Timed Out Waiting For Position ...')
                    time.sleep(2)

    except KeyboardInterrupt:
        print("\n Shutting down the server...")
        interface.close()

if __name__ == "__main__":
    main()