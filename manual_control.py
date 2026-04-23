import os
os.environ['JETSON_MODEL'] = 'JETSON_ORIN_NANO'
import Jetson.GPIO as GPIO
import cv2
import time
import threading
import numpy as np
from datetime import datetime

# Pin definitions
ENA = 17  # Left motor PWM (Pin 11)
IN1 = 5   # Pin 29
IN2 = 6   # Pin 31
ENB = 27  # Right motor PWM (Pin 13)
IN3 = 16  # Pin 36
IN4 = 20  # Pin 38

# Speed trim — reduce whichever side is faster (0.0–1.0)
LEFT_TRIM  = 1.0
RIGHT_TRIM = 0.85

SAVE_DIR = os.path.expanduser("~/lane_data/raw")
os.makedirs(SAVE_DIR, exist_ok=True)

class SoftPWM:
    def __init__(self, pin, freq=100):
        self.pin = pin
        self.period = 1.0 / freq
        self.duty = 0
        self._running = False
        self._thread = None

    def start(self, duty):
        self.duty = duty
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self._running:
            dc = self.duty
            if dc <= 0:
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(self.period)
            elif dc >= 100:
                GPIO.output(self.pin, GPIO.HIGH)
                time.sleep(self.period)
            else:
                GPIO.output(self.pin, GPIO.HIGH)
                time.sleep(self.period * dc / 100.0)
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(self.period * (100.0 - dc) / 100.0)

    def ChangeDutyCycle(self, duty):
        self.duty = duty

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.1)
        GPIO.output(self.pin, GPIO.LOW)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)
pwm_left = SoftPWM(ENA, 100)
pwm_right = SoftPWM(ENB, 100)
pwm_left.start(0)
pwm_right.start(0)

# Camera setup
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    for i in [1, 2]:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            break

def stop_motors():
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
    pwm_left.ChangeDutyCycle(speed * LEFT_TRIM)
    pwm_right.ChangeDutyCycle(speed * RIGHT_TRIM)

def backward(speed=40):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed * LEFT_TRIM)
    pwm_right.ChangeDutyCycle(speed * RIGHT_TRIM)

def turn_left(speed=40):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed * LEFT_TRIM)
    pwm_right.ChangeDutyCycle(speed * RIGHT_TRIM)

def turn_right(speed=40):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

capture_count = 0
flash_frames = 0

print(f"Saving images to: {SAVE_DIR}")
print("W=Forward  S=Backward  A=Left  D=Right  Space=Stop")
print("C=Capture image  Q=Quit")
print(">>> CLICK THE 'Car View' WINDOW BEFORE PRESSING KEYS <<<")

try:
    cv2.namedWindow('Car View', cv2.WINDOW_AUTOSIZE)

    while True:
        if cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                frame = np.zeros((240, 480, 3), dtype='uint8')
        else:
            frame = np.zeros((240, 480, 3), dtype='uint8')

        display = frame.copy()

        # White flash feedback on capture
        if flash_frames > 0:
            overlay = np.ones_like(display) * 255
            alpha = flash_frames / 6.0
            display = cv2.addWeighted(display, 1 - alpha, overlay, alpha, 0)
            flash_frames -= 1

        cv2.putText(display, f"W/S/A/D=Drive  Space=Stop  C=Capture  Q=Quit",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(display, f"Captured: {capture_count}",
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.imshow('Car View', display)

        key = cv2.waitKey(30) & 0xFF

        if key == ord('w'):
            forward(40)
        elif key == ord('s'):
            backward(40)
        elif key == ord('a'):
            turn_left(40)
        elif key == ord('d'):
            turn_right(40)
        elif key == ord(' '):
            stop_motors()
        elif key == ord('c'):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(SAVE_DIR, f"lane_{ts}.jpg")
            cv2.imwrite(path, frame)
            capture_count += 1
            flash_frames = 6
            print(f"Captured {capture_count}: {path}")
        elif key == ord('q'):
            break

except KeyboardInterrupt:
    print("\nStopped")
finally:
    stop_motors()
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    print(f"Done. {capture_count} images saved to {SAVE_DIR}")
