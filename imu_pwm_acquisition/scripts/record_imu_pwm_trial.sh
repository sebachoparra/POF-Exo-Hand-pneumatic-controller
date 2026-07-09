#!/usr/bin/env bash
# record_imu_pwm_trial.sh
# Graba un rosbag con IMU1, IMU2, señal de válvula y peaks de Hyperion.
# Detén la grabación con Ctrl+C cuando quieras.
#
# Uso:
#   bash record_imu_pwm_trial.sh                  # modo test (bags/test/)
#   bash record_imu_pwm_trial.sh --trial T1       # trial nombrado (bags/raw/)
#   bash record_imu_pwm_trial.sh --trial T1 --no-imu
#   bash record_imu_pwm_trial.sh --trial T1 --no-hyperion

set -e

BASE="$(cd "$(dirname "$0")/.." && pwd)"

TRIAL=""
TEST_MODE=true
INCLUDE_IMU=true
INCLUDE_HYPERION=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --trial)
            TRIAL="$2"; TEST_MODE=false; shift 2 ;;
        --no-imu)
            INCLUDE_IMU=false; shift ;;
        --no-hyperion)
            INCLUDE_HYPERION=false; shift ;;
        --test)
            TEST_MODE=true; shift ;;
        -h|--help)
            sed -n '2,12p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        *)
            echo "Argumento desconocido: $1"; exit 1 ;;
    esac
done

# Build topic list
RECORD_TOPICS=("/valve_dc")
if [ "$INCLUDE_IMU" = true ]; then
    RECORD_TOPICS+=("/exohand/sensor/imu1_data" "/exohand/sensor/imu2_data")
fi
if [ "$INCLUDE_HYPERION" = true ]; then
    RECORD_TOPICS+=("/hyperion/peaks")
fi

# Build bag name and output dir
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
if [ "$TEST_MODE" = true ]; then
    OUT_DIR="$BASE/bags/test"
    BAG_NAME="test_${TIMESTAMP}"
else
    OUT_DIR="$BASE/bags/raw"
    BAG_NAME="${TRIAL}_${TIMESTAMP}"
fi

mkdir -p "$OUT_DIR"
BAG_PATH="$OUT_DIR/$BAG_NAME"

echo ""
echo "======================================="
echo " ROS 2 Bag Recording"
echo "======================================="
echo "  Modo:       $([ "$TEST_MODE" = true ] && echo 'TEST' || echo "TRIAL: $TRIAL")"
echo "  Duración:   hasta Ctrl+C"
echo "  Topics:     ${RECORD_TOPICS[*]}"
echo "  Destino:    $BAG_PATH"
echo "======================================="
echo ""
echo "Iniciando en 3 segundos... (Ctrl+C para cancelar)"
sleep 3

ros2 bag record \
    --output "$BAG_PATH" \
    --storage mcap \
    "${RECORD_TOPICS[@]}"

echo ""
echo "Grabación finalizada."
echo "  Bag guardado en: $BAG_PATH"
echo ""
echo "Para extraer datos:"
echo "  python3 scripts/extract_imu_pwm_rosbag.py --bag $BAG_PATH --output data/raw"