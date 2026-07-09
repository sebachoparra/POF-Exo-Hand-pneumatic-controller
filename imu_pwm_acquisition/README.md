# ICRA2026 — Protocolo de Adquisición de Datos IMU + PWM

Directorio base: `~/ICRA2026/NEW_TEST/`

---

## Estructura de carpetas

```
NEW_TEST/
├── bags/
│   ├── raw/          # Bags de trials reales
│   └── test/         # Bags de prueba (descartar)
├── data/
│   ├── raw/          # CSV extraídos directamente de los bags
│   └── processed/    # CSV post-procesados (filtros, normalizados, etc.)
├── figures/
│   └── imu_pwm_analysis/
├── metadata/
│   └── trials_log.csv
└── scripts/
    ├── setup_data_folders.sh
    ├── check_imu_pwm_topics.sh
    ├── record_imu_pwm_trial.sh
    ├── extract_imu_pwm_rosbag.py
    └── commands_data_acquisition.sh
```

---

## Hardware y software

| Elemento | Detalle |
|---|---|
| IMU | 2× BNO055 en I2C bus 1 (0x28 = ADR a GND, 0x29 = ADR a 3.3V) |
| Válvula | Señal PWM publicada en `/valve_dc` (`std_msgs/Int32`) |
| ROS 2 | Jazzy |
| Bag format | MCAP |
| Frecuencia IMU | 35 Hz |

---

## Pasos: sesión de adquisición

### 1. Setup inicial (una sola vez)

```bash
cd ~/ICRA2026/NEW_TEST
bash scripts/setup_data_folders.sh
```

### 2. Calibrar los sensores (si es necesario)

Detén cualquier nodo IMU activo, luego:

```bash
source ~/ros2_ws/install/setup.bash
ros2 run imu bno055_calibration_tool
```

Sigue las instrucciones en pantalla:
1. Deja quieto ~5 s → GYR=3
2. Orienta en 6 posiciones distintas → ACC=3
3. Mueve en figura de 8 alejado de metales → MAG=3

Presiona **ENTER** para guardar. Los archivos van a:
- `~/.ros/bno055_calibration/bno055_0x28_calibration.json`
- `~/.ros/bno055_calibration/bno055_0x29_calibration.json`

### 3. Lanzar nodos (terminal 1 y 2)

**Terminal 1 — IMUs:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 launch imu bno055_dual.launch.py load_calibration:=true
```

**Terminal 2 — Válvulas** (ajusta el package según tu sistema):
```bash
source ~/ros2_ws/install/setup.bash
ros2 run <package> <valve_node>
```

### 4. Verificar topics

```bash
bash scripts/check_imu_pwm_topics.sh
```

Frecuencias esperadas: IMU ~35 Hz, válvula según diseño experimental.

### 5. Grabar un trial

```bash
bash scripts/record_imu_pwm_trial.sh --trial T1 --duration 30
```

El bag queda en `bags/raw/T1_YYYYMMDD_HHMMSS/`.

Para un test rápido de verificación:
```bash
bash scripts/record_imu_pwm_trial.sh   # va a bags/test/
```

### 6. Extraer datos a CSV

```bash
source /opt/ros/jazzy/setup.bash
python3 scripts/extract_imu_pwm_rosbag.py \
    --bag bags/raw/T1_20260615_120000 \
    --output data/raw
```

El CSV resultante: `data/raw/T1_20260615_120000_imu_pwm.csv`

Para procesar todos los bags en lote:
```bash
python3 scripts/extract_imu_pwm_rosbag.py --bag bags/raw/* --output data/raw
```

### 7. Registrar el trial

Abre `metadata/trials_log.csv` y añade una fila:

```
trial_id, date, bag_name, duration_s, operation_mode, load_calibration, subject, condition, notes, csv_extracted
```

---

## Formato del CSV extraído

Archivo: `data/raw/<bag_name>_imu_pwm.csv`

El timestamp de referencia es el de cada mensaje `/valve_dc`. Los valores de IMU se interpolan al mensaje de válvula más cercano (descartado si >50 ms de diferencia).

| Columna | Descripción |
|---|---|
| `timestamp_ns` | Timestamp ROS 2 en nanosegundos |
| `imu1_roll/pitch/yaw` | Euler IMU1 en grados (convención XYZ) |
| `imu2_roll/pitch/yaw` | Euler IMU2 en grados |
| `rel_roll/pitch/yaw` | Euler relativo IMU1→IMU2 en grados |
| `rel_theta` | Distancia angular geodésica en grados |
| `valve_dc` | Señal de válvula (Int32) |
| `imu1/2_lin_x/y/z` | Aceleración lineal m/s² |
| `imu1/2_ang_x/y/z` | Velocidad angular rad/s |

La orientación relativa se calcula como:
```
q_rel = q1.inv() * q2
```

---

## Notas

- **SYS** oscila 0–2 en entornos con interferencia magnética: es normal. GYR=3, ACC=3, MAG=3 son los indicadores críticos para calidad de datos.
- En modo `imu` (giroscopio + acelerómetro), el yaw puede derivar. Usar `ndof` con calibración para yaw absoluto.
- Los bags de `bags/test/` son temporales y no deben incluirse en el análisis final.
