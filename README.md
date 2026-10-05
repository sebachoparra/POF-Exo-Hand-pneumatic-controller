<div align="center">

# ExoHand ROS 2 Workspace

### ROS 2 control and sensing framework for a pneumatic soft hand exoskeleton

<p align="center">
  <img
    src="https://github.com/user-attachments/assets/7cd1d72d-2325-4c24-b981-fe07d23a7242"
    alt="ExoHand soft robotic hand exoskeleton"
    width="500"
  />
</p>

</div>

## Overview

**ExoHand ROS 2 Workspace** contains the software developed for sensing,
control, actuation, and experimental evaluation of a pneumatic soft hand
exoskeleton for assistive and rehabilitation applications.

The platform integrates pneumatic actuation, optical and inertial sensing,
signal processing, and closed-loop control through a modular ROS 2
architecture.

The system was initially developed for closed-loop finger-curvature control
using Polymer Optical Fiber (POF) sensing and a PI controller. The workspace
has since been extended with additional sensing and experimental modules,
including dual IMUs and support for optical interrogation systems.

---

## System Architecture

<p align="center">
  <img
    src="https://github.com/user-attachments/assets/5409971e-2a1c-44f4-a684-abb8a43007b5"
    alt="ExoHand ROS 2 system architecture"
    width="750"
  />
</p>

The software architecture separates the system into sensing, signal
processing, control, pneumatic actuation, communication, and user-interface
modules.

At a high level, the control pipeline follows:

```text
Sensors
   │
   ▼
Signal acquisition
   │
   ▼
Signal processing / filtering
   │
   ▼
Curvature or motion feedback
   │
   ▼
PI controller
   │
   ▼
PWM command
   │
   ▼
Pneumatic valves + pumps
   │
   ▼
Soft hand exoskeleton
```

---

## ROS 2 Workspace

The repository follows the standard ROS 2 workspace organization:

```text
POF-Exo-Hand-pneumatic-controller/
├── src/
│   ├── adc_node/
│   ├── exohand_signal_proc/
│   ├── hyperion_ros2_driver/
│   ├── imu/
│   ├── pi_controller/
│   ├── pneumatic_system/
│   ├── valve_control/
│   ├── MQTT_bridge/
│   ├── web_interface/
│   ├── huskylens/
│   └── py_pubsub_test/
│
├── imu_pwm_acquisition/
├── legacy_prototypes/
├── COMMANDS.md
└── README.md
```

### Main packages

| Package | Function |
|---|---|
| `adc_node` | Analog signal acquisition |
| `exohand_signal_proc` | Sensor filtering and POF signal processing |
| `pi_controller` | Closed-loop PI curvature controller |
| `pneumatic_system` | ROS 2 interfaces for pumps and pneumatic valves |
| `valve_control` | PWM valve control and experimental command sequences |
| `imu` | Dual BNO055 inertial sensing |
| `hyperion_ros2_driver` | ROS 2 interface for the Hyperion SI255 optical interrogator |
| `MQTT_bridge` | ROS 2 / MQTT communication bridge |
| `web_interface` | Web-based system interface |
| `huskylens` | Experimental vision interface |

Some packages correspond to ongoing experimental development and are not
part of the original POF-based closed-loop validation.

---

## Hardware Platform

The experimental platform is based on a pneumatically actuated soft hand
exoskeleton controlled through ROS 2.

The POF-based experimental configuration includes:

- Soft pneumatic hand exoskeleton
- Raspberry Pi 4
- Pneumatic diaphragm pumps
- 3/2 solenoid valves
- POF curvature sensors
- Optical emitter/receiver electronics
- ADS1263 analog-to-digital converter
- MOSFET-based pneumatic actuation electronics

Additional experimental configurations in this repository include dual
BNO055 IMUs and optical interrogation hardware.

---

## Closed-Loop Curvature Control

The original control architecture regulates finger curvature directly rather
than using pneumatic pressure as the primary controlled variable.

The actuator-sensor dynamics were approximated using first-order models:

\[
G(s)=\frac{K}{\tau s+1}
\]

and a PI controller was implemented in ROS 2 using the incremental discrete
form

\[
u[k]=u[k-1]+q_0e[k]+q_1e[k-1].
\]

The control output is mapped to the PWM duty cycle commanding the pneumatic
selector valve.

For the reported POF-based experiments, the implemented controller used:

```text
Kp = 15.58
Ki = 6.34
```

The controller was evaluated over normalized finger-curvature references
between 20 % and 80 %.

---

## Software Requirements

The current workspace is developed for:

```text
Ubuntu
ROS 2 Jazzy
Python 3
colcon
```

Additional hardware-specific dependencies are required by individual
packages.

### Hyperion SI255 dependency

The `hyperion_ros2_driver` requires the proprietary Micron Optics/LUNA
Hyperion C++ SDK.

The SDK is **not distributed in this repository**.

See the package documentation for the required SDK configuration.

---

## Build

Clone the repository into a ROS 2 workspace:

```bash
git clone https://github.com/sebachoparra/exohand-ros2-ws.git
cd exohand-ros2-ws
```

Source ROS 2:

```bash
source /opt/ros/jazzy/setup.bash
```

Install the required dependencies for the packages being used and build:

```bash
colcon build
```

Then source the workspace:

```bash
source install/setup.bash
```

---

## Quick Start

### Pneumatic system

```bash
ros2 launch pneumatic_system multi_nodes_launch.py
```

### Dual IMU acquisition

```bash
ros2 launch imu bno055_dual.launch.py
```

### POF signal processing

```bash
ros2 launch exohand_signal_proc exohand_filter_multi.launch.py
```

### PI controller

```bash
ros2 run pi_controller pi_controller_node
```

A complete command reference, including parameters and experimental
acquisition procedures, is available in:

[`COMMANDS.md`](COMMANDS.md)

---

## Experimental Validation

The POF-based control architecture was experimentally evaluated using the
middle finger as the closed-loop feedback reference while applying the same
pneumatic command to the remaining fingers.

Experiments used step references between 20 % and 80 % normalized curvature.

Reported closed-loop performance:

| Metric | Result |
|---|---:|
| IAE | 2.13 ± 0.58 |
| Rise time | 12.44 ± 3.42 s |
| Control total variation | 557.63 ± 135.00 |

The experiments showed stable and repeatable curvature regulation suitable
for low-frequency assistive and rehabilitation-oriented movements.

---

## Demo

A demonstration of the experimental platform is available here:

https://www.youtube.com/watch?v=IzqCy_9qLhE

---

## Related Publication

The POF-based curvature-control implementation is described in:

**J. S. Parra-Perdomo, J. C. Maldonado-Mejía, C. J. Munaro,
C. A. Cifuentes, and C. A. R. Díaz,  
“POF-Based Curvature Closed-Loop PI Control for a Pneumatic Soft Hand
Exoskeleton.”**

The publication describes the POF sensing system, pneumatic hardware,
system identification procedure, PI control formulation, and experimental
closed-loop validation.

---

## Documentation

Detailed ROS 2 command reference:

- [`COMMANDS.md`](COMMANDS.md)

Source packages:

- [`src/`](src/)

Experimental IMU/PWM acquisition:

- [`imu_pwm_acquisition/`](imu_pwm_acquisition/)

Legacy development:

- [`legacy_prototypes/`](legacy_prototypes/)

---

## Project Status

This repository contains both the validated POF-based control architecture
and ongoing development toward additional sensing and control approaches.

The software should therefore be considered a **research platform** rather
than a production-ready rehabilitation device.

---

## Authors

Developed as part of research on sensing and control of soft robotic hand
exoskeletons at the Federal University of Espírito Santo (UFES), with
collaboration from the Bristol Robotics Laboratory, University of the West
of England.

---

## Acknowledgments

The research associated with the POF-based control platform received support
from FAPES, CNPq, CAPES, and IEEE RAS SPARX.
