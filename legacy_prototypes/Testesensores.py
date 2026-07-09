#!/usr/bin/python3
# -*- coding: utf-8 -*-

import smbus
import time

# Enderecos I2C dos sensores
L3GD20H_ADDR = 0x6B  # Endereco I2C do giroscopio L3GD20H
LSM303D_ADDR = 0x1D  # Endereco I2C do acelerometro/magnetometro LSM303D

# Registradores do giroscopio (L3GD20H)
GYROSCOPE_X_LSB = 0x28
GYROSCOPE_Y_LSB = 0x2A
GYROSCOPE_Z_LSB = 0x2C
CTRL_REG1 = 0x20  # Control Register 1
CTRL_REG4 = 0x23  # Control Register 4

# Registradores do acelerometro e magnetometro (LSM303D)
ACCEL_X_LSB = 0x28
ACCEL_Y_LSB = 0x2A
ACCEL_Z_LSB = 0x2C
MAG_X_LSB = 0x08
MAG_Y_LSB = 0x0A
MAG_Z_LSB = 0x0C
CTRL1 = 0x20
CTRL2 = 0x21
CTRL5 = 0x24
CTRL6 = 0x25
CTRL7 = 0x26

# Configuracao do barramento I2C
bus = smbus.SMBus(1)

# Funcao para ler um valor de 16 bits (LSB + MSB)
def read_word(address, register):
    low = bus.read_byte_data(address, register)
    high = bus.read_byte_data(address, register + 1)
    return (high << 8) + low

# Ajustar valores para numeros com sinal (inteiros negativos ou positivos)
def adjust_signed(value):
    if value >= 32768:
        value -= 65536
    return value

# Funcao para configurar o giroscopio (L3GD20H)
def configure_gyro():
    # Habilitar o giroscopio no modo normal
    bus.write_byte_data(L3GD20H_ADDR, CTRL_REG1, 0x0F)  # Habilita eixos XYZ
    bus.write_byte_data(L3GD20H_ADDR, CTRL_REG4, 0x00)  # Escala de ±250 dps

# Funcao para configurar o LSM303D (acelerometro e magnetometro)
def configure_lsm303d():
    # Configurar acelerometro
    bus.write_byte_data(LSM303D_ADDR, CTRL1, 0x57)  # Habilitar XYZ e 100Hz (revisar porque en el datasheet dice que 57 son 50 Hz)
    bus.write_byte_data(LSM303D_ADDR, CTRL5, 0x64)  # Atualizacao de 50Hz
    bus.write_byte_data(LSM303D_ADDR, CTRL6, 0x20)  # Escala de ±4 gauss
    bus.write_byte_data(LSM303D_ADDR, CTRL7, 0x00)  # Modo continuo

# Funcao para ler o giroscopio
def read_gyro():
    x = adjust_signed(read_word(L3GD20H_ADDR, GYROSCOPE_X_LSB))
    y = adjust_signed(read_word(L3GD20H_ADDR, GYROSCOPE_Y_LSB))
    z = adjust_signed(read_word(L3GD20H_ADDR, GYROSCOPE_Z_LSB))

    # Conversao para graus por segundo (dps)
    scale = 0.00875  # ±250 dps
    x_dps = x * scale
    y_dps = y * scale
    z_dps = z * scale

    print(f"Giroscopio: X={x_dps:.2f} dps, Y={y_dps:.2f} dps, Z={z_dps:.2f} dps")
    print("")
    return x_dps, y_dps, z_dps

# Funcao para ler o acelerometro
def read_accel():
    x = adjust_signed(read_word(LSM303D_ADDR, ACCEL_X_LSB))
    y = adjust_signed(read_word(LSM303D_ADDR, ACCEL_Y_LSB))
    z = adjust_signed(read_word(LSM303D_ADDR, ACCEL_Z_LSB))

    # Conversao para g (gravidade)
    scale = 0.000061  # ±2g
    x_g = x * scale
    y_g = y * scale
    z_g = z * scale

    print(f"Acelerometro: X={x_g:.3f} g, Y={y_g:.3f} g, Z={z_g:.3f} g")
    print("")	 
    return x_g, y_g, z_g

# Funcao para ler o magnetometro
def read_mag():
    x = adjust_signed(read_word(LSM303D_ADDR, MAG_X_LSB))
    y = adjust_signed(read_word(LSM303D_ADDR, MAG_Y_LSB))
    z = adjust_signed(read_word(LSM303D_ADDR, MAG_Z_LSB))

    # Conversao para gauss (aproximado)
    scale = 0.00014  # ±4 gauss
    x_gauss = x * scale
    y_gauss = y * scale
    z_gauss = z * scale

    print(f"Magnetometro: X={x_gauss:.3f} G, Y={y_gauss:.3f} G, Z={z_gauss:.3f} G")
    print("")
    return x_gauss, y_gauss, z_gauss

# Funcao principal
def main():
    try:
        configure_gyro()
        configure_lsm303d()

        while True:
            # Ler dados dos sensores
            read_gyro()
            read_accel()
            read_mag()

            # Espera 1 segundo antes da proxima leitura
            #time.sleep(0.5)

    except KeyboardInterrupt:
        print("Programa encerrado")

if __name__ == "__main__":
    main()
