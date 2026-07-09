# exohand-ros2-ws

ROS2 packages for the Exohand project, including the `hyperion_ros2_driver`
node for the Micron Optics/LUNA Hyperion SI255 optical interrogator.

## Third-party SDK dependency (not included)

`hyperion_ros2_driver` links against the Micron Optics Hyperion C++ API
(`hLibrary.cpp` / `hCommLibrary.cpp` and their headers). That SDK is
**Copyright Micron Optics, Inc., all rights reserved**, and is **not
included in this repository** to avoid redistributing vendor-proprietary
code.

To build `hyperion_ros2_driver`, obtain the SDK directly from Micron
Optics/LUNA (or from your instrument's accompanying media) and place it at:

```
../scripts/interrogator_si255/si255_Hyperion_CPP_hLibrary-0.9.5.1/
```

relative to this repository's root (i.e. a sibling of the directory this
repo is cloned into), matching the path referenced in
`hyperion_ros2_driver/CMakeLists.txt`. Adjust `HYPERION_SDK_DIR` in that
file if you place it elsewhere.

## Building

```bash
cd <ros2_ws>
colcon build --packages-select hyperion_ros2_driver
source install/setup.bash
```

## Running

```bash
ros2 run hyperion_ros2_driver hyperion_driver_node --ros-args \
  -p interrogator_ip:=10.0.0.55 \
  -p publish_rate_hz:=100.0 \
  -p stream_divider:=1
```

Published topic: `hyperion/peaks` (`hyperion_ros2_driver/msg/HyperionPeaks`),
using `SensorDataQoS` (best-effort). To echo it:

```bash
ros2 topic echo /hyperion/peaks --qos-reliability best_effort --qos-durability volatile
```

## Packages in this workspace

- `hyperion_ros2_driver` — Hyperion SI255 peak-streaming ROS2 driver.
- `MQTT_bridge`, `adc_node`, `exohand_signal_proc`, `huskylens`, `imu`,
  `pi_controller`, `pneumatic_system`, `py_pubsub_test`, `valve_control`,
  `web_interface` — other project packages.

## Excluded from this repository

- `examples/` — excluded by request.
- `build/`, `install/`, `log/` — colcon build artifacts.
- `.vscode/` — editor-local config (previously contained a plaintext
  credential in `sftp.json`).
- The Micron Optics Hyperion SDK (see above).
