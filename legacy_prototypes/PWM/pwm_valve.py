#Define Libraries
import RPi.GPIO as gpio
import time

def configure_gpio(pins):
    gpio.setmode(gpio.BCM)

    for name, pin in pins.items():
        gpio.setup(pin, gpio.OUT)
        gpio.output(pin, gpio.LOW)
        # print(f"Pin {name} configured as GPIO {pin}")
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

#Configure the pwm objects and initialize its value
# pwm = gpio.PWM(pins["valve"], 20)
# pwm.start(0)
pwm2 = gpio.PWM(pins["air_pump1"], 1000)
pwm2.start(0)
pwm3 = gpio.PWM(pins["air_pump2"], 1000)
pwm3.start(0)
# #Create the dutycycle variables
dc = 0
state = 0

try:
    #Loop infinite
    while True:
        # pwm.ChangeDutyCycle(50)
        gpio.output(pins["valve"], gpio.LOW)
        gpio.output(pins["valve1"], gpio.HIGH)
        gpio.output(pins["valve2"], gpio.HIGH)
        gpio.output(pins["valve3"], gpio.HIGH)
        gpio.output(pins["valve4"], gpio.HIGH)
        gpio.output(pins["valve5"], gpio.HIGH)
        pwm2.ChangeDutyCycle(0)
        pwm3.ChangeDutyCycle(100)
        # if state == 0:
        #     #increment gradually the luminosity
        #     # gpio.output(pins["valve"], gpio.LOW) # Ext
        #     pwm.ChangeDutyCycle(dc)
        #     pwm2.ChangeDutyCycle(100)
        #     pwm3.ChangeDutyCycle(10)
        #     time.sleep(1)
        #     dc = dc + 10
        #     if dc == 100:
        #         state = 1

        # else:
        #     #decrement gradually the luminosity
        #     # gpio.output(pins["valve"], gpio.LOW) # Ext
        #     pwm.ChangeDutyCycle(dc)
        #     pwm2.ChangeDutyCycle(100)
        #     pwm3.ChangeDutyCycle(10)
        #     time.sleep(1)
        #     dc = dc - 10
        #     if dc == 0:
        #         state = 0
                
        # print(dc) 
               
        
except KeyboardInterrupt:
    #End code
    gpio.cleanup()
    exit()
