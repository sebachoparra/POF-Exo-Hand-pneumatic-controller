import smbus2
import time

# --- Definiciones del BNO055 (valores del datasheet) ---

# Dirección I2C del sensor (0x28 es la más común)
BNO055_ADDRESS = 0x28

# Registro de Aceleración (Datos LSB)
# Los datos de aceleración X, Y, Z se leen como valores de 16 bits (dos bytes por eje)
# El registro de aceleración X (LSB) es 0x08
# Los registros son consecutivos: ACCEL_X_LSB (0x08), ACCEL_X_MSB (0x09), ACCEL_Y_LSB (0x0A), etc.
BNO055_ACCEL_X_LSB = 0x08

# Registros de Modo de Operación
BNO055_OPR_MODE_REG = 0x3D
# Modos comunes (ver datasheet para todos):
OPERATION_MODE_CONFIG = 0x00
OPERATION_MODE_ACCONLY = 0x01
OPERATION_MODE_NDOF = 0x0C # Nueve Grados de Libertad (fusión de sensor)

# Registro de Reset del sistema
BNO055_SYS_TRIGGER_REG = 0x3F
SYS_RST_BIT = 0x20 # Bit para resetear el sistema

# Registro de Estado de Calibración
BNO055_CALIB_STAT_REG = 0x35 # sys (bit 7-6), gyro (bit 5-4), accel (bit 3-2), mag (bit 1-0)

# --- Funciones de lectura y escritura I2C ---

def bno_write_byte(bus, reg_addr, data):
    """Escribe un byte en un registro específico del BNO055."""
    try:
        bus.write_byte_data(BNO055_ADDRESS, reg_addr, data)
    except IOError as e:
        print(f"Error al escribir en I2C: {e}")
        # Puedes añadir lógica de reintento o manejo de errores más sofisticada aquí

def bno_read_byte(bus, reg_addr):
    """Lee un byte de un registro específico del BNO055."""
    try:
        return bus.read_byte_data(BNO055_ADDRESS, reg_addr)
    except IOError as e:
        print(f"Error al leer de I2C: {e}")
        return None

def bno_read_bytes(bus, reg_addr, num_bytes):
    """Lee múltiples bytes de registros consecutivos del BNO055."""
    try:
        return bus.read_i2c_block_data(BNO055_ADDRESS, reg_addr, num_bytes)
    except IOError as e:
        print(f"Error al leer bloque I2C: {e}")
        return None

# --- Inicialización del BNO055 ---

def initialize_bno055(bus):
    print("Inicializando BNO055...")

    # 1. Resetear el sensor
    print("Enviando comando de reset al sensor...")
    bno_write_byte(bus, BNO055_SYS_TRIGGER_REG, SYS_RST_BIT)
    time.sleep(0.03) # Esperar al menos 30ms después del reset

    # 2. Cambiar a modo CONFIG
    print("Cambiando a modo CONFIG...")
    bno_write_byte(bus, BNO055_OPR_MODE_REG, OPERATION_MODE_CONFIG)
    time.sleep(0.02) # Esperar al menos 19ms para el cambio de modo

    # 3. (Opcional) Configurar unidades, etc.
    # Por defecto viene en m/s^2, rad/s y grados Celsius.
    # Si quisieras cambiar unidades (ver registro UNIT_SEL 0x3B), aquí lo harías.

    # 4. Cambiar a modo NDOF (o el que necesites)
    print("Cambiando a modo NDOF (9 Grados de Libertad)...")
    bno_write_byte(bus, BNO055_OPR_MODE_REG, OPERATION_MODE_NDOF)
    time.sleep(0.01) # Esperar al menos 7ms para el cambio de modo

    print("BNO055 inicializado. Esperando calibración...")

def get_calibration_status(bus):
    """Obtiene el estado de calibración."""
    status_byte = bno_read_byte(bus, BNO055_CALIB_STAT_REG)
    if status_byte is None:
        return (0, 0, 0, 0) # Retorna 0 si hay error de lectura

    sys = (status_byte >> 6) & 0x03
    gyro = (status_byte >> 4) & 0x03
    accel = (status_byte >> 2) & 0x03
    mag = status_byte & 0x03
    return (sys, gyro, accel, mag)

# --- Función para leer aceleración ---

def read_acceleration(bus):
    """
    Lee los valores de aceleración X, Y, Z del BNO055.
    Los valores se representan como int16 (signed 16-bit integers)
    y luego se escalan por el factor de 100 (del datasheet para m/s^2).
    """
    try:
        # Leer 6 bytes a partir del registro ACCEL_X_LSB (X, Y, Z, cada uno con LSB y MSB)
        data = bno_read_bytes(bus, BNO055_ACCEL_X_LSB, 6)
        if data is None:
            return None, None, None

        # Concatenar bytes para obtener valores de 16 bits
        accel_x = (data[1] << 8) | data[0]
        accel_y = (data[3] << 8) | data[2]
        accel_z = (data[5] << 8) | data[4]

        # Convertir a signed 16-bit (manejar números negativos)
        if accel_x > 32767: accel_x -= 65536
        if accel_y > 32767: accel_y -= 65536
        if accel_z > 32767: accel_z -= 65536

        # Escalar a m/s^2 (factor de 100 del datasheet para aceleración en m/s^2)
        accel_x = accel_x / 100.0
        accel_y = accel_y / 100.0
        accel_z = accel_z / 100.0

        return accel_x, accel_y, accel_z
    except Exception as e:
        print(f"Error al leer aceleración: {e}")
        return None, None, None

# --- Bucle principal ---

def main():
    # El bus I2C en Raspberry Pi es típicamente el 1
    # Asegúrate de que tu sensor esté conectado al bus I2C correcto
    # Puedes verificarlo con 'ls /dev/i2c-*' y 'sudo i2cdetect -y 1'
    i2c_bus_number = 1

    try:
        with smbus2.SMBus(i2c_bus_number) as bus:
            initialize_bno055(bus)

            # Esperar a la calibración (opcional, pero mejora la precisión)
            print("Esperando calibración del BNO055 (puede tomar unos minutos, mueve el sensor)...")
            while True:
                sys, gyro, accel, mag = get_calibration_status(bus)
                print(f"Estado de Calibración: Sistema={sys}, Gyro={gyro}, Accel={accel}, Mag={mag}")
                if sys == 3 and gyro == 3 and accel == 3 and mag == 3:
                    print("¡Calibración completa!")
                    break
                time.sleep(1)

            print("\nIniciando lectura de datos de aceleración:")
            while True:
                accel_x, accel_y, accel_z = read_acceleration(bus)
                if accel_x is not None:
                    print(f"Aceleración (m/s^2): X={accel_x:.2f}, Y={accel_y:.2f}, Z={accel_z:.2f}")
                time.sleep(0.5)

    except FileNotFoundError:
        print(f"Error: El bus I2C /dev/i2c-{i2c_bus_number} no se encontró.")
        print("Asegúrate de que I2C esté habilitado en tu Raspberry Pi (sudo raspi-config o config.txt).")
    except PermissionError:
        print(f"Error de permisos: No se puede acceder al bus I2C /dev/i2c-{i2c_bus_number}.")
        print("Asegúrate de que tu usuario esté en el grupo 'i2c' o ejecuta con 'sudo'.")
        print("Para añadir tu usuario al grupo 'i2c': sudo adduser $USER i2c y luego reinicia la sesión.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    main()
