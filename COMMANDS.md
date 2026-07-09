# Comandos ROS2 — referencia rápida

Extraído directamente de `setup.py`/`CMakeLists.txt`/archivos de `launch` de
cada paquete en `src/`. Si se agregan o cambian ejecutables, actualizar este
archivo.

## 1. Preliminares (una sola vez por terminal)

```bash
source /opt/ros/jazzy/setup.bash
source /home/exohand/ros2_ws/install/setup.bash
```

## 2. Nodos con archivo de `launch` (aceptan argumentos)

### Hyperion (interrogador óptico SI255)

```bash
ros2 launch hyperion_ros2_driver hyperion_driver.launch.py \
  interrogator_ip:=10.0.0.55 \
  publish_rate_hz:=100.0 \
  stream_divider:=1 \
  frame_id:=hyperion
```

- `interrogator_ip` (default `10.0.0.55`)
- `publish_rate_hz` (default `100.0`)
- `stream_divider` (default `1`)
- `frame_id` (default `hyperion`)

Todos opcionales, se puede correr sin argumentos y toma los defaults.

### IMU dual (2x BNO055)

```bash
ros2 launch imu bno055_dual.launch.py

# modo NDOF con calibración guardada:
ros2 launch imu bno055_dual.launch.py operation_mode:=ndof load_calibration:=true
```

- `operation_mode` (default `imu`): `imu` (giro+acel, yaw relativo, puede
  derivar) | `ndof_fmc_off` (9DOF sin fast mag cal) | `ndof` (9DOF completo,
  necesita magnetómetro calibrado).
- `load_calibration` (default `false`): `true` para cargar los JSON de
  calibración guardados.

Internamente lanza dos `bno055_imu_node` (direcciones I2C `0x28`/`0x29`),
publicando en `/exohand/sensor/imu1_data` e `/imu2_data`, a 35Hz.

### Calibración de las IMUs

```bash
# (primero detené los nodos bno055_imu_node activos)
ros2 launch imu bno055_calibration.launch.py

# personalizando:
ros2 launch imu bno055_calibration.launch.py bus:=1 auto_save:=10 output_dir:=/ruta/personalizada
```

- `bus` (default `1`): bus I2C.
- `auto_save` (default `10`): segundos de calibración aceptable antes de
  autoguardar.
- `output_dir` (default `~/.ros/bno055_calibration`): dónde quedan los JSON.

### Filtro de presión POF (multi-dedo)

```bash
ros2 launch exohand_signal_proc exohand_filter_multi.launch.py
```

Sin argumentos de launch — toma los parámetros desde
`config/filter_multi_params.yaml` (incluye `pof_indices`, `pof_names`,
`fs_adc`, `rate_hz`, `fc_pof`, `publish_per_finger`, `topic_prefix`). Para
cambiar algo, se edita ese YAML.

### Sistema neumático completo (bombas + 5 válvulas de una vez)

```bash
ros2 launch pneumatic_system multi_nodes_launch.py
```

Sin argumentos — lanza `air_pump_1`, `air_pump_2`, `valve`, `valve1`...`valve5`,
cada uno en su propio namespace (`/air_pump_1/...`, `/valve1/...`, etc.).

## 3. Nodos simples (sin launch, `ros2 run` directo)

```bash
ros2 run MQTT_bridge MQTT_bridge_node
ros2 run adc_node adc
ros2 run huskylens huskylens_node
ros2 run pi_controller pi_controller_node
ros2 run web_interface app
ros2 run py_pubsub_test teste
ros2 run py_pubsub_test teste2
```

**MQTT_bridge** acepta parámetros si el broker no es local:

```bash
ros2 run MQTT_bridge MQTT_bridge_node --ros-args \
  -p mqtt_broker_address:=192.168.x.x \
  -p mqtt_port:=1883
```

(default `mqtt_broker_address=127.0.0.1`, `mqtt_port=1883`, `finger_names` y
`pof_indices` también son parámetros con default razonable).

**Filtro POF individual** (si no querés el launch completo):

```bash
ros2 run exohand_signal_proc pof_pressure_filter_multi
ros2 run exohand_signal_proc pof_ewma_filter_node
ros2 run exohand_signal_proc pof_calibration_node
```

**IMU, ejecutables individuales** (normalmente se usan vía el launch dual,
pero se pueden correr sueltos):

```bash
ros2 run imu bno055_imu_node --ros-args -p i2c_address:=40 -p topic_name:=/exohand/sensor/imu1_data
ros2 run imu imu_node
ros2 run imu imu2_node
ros2 run imu bno055_calibration_tool
```

**Neumático, ejecutables individuales** (por si no querés lanzar los 8
juntos):

```bash
ros2 run pneumatic_system air_pump_1
ros2 run pneumatic_system air_pump_2
ros2 run pneumatic_system valve
ros2 run pneumatic_system valve1
ros2 run pneumatic_system valve2
ros2 run pneumatic_system valve3
ros2 run pneumatic_system valve4
ros2 run pneumatic_system valve5
```

**Control de válvulas (secuenciador):**

```bash
ros2 run valve_control valve_pwm_control
ros2 run valve_control valve_sequencer
```

`valve_sequenceralt` (variante) tiene bastantes parámetros propios:

```bash
ros2 run valve_control valve_sequenceralt --ros-args \
  -p steps:="[100.0, 60.0, 20.0, 0.0, 40.0, 80.0]" \
  -p duration:=5.0 \
  -p repeat:=false \
  -p valve_pwm_hz:=25 \
  -p pump1_dc:=25.0 \
  -p pump2_dc:=100.0
```

(`steps`: % duty cycle por paso; `durations`/`duration`: tiempo por paso;
`repeat`: si repite la secuencia; `tick_hz`, `valve_pwm_hz`, `pump1_pwm_hz`,
`pump2_pwm_hz`, `pump1_dc`, `pump2_dc` con sus defaults ya sensatos).

## 4. Flujo completo de adquisición IMU+PWM

```bash
# Setup inicial (una sola vez)
cd ~/ICRA2026/NEW_TEST
bash scripts/setup_data_folders.sh

# Lanzar IMUs
source ~/ros2_ws/install/setup.bash
ros2 launch imu bno055_dual.launch.py load_calibration:=true

# (otra terminal) Lanzar válvula/bomba según lo que estés probando
ros2 run pneumatic_system valve
# o el sistema completo:
ros2 launch pneumatic_system multi_nodes_launch.py

# Verificar tópicos
bash scripts/check_imu_pwm_topics.sh

# Grabar
bash scripts/record_imu_pwm_trial.sh --trial T1

# Extraer a CSV
source /opt/ros/jazzy/setup.bash
python3 scripts/extract_imu_pwm_rosbag.py --bag bags/raw/T1_YYYYMMDD_HHMMSS --output data/raw

# Anotar trial
nano metadata/trials_log.csv
```

Scripts referidos: ver `imu_pwm_acquisition/scripts/` en este repo (código
copiado desde `~/ICRA2026/NEW_TEST/scripts/`; los datos/bags no se versionan
aquí, quedan solo en la Pi).
