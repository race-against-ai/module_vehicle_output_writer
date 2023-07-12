# Copyright (C) 2022 twyleg
import json

from serial import Serial


class HeadTracker:
    def __init__(self, serial: Serial):
        self.serial = serial
        if self.serial.isOpen():
            self.serial.close()
        self.serial.baudrate = 115200
        self.serial.open()
        self.input_buffer = ""
        # Type annotation just exists for tox, definitely needs to be changed
        self.head_tracker_data: dict[str, float] = {}
        self.initial_yaw_angle: float = 0.0
        self.initial_yaw_angle_set: bool = False

    def is_eol(self, data_to_check) -> bool:
        return data_to_check[len(data_to_check) - 1] == 10

    def reset_input_buffer(self):
        self.input_buffer = ""

    def read_head_tracker_data(self) -> bool:
        input_raw_data = self.serial.readline()
        try:
            if len(input_raw_data):
                self.input_buffer = self.input_buffer + input_raw_data.decode("utf-8")
                if self.is_eol(input_raw_data):
                    self.head_tracker_data = json.loads(self.input_buffer)
                    self.reset_input_buffer()
                    return True
        except json.JSONDecodeError:
            print("JSONDecodeError")
            self.reset_input_buffer()
        except UnicodeDecodeError:
            print("UnicodeDecodeError")
            self.reset_input_buffer()

        return False

    def get_yaw_angle(self) -> float:
        angle_yaw = float(self.head_tracker_data["angleYaw"])
        if angle_yaw > 180:
            angle_yaw = angle_yaw - 360
        return angle_yaw

    def read_neutralized_yaw_angle(self) -> float:
        current_yaw_angle: float = self.get_yaw_angle()
        if not self.initial_yaw_angle_set:
            self.initial_yaw_angle_set = True
            self.initial_yaw_angle = current_yaw_angle

        return current_yaw_angle - self.initial_yaw_angle

    def reset_initial_yaw_angle(self):
        self.initial_yaw_angle = None
