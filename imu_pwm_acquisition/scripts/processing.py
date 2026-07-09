import argparse
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from std_msgs.msg import String
import rosbag2_py
import pandas as pd
import matplotlib.pyplot as plt

# Lista para almacenar los diccionarios de cada fila
data_list = []
data_list_2 = []
data_list_3 = []
data_list_4 = []

def read_messages(input_bag: str):
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=input_bag, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )

    topic_types = reader.get_all_topics_and_types()

    def typename(topic_name):
        for topic_type in topic_types:
            if topic_type.name == topic_name:
                return topic_type.type
        raise ValueError(f"topic {topic_name} not in bag")

    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        msg_type = get_message(typename(topic))
        msg = deserialize_message(data, msg_type)
        yield topic, msg, timestamp
    del reader

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", help = "input bag path (folder or filepath) to read from"
    )

    args = parser.parse_args()
    
    for topic, msg, timestamp in read_messages(args.input):
        #print(type(topic), type(timestamp), type(msg.data))

        if topic == "/exohand/adc_data":
            timestamp_val = timestamp
            thumb_pof = msg.data[0]
            index_pof = msg.data[1]
            middle_pof = msg.data[2]
            ring_pof = msg.data[3]
            little_pof = msg.data[4]
            thumb_press = msg.data[5]
            index_press = msg.data[6]
            middle_press = msg.data[7]
            ring_press = msg.data[8]
            little_press = msg.data[9]

            row_dict = {
            'timestamp': timestamp_val,
            'thumb_pof': thumb_pof,
            'index_pof': index_pof,
            'middle_pof': middle_pof,
            'ring_pof': ring_pof,
            'little_pof': little_pof,
            'thumb_press': thumb_press,
            'index_press': index_press,
            'middle_press': middle_press,
            'ring_press': ring_press,
            'little_press': little_press
            }

            data_list.append(row_dict)

        elif topic == "/exohand/pof_filtered_array":
            timestamp_val = timestamp
            thumb_pof = msg.data[0]
            index_pof = msg.data[1]
            middle_pof = msg.data[2]
            ring_pof = msg.data[3]
            little_pof = msg.data[4]

            row_dict = {
            'timestamp': timestamp_val,
            'thumb_pof': thumb_pof,
            'index_pof': index_pof,
            'middle_pof': middle_pof,
            'ring_pof': ring_pof,
            'little_pof': little_pof
            }

            data_list_2.append(row_dict)

        elif topic == "/exohand/pression_filtered_array":
            timestamp_val = timestamp
            thumb_press = msg.data[0]
            index_press = msg.data[1]
            middle_press = msg.data[2]
            ring_press = msg.data[3]
            little_press = msg.data[4]

            row_dict = {
            'timestamp': timestamp_val,
            'thumb_press': thumb_press,
            'index_press': index_press,
            'middle_press': middle_press,
            'ring_press': ring_press,
            'little_press': little_press
            }

         #   data_list_3.append(row_dict)                

        elif topic == "/valve_dc":
            timestamp_val = timestamp
            duty_cycle = msg.data

            row_dict = {
            'timestamp': timestamp_val,
            'duty_cycle': duty_cycle,
            }

            data_list_4.append(row_dict)             

    df = pd.DataFrame(data_list)
    df2 = pd.DataFrame(data_list_2)
    df3 = pd.DataFrame(data_list_3)
    df4 = pd.DataFrame(data_list_4)

    df['timestamp_date'] = pd.to_datetime(df['timestamp'], unit='ns')
    df.to_csv('30s_30Hz_valve_25_Bomb_T1_1.csv', index=False)

    df2['timestamp_date'] = pd.to_datetime(df2['timestamp'], unit='ns')
    df2.to_csv('30s_30Hz_valve_25_Bomb_T1_2.csv', index=False)

    df3['timestamp_date'] = pd.to_datetime(df3['timestamp'], unit='ns')
    df3.to_csv('30s_30Hz_valve_25_Bomb_T1_3.csv', index=False)

    df4['timestamp_date'] = pd.to_datetime(df4['timestamp'], unit='ns')
    df4.to_csv('30s_30Hz_valve_25_Bomb_T1_4.csv', index=False)

if __name__ == "__main__":
    main()

#ejecucion del programa python3 processing.py "/home/juan/Documents/Doctorado/POFs_dedos/rosbag2_2025_08_02-18_01_09"