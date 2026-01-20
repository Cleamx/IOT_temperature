import dht
import time
from machine import I2C, Pin
import math
from wifi import connect
from umqtt.simple import MQTTClient
import json
import network 

d = dht.DHT11(Pin(4))
connect('M2DENG_hotspot', 'M2DENG_password')
server = "10.42.0.1"
c = MQTTClient("clem", server)
c.connect()
i = 0

while True:
    d.measure()
    T = d.temperature()
    HR = d.humidity()

    VPS = 0.6108 * math.exp((17.27 * T/(T + 237.3)))
    VPD = VPS * (1 - HR/100)

    i2c = I2C(0,scl=Pin(23), sda=Pin(22), freq=400000)

    data = {"temperature": T, "humidity": HR, "VPD": VPD}
    c.publish(b"temperature", json.dumps(data))
    time.sleep(3)

c.disconnect()
    
