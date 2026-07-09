from flask import Flask, render_template, request, jsonify
import rclpy
from rclpy.node import Node
from std_msgs.msg import String  # Tipo de mensagem que será publicada

# Inicializa o Flask
app = Flask(__name__)

# Inicializa o ROS 2 (fora do Flask para evitar múltiplas inicializações)
rclpy.init()

# Classe para o nó ROS 2
class ROS2Node(Node):
    def __init__(self):
        super().__init__('flask_ros2_node')
        self.publisher = self.create_publisher(String, 'comandos', 10)  # Cria um publisher no tópico 'comandos'

    def enviar_comando(self, comando):
        msg = String()
        msg.data = comando
        self.publisher.publish(msg)
        self.get_logger().info(f'Comando enviado ao ROS 2: {comando}')


# Inicializa o nó ROS 2
ros2_node = ROS2Node()


@app.route('/')
def index():
    return render_template('Interface.html')


@app.route('/comando', methods=['POST'])
def receber_comando():
    data = request.get_json()
    comando = data.get('comando')
    
    # Enviar o comando para o ROS 2
    ros2_node.enviar_comando(comando)
    
    print(f'Comando recebido: {comando}')
    return jsonify({'status': 'success', 'comando': comando})


if __name__ == '__main__':
    try:
        # Executa o servidor Flask
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        # Fecha o ROS 2 corretamente ao encerrar o Flask
        ros2_node.destroy_node()
        rclpy.shutdown()
