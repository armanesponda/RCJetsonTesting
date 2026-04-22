import cv2
import os
import time
import threading
from datetime import datetime
from flask import Flask, Response, jsonify, render_template_string, request

SAVE_DIR = os.path.expanduser("~/lane_data/raw")
os.makedirs(SAVE_DIR, exist_ok=True)

# --- Camera setup ---
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    for i in [1, 2]:
        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        if cap.isOpened():
            break
if not cap.isOpened():
    raise RuntimeError("No camera found")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# --- Shared state ---
state_lock = threading.Lock()
latest_frame = None
count = 0
auto_mode = False
auto_interval = 0.5

# --- Capture thread: keeps latest_frame fresh ---
def capture_loop():
    global latest_frame, count
    last_auto = 0.0
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue
        with state_lock:
            latest_frame = frame
            do_auto = auto_mode and (time.time() - last_auto) >= auto_interval
        if do_auto:
            save_frame(frame, tag="AUTO")
            last_auto = time.time()

def save_frame(frame, tag="MANUAL"):
    global count
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(SAVE_DIR, f"lane_{ts}.jpg")
    cv2.imwrite(path, frame)
    with state_lock:
        count += 1
        current = count
    print(f"[{tag}] {current}: {path}")
    return path, current

threading.Thread(target=capture_loop, daemon=True).start()

# --- Flask app ---
app = Flask(__name__)

PAGE = """
<!doctype html>
<html>
<head><title>Lane Data Collection</title>
<style>
body{font-family:sans-serif;max-width:720px;margin:20px auto;padding:0 12px}
img{width:100%;border:1px solid #ccc;border-radius:6px}
.row{display:flex;gap:8px;align-items:center;margin:12px 0;flex-wrap:wrap}
button{padding:10px 16px;font-size:16px;cursor:pointer}
#count{font-size:24px;font-weight:bold}
.on{background:#1a7f37;color:white}
.off{background:#eee}
input[type=number]{width:80px;padding:6px;font-size:16px}
</style></head>
<body>
<h2>Lane Data Collection</h2>
<img src="/stream" alt="live feed">
<div class="row">
  <button onclick="capture()">Capture (space)</button>
  <button id="autobtn" onclick="toggleAuto()">Auto: OFF</button>
  <label>Interval (s):
    <input type="number" id="interval" value="0.5" step="0.1" min="0.1" onchange="setInterval_()">
  </label>
</div>
<div>Saved: <span id="count">0</span></div>
<script>
async function capture(){
  const r = await fetch('/capture', {method:'POST'});
  const j = await r.json();
  document.getElementById('count').textContent = j.count;
}
async function toggleAuto(){
  const r = await fetch('/auto/toggle', {method:'POST'});
  const j = await r.json();
  const btn = document.getElementById('autobtn');
  btn.textContent = 'Auto: ' + (j.auto ? 'ON' : 'OFF');
  btn.className = j.auto ? 'on' : 'off';
}
async function setInterval_(){
  const v = document.getElementById('interval').value;
  await fetch('/auto/interval?v=' + v, {method:'POST'});
}
async function refresh(){
  const r = await fetch('/status');
  const j = await r.json();
  document.getElementById('count').textContent = j.count;
}
setInterval(refresh, 1000);
document.addEventListener('keydown', e => {
  if (e.code === 'Space'){ e.preventDefault(); capture(); }
  if (e.key === 'a' || e.key === 'A'){ toggleAuto(); }
});
</script>
</body></html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

def mjpeg_generator():
    while True:
        with state_lock:
            frame = None if latest_frame is None else latest_frame.copy()
        if frame is None:
            time.sleep(0.05)
            continue
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ok:
            continue
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        time.sleep(1/15)  # ~15fps stream, easy on hotspot bandwidth

@app.route("/stream")
def stream():
    return Response(mjpeg_generator(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/capture", methods=["POST"])
def capture():
    with state_lock:
        frame = None if latest_frame is None else latest_frame.copy()
    if frame is None:
        return jsonify(error="no frame"), 503
    _, current = save_frame(frame, tag="MANUAL")
    return jsonify(count=current)

@app.route("/auto/toggle", methods=["POST"])
def auto_toggle():
    global auto_mode
    with state_lock:
        auto_mode = not auto_mode
        mode = auto_mode
    return jsonify(auto=mode)

@app.route("/auto/interval", methods=["POST"])
def auto_set_interval():
    global auto_interval
    try:
        v = float(request.args.get("v", "0.5"))
        v = max(0.1, v)
    except ValueError:
        return jsonify(error="bad value"), 400
    with state_lock:
        auto_interval = v
    return jsonify(interval=v)

@app.route("/status")
def status():
    with state_lock:
        return jsonify(count=count, auto=auto_mode, interval=auto_interval)

if __name__ == "__main__":
    print(f"Saving to: {SAVE_DIR}")
    print("Open http://<jetson-ip>:5000 in a browser")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
