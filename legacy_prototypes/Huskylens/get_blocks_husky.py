import smbus
import time

I2C_ADDR = 0x32
bus = smbus.SMBus(1)

# Comando para solicitar los blocks  
cmd = [0x55, 0xAA, 0x11, 0x00, 0x21, 0x31] 

while True:
    # Enviar comando
    bus.write_i2c_block_data(I2C_ADDR, cmd[0], cmd[1:])

    time.sleep(0.1)

    # Leer respuesta (máximo 16 bytes, ajusta si es necesario)
    data = bus.read_i2c_block_data(I2C_ADDR, 0, 16)
    number_of_blocks = data[5] + data[6]
    number_of_ID_learned = data[7] + data[8]
    frame_number = data[9] + data[10] # Revisar
    is_block = True

    for i in range(number_of_blocks):
        data_blocks = []
        for i in range(5):
            data_blocks.append(bus.read_byte(I2C_ADDR))
        for i in range(int(data_blocks[3])+1):
            data_blocks.append(bus.read_byte(I2C_ADDR))

        if data_blocks[4] == 42:
            is_block = True
        else:
            is_block = False

        x = data_blocks[5] + data_blocks[6]
        y = data_blocks[7] + data_blocks[8]
        width = data_blocks[9] + data_blocks[10]
        height = data_blocks[11] + data_blocks[12]
        ID = data_blocks[13] + data_blocks[14]

        print(f"ID: {ID}, X: {x}, Y: {y}, width: {width}, height: {height}")
    print("\n")

