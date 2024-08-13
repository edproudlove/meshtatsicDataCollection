# Meshtatsic Data Collection
- Simple scripts to collect RSSI, SNR, and position data using the meshtastic CLI and LilyGo T3S3 boards. 

- Collect_Data_Simple.py: code used to collect csv data using the Meshtastic Cli
- Python_Cli_Simple.py: just prints all raw packet data recived by the node
- Stream_Utils.py: python implementation of sending text, traceroutes, and protobufs to the device over the serial. 
- Raw_Serial_Scrape.py: code to print the raw output of the serial port of the device

- #### Issues
- Cannot read and write to serial at same time (in Raw_Serial_Scrape.py). As soon as you write to the serial, the debug messages stop / are not being read. 
- You can read the protobufs but then you might aswell just use the python cli as done in Collect_Data_Simple.py. 
- This has been succsessfully implemented in: https://github.com/edproudlove/meshtasticScraper, using the Bluetooth client and serial client together. 


### Usefull Resorces:
- https://github.com/pdxlocations/Meshtastic-Python-Examples/blob/main/print-packets.py
- https://github.com/meshtastic/python/blob/master/meshtastic/mesh_interface.py
- https://meshtastic.org/docs/development/device/client-api/
