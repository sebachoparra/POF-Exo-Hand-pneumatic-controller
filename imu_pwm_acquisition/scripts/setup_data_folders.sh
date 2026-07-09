#!/usr/bin/env bash
# setup_data_folders.sh
# Crea la estructura de carpetas del proyecto. No borra nada existente.

set -e
BASE="$(cd "$(dirname "$0")/.." && pwd)"

echo "Proyecto: $BASE"
echo ""

dirs=(
    "bags/raw"
    "bags/test"
    "data/raw"
    "data/processed"
    "figures/imu_pwm_analysis"
    "metadata"
    "scripts"
)

for d in "${dirs[@]}"; do
    if [ ! -d "$BASE/$d" ]; then
        mkdir -p "$BASE/$d"
        echo "  [CREADO]   $d"
    else
        echo "  [OK]       $d"
    fi
done

echo ""
echo "Estructura actual:"
find "$BASE" -maxdepth 2 -type d | sort | sed "s|$BASE/||" | sed 's/^/  /'
