import pikoder.ppm_encoder
from serial import Serial


class PPMEncoder(pikoder.ppm_encoder.PPMEncoder):

    def __init__(self, serial: Serial):
        if serial is not None:
            if serial.isOpen():
                serial.close()
            serial.baudrate = 9600
            serial.open()
        super().__init__(serial)

    def flush_input_buffer(self):
        # TODO: This seems to be necessary because the pikoder USB2PPN interface returns an acknowledgement on every
        #       command it receives. Without this command the program silently hangs at some point in time when
        #       trying to send a new value to the pikoder.
        #       The Assumption is that without reading from the inbound buffer it overflows at some point which
        #       makes the application hang. I can't verify this entirely but since this command exists and reads the
        #       inbound buffer frequently, the program did not hand so far. If my assumption is correct,
        #       a serial.flushInput() would als do the trick but I kept this in to see if the pikoder return anything
        #       if it happens again. Fingers crossed that the assumption is correct.
        self.serial.read(self.serial.in_waiting)

    def update_driver_input(self, throttle_percent, brake_percent, steering_percent):
        self.set_channel_percentage_bounded(2, -steering_percent)

        # the limits are already set, it's just needed to check if they are set at all
        # no input, default to 0
        if brake_percent == 0 and throttle_percent == 0:
            self.set_channel_percentage_bounded(1, 0)
        elif throttle_percent > brake_percent:
            self.set_channel_percentage_bounded(1, throttle_percent)
        else:
            self.set_channel_percentage_bounded(1, -brake_percent)

        # old style, prefers brake over throttle
        # if brake_percent != 0:
            # self.set_channel_percentage_bounded(1, -brake_percent)
        # elif throttle_percent != 0:
            # self.set_channel_percentage_bounded(1, throttle_percent)
        # else:
            # self.set_channel_percentage_bounded(1, 0)

        self.flush_input_buffer()

    def update_head_tracker_input(self, yaw_angle: float):
        ppm_raw_value = 1500 - (1000 * (yaw_angle / 45.0))
        self.set_channel_raw_unbounded(3, int(ppm_raw_value))
        self.flush_input_buffer()


