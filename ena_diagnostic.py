import os
os.environ['JETSON_MODEL'] = 'JETSON_ORIN_NANO'
import Jetson.GPIO as GPIO
import time

ENA = 22  # Left motor PWM (Pin 15)
IN1 = 5   # Pin 29
IN2 = 6   # Pin 31

GPIO.setmode(GPIO.BCM)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

# Set ENA HIGH directly — no PWM, full speed
# If left motor spins: PWM on ENA is the issue
# If left motor still doesn't spin: IN1/IN2 or DTS is the issue
GPIO.output(ENA, GPIO.HIGH)
GPIO.output(IN1, GPIO.HIGH)
GPIO.output(IN2, GPIO.LOW)

print("ENA set HIGH (no PWM), IN1 HIGH, IN2 LOW")
print("Left motor should be running at full speed for 5 seconds...")
time.sleep(5)

GPIO.cleanup()
print("Done")
