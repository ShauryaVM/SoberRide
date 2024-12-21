#New code after getting ADC

import spidev
import time
import datetime
from scipy.stats import norm
import RPi.GPIO as GPIO

# Individual Parameters
gender = "male"
bday = "09082008"
face_chance = 0.7

# Score functions
def day_score():
    today = datetime.datetime.today().weekday()
    return 1 if 0 <= today <= 3 else 3

def time_score():
    current_hour = datetime.datetime.now().hour
    if 0 <= current_hour < 4:
        return 4
    elif 4 <= current_hour < 8:
        return 2
    elif 8 <= current_hour < 12:
        return 1
    elif 12 <= current_hour < 16:
        return 1
    elif 16 <= current_hour < 20:
        return 2
    elif 20 <= current_hour < 24:
        return 3
    return 0

def gender_score():
    return 2 if gender == "male" else 1

def get_age(bday):
    month, day, year = int(bday[:2]), int(bday[2:4]), int(bday[4:])
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
    return 1 if age >= 51 else 0

# SPI setup for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((adc[1] & 3) << 8) + adc[2]

# GPIO setup
GPIO.setmode(GPIO.BCM)

person_points = age_score() + gender_score() + time_score() + day_score()
if 12 <= person_points <= 13:
    tolerance_diff = -100
elif 9 <= person_points < 12:
    tolerance_diff = -50
elif person_points == 9:
    tolerance_diff = 0
elif 6 <= person_points < 9:
    tolerance_diff = 30
else:
    tolerance_diff = 50

threshold = 500 + tolerance_diff
stddev = 0.1 * threshold

try:
    while True:
        sensor_value = read_adc(0)
        breathalyzer_chance = norm.cdf(sensor_value, threshold, stddev)
        face_change = 0.7
        final_chance = 0.8 * breathalyzer_chance + 0.2 * face_chance
        if final_chance > 0.5:
            print("Drunk")
        else:
            print("Sober")
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    spi.close()