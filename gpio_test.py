import os
os.environ['JETSON_MODEL'] = 'JETSON_ORIN_NANO'  # Fix model detection

import Jetson.GPIO as GPIO
import time

# Pin definitions (BCM numbering)
ENA = 13  # Left motor PWM (Pin 33)
IN1 = 19  # Left direction 1 (Pin 35)
IN2 = 26  # Left direction 2 (Pin 37)
ENB = 12  # Right motor PWM (Pin 32)
IN3 = 16  # Right direction 1 (Pin 36)
IN4 = 20  # Right direction 2 (Pin 38)

# Setup
GPIO.setmode(GPIO.BCM)

GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
GPIO.output(ENA, GPIO.HIGH)
GPIO.output(ENB, GPIO.HIGH)


print("GPIO Test - Press Ctrl+C to stop")

try:
    # Test: All motors stopped
    print("Test 1: All motors stopped")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    time.sleep(2)
    
    # Test: Left motors forward at 50% speed
    print("Test 2: Left motors forward (50%)")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    time.sleep(3)
    
    # Stop
    time.sleep(1)
    
    # Test: Right motors forward at 50% speed
    print("Test 3: Right motors forward (50%)")
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    time.sleep(3)
    
    # Stop

    time.sleep(1)
    
    # Test: Both motors forward at 30% speed
    print("Test 4: Both motors forward (30%)")
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)

    time.sleep(3)
    
    # Stop

    time.sleep(1)
    
    # Test: Both motors reverse at 30% speed
    print("Test 5: Both motors reverse (30%)")
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    
    time.sleep(3)
    
    # Stop
    print("Test complete - stopping motors")


except KeyboardInterrupt:
    print("\nStopped by user")

finally:
    # Cleanup

    GPIO.cleanup()
    print("GPIO cleanup complete")
