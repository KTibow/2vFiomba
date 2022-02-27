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
    time.sleep(0.05)
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
    print(sensor_statuses)
    if not any(sensor_statuses):
        print("no resp")
        wake_roomba()
        continue
    if last_left_encoder is None or last_right_encoder is None:
        last_left_encoder = sensor_statuses[0]
        last_right_encoder = sensor_statuses[1]
        continue
    encoder_delta = (sensor_statuses[0] - last_left_encoder) + (
        sensor_statuses[1] - last_right_encoder
    )
    degrees_turned = sensor_statuses[2]
    if degrees_turned > 0x8000:
        degrees_turned = degrees_turned - 0x10000
    light_bumper = sensor_statuses[3] > 0
    cliff = (
        sensor_statuses[4] > 0
        or sensor_statuses[5] > 0
        or sensor_statuses[6] > 0
        or sensor_statuses[7] > 0
    )
    bumper_wheel_drop = sensor_statuses[8] > 0
    try:
        with open("movement.json") as orig_f:
            movement_history = orig_f.read()
            movement_history = ujson.loads(movement_history)
    except Exception as e:
        print("error :/")
        print(e)
        movement_history = []
    with open("movement.json", "w") as f:
        movement_history.append(
            {
                "encoder_delta": encoder_delta,
                "degrees_turned": degrees_turned,
                "light_bumper": light_bumper,
                "cliff": cliff,
                "bumper_wheel_drop": bumper_wheel_drop,
            }
        )
        ujson.dump(movement_history, f, indent=2)
        print(movement_history)
    last_left_encoder = sensor_statuses[0]
    last_right_encoder = sensor_statuses[1]
    time.sleep(0.5)
