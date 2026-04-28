import os
os.environ['JETSON_MODEL'] = 'JETSON_ORIN_NANO'
import Jetson.GPIO as GPIO
import cv2
import time
import threading
import signal
import sys
from flask import Flask, Response, jsonify, render_template_string, request

# ── Pin definitions ────────────────────────────────────────────────
ENA = 17  # Left motor PWM  (Pin 11)
IN1 = 5   # Pin 29
IN2 = 6   # Pin 31
ENB = 27  # Right motor PWM (Pin 13)
IN3 = 16  # Pin 36
IN4 = 20  # Pin 38


# ── SoftPWM ────────────────────────────────────────────────────────
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

# ── GPIO setup ─────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup([ENA, IN1, IN2, ENB, IN3, IN4], GPIO.OUT)
pwm_left  = SoftPWM(ENA, 100)
pwm_right = SoftPWM(ENB, 100)
pwm_left.start(0)
pwm_right.start(0)

# ── Motor commands ─────────────────────────────────────────────────
def stop_motors():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)

def forward(speed=60):
    GPIO.output(IN1, GPIO.HIGH); GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH); GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def backward(speed=60):
    GPIO.output(IN1, GPIO.LOW);  GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW);  GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def turn_left(speed=60):
    GPIO.output(IN1, GPIO.LOW);  GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH); GPIO.output(IN4, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

def turn_right(speed=60):
    GPIO.output(IN1, GPIO.HIGH); GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW);  GPIO.output(IN4, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)

COMMANDS = {
    "forward":    forward,
    "backward":   backward,
    "turn_left":  turn_left,
    "turn_right": turn_right,
    "stop":       stop_motors,
}

# ── Camera ─────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    for i in [1, 2]:
        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        if cap.isOpened():
            break

cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

frame_lock   = threading.Lock()
latest_frame = None

def capture_loop():
    global latest_frame
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue
        with frame_lock:
            latest_frame = frame

threading.Thread(target=capture_loop, daemon=True).start()

# ── Flask ──────────────────────────────────────────────────────────
app = Flask(__name__)

PAGE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RC Manual Control</title>
<style>
  body{font-family:sans-serif;max-width:700px;margin:20px auto;padding:0 12px;text-align:center}
  img{width:100%;border-radius:6px;border:1px solid #ccc}
  .grid{display:grid;grid-template-columns:repeat(3,80px);grid-template-rows:repeat(3,60px);
        gap:6px;justify-content:center;margin:16px auto}
  button{font-size:22px;border:none;border-radius:8px;cursor:pointer;background:#ddd;
         user-select:none;touch-action:none}
  button:active, button.held{background:#4a90d9;color:#fff}
  #stop-btn{background:#e74c3c;color:#fff;font-size:16px}
  .speed-row{display:flex;align-items:center;justify-content:center;gap:10px;margin:10px 0}
  #speed-val{font-weight:bold;width:30px}
  #status{margin-top:8px;font-size:13px;color:#888}
</style>
</head>
<body>
<h2>RC Manual Control</h2>
<img src="/stream" alt="camera feed">

<div class="grid">
  <div></div>
  <button id="btn-forward"   data-cmd="forward"   >▲</button>
  <div></div>
  <button id="btn-turn_left" data-cmd="turn_left" >◀</button>
  <button id="btn-stop"      data-cmd="stop" id="stop-btn">■</button>
  <button id="btn-turn_right"data-cmd="turn_right">▶</button>
  <div></div>
  <button id="btn-backward"  data-cmd="backward"  >▼</button>
  <div></div>
</div>

<div class="speed-row">
  Speed: <input type="range" id="speed" min="20" max="100" value="60">
  <span id="speed-val">60</span>%
</div>
<div id="status">Use buttons or W/A/S/D — hold to move, release to stop</div>

<script>
const speedEl = document.getElementById('speed');
const speedVal = document.getElementById('speed-val');
speedEl.oninput = () => speedVal.textContent = speedEl.value;

function send(cmd) {
  fetch('/move', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({cmd, speed: parseInt(speedEl.value)})
  });
}

// Button hold behaviour
document.querySelectorAll('button[data-cmd]').forEach(btn => {
  const cmd = btn.dataset.cmd;
  const isStop = cmd === 'stop';
  btn.addEventListener('pointerdown', e => { e.preventDefault(); send(cmd); if(!isStop) btn.classList.add('held'); });
  btn.addEventListener('pointerup',   e => { e.preventDefault(); if(!isStop){ send('stop'); btn.classList.remove('held'); } });
  btn.addEventListener('pointerleave',e => { if(!isStop && btn.classList.contains('held')){ send('stop'); btn.classList.remove('held'); } });
});

// Keyboard hold behaviour
const keyMap = { KeyW:'forward', KeyS:'backward', KeyA:'turn_left', KeyD:'turn_right' };
const held = new Set();
document.addEventListener('keydown', e => {
  if (e.code === 'Space') { e.preventDefault(); send('stop'); return; }
  const cmd = keyMap[e.code];
  if (cmd && !held.has(e.code)) { held.add(e.code); send(cmd); }
});
document.addEventListener('keyup', e => {
  if (keyMap[e.code]) { held.delete(e.code); send('stop'); }
});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

def mjpeg_generator():
    while True:
        with frame_lock:
            frame = None if latest_frame is None else latest_frame.copy()
        if frame is None:
            time.sleep(0.05)
            continue
        small = cv2.resize(frame, (320, 240))
        ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 30])
        if not ok:
            continue
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        time.sleep(1 / 10)

@app.route("/stream")
def stream():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/move", methods=["POST"])
def move():
    data  = request.get_json(force=True)
    cmd   = data.get("cmd", "stop")
    speed = int(data.get("speed", 60))
    fn = COMMANDS.get(cmd, stop_motors)
    fn(speed) if cmd != "stop" else stop_motors()
    return jsonify(ok=True)

# ── Clean shutdown on any signal ───────────────────────────────────
def shutdown(sig, frame):
    stop_motors()
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
    cap.release()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGHUP,  shutdown)

if __name__ == "__main__":
    print("Open http://<jetson-ip>:5000 in a browser on the same network")
    try:
        app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
    finally:
        shutdown(None, None)
