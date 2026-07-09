#/usr/bin/python3

import RPi.GPIO as GPIO
import time

def configure_gpio(pins):
    GPIO.setmode(GPIO.BCM)

    for name, pin in pins.items():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
        print(f"Pin {name} configured as GPIO {pin}")
        time.sleep(0.2)

# Ejemplo de uso
if __name__ == "__main__":
    pins = {
        "pin_test": 12,
    }
    
    # Configure Pins
    configure_gpio(pins)
    GPIO.output(pins["pin_test"], GPIO.HIGH)
    time.sleep(30)
    GPIO.output(pins["pin_test"], GPIO.LOW)
    time.sleep(1)
    GPIO.cleanup()
