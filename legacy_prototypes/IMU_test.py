#!/usr/bin/python3
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import smbus
import time

# Configuración del bus I2C (igual que tu código)
bus = smbus.SMBus(1)
L3GD20H_ADDR = 0x6B  # Dirección del giroscopio

# Registros del giroscopio
GYRO_X_LSB = 0x28
GYRO_Y_LSB = 0x2A
GYRO_Z_LSB = 0x2C
CTRL_REG1 = 0x20
CTRL_REG4 = 0x23

# Función para leer datos del giroscopio
def read_word(address, register):
    low = bus.read_byte_data(address, register)
    high = bus.read_byte_data(address, register + 1)
    return (high << 8) + low

def adjust_signed(value):
    return value - 65536 if value >= 32768 else value

# Configurar giroscopio
def configure_gyro():
    bus.write_byte_data(L3GD20H_ADDR, CTRL_REG1, 0x0F)  # Habilita XYZ
    bus.write_byte_data(L3GD20H_ADDR, CTRL_REG4, 0x00)  # ±250 dps

# Leer datos del giroscopio
def read_gyro():
    x = adjust_signed(read_word(L3GD20H_ADDR, GYRO_X_LSB))
    y = adjust_signed(read_word(L3GD20H_ADDR, GYRO_Y_LSB))
    z = adjust_signed(read_word(L3GD20H_ADDR, GYRO_Z_LSB))
    scale = 0.00875  # Escala para convertir a dps
    return x * scale, y * scale, z * scale

# Inicialización de variables
configure_gyro()
angle_x, angle_y, angle_z = 0, 0, 0
dt = 0.1  # Intervalo de tiempo entre mediciones

# Configuración de la figura en Matplotlib
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_zlim(-1, 1)

# Crear líneas para representar el avión
plane, = ax.plot([], [], [], 'bo-', linewidth=2)

# Función de actualización para la animación
def update(frame):
    global angle_x, angle_y, angle_z

    # Leer el giroscopio y actualizar ángulos
    gyro_x, gyro_y, gyro_z = read_gyro()
    angle_x += gyro_x * dt
    angle_y += gyro_y * dt
    angle_z += gyro_z * dt

    # Calcular la orientación del plano usando matrices de rotación
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(np.radians(angle_x)), -np.sin(np.radians(angle_x))],
                    [0, np.sin(np.radians(angle_x)), np.cos(np.radians(angle_x))]])

    R_y = np.array([[np.cos(np.radians(angle_y)), 0, np.sin(np.radians(angle_y))],
                    [0, 1, 0],
                    [-np.sin(np.radians(angle_y)), 0, np.cos(np.radians(angle_y))]])

    R_z = np.array([[np.cos(np.radians(angle_z)), -np.sin(np.radians(angle_z)), 0],
                    [np.sin(np.radians(angle_z)), np.cos(np.radians(angle_z)), 0],
                    [0, 0, 1]])

    R = R_x @ R_y @ R_z

    # Definir el cuerpo del avión (una línea en 3D)
    base_plane = np.array([[0, 0, 0], [1, 0, 0]]).T
    rotated_plane = R @ base_plane

    # Actualizar la línea del avión
    plane.set_data(rotated_plane[0, :], rotated_plane[1, :])
    plane.set_3d_properties(rotated_plane[2, :])

    return plane,

# Configurar la animación
ani = animation.FuncAnimation(fig, update, frames=100, interval=100, blit=False)
plt.show()

