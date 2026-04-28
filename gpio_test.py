import os
os.environ['JETSON_MODEL'] = 'JETSON_ORIN_NANO'
import Jetson.GPIO as GPIO
import time
import threading

class SoftPWM:
    def __init__(self, pin, freq=1000):
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

ENA = 17  # Left motor PWM (Pin 11)
IN1 = 5   # Pin 29
IN2 = 6   # Pin 31
ENB = 27  # Right motor PWM (Pin 13)
IN3 = 16  # Right direction 1 (Pin 36)
IN4 = 20  # Right direction 2 (Pin 38)

GPIO.setmode(GPIO.BCM)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

pwm_left = SoftPWM(ENA, 1000)
pwm_right = SoftPWM(ENB, 1000)
pwm_left.start(0)
pwm_right.start(0)

def all_stop():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)

def run_test(label, setup_fn, duration=2.0):
    input(f"\n[Press Enter] {label}")
    all_stop()
    setup_fn()
    print(f"  Running {duration}s — note which wheel(s) move and direction")
    time.sleep(duration)
    all_stop()
    print("  Stopped.")

print("GPIO Test — press Enter to step through each test, Ctrl+C to quit at any time")
print("For each test, note: which wheel(s) spin, and which direction (forward/backward)")

try:
    run_test("Channel A (ENA/IN1/IN2) — IN1 HIGH  [code calls this 'left forward']",
             lambda: (GPIO.output(IN1, GPIO.HIGH), GPIO.output(IN2, GPIO.LOW),
                      pwm_left.ChangeDutyCycle(50)))

    run_test("Channel A (ENA/IN1/IN2) — IN2 HIGH  [code calls this 'left backward']",
             lambda: (GPIO.output(IN1, GPIO.LOW), GPIO.output(IN2, GPIO.HIGH),
                      pwm_left.ChangeDutyCycle(50)))

    run_test("Channel B (ENB/IN3/IN4) — IN3 HIGH  [code calls this 'right forward']",
             lambda: (GPIO.output(IN3, GPIO.HIGH), GPIO.output(IN4, GPIO.LOW),
                      pwm_right.ChangeDutyCycle(50)))

    run_test("Channel B (ENB/IN3/IN4) — IN4 HIGH  [code calls this 'right backward']",
             lambda: (GPIO.output(IN3, GPIO.LOW), GPIO.output(IN4, GPIO.HIGH),
                      pwm_right.ChangeDutyCycle(50)))

    run_test("Both channels — code's 'forward' (IN1+IN3 HIGH)",
             lambda: (GPIO.output(IN1, GPIO.HIGH), GPIO.output(IN2, GPIO.LOW),
                      GPIO.output(IN3, GPIO.HIGH), GPIO.output(IN4, GPIO.LOW),
                      pwm_left.ChangeDutyCycle(40), pwm_right.ChangeDutyCycle(40)))

    run_test("Both channels — code's 'backward' (IN2+IN4 HIGH)",
             lambda: (GPIO.output(IN1, GPIO.LOW), GPIO.output(IN2, GPIO.HIGH),
                      GPIO.output(IN3, GPIO.LOW), GPIO.output(IN4, GPIO.HIGH),
                      pwm_left.ChangeDutyCycle(40), pwm_right.ChangeDutyCycle(40)))

    print("\nAll tests done. Report back which wheel moved for each test!")

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    all_stop()
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
    print("GPIO cleanup complete")

