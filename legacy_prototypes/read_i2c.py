import smbus

def scan_i2c_bus(bus_number=1):
    # Crear un objeto para el bus I2C
    bus = smbus.SMBus(bus_number)
    devices = []
    
    print(f"Escaneando el bus I2C {bus_number}...")
    
    for address in range(0x03, 0x78):  # Rango típico de direcciones I2C (7 bits)
        try:
            bus.read_byte(address)  # Intenta leer un byte de la dirección
            devices.append(hex(address))  # Si tiene éxito, almacena la dirección
        except OSError:
            pass  # Ignorar errores (sin dispositivo en esta dirección)

    if devices:
        print(f"Dispositivos encontrados: {', '.join(devices)}")
    else:
        print("No se encontraron dispositivos en el bus I2C.")
    
    bus.close()

# Ejecutar la función de escaneo
scan_i2c_bus()
