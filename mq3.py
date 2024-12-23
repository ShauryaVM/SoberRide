import RPi.GPIO as GPIO
import time
from gpiozero import LED

GPIO.setmode(GPIO.BCM)

sensor = 2
redLed = 15
greenLed = 14

GPIO.setwarnings(False)

GPIO.setup(sensor, GPIO.IN)
#GPIO.setup(redLed, GPIO.OUT)
#GPIO.setup(greenLed, GPIO.OUT)
green = LED(greenLed)
red = LED(redLed)
#red.on()
time.sleep(1)

try:
    while True:
        sensorValue = GPIO.input(sensor)
        
        if(sensorValue == 0):
            #GPIO.output(redLed, GPIO.HIGH)
            #GPIO.output(greenLed, GPIO.LOW)
            red.on()
            green.off()
        else:
            print("Here")
            #GPIO.output(redLed, GPIO.LOW)
            #GPIO.output(greenLed, GPIO.HIGH)
            green.on()
            red.off()
        time.sleep(0.1)
        print(sensorValue)
        
except KeyboardInterrupt:
    GPIO.cleanup()
