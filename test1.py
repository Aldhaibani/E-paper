"""
Example for 4.2 inch E-ink screen
Run on pycom (LoPy/FiPy)

Copy right (c) 2019 Ghulam Mohi-Ud-Din
Copy Right (c) 2019 Omar Aldhaibani
Free of charge, to any person obtaining a copy of this software
Sourse of code (Waveshare)
https://github.com/mcauser/micropython-waveshare-epaper
Sourse of code (Pycom)
Notce: LoRa supports only Europe aera  = LoRa.EU868
"""
from network import LoRa
import socket
import time
import ubinascii
import epaper4in2
import epaper4in2b
from machine import Pin, SPI

import font12
import font20
import font24

import pycom
pycom.heartbeat(False)

from machine import Pin, SPI
# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

# create an OTAA authentication parameters
app_eui = ubinascii.unhexlify('70B3D57ED001BF99')
app_key = ubinascii.unhexlify('EFFBEFFEDDDD2A9759000CA134C5C26A')

# join a network using OTAA (Over the Air Activation)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(2.5)
    print('Not yet joined...')

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
s.setblocking(True)

# send some data
s.send(bytes([0x01, 0x02, 0x03]))

# make the socket non-blocking
# (because if there's no data received it will block forever...)
s.setblocking(False)

# get any data received (if any...)
data = s.recv(64)
print(data)

rst = Pin('P11')
dc = Pin('P10')
busy = Pin('P12')
cs = Pin('P4')
clk = Pin('P21')
mosi = Pin('P22')

spi = SPI(0, mode=SPI.MASTER, baudrate=2000000, polarity=0, phase=0, pins=(clk, mosi, None))

#spi = SPI(2, baudrate=20000000, polarity=0, phase=0, sck=sck, miso=None, mosi=mosi)

e = epaper4in2b.EPD(spi, cs, dc, rst, busy)
e.init()

w = 400
h = 300
x = 0
y = 0

# --------------------

fb_size = int(e.width * e.height)
frame_black = bytearray(fb_size)
frame_red = bytearray(fb_size)
print(e.width)

# For simplicity, the arguments are explicit numerical coordinates
stringdata = data.decode('utf-8')
e.clear_frame(frame_black, frame_red)
# For simplicity, the arguments are explicit numerical coordinates
#e.draw_rectangle(frame_black, 10, 60, 50, 110, 1)
#e.draw_filled_rectangle(frame_black, 10, 130, 50, 180, 1)
e.draw_filled_rectangle(frame_red, 0, 6, 400, 200, 1)
# choose text positions / font/ color/e.display_string_at(frame_red, X,Y, stringdata, font20, 0)
e.display_string_at(frame_red, 150, 150, stringdata, font20, 0)

e.display_frame(frame_black, frame_red)
