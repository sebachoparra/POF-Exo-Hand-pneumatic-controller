import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

class RealtimeEWMA:
    """A class to apply an EWMA filter to a stream of data."""
    def __init__(self, alpha: float):
        self.alpha = alpha
        self.last_value = None

    def update(self, new_value: float) -> float:
        if self.last_value is None:
            self.last_value = new_value
            return self.last_value
        filtered_value = self.alpha * new_value + (1.0 - self.alpha) * self.last_value
        self.last_value = filtered_value
        return filtered_value

class MinimalFilterNode(Node):
    def __init__(self):
        super().__init__('minimal_filter_node')

        # 1. Define the working QoS Profile
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            durability=DurabilityPolicy.VOLATILE
        )
        
        # 2. Create the subscriber (this is the part that we know works)
        self.sub = self.create_subscription(
            Float32MultiArray,
            '/exohand/adc_data',
            self.listener_callback, # Process data directly in the callback
            qos_profile=qos_profile)
            
        # 3. Create the publisher for the filtered data
        self.pub = self.create_publisher(Float32MultiArray, '/exohand/pression_filtered_array', 10)

        # 4. Create 5 EWMA filter instances (one for each finger)
        self.ewma_filters = [RealtimeEWMA(alpha=0.2) for _ in range(5)]
            
        self.get_logger().info('Minimal filter node started and listening...')

    def listener_callback(self, msg):
        # This function now contains all the logic
        
        # Check if the incoming data array is long enough
        if len(msg.data) < 5:
            self.get_logger().warn("Received data array is too short.", throttle_duration_sec=5)
            return

        # Get the first 5 values, as you specified
        raw_pression_values = msg.data[5:10]
        
        # Apply the EWMA filter to each of the 5 values
        filtered_values = [self.ewma_filters[i].update(raw_pression_values[i]) for i in range(5)]

        # Prepare the output message and publish it
        # FIX: Corrected the typo here
        output_msg = Float32MultiArray()
        output_msg.data = filtered_values
        self.pub.publish(output_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MinimalFilterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()