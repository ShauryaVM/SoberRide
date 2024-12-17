import RPi.GPIO as GPIO
import time
import datetime
from scipy.stats import norm

#Individual Parameters 
gender = "male"
bday = "09082008"
face_chance = 0.7

#Score functions
def day_score():
    today = datetime.datetime.today().weekday()
    if 0<=today<=3:
        return 1
    else:
        return 3
    
def time_score():
    current_hour = datetime.datetime.now().hour
    if 0 <= current_hour < 4:  # 12am - 4am
        return 4
    elif 4 <= current_hour < 8:  # 4am - 8am
        return 2
    elif 8 <= current_hour < 12:  # 8am - 12pm
        return 1
    elif 12 <= current_hour < 16:  # 12pm - 4pm
        return 1
    elif 16 <= current_hour < 20:  # 4pm - 8pm
        return 2
    elif 20 <= current_hour < 24:  # 8pm - 12am
        return 3
    else:
        return 0
    
def gender_score():
    if gender == "male":
        return 2
    else:
        return 1

def get_age(bday):
    month = int(bday[:2])
    day = int(bday[2:4])
    year = int(bday[4:])
    birth_date = datetime.date(year, month, day)
    today = datetime.date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

def age_score():
    age = get_age(bday)
    if age <= 30:
        return 4
    elif 31 <= age <= 40:
        return 3
    elif 41 <= age <= 50:
        return 2
    elif age >= 51:
        return 1
    else:
        return 0

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Define GPIO pins for MQ-3 sensor and LEDs
SENSOR_PIN = 2
RED_LED_PIN = 10
GREEN_LED_PIN = 8

# Setup GPIO pins
GPIO.setup(SENSOR_PIN, GPIO.IN)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)


person_points = age_score()+gender_score()+time_score()+day_score()
if person_points >= 12 and person_points <= 13:
    tolerance_diff = -100
elif person_points >= 9 and person_points <12:
    tolerance_diff = -50
elif person_points == 9:
    tolerance_diff = 0
elif person_points >= 6 and person_points <9:
    tolerance_diff = 30
else:
    tolerance_diff = 50

threshold = 500 + tolerance_diff
stddev = 0.1*threshold

try:
    while True:
        # Read analog value from MQ-3 sensor
        sensor_value = GPIO.input(SENSOR_PIN)

        # # Check the sensor value and control LEDs accordingly
        # if sensor_value > 300:
        #     GPIO.output(RED_LED_PIN, GPIO.HIGH)
        #     GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        # else:
        #     GPIO.output(RED_LED_PIN, GPIO.LOW)
        #     GPIO.output(GREEN_LED_PIN, GPIO.HIGH)

        breathalyzer_chance = norm.cdf(sensor_value, threshold, stddev)
        final_chance = 0.8*breathalyzer_chance + 0.2*face_chance
        if final_chance > 0.5:
            GPIO.output(RED_LED_PIN, GPIO.HIGH)
            GPIO.output(GREEN_LED_PIN, GPIO.LOW)
        else:
            GPIO.output(RED_LED_PIN, GPIO.LOW)
            GPIO.output(GREEN_LED_PIN, GPIO.HIGH)

        # Wait for a short duration before reading again
        time.sleep(0.1)

except KeyboardInterrupt:
    # Clean up GPIO settings on program exit
    GPIO.cleanup()

