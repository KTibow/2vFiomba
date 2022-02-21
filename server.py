# Needed imports
print("We'll Be Right Back")
import time

import paho.mqtt.client as mqtt
import serial, ujson

from interface import *

# Connect to the Roomba and Home Assistant
roomba = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.1)
ha = mqtt.Client("roomba")
ha.username_pw_set("mqtt", "M2vRaGmH")
ha.connect("homeassistant.local")

print("*ahem*")


def to_bytes(number: int) -> bytes:
    """Convert a number to a byte"""
    return number.to_bytes(1, "big")


def find_state():
    """Do epic mathz to find the state of the roomba"""
    roomba.read_all()
    roomba.write(
        OPCODE_SEND_SENSORS
        + bytes(
            [
                6,  # 6 sensors
                34,  # Is it charging?
                56,  # Is the main brush on?
                54,  # Is the left wheel on?
                55,  # Is the right wheel on?
                25,  # How charged is the battery?
                26,  # How charged can the battery be?
            ]
        )
    )
    time.sleep(0.025)
    sensor_statuses = (
        int.from_bytes(roomba.read(1), "big"),
        int.from_bytes(roomba.read(2), "big"),
        int.from_bytes(roomba.read(2), "big"),
        int.from_bytes(roomba.read(2), "big"),
        int.from_bytes(roomba.read(2), "big"),
        int.from_bytes(roomba.read(2), "big"),
    )
    is_charging = sensor_statuses[0] > 0
    is_moving = sensor_statuses[1] > 0 or sensor_statuses[2] > 0 or sensor_statuses[3] > 0
    try:
        battery_level = sensor_statuses[4] / sensor_statuses[5]
    except ZeroDivisionError:
        battery_level = 0
    did_not_respond = all(packet == 0 for packet in sensor_statuses)
    # Available states: cleaning, docked, paused, idle, returning, error
    if did_not_respond:
        return ("error", 0)
    if is_charging:
        return ("docked", battery_level)
    if is_moving:
        return ("cleaning", battery_level)
    return ("idle", battery_level)


def wake_roomba():
    """Wake up the roomba"""
    roomba.close()
    roomba.open()
    time.sleep(0.05)
    roomba.write(OPCODE_START)
    time.sleep(0.05)


def on_command(client, userdata, message):
    global command_queue
    command_queue.append(message.payload.decode("utf-8"))


command_queue = []
last_update_sent = 0
last_state_sent = ""
last_state_check = 0
ha.subscribe("roomba/command")
ha.message_callback_add("roomba/command", on_command)
ha.loop_start()

print("Let's get into it, shall we?")

while True:
    # Check what the roomba is doing
    if time.time() - last_state_check > 10:
        current_state, battery_level = find_state()
        if current_state == "error" and time.time() - last_state_check > 600:
            wake_roomba()
            continue
        last_state_check = time.time()
    if time.time() - last_update_sent > 15 or current_state != last_state_sent:
        last_update_sent = time.time()
        last_state_sent = current_state
        ha.publish(
            "roomba/state",
            ujson.dumps(
                {"state": current_state, "battery_level": round(battery_level * 1000) / 10}
            ),
        )
        print("State:", current_state, "Battery:", battery_level)
    if len(command_queue) > 0:
        wake_roomba()
        command = command_queue.pop(0)
        print("Running command", command)
        if command == "start":
            roomba.write(OPCODE_CLEAN)
        elif command == "pause":
            roomba.write(OPCODE_SAFE)
            time.sleep(0.05)
            roomba.write(OPCODE_START)
        elif command == "return_to_base":
            roomba.write(OPCODE_DOCK)
        elif command == "clean_spot":
            roomba.write(OPCODE_SPOT)
        elif command == "locate":
            roomba.write(OPCODE_SAFE)
            time.sleep(0.05)
            roomba.write(
                OPCODE_STORE_SONG
                + bytes(
                    [
                        0,
                        11,
                        64,
                        22,
                        67,
                        22,
                        70,
                        22,
                        73,
                        22,
                        70,
                        22,
                        67,
                        22,
                        64,
                        22,
                        0,
                        50,
                        64,
                        12,
                        67,
                        12,
                        64,
                        12,
                    ]
                )
            )  # Among Us
            time.sleep(0.05)
            roomba.write(OPCODE_PLAY_SONG + b"\x00")
            time.sleep(22 * 7 / 64 + 50 / 64 + 12 * 3 / 64)
            roomba.write(OPCODE_START)
        else:
            print("Unknown command:", command)
    time.sleep(0.25)
