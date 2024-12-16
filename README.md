# RAAI Module Vehicle Output Writer

RAAI Component responsible for sending data to the Pikoder controlling the RC Car.

## Overview
The `Vehicle Output Writer` module integrates input from the Driver Input Reader and Control Panel modules, processes the data, and sends commands to the Pikoder to control the RC car’s throttle, brake, clutch, and steering. It also optionally supports head tracking for additional control inputs.

## Data Flow
1. **Input**:
   - Driver input is received via `pynng` at:
     ```
     ipc:///tmp/RAAI/driver_input_reader.ipc
     ```
   - Configuration data is received from the Control Panel at:
     ```
     ipc:///tmp/RAAI/control_panel.ipc
     ```
2. **Processing**:
   - The module applies throttle, brake, clutch, and steering configurations defined in the `driver_output_config.json` file.
3. **Output**:
   - Commands are sent to the Pikoder via serial communication.
   - Processed data is published over:
     ```
     ipc:///tmp/RAAI/vehicle_output_writer.ipc
     ```

## Configuration
The module relies on a JSON configuration file (`driver_output_config.json`) to define serial ports and control parameters. If the file is missing, a default configuration is generated.

## Dependencies
- `pynng`
- `pyserial`
- Python 3.7+
