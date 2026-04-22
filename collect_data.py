import cv2
import os
from datetime import datetime

SAVE_DIR = os.path.expanduser("~/lane_data/raw")
AUTO_INTERVAL_SEC = 0.5  # how often to capture in auto mode

os.makedirs(SAVE_DIR, exist_ok=True)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    for i in [1, 2]:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            break

if not cap.isOpened():
    print("ERROR: No camera found")
    exit(1)

count = 0
auto_mode = False
last_auto_capture = 0

print(f"Saving to: {SAVE_DIR}")
print("SPACE = capture  |  A = toggle auto-capture  |  Q = quit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera read failed")
        break

    now = cv2.getTickCount() / cv2.getTickFrequency()

    if auto_mode and (now - last_auto_capture) >= AUTO_INTERVAL_SEC:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(SAVE_DIR, f"lane_{ts}.jpg")
        cv2.imwrite(path, frame)
        count += 1
        last_auto_capture = now
        print(f"[AUTO] {count}: {path}")

    display = frame.copy()
    mode_label = "AUTO" if auto_mode else "MANUAL"
    cv2.putText(display, f"{mode_label} | Captured: {count} | A=toggle Q=quit",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 200, 0) if auto_mode else (0, 180, 255), 2)
    cv2.imshow("Lane Data Collection", display)

    key = cv2.waitKey(30) & 0xFF
    if key == ord(' '):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = os.path.join(SAVE_DIR, f"lane_{ts}.jpg")
        cv2.imwrite(path, frame)
        count += 1
        print(f"[MANUAL] {count}: {path}")
    elif key == ord('a'):
        auto_mode = not auto_mode
        last_auto_capture = now
        print(f"Auto-capture {'ON' if auto_mode else 'OFF'}")
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\nDone. {count} images saved to {SAVE_DIR}")
