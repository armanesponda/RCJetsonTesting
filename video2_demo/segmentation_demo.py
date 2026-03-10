#!/usr/bin/env python3
"""
DeepLabV3+ Semantic Segmentation Demo
Runs pre-trained DeepLabV3+ (MobileNetV3-Large backbone) on webcam feed or images.
Uses Pascal VOC 21-class segmentation — background class captures floors/roads/sidewalks.

Controls:
  q - quit
  s - save screenshot
"""

import argparse
import time
import os
import warnings

# Suppress harmless torchvision and sympy warnings
warnings.filterwarnings("ignore", message="Failed to load image Python extension")
warnings.filterwarnings("ignore", message="gmpy2 version is too old")

import cv2
import numpy as np
import torch
from torchvision import transforms
from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large

# ──────────────────────────────────────────────────────────────────────────────
# Pascal VOC class names (21 classes, index 0 = background)
# ──────────────────────────────────────────────────────────────────────────────
VOC_CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair",
    "cow", "diningtable", "dog", "horse", "motorbike",
    "person", "pottedplant", "sheep", "sofa", "train",
    "tvmonitor"
]

# Color palette for each class (BGR format for OpenCV)
# Every class gets a visible, distinct color so the segmentation map is always readable.
# Background (class 0) = drivable area concept → highlighted in green.
VOC_COLORMAP = np.array([
    [0, 180, 0],        # 0  background (floor/road/sky) — green = "drivable area"
    [128, 0, 0],        # 1  aeroplane — dark blue
    [0, 128, 0],        # 2  bicycle — green
    [128, 128, 0],      # 3  bird — teal
    [0, 0, 128],        # 4  boat — red
    [128, 0, 128],      # 5  bottle — purple
    [0, 200, 200],      # 6  bus — yellow
    [0, 255, 255],      # 7  car — bright yellow
    [200, 0, 128],      # 8  cat — magenta
    [192, 128, 0],      # 9  chair — cyan
    [64, 128, 0],       # 10 cow — teal
    [80, 50, 200],      # 11 diningtable — orange
    [64, 128, 128],     # 12 dog — olive
    [192, 128, 128],    # 13 horse — light teal
    [0, 64, 200],       # 14 motorbike — orange
    [255, 50, 50],      # 15 person — bright blue
    [0, 128, 64],       # 16 pottedplant — green-blue
    [128, 128, 64],     # 17 sheep — teal
    [128, 64, 192],     # 18 sofa — pink
    [0, 192, 64],       # 19 train — green
    [64, 64, 192],      # 20 tvmonitor — orange
], dtype=np.uint8)

# Maximum width for the side-by-side display window
MAX_DISPLAY_WIDTH = 1280

# ──────────────────────────────────────────────────────────────────────────────
# Preprocessing transform (ImageNet normalization at 520x520)
# ──────────────────────────────────────────────────────────────────────────────
preprocess = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((520, 520)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


def resize_for_display(image, max_width=MAX_DISPLAY_WIDTH):
    """Resize image to fit display if it's too wide."""
    h, w = image.shape[:2]
    if w > max_width:
        scale = max_width / w
        image = cv2.resize(image, (max_width, int(h * scale)))
    return image


def build_overlay(frame, prediction):
    """Build a color segmentation overlay blended onto the original frame."""
    h, w = frame.shape[:2]

    # Map each pixel's class ID to its color
    color_mask = VOC_COLORMAP[prediction]  # (520, 520, 3)

    # Resize color mask back to original frame size
    color_mask = cv2.resize(color_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    # Blend color overlay onto original frame at 40% opacity
    overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
    return overlay


def process_frame(frame, model, device):
    """Run segmentation on a single frame and return the overlay."""
    # Preprocess: BGR → RGB, resize, normalize
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    input_tensor = preprocess(rgb).unsqueeze(0).to(device)

    # Inference
    with torch.no_grad():
        output = model(input_tensor)["out"]

    # Argmax → per-pixel class IDs
    prediction = output.argmax(1).squeeze().cpu().numpy().astype(np.uint8)

    # Print detected classes (useful for debugging)
    unique_classes = np.unique(prediction)
    class_names = [VOC_CLASSES[c] for c in unique_classes]
    print(f"  Detected classes: {', '.join(class_names)}")

    return build_overlay(frame, prediction)


def run_on_image(image_path, model, device):
    """Run segmentation on a single image, display, and wait for keypress."""
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not read image '{image_path}'")
        return

    overlay = process_frame(frame, model, device)

    # Side-by-side display, resized to fit screen
    side_by_side = np.hstack([frame, overlay])
    side_by_side = resize_for_display(side_by_side)
    cv2.imshow("DeepLabV3+ Segmentation", side_by_side)
    print("Showing result. Press any key to exit.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def run_on_video(source, model, device):
    """Run segmentation on webcam or video file with live display."""
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        if isinstance(source, int):
            print(f"Error: Could not open camera {source}.")
            print("Try a different camera ID with --camera-id (e.g., 0, 1, or 2).")
        else:
            print(f"Error: Could not open video file '{source}'.")
        return

    screenshot_count = 0
    prev_time = time.time()

    print("Model loaded. Press 'q' to quit, 's' to screenshot.")

    while True:
        ret, frame = cap.read()
        if not ret:
            # End of video file or camera error
            if not isinstance(source, int):
                print("End of video file.")
            break

        overlay = process_frame(frame, model, device)

        # Calculate FPS
        curr_time = time.time()
        fps = 1.0 / max(curr_time - prev_time, 1e-6)
        prev_time = curr_time

        # Draw FPS on overlay panel
        cv2.putText(overlay, f"FPS: {fps:.1f}", (10, 30),
                     cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        # Side-by-side display, resized to fit screen
        side_by_side = np.hstack([frame, overlay])
        side_by_side = resize_for_display(side_by_side)
        cv2.imshow("DeepLabV3+ Segmentation", side_by_side)

        # Handle key presses (wait ~1ms per frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            filename = f"screenshot_{screenshot_count:04d}.jpg"
            cv2.imwrite(filename, side_by_side)
            print(f"Saved {filename}")
            screenshot_count += 1

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="DeepLabV3+ Semantic Segmentation Demo")
    parser.add_argument("--input", type=str, default="webcam",
                        help="'webcam', path to image, or path to video file")
    parser.add_argument("--camera-id", type=int, default=0,
                        help="Camera device index (default: 0)")
    args = parser.parse_args()

    # Auto-detect device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Startup banner
    input_desc = (f"webcam (camera {args.camera_id})"
                  if args.input == "webcam" else args.input)
    print(f"Model: DeepLabV3+ (MobileNetV3-Large backbone)")
    print(f"Device: {device}")
    print(f"Input: {input_desc}")
    print("Loading model...")

    # Load pre-trained model
    model = deeplabv3_mobilenet_v3_large(weights="DEFAULT")
    model = model.to(device)
    model.eval()

    print("Model loaded.")

    # Dispatch based on input type
    if args.input == "webcam":
        run_on_video(args.camera_id, model, device)
    elif os.path.isfile(args.input):
        # Check if it's an image or video by extension
        ext = os.path.splitext(args.input)[1].lower()
        image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
        if ext in image_exts:
            run_on_image(args.input, model, device)
        else:
            run_on_video(args.input, model, device)
    else:
        print(f"Error: '{args.input}' is not a valid file or 'webcam'.")


if __name__ == "__main__":
    main()
