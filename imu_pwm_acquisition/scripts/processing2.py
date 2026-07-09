#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import rosbag2_py
import pandas as pd
import os
from datetime import datetime

# ==============================================================
# Diccionario principal con todos los tópicos relevantes
# ==============================================================

data_dict = {
    '/exohand/adc_data': [],
    '/exohand/pof_filtered_array': [],
    '/exohand/pression_filtered_array': [],
    '/valve_dc': [],
    '/exohand/debug_control': []     # ✅ Nuevo tópico agregado
}

# ==============================================================
# Función para leer mensajes del bag MCAP
# ==============================================================

def read_messages(input_bag: str):
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=input_bag, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr",
            output_serialization_format="cdr",
        ),
    )

    topic_types = reader.get_all_topics_and_types()

    def typename(topic_name):
        for topic_type in topic_types:
            if topic_type.name == topic_name:
                return topic_type.type
        raise ValueError(f"Topic {topic_name} not found in bag")

    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        msg_type = get_message(typename(topic))
        msg = deserialize_message(data, msg_type)
        yield topic, msg, timestamp

    del reader

# ==============================================================
# Función para guardar DataFrame en CSV
# ==============================================================

def save_df(df, topic_name, output_prefix):
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp_date'] = pd.to_datetime(df['timestamp'], unit='ns')
        topic_clean = topic_name.strip('/').replace('/', '_')
        filename = f"{output_prefix}_{topic_clean}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Guardado: {filename}")
    else:
        print(f"⚠️ No se encontraron datos para el tópico: {topic_name}")

# ==============================================================
# Programa principal
# ==============================================================

def main():
    parser = argparse.ArgumentParser(description="Procesamiento de rosbag MCAP")
    parser.add_argument("input", help="Ruta al bag (carpeta o archivo)")
    args = parser.parse_args()

    # Prefijo dinámico basado en nombre del bag y fecha actual
    bag_name = os.path.basename(args.input.rstrip('/'))
    timestamp_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_prefix = f"{bag_name}_{timestamp_now}"

    for topic, msg, timestamp in read_messages(args.input):
        row_dict = {'timestamp': timestamp}

        # ==================================================
        # ADC Data (POF + Pressure sin filtrar)
        # ==================================================
        if topic == "/exohand/adc_data":
            row_dict.update({
                'thumb_pof': msg.data[0],
                'index_pof': msg.data[1],
                'middle_pof': msg.data[2],
                'ring_pof': msg.data[3],
                'little_pof': msg.data[4],
                'thumb_press': msg.data[5],
                'index_press': msg.data[6],
                'middle_press': msg.data[7],
                'ring_press': msg.data[8],
                'little_press': msg.data[9]
            })
            data_dict[topic].append(row_dict)

        # ==================================================
        # POF filtrados
        # ==================================================
        elif topic == "/exohand/pof_filtered_array":
            row_dict.update({
                'thumb_pof': msg.data[0],
                'index_pof': msg.data[1],
                'middle_pof': msg.data[2],
                'ring_pof': msg.data[3],
                'little_pof': msg.data[4]
            })
            data_dict[topic].append(row_dict)

        # ==================================================
        # Presión filtrada
        # ==================================================
        elif topic == "/exohand/pression_filtered_array":
            row_dict.update({
                'thumb_press': msg.data[0],
                'index_press': msg.data[1],
                'middle_press': msg.data[2],
                'ring_press': msg.data[3],
                'little_press': msg.data[4]
            })
            data_dict[topic].append(row_dict)

        # ==================================================
        # Duty cycle (PWM)
        # ==================================================
        elif topic == "/valve_dc":
            row_dict.update({
                'duty_cycle': msg.data
            })
            data_dict[topic].append(row_dict)

        # ==================================================
        # Debug control (nuevo)
        # ==================================================
        elif topic == "/exohand/debug_control":
            # ⚠️ Ajusta nombres según tus variables reales
            row_dict.update({
                'reference': msg.data[0],
                'measured': msg.data[1],
                'error': msg.data[2],
                'control_signalPWM': msg.data[3],
                'control_signal': msg.data[4],
            })
            data_dict[topic].append(row_dict)

    # ==================================================
    # Guardar resultados
    # ==================================================
    for topic_name, data_list in data_dict.items():
        df = pd.DataFrame(data_list)
        save_df(df, topic_name, output_prefix)

# ==============================================================
# Ejecución del script
# ==============================================================

if __name__ == "__main__":
    main()




#ejecucion del programa python3 processing2.py "/home/exohand/ICRA2026/NEW_TEST/exohand_step_2025-11-05_1431"