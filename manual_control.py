import os
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

# Camera setup with debug
print(f"DISPLAY env var: {os.environ.get('DISPLAY', 'NOT SET')}")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Camera did not open on index 0")
    # Try a couple other indices just in case
    for i in [1, 2]:
        print(f"Trying index {i}...")
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera opened on index {i}")
            break
else:
    print("Camera opened OK on index 0")

if cap.isOpened():
    ret, frame = cap.read()
    print(f"Test frame read: {ret}, shape: {frame.shape if ret else 'none'}")
else:
    print("ERROR: No camera available on any index")

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
print(">>> CLICK THE 'Car View' WINDOW BEFORE PRESSING KEYS <<<")

try:
    # Force a window to exist even before first frame
    cv2.namedWindow('Car View', cv2.WINDOW_AUTOSIZE)

    while True:
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cv2.putText(frame, "W/A/S/D move, Space=Stop, Q=Quit",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.imshow('Car View', frame)
            else:
                print("Frame read failed")
        else:
            # No camera — show a blank image so the window still exists for key input
            import numpy as np
            blank = np.zeros((240, 480, 3), dtype='uint8')
            cv2.putText(blank, "NO CAMERA - keys still work",
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow('Car View', blank)

        key = cv2.waitKey(30) & 0xFF

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
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    print("Cleanup complete")
