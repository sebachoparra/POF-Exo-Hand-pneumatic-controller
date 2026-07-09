#!/usr/bin/python3
# -*- coding: utf-8 -*-

import smbus
import time
import numpy as np
from scipy.spatial.transform import Rotation as R

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
    #bus.write_byte_data(L3GD20H_ADDR, CTRL_REG4, 0x00)  # Escala de 250 dps
    bus.write_byte_data(L3GD20H_ADDR, CTRL_REG4, 0x20)  # Escala de 2000 dps

# Funcao para configurar o LSM303D (acelerometro e magnetometro)
def configure_lsm303d():
    # Configurar acelerometro
    bus.write_byte_data(LSM303D_ADDR, CTRL1, 0x57)  # Habilitar XYZ e 100Hz (revisar porque en el datasheet dice que 57 son 50 Hz)
    bus.write_byte_data(LSM303D_ADDR, CTRL2, 0x18)
    bus.write_byte_data(LSM303D_ADDR, CTRL5, 0x64)  # Atualizacao de 50Hz
    bus.write_byte_data(LSM303D_ADDR, CTRL6, 0x20)  # Escala de 4 gauss
    bus.write_byte_data(LSM303D_ADDR, CTRL7, 0x00)  # Modo continuo

# Funcao para ler o giroscopio
def read_gyro():
    x = adjust_signed(read_word(L3GD20H_ADDR, GYROSCOPE_X_LSB))
    y = adjust_signed(read_word(L3GD20H_ADDR, GYROSCOPE_Y_LSB))
    z = adjust_signed(read_word(L3GD20H_ADDR, GYROSCOPE_Z_LSB))

    # Conversao para graus por segundo (dps)
    scale = 0.00875  # 250 dps
    scale = 1  # 2000 dps
    x_dps = x * scale
    y_dps = y * scale
    z_dps = z * scale

    #print(f"Giroscopio: X={x_dps:.2f} dps, Y={y_dps:.2f} dps, Z={z_dps:.2f} dps")
    #print("")
    return np.array([x_dps, y_dps, z_dps])

def read_gyro_offsets():
    total_samples = 32
    samples = np.array([read_gyro() for _ in range(total_samples)])
    return np.mean(samples, axis=0)

# Funcao para ler o acelerometro
def read_accel():
    x = adjust_signed(read_word(LSM303D_ADDR, ACCEL_X_LSB))
    y = adjust_signed(read_word(LSM303D_ADDR, ACCEL_Y_LSB))
    z = adjust_signed(read_word(LSM303D_ADDR, ACCEL_Z_LSB))

    # Conversao para g (gravidade)
    scale = 0.000061  # �2g
    
    scale = 1  # �2g
    scale = 0.000244
    x_g = x * scale
    y_g = y * scale
    z_g = z * scale

    #print(f"Acelerometro: X={x_g:.3f} g, Y={y_g:.3f} g, Z={z_g:.3f} g")
    #print("")
    return np.array([x_g, y_g, z_g])

# Funcao para ler o magnetometro
def read_mag():
    x = adjust_signed(read_word(LSM303D_ADDR, MAG_X_LSB))
    y = adjust_signed(read_word(LSM303D_ADDR, MAG_Y_LSB))
    z = adjust_signed(read_word(LSM303D_ADDR, MAG_Z_LSB))

    # Conversao para gauss (aproximado)
    # scale = 0.00014  # �4 gauss
    scale = 1
    x_gauss = x * scale
    y_gauss = y * scale
    z_gauss = z * scale

    #print(f"Magnetometro: X={x_gauss:.3f} G, Y={y_gauss:.3f} G, Z={z_gauss:.3f} G")
    #print("")
    return np.array([x_gauss, y_gauss, z_gauss])


def rotation_from_compass(acceleration, magnetic_field):
    # Calcula la rotación utilizando los vectores aceleración y campo magnético
    # Esta es una estimación simple; en un caso real, puede involucrar más cálculos.
    #up = accel_norm  # El vector aceleración ya está normalizado
    up = acceleration  # El vector aceleración ya está normalizado
    east = np.cross(-up, magnetic_field) # Esto nos da la dirección "este" (normalizada)
    # print(east)
    north = np.cross(east, -up)  # Esto nos da la dirección "norte" (normalizada)
    # print(north)

    east_normalized = east / np.linalg.norm(east)
    north_normalized = north / np.linalg.norm(north)
    up_normalized = up / np.linalg.norm(up)

    # Crear la matriz de rotación 3x3
    rotation_matrix = np.vstack([north_normalized, east_normalized, -up_normalized]).T
    #rotation_matrix = np.vstack([north_normalized, east_normalized, up_normalized])
    return rotation_matrix

def rotate(rotation, angular_velocity, dt):
    # Esta función realiza una rotación sobre el cuaternión utilizando la velocidad angular
    omega = angular_velocity * dt
    delta_rotation = R.from_rotvec(omega)
    rotation = rotation * delta_rotation
    return rotation

def fuse_default(rotation, dt, angular_velocity, acceleration, magnetic_field):
    correction = np.zeros(3)

    if np.abs(np.linalg.norm(acceleration) - 1) <= 0.3:
        
        # La magnitud de la aceleración está cerca de 1g, lo que sugiere que está apuntando hacia arriba
        # y podemos hacer una corrección de deriva.

        correction_strength = 1.0

        # Obtener la matriz de rotación basada en el compás
        rotation_compass = rotation_from_compass(acceleration, magnetic_field)
        #print(rotation_compass.T)
        rotation_matrix = rotation.as_matrix()
        #print(rotation_matrix)
        
        

        # Calcular la corrección
        correction = (
            np.cross(rotation_compass[0], rotation_matrix[0]) +
            np.cross(rotation_compass[1], rotation_matrix[1]) +
            np.cross(rotation_compass[2], rotation_matrix[2])
        ) * correction_strength
        #print(rotation_matrix[2])

        # Mostrar el tiempo delta
        #print(dt)

    # Aplicar la rotación
    rotation = rotate(rotation, angular_velocity + correction, dt)
    return rotation

# Funcao principal
def main():
    try:
        configure_gyro()
        configure_lsm303d()

        gyro_offsets = read_gyro_offsets()
        mag_calibration = np.loadtxt("/home/exohand/.minimu9-ahrs-cal", dtype=int)
        start = time.perf_counter()

        rotation = R.identity()

        while True:
            last_start = start
            start = time.perf_counter()
            dt = start - last_start
            
            if dt < 0:
                raise RuntimeError("Time went backwards.")
        
            #print(dt)
            gyro = (read_gyro() - gyro_offsets) * (0.07 * 3.14159265 / 180)
            #print(gyro)
            acc = read_accel()
            #print(acc)
            mag = (read_mag() - mag_calibration[::2]) / (mag_calibration[1::2] - mag_calibration[::2]) * 2 - 1
            #print(mag)
            rotation = fuse_default(rotation, dt, gyro, acc, mag)
            #print(-1*rotation.as_euler('zyx', degrees=True)) 
            #print(rotation.as_euler('zyx', degrees=True)) 
            print(f"Quat: {rotation.as_quat()}") 
            print(f"Euler: {rotation.as_euler('zyx', degrees=True)}") 

    except KeyboardInterrupt:
        print("Programa encerrado")

if __name__ == "__main__":
    main()
