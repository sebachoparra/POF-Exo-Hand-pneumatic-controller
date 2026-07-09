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
        "valve": 19,
        "air_pump_flex": 12,
        "air_pump_ext": 13,
        "valve1": 21,
        "valve2": 20,
        "valve3": 16,
        "valve4": 6,
        "valve5": 5
    }
    
    # Configure Pins
    configure_gpio(pins)
    GPIO.output(pins["valve"], GPIO.LOW)
    GPIO.output(pins["air_pump_ext"], GPIO.HIGH)
    GPIO.output(pins["air_pump_flex"], GPIO.LOW)
    GPIO.output(pins["valve1"], GPIO.HIGH)
    GPIO.output(pins["valve2"], GPIO.HIGH)
    GPIO.output(pins["valve3"], GPIO.HIGH)
    GPIO.output(pins["valve4"], GPIO.HIGH)
    GPIO.output(pins["valve5"], GPIO.HIGH)

    time.sleep(5)

    GPIO.output(pins["valve5"], GPIO.HIGH)
    GPIO.output(pins["valve4"], GPIO.HIGH)
    GPIO.output(pins["valve3"], GPIO.HIGH)
    GPIO.output(pins["valve2"], GPIO.HIGH)
    GPIO.output(pins["valve1"], GPIO.HIGH)
    GPIO.output(pins["air_pump_ext"], GPIO.LOW)
    GPIO.output(pins["air_pump_flex"], GPIO.LOW)
    GPIO.output(pins["valve"], GPIO.LOW)
    
    time.sleep(5)

    GPIO.output(pins["valve"], GPIO.LOW)

    GPIO.cleanup()

