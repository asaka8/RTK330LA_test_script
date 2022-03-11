import time
try:
    import RPI.GPIO as GPIO
except RuntimeError:
    print("Can't find GPIO, pls check the enviroment")

class GPIO_excutor:
    def __init__(self, pin):
        self.power_pin = pin
        self.GPIO_setting()

    def GPIO_setting(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.power_pin, GPIO.OUT)
        GPIO.output(self.power_pin, GPIO.HIGH)
        GPIO.output(self.power_pin, GPIO.LOW)

    def power_switch(self):
        GPIO.output(self.power_pin, GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(self.power_pin, GPIO.HIGH)
        time.sleep(0.5)

