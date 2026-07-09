#!/usr/bin/env python3

from flask import Flask, render_template, request, jsonify
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class WebInterfaceNode(Node):
    @property
    def app(self) -> Flask:
        return self._app
  
    @app.setter
    def app(self, app: Flask):
        self._app = app

    def __init__(self, name) -> None:
        super().__init__(name)
        self.app = Flask(__name__)

        self.publisher_ = self.create_publisher(
            String,
            '/exoskeleton/command',
            10)
        self.register_endpoints()
        self.get_logger().info(f'Node {name} initialized.')        

    def publish_message(self, content):
        msg = String()
        msg.data = content
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: "{msg.data}"')        

    def register_endpoints(self):
        self.app.add_url_rule(rule='/', endpoint='Interface', view_func=self.interface, methods=['GET']) 
        self.app.add_url_rule(rule='/thumb_close', endpoint='Thumb_close', view_func=self.thumb_close, methods=['POST'])
        self.app.add_url_rule(rule='/index_close', endpoint='Index_close', view_func=self.index_close, methods=['POST'])
        self.app.add_url_rule(rule='/middle_close', endpoint='Middle_close', view_func=self.middle_close, methods=['POST'])
        self.app.add_url_rule(rule='/ring_close', endpoint='Ring_close', view_func=self.ring_close, methods=['POST'])
        self.app.add_url_rule(rule='/pinky_close', endpoint='Pinky_close', view_func=self.pinky_close, methods=['POST'])
        self.app.add_url_rule(rule='/power_grip_close', endpoint='Power_grip_close', view_func=self.power_grip_close, methods=['POST'])
        self.app.add_url_rule(rule='/pulp_pinch_close', endpoint='Pulp_pinch_close', view_func=self.pulp_pinch_close, methods=['POST'])
        self.app.add_url_rule(rule='/tripod_pinch_close', endpoint='Tripod_pinch_close', view_func=self.tripod_pinch_close, methods=['POST']) 
        self.app.add_url_rule(rule='/close_four_finger', endpoint='Close_four_finger', view_func=self.close_four_finger, methods=['POST'])

        self.app.add_url_rule(rule='/thumb_open', endpoint='Thumb_open', view_func=self.thumb_open , methods=['POST'])
        self.app.add_url_rule(rule='/index_open', endpoint='Index_open', view_func=self.index_open , methods=['POST'])
        self.app.add_url_rule(rule='/middle_open', endpoint='Middle_open', view_func=self.middle_open , methods=['POST'])
        self.app.add_url_rule(rule='/ring_open', endpoint='Ring_open', view_func=self.ring_open , methods=['POST'])
        self.app.add_url_rule(rule='/pinky_open', endpoint='Pinky_open', view_func=self.pinky_open , methods=['POST'])
        self.app.add_url_rule(rule='/power_grip_open', endpoint='Power_grip_open', view_func=self.power_grip_open , methods=['POST'])
        self.app.add_url_rule(rule='/pulp_pinch_open', endpoint='Pulp_pinch_open', view_func=self.pulp_pinch_open , methods=['POST'])
        self.app.add_url_rule(rule='/tripod_pinch_open', endpoint='Tripod_pinch_open', view_func=self.tripod_pinch_open , methods=['POST']) 
        self.app.add_url_rule(rule='/open_four_finger', endpoint='Open_four_finger', view_func=self.open_four_finger, methods=['POST'])
        self.app.add_url_rule(rule='/open', endpoint='Open', view_func=self.open, methods=['POST'])  
        self.app.add_url_rule(rule='/open2', endpoint='Open2', view_func=self.open2, methods=['POST'])      

    def interface(self):
        return render_template('Interface.html')
    
    def thumb_close(self):
        self.publish_message('thumb_close')
        print("Command 'thumb_close' sent")
        return jsonify({'status': 'success', 'command': 'thumb_close'})

    def index_close(self):
        self.publish_message('index_close')
        print("Command 'index_close' sent")
        return jsonify({'status': 'success', 'command': 'index_close'})
    
    def middle_close(self):
        self.publish_message('middle_close')
        print("Command 'middle_close' sent")
        return jsonify({'status': 'success', 'command': 'middle_close'})
    
    def ring_close(self):
        self.publish_message('ring_close')
        print("Command 'ring_close' sent")
        return jsonify({'status': 'success', 'command': 'ring_close'})
    
    def pinky_close(self):
        self.publish_message('pinky_close')
        print("Command 'pinky_close' sent")
        return jsonify({'status': 'success', 'command': 'pinky_close'})
    
    def power_grip_close(self):
        self.publish_message('power_grip_close')
        print("Command 'power_grip_close' sent")
        return jsonify({'status': 'success', 'command': 'power_grip_close'})
    
    def pulp_pinch_close(self):
        self.publish_message('pulp_pinch_close')
        print("Command 'pulp_pinch_close' sent")
        return jsonify({'status': 'success', 'command': 'pulp_pinch_close'})
    
    def tripod_pinch_close(self):
        self.publish_message('tripod_pinch_close')
        print("Command 'tripod_pinch_close' sent")
        return jsonify({'status': 'success', 'command': 'tripod_pinch_close'})
    
    def close_four_finger(self):
        self.publish_message('close_four_finger')
        print("Command 'close_four_finger' sent")
        return jsonify({'status': 'success', 'command': 'close_four_finger'})

    def thumb_open (self):
        self.publish_message('thumb_open')
        print("Command 'thumb_open' sent")
        return jsonify({'status': 'success', 'command': 'thumb_open'})

    def index_open (self):
        self.publish_message('index_open')
        print("Command 'index_open' sent")
        return jsonify({'status': 'success', 'command': 'index_open'})
    
    def middle_open (self):
        self.publish_message('middle_open')
        print("Command 'middle_open' sent")
        return jsonify({'status': 'success', 'command': 'middle_open'})
    
    def ring_open (self):
        self.publish_message('ring_open')
        print("Command 'ring_open' sent")
        return jsonify({'status': 'success', 'command': 'ring_open'})
    
    def pinky_open (self):
        self.publish_message('pinky_open')
        print("Command 'pinky_open' sent")
        return jsonify({'status': 'success', 'command': 'pinky_open'})
    
    def power_grip_open (self):
        self.publish_message('power_grip_open')
        print("Command 'power_grip_open' sent")
        return jsonify({'status': 'success', 'command': 'power_grip_open'})
    
    def pulp_pinch_open (self):
        self.publish_message('pulp_pinch_open')
        print("Command 'pulp_pinch_open' sent")
        return jsonify({'status': 'success', 'command': 'pulp_pinch_open'})
    
    def tripod_pinch_open (self):
        self.publish_message('tripod_pinch_open')
        print("Command 'tripod_pinch_open' sent")
        return jsonify({'status': 'success', 'command': 'tripod_pinch_open'})
    
    def open_four_finger(self):
        self.publish_message('open_four_finger')
        print("Command 'open_four_finger' sent")
        return jsonify({'status': 'success', 'command': 'open_four_finger'})
    
    def open(self):
        self.publish_message('free_air')
        print("Command 'free_air' sent")
        return jsonify({'status': 'success', 'command': 'free_air'})
    
    def open2(self):
        self.publish_message('free_air2')
        print("Command 'free_air2' sent")
        return jsonify({'status': 'success', 'command': 'free_air2'})

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)

def main(args=None):
    rclpy.init(args=args)
    name = 'web_interface'
    node = WebInterfaceNode(name)
    node.run(host='0.0.0.0', port=5000 ,debug=True)

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
