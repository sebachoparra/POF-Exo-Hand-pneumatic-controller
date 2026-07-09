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

def test_all_pins(pins):
    for pin in pins:
        GPIO.output(pins[pin], GPIO.HIGH)
        print(f"Pin {pins[pin]} HIGH")
        time.sleep(2)
        GPIO.output(pins[pin], GPIO.LOW)
        print(f"Pin {pins[pin]} LOW\n")
        time.sleep(2)

# Ejemplo de uso
if __name__ == "__main__":
    pins = {
        "valve ": 19,
        "air_pump1": 12,
        "air_pump2": 13,
        "valve1": 21,
        "valve2": 20,
        "valve3": 16,
        "valve4": 6,
        "valve5": 5
    }
    
    # Configure Pins
    configure_gpio(pins)
    test_all_pins(pins)

    GPIO.cleanup()
