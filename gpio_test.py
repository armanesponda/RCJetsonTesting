import os
os.environ['JETSON_MODEL'] = 'JETSON_ORIN_NANO'
import Jetson.GPIO as GPIO
import time

ENA = 13  # Left motor PWM (Pin 33)
IN1 = 19  # Left direction 1 (Pin 35)
IN2 = 26  # Left direction 2 (Pin 37)
ENB = 12  # Right motor PWM (Pin 32)
IN3 = 16  # Right direction 1 (Pin 36)
IN4 = 20  # Right direction 2 (Pin 38)

GPIO.setmode(GPIO.BCM)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

pwm_left = GPIO.PWM(ENA, 1000)
pwm_right = GPIO.PWM(ENB, 1000)
pwm_left.start(0)
pwm_right.start(0)

print("GPIO Test - Press Ctrl+C to stop")
try:
    print("Test 1: All motors stopped")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    time.sleep(2)

    print("Test 2: Left motors forward (50%)")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    pwm_left.ChangeDutyCycle(50)
    time.sleep(3)

    pwm_left.ChangeDutyCycle(0)
    time.sleep(1)

    print("Test 3: Right motors forward (50%)")
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_right.ChangeDutyCycle(50)
    time.sleep(3)

    pwm_right.ChangeDutyCycle(0)
    time.sleep(1)

    print("Test 4: Both motors forward (30%)")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(30)
    pwm_right.ChangeDutyCycle(30)
    time.sleep(3)

    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
    time.sleep(1)

    print("Test 5: Both motors reverse (30%)")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(30)
    pwm_right.ChangeDutyCycle(30)
    time.sleep(3)

    print("Test complete - stopping motors")
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)
except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
    print("GPIO cleanup complete")
