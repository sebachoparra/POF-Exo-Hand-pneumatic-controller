#!/usr/bin/env bash
# commands_data_acquisition.sh
# Referencia rápida de comandos para adquisición de datos ICRA2026.
# Este archivo es SÓLO documentación — no lo ejecutes directamente.
# Copia y pega los bloques que necesites.

cat << 'EOF'
================================================================================
 ICRA2026 — REFERENCIA DE COMANDOS  (~/ICRA2026/NEW_TEST/)
================================================================================

--- 0. SETUP (una sola vez) ---

cd ~/ICRA2026/NEW_TEST
bash scripts/setup_data_folders.sh


--- 1. INICIAR NODOS ---

# Terminal 1: nodos IMU (modo IMU, sin calibración guardada)
source ~/ros2_ws/install/setup.bash
ros2 launch imu bno055_dual.launch.py

# Con calibración guardada (necesita archivos JSON en ~/.ros/bno055_calibration/):
ros2 launch imu bno055_dual.launch.py load_calibration:=true

# Modo NDOF (fusión completa con magnetómetro):
ros2 launch imu bno055_dual.launch.py operation_mode:=ndof load_calibration:=true

# Terminal 2: nodo de válvulas (ajusta según tu package)
source ~/ros2_ws/install/setup.bash
ros2 run <package> <valve_node>


--- 2. VERIFICAR TOPICS ---

bash scripts/check_imu_pwm_topics.sh

# Manual:
ros2 topic hz /exohand/sensor/imu1_data
ros2 topic hz /exohand/sensor/imu2_data
ros2 topic hz /valve_dc


--- 3. CALIBRACIÓN BNO055 ---

# Detén los nodos IMU primero, luego:
ros2 run imu bno055_calibration_tool
# Sigue las instrucciones en pantalla. ENTER para guardar.

# Los archivos quedan en:
#   ~/.ros/bno055_calibration/bno055_0x28_calibration.json
#   ~/.ros/bno055_calibration/bno055_0x29_calibration.json


--- 4. GRABAR BAGS ---

# Test rápido (30s, en bags/test/):
bash scripts/record_imu_pwm_trial.sh

# Trial nombrado (bags/raw/):
bash scripts/record_imu_pwm_trial.sh --trial T1

# Trial con duración personalizada:
bash scripts/record_imu_pwm_trial.sh --trial T1 --duration 60

# Sin IMU (sólo válvula):
bash scripts/record_imu_pwm_trial.sh --trial T1 --no-imu

# Manual con ros2 bag:
ros2 bag record \
    --output bags/raw/T1_$(date +%Y%m%d_%H%M%S) \
    --storage mcap \
    --duration 30 \
    /exohand/sensor/imu1_data \
    /exohand/sensor/imu2_data \
    /valve_dc


--- 5. EXTRAER DATOS ---

source /opt/ros/jazzy/setup.bash

# Un bag:
python3 scripts/extract_imu_pwm_rosbag.py \
    --bag bags/raw/T1_20250601_120000 \
    --output data/raw

# Todos los bags raw (batch):
python3 scripts/extract_imu_pwm_rosbag.py \
    --bag bags/raw/* \
    --output data/raw

# Listar topics de un bag:
python3 scripts/extract_imu_pwm_rosbag.py --list-topics --bag bags/test/test_20250601_120000

# También con herramienta nativa:
ros2 bag info bags/raw/T1_20250601_120000


--- 6. REGISTRO DE TRIALS ---

nano metadata/trials_log.csv
# Añade una fila por cada trial grabado.


================================================================================
EOF
