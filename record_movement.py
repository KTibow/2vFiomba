"""
Record the movement of the Roomba, and save it to a file for later analysis.

The file is saved in the current working directory.

The file format is a JSON file, with the following columns:

- Amount that the Roomba has moved forwards/backwards
- Amount that the Roomba has turned left/right (left is positive, right is negative)
- Light bumper (true/false)
- Cliff (true/false)
- Bumper/wheel drop (true/false)
"""
import time

import serial
import ujson

from interface import *

roomba = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.1)


def wake_roomba():
    """Wake up the roomba"""
    roomba.close()
    roomba.open()
    time.sleep(0.05)
    roomba.write(OPCODE_START)
    time.sleep(0.05)


last_left_encoder = None
last_right_encoder = None

wake_roomba()
while True:
    roomba.write(
        OPCODE_SEND_SENSORS
        + bytes(
            [
                9,  # Count
                43,  # Left wheel encoder
                44,  # Right wheel encoder
                20,  # Degrees
                45,  # Light bumper
                9,  # Cliff left
                10,  # Cliff front left
                11,  # Cliff front right
                12,  # Cliff right
                7,  # Bumper/wheel drop
            ]
        )
    )
    time.sleep(0.025)
    sensor_statuses = (
        int.from_bytes(roomba.read(2), "big"),
        int.from_bytes(roomba.read(2), "big"),
        int.from_bytes(roomba.read(2), "big"),
        int.from_bytes(roomba.read(1), "big"),
        int.from_bytes(roomba.read(1), "big"),
        int.from_bytes(roomba.read(1), "big"),
        int.from_bytes(roomba.read(1), "big"),
        int.from_bytes(roomba.read(1), "big"),
        int.from_bytes(roomba.read(1), "big"),
    )
    if sensor_statuses[0] < last_left_encoder:
        last_left_encoder -= 0x10000
    if sensor_statuses[1] < last_right_encoder:
        last_right_encoder -= 0x10000
    encoder_delta = (sensor_statuses[0] - last_left_encoder) + (
        sensor_statuses[1] - last_right_encoder
    )
    degrees_turned = sensor_statuses[2]
    light_bumper = sensor_statuses[3] > 0
    cliff = (
        sensor_statuses[4] > 0
        or sensor_statuses[5] > 0
        or sensor_statuses[6] > 0
        or sensor_statuses[7] > 0
    )
    bumper_wheel_drop = sensor_statuses[8] > 0
    with open("movement.json", "w") as f:
        try:
            movement_history = ujson.load(f)
        except Exception:
            movement_history = []
        movement_history.append(
            {
                "encoder_delta": encoder_delta,
                "degrees_turned": degrees_turned,
                "light_bumper": light_bumper,
                "cliff": cliff,
                "bumper_wheel_drop": bumper_wheel_drop,
            }
        )
        ujson.dump(movement_history, f)
    last_left_encoder = sensor_statuses[0]
    last_right_encoder = sensor_statuses[1]
    time.sleep(0.5)
