import os
os.environ['JETSON_MODEL'] = 'JETSON_ORIN_NANO'

import Jetson.GPIO as GPIO
import cv2

# Pin definitions
ENA = 13
IN1 = 19
IN2 = 26
ENB = 12
IN3 = 16
IN4 = 20

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)
pwm_left = GPIO.PWM(ENA, 1000)
pwm_right = GPIO.PWM(ENB, 1000)
pwm_left.start(0)
pwm_right.start(0)

# Camera setup
cap = cv2.VideoCapture(0)

def stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)

def forward(speed=40):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def backward(speed=40):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def left(speed=40):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def right(speed=40):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

print("Manual Control")
print("W=Forward S=Backward A=Left D=Right Space=Stop Q=Quit")

try:
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.putText(frame, "W/A/S/D to move, Space=Stop, Q=Quit",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.imshow('Car View', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('w'):
            forward(40)
        elif key == ord('s'):
            backward(40)
        elif key == ord('a'):
            left(40)
        elif key == ord('d'):
            right(40)
        elif key == ord(' '):
            stop()
        elif key == ord('q'):
            break

except KeyboardInterrupt:
    print("\nStopped")

finally:
    stop()
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
    cap.release()
    cv2.destroyAllWindows()
