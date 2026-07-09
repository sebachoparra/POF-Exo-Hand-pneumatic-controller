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

pins = {
    "valve": 16,
    "air_pump1": 21,
    "air_pump2": 20,
    #"air_pump2": 5,
    "valve1": 18,
    "valve2": 25,
    "valve3": 24,
    "valve4": 1,
    "valve5": 23
}

# Configure Pins
configure_gpio(pins)
pwm = GPIO.PWM(pins["air_pump1"], 1000)
pwm.start(0)
pwm2 = GPIO.PWM(pins["air_pump2"], 1000)
pwm2.start(0)

variable = 0

while(variable) != 5:
    GPIO.output(pins["valve"], GPIO.LOW) # Ext

    pwm.ChangeDutyCycle(100) # Ext
    pwm2.ChangeDutyCycle(0) #Flex
    GPIO.output(pins["valve1"], GPIO.HIGH)
    GPIO.output(pins["valve2"], GPIO.HIGH)
    GPIO.output(pins["valve3"], GPIO.HIGH)
    GPIO.output(pins["valve4"], GPIO.HIGH)
    GPIO.output(pins["valve5"], GPIO.HIGH)

    time.sleep(3)

    pwm.ChangeDutyCycle(0) # Ext
    pwm2.ChangeDutyCycle(0) #Flex
    GPIO.output(pins["valve1"], GPIO.LOW)
    GPIO.output(pins["valve2"], GPIO.LOW)
    GPIO.output(pins["valve3"], GPIO.LOW)
    GPIO.output(pins["valve4"], GPIO.LOW)
    GPIO.output(pins["valve5"], GPIO.LOW)

    time.sleep(1)

    GPIO.output(pins["valve"], GPIO.HIGH) # Ext

    pwm.ChangeDutyCycle(0) # Ext
    pwm2.ChangeDutyCycle(20) #Flex
    GPIO.output(pins["valve1"], GPIO.HIGH)
    GPIO.output(pins["valve2"], GPIO.HIGH)
    GPIO.output(pins["valve3"], GPIO.HIGH)
    GPIO.output(pins["valve4"], GPIO.HIGH)
    GPIO.output(pins["valve5"], GPIO.HIGH)

    time.sleep(3)
    variable += 1

GPIO.cleanup()
