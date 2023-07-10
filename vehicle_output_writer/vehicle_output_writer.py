import pynng
import os
import json
import select

from serial import Serial
from vehicle_output_writer.ppm_encoder import PPMEncoder
from vehicle_output_writer.head_tracker import HeadTracker

CONTROL_PANEL_PYNNG_ADDRESS = "ipc:///tmp/RAAI/control_panel.ipc"
CONTROL_COMPONENT_PYNNG_ADDRESS = "ipc:///tmp/RAAI/vehicle_output_writer.ipc"
PLATFORM_CONTROLLER_PYNNG_ADDRESS = "ipc:///tmp/RAAI/driver_input_reader.ipc"

example_config = {
    "pikoder_serial": "COM3",
    "head_tracker_serial": "COM10",
    "throttle_config": {
        "max_throttle": 15,
        "max_brake": 50,
        "max_clutch": 50,
        "max_steering": 100,
        "steering_offset": 0.0
    },
    "head_tracking_status": False
}


def send_data(pub: pynng.Pub0, payload: dict, topic: str = " ", p_print: bool = True) -> None:
    """
    publishes data via pynng

    :param pub: publisher
    :param payload: data that should be sent in form of a dictionary
    :param topic: the topic under which the data should be published  (e.g. "lap_time: ")
    :param p_print: if true, the message that is sent will be printed out. Standard is set to true
    """
    json_data = json.dumps(payload)
    msg = topic + json_data
    if p_print is True: print(f"data send: {msg}")
    pub.send(msg.encode())


def receive_data(sub: pynng.Sub0) -> dict:
    """
    receives data via pynng and returns a variable that stores the content

    :param sub: subscriber
    :param timer: timeout timer for max waiting time for new signal
    """
    msg = sub.recv()
    data = remove_pynng_topic(msg)
    data = json.loads(data)
    return data


def remove_pynng_topic(data, sign: str = " ") -> str:
    """
    removes the topic from data that got received via pynng and returns a variable that stores the content

    :param data: date received from subscriber
    :param sign: last digit from the topic
    """
    decoded_data: str = data.decode()
    i = decoded_data.find(sign)
    decoded_data = decoded_data[i + 1:]
    return decoded_data


def read_config(config_file_path: str) -> dict:
    if os.path.isfile(config_file_path):
        print("Config file found")
        with open(config_file_path, "r") as file:
            return json.load(file)

    else:
        print("---!Config File not Found!---")
        print("pikoder_serial: COM9 and head_tracker_serial: COM10")

        config_data = json.dumps(example_config, indent=4)
        with open(config_file_path, "w") as file:
            file.write(config_data)
            return example_config


class VehicleOutputWriter:

    def __init__(self):

        self.config = read_config("./driver_output_config.json")


        self.output_writer_publisher = pynng.Pub0()
        self.output_writer_publisher.listen(CONTROL_COMPONENT_PYNNG_ADDRESS)

        self.control_panel_subscriber = pynng.Sub0()
        self.control_panel_subscriber.subscribe("config")
        self.control_panel_subscriber.dial(CONTROL_PANEL_PYNNG_ADDRESS, block=False)

        self.control_panel_config = self.config["throttle_config"]

        self.driver_input_subscriber = pynng.Sub0()
        self.driver_input_subscriber.subscribe("driver_input")
        self.driver_input_subscriber.dial(PLATFORM_CONTROLLER_PYNNG_ADDRESS, block=False)

        self.ppm_encoder = None
        try:
            self.ppm_encoder_serial = Serial(self.config["pikoder_serial"])
            self.ppm_encoder = PPMEncoder(self.ppm_encoder_serial)
        except:
            print('ppm_encoder unavailable or on wrong port in driver_output_settings.json')

        self.head_tracker = None
        try:
            self.head_tracker_serial = Serial(self.config['head_tracker_serial'], timeout=0)
            self.head_tracker = HeadTracker(self.head_tracker_serial)
            # normally a qtimer is here. probably has a function that needs to be in a loop
        except:
            print("head tracker unavailable or wrong port in driver_output_settings.json")

        self.driver_input = {
            "throttle": 0.0,
            "brake": 0.0,
            "clutch": 0.0,
            "steering": 0.0
        }

        self.throttle = 0
        self.brake = 0
        self.steering = 0.0

        self.inputs = [self.control_panel_subscriber.recv_fd, self.driver_input_subscriber.recv_fd]
        self.fd_dict = {
            self.control_panel_subscriber.recv_fd: [self.control_panel_subscriber, self.control_panel_config],
            self.driver_input_subscriber.recv_fd: [self.driver_input_subscriber, self.driver_input]
        }

    def receive_subscriber_data(self) -> None:
        readable_fds, _, _ = select.select(self.inputs, [], [])

        for readable_fds in readable_fds:
            subscriber = self.fd_dict[readable_fds][0]
            self.fd_dict[readable_fds][1] = receive_data(subscriber)
            # print(self.fd_dict[readable_fds][1])

        self.control_panel_config = self.fd_dict[self.control_panel_subscriber.recv_fd][1]
        # print(self.control_panel_config)
        # print(self.driver_input)
        self.driver_input = self.fd_dict[self.driver_input_subscriber.recv_fd][1]

    def process_data(self) -> None:
        self.receive_subscriber_data()

        self.throttle = self.driver_input["throttle"] * (self.control_panel_config["max_throttle"] / 100.0)

        if self.driver_input["clutch"] > self.driver_input["brake"]:
            self.brake = self.driver_input["clutch"] * (self.control_panel_config["max_clutch"] / 100.0)
        else:
            self.brake = self.driver_input["brake"] * (self.control_panel_config["max_brake"] / 100.0)

        self.steering = self.driver_input["steering"] * (self.control_panel_config["max_steering"] / 100.0)
        self.steering += self.control_panel_config["steering_offset"]

    def send_info_to_encoder(self) -> None:
        if self.ppm_encoder:
            self.ppm_encoder.update_driver_input(self.throttle, self.brake, self.steering)

    def run(self) -> None:
        self.process_data()
        self.send_info_to_encoder()
        # print(self.steering)


if __name__ == "__main__":
    vehicle_control = VehicleOutputWriter()
