import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class StringPublisher(Node):
    def __init__(self):
        super().__init__('string_publisher')
        self.publisher_ = self.create_publisher(String, '/exoskeleton/command', 10)
        
        # Contador de repeticiones
        self.cycle_count = 0
        self.max_cycles = 5  # Número de veces que se repetirá el proceso

        # Iniciar el primer mensaje a los 20s
        self.timer1 = self.create_timer(20.0, self.first_message)

    def first_message(self):
        """Publica el primer mensaje y programa el siguiente a 15s."""
        self.publish_message("index_close")
        self.timer2 = self.create_timer(20.0, self.second_message)
        self.timer1.cancel()  # Cancelamos este timer para que no vuelva a llamarse

    def second_message(self):
        """Publica el segundo mensaje y programa el siguiente a 5s."""
        self.publish_message("free_air")
        self.timer3 = self.create_timer(20.0, self.third_message)
        self.timer2.cancel()  # Cancelamos este timer para que no vuelva a llamarse

    def third_message(self):
        """Publica el tercer mensaje y programa el siguiente a 5s."""
        self.publish_message("index_open")
        self.timer4 = self.create_timer(15.0, self.fourth_message)
        self.timer3.cancel()  # Cancelamos este timer para que no vuelva a llamarse

    def fourth_message(self):
        """Publica el cuarto mensaje y programa el siguiente a 5s."""
        self.publish_message("free_air2")
        self.timer5 = self.create_timer(5.0, self.fifth_message)
        self.timer4.cancel()  # Cancelamos este timer para que no vuelva a llamarse        

    def fifth_message(self):
        """Publica el quinto mensaje y programa la repetición si es necesario."""
        self.publish_message("free_air")
        self.timer5.cancel()  # Cancelamos este timer para que no vuelva a llamarse

        self.cycle_count += 1
        if self.cycle_count < self.max_cycles:
            # Si no hemos alcanzado el máximo, reiniciamos el ciclo con un nuevo timer
            self.get_logger().info(f'Repitiendo ciclo {self.cycle_count + 1}/{self.max_cycles}')
            self.timer1 = self.create_timer(20.0, self.first_message)
        else:
            self.get_logger().info('Finalizando publicación')
            self.destroy_node()
            rclpy.shutdown()

    def publish_message(self, text):
        """Función auxiliar para publicar el mensaje en el topic."""
        msg = String()
        msg.data = text
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publicado: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    node = StringPublisher()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
