import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import paho.mqtt.client as mqtt
from rcl_interfaces.msg import ParameterDescriptor
# Import the tools needed to build a custom QoS profile
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

class MQTTBridgeNode(Node):
    """
    Subscribes to BOTH raw and filtered data and forwards each value
    to a separate topic on an MQTT broker.
    """
    def __init__(self):
        super().__init__('mqtt_bridge_node')

        # --- Parameters ---
        self.declare_parameter("mqtt_broker_address", "127.0.0.1")
        self.declare_parameter("mqtt_port", 1883)
        self.declare_parameter("finger_names", ["thumb", "index", "middle", "ring", "little"])
        # NEW: Added pof_indices to know which raw data to pick
        self.declare_parameter("pof_indices", [0, 1, 2, 3, 4])

        # --- Get Parameter Values ---
        broker_address = self.get_parameter("mqtt_broker_address").value
        port = self.get_parameter("mqtt_port").value
        self.finger_names = self.get_parameter("finger_names").value
        self.pof_indices = self.get_parameter("pof_indices").value
        
        # --- MQTT Client Setup ---
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.connect(broker_address, port, 60)
        self.mqtt_client.loop_start()

        # --- ROS2 Subscribers ---
        # Subscriber 1: Listens to the FILTERED data array
        self.filtered_sub = self.create_subscription(
            Float32MultiArray,
            '/exohand/pof_filtered_array',
            self.filtered_callback,
            10
        )

        # Subscriber 3: Listens to the PRESSION FILTERED data array
        self.pression_filtered_sub = self.create_subscription(
            Float32MultiArray,
            '/exohand/pression_filtered_array',
            self.pression_filtered_callback,
            10
        )

        # Subscriber 2: Listens to the RAW data array
        # This requires the RELIABLE QoS profile we discovered earlier
        qos_profile_reliable = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE
        )
        self.raw_sub = self.create_subscription(
            Float32MultiArray,
            '/exohand/adc_data',
            self.raw_callback,
            qos_profile=qos_profile_reliable
        )

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.get_logger().info(f"Successfully connected to MQTT Broker.")
        else:
            self.get_logger().error(f"Failed to connect to MQTT Broker, return code {rc}")

    def filtered_callback(self, msg: Float32MultiArray):
        """Callback for FILTERED data."""
        data = msg.data
        if len(data) != len(self.finger_names):
            return # Skip if data is malformed

        for i, finger_name in enumerate(self.finger_names):
            mqtt_topic = f"exohand/pof/{finger_name}/filtered"
            self.mqtt_client.publish(mqtt_topic, payload=str(data[i]))
        
        #self.get_logger().info("Forwarded FILTERED data to MQTT.", throttle_duration_sec=2)

    def pression_filtered_callback(self, msg: Float32MultiArray):
        """Callback for PRESSION FILTERED data."""
        data = msg.data
        if len(data) != len(self.finger_names):
            return  # Skip if data is malformed

        for i, finger_name in enumerate(self.finger_names):
            mqtt_topic = f"exohand/pression/{finger_name}/filtered"
            self.mqtt_client.publish(mqtt_topic, payload=str(data[i]))

    def raw_callback(self, msg: Float32MultiArray):
        """Callback for RAW data: Handles both PoF and Pression."""
        data = msg.data

        if len(data) < 10:
            return  # Ensure the array has all 10 expected values

        # Extract raw PoF and Pression values
        raw_pof_values = data[:5]
        raw_pression_values = data[5:10]

        # Publish PoF values
        for i, finger_name in enumerate(self.finger_names):
            mqtt_topic = f"exohand/pof/{finger_name}"
            self.mqtt_client.publish(mqtt_topic, payload=str(raw_pof_values[i]))

        # Publish Pression values
        for i, finger_name in enumerate(self.finger_names):
            mqtt_topic = f"exohand/pression/{finger_name}"
            self.mqtt_client.publish(mqtt_topic, payload=str(raw_pression_values[i]))


    def destroy_node(self):
        self.get_logger().info("Disconnecting from MQTT broker.")
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = MQTTBridgeNode()
        print("MQTT Bridge node is running... (Press Ctrl+C to stop)")
        rclpy.spin(node)
    except ConnectionRefusedError:
        if node:
            node.get_logger().error("MQTT connection refused.")
        else:
            print("MQTT connection refused.")
    except KeyboardInterrupt:
        print("Node shutting down.")
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()