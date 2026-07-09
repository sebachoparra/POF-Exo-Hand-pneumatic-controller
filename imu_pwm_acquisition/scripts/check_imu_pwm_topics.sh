#!/usr/bin/env bash
# check_imu_pwm_topics.sh
# Verifica que los topics de IMU y válvula están activos y mide su frecuencia.

TOPICS=(
    "/exohand/sensor/imu1_data"
    "/exohand/sensor/imu2_data"
    "/valve_dc"
)

echo ""
echo "======================================="
echo " Verificación de topics ROS 2"
echo "======================================="
echo ""

# Esperar a que haya algún topic publicado
echo "Esperando publicadores activos..."
sleep 2

ACTIVE_TOPICS=$(ros2 topic list 2>/dev/null)
all_ok=true

for topic in "${TOPICS[@]}"; do
    if echo "$ACTIVE_TOPICS" | grep -q "^${topic}$"; then
        echo "  [OK]  $topic"
    else
        echo "  [FALTA]  $topic"
        all_ok=false
    fi
done

echo ""

if [ "$all_ok" = false ]; then
    echo "Algunos topics no están activos. Asegúrate de:"
    echo "  1. ros2 launch imu bno055_dual.launch.py"
    echo "  2. El nodo de válvulas esté corriendo"
    echo ""
    exit 1
fi

echo "Midiendo frecuencia (3 segundos por topic)..."
echo ""

for topic in "${TOPICS[@]}"; do
    printf "  %-45s  " "$topic"
    # Captura la línea de frecuencia de hz
    hz_out=$(timeout 4 ros2 topic hz "$topic" --window 50 2>/dev/null | grep "^average rate:" | head -1)
    if [ -n "$hz_out" ]; then
        echo "$hz_out"
    else
        echo "sin datos"
    fi
done

echo ""
echo "Tipos de mensaje:"
for topic in "${TOPICS[@]}"; do
    type_out=$(ros2 topic type "$topic" 2>/dev/null)
    printf "  %-45s  %s\n" "$topic" "$type_out"
done

echo ""
echo "Listo."
