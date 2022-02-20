# Needed imports
print("We'll Be Right Back")
import time

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import serial

from interface import *

# Connect to the Roomba and Home Assistant
roomba = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.1)
ha = mqtt.Client("roomba")
ha.username_pw_set("mqtt", "M2vRaGmH")
ha.connect("homeassistant.local")
# ha.subscribe("roomba/command")
# ha.message_callback_add("roomba/command", on_command)
# ha.publish("roomba/status", "online")

print("*ahem*")


def to_bytes(number: int) -> bytes:
    return number.to_bytes(1, "big")


def find_state():
    # Do epic mathz to find the state of the roomba
    roomba.read_all()
    roomba.write(OPCODE_START)
    roomba.write(
        OPCODE_SEND_SENSORS
        + to_bytes(6)  # 6 sensors
        + to_bytes(34)  # Is it charging?
        + to_bytes(56)  # Is the main brush on?
        + to_bytes(54)  # Is the left wheel on?
        + to_bytes(55)  # Is the right wheel on?
        + to_bytes(25)  # How charged is the battery?
        + to_bytes(26)  # How charged can the battery be?
    )
    for i in range(5):
        print(roomba.read_all())
        time.sleep(0.01)
        print(i)


find_state()
