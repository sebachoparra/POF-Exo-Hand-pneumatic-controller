from smbus2 import SMBus, i2c_msg
import time

HUSKYLENS_I2C_ADDR = 0x32  # Dirección 7-bit
I2C_BUS = 1  # Bus I2C de la Raspberry Pi

def calcular_checksum(data):
    return sum(data) & 0xFF

def enviar_request_blocks(bus):
    # Comando: Header + Cmd + Length (0x00 0x00) + Checksum
    cmd = [0x55, 0xAA, 0x11, 0x20, 0x00, 0x00]
    checksum = calcular_checksum(cmd)
    cmd.append(checksum)
    write = i2c_msg.write(HUSKYLENS_I2C_ADDR, cmd)
    bus.i2c_rdwr(write)
    print("Comando enviado:", [hex(b) for b in cmd])

def leer_respuesta(bus, n=32):
    try:
        read = i2c_msg.read(HUSKYLENS_I2C_ADDR, n)
        bus.i2c_rdwr(read)
        data = list(read)
        print("Datos recibidos:", [hex(b) for b in data])
    except Exception as e:
        print("Error al leer:", e)

def main():
    with SMBus(I2C_BUS) as bus:
        while True:
            enviar_request_blocks(bus)
            time.sleep(0.1)  # Esperar a que HuskyLens procese
            leer_respuesta(bus, 32)
            time.sleep(1)

if __name__ == "__main__":
    main()
