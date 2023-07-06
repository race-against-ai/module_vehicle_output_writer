# RAAI Module Vehicle Output Writer

RAAI Component responsible for sending Data to the Pikoder controlling the RC Car

## Structure
Input data is received from the Driver Input Reader module over the pynng address <br>
``ipc:///tmp/RAAI/driver_input_reader.ipc``

The Data then gets processed with the Throttles send by the Control Panel over the address <br>
``ipc:///tmp/RAAI/control_panel.ipc``

The Data itself gets send to the Pikoder specified in the config file and also gets published over the address <br>
``ipc:///tmp/RAAI/vehicle_output_writer.ipc``
