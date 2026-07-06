# RC Jetson Testing

Hardware bring-up, motor diagnostics, and data collection for our automated
driving RC car project on the NVIDIA Jetson Orin Nano. These are the scripts we
used to get the motors wired up and turning correctly, collect training images,
and drive the car manually before the autonomous system was ready.

The machine-learning and autonomous driving code lives in the companion repo,
[RCJetsonAutomatedDriving](https://github.com/armanesponda/RCJetsonAutomatedDriving).

## Background

The car uses an L298N dual H-bridge driver controlled by the Jetson's GPIO pins.
The Jetson Orin Nano has no hardware PWM on its GPIO header, so every script here
uses a small software-PWM class (a background thread toggling the pin at 100 Hz)
to control motor speed. Getting the pins to behave as GPIO outputs also required a
device-tree overlay, included here as `motor-gpio.dts`.

## Contents

| File | Purpose |
|---|---|
| `motor-gpio.dts` | Device-tree overlay that configures the 40-pin header pins for motor control |
| `ena_diagnostic.py` | Minimal test that drives the enable pin HIGH with no PWM, to isolate whether a dead motor is a PWM, wiring, or overlay problem |
| `gpio_test.py` | Steps through each motor channel and direction one at a time so you can confirm which wheel responds to which pin |
| `manual_control.py` | Drive the car by keyboard, with per-side speed trim to correct a car that pulls to one side |
| `manual_control_server.py` | Same manual control exposed over a Flask web page with a live camera stream |
| `collect_data.py` | Capture training images to disk, manually or on a timer |
| `collect_data_server.py` | Web-based image capture with a live preview and a capture button |
| `video2_demo/` | Standalone DeepLabV3 segmentation demo (see below) |

## Setup and workflow

The typical order we used to bring the car up:

1. **Apply the device-tree overlay** (`motor-gpio.dts`) so the header pins act as
   GPIO outputs, then reboot.
2. **Run `ena_diagnostic.py`** to confirm a single motor spins at all.
3. **Run `gpio_test.py`** to map each pin to a wheel and direction.
4. **Run `manual_control.py`** to drive the car and tune the left/right speed trim.
5. **Run `collect_data.py`** (or the server version) to gather training images of
   the track for the segmentation model.

Requirements: Python 3.10, `Jetson.GPIO`, `opencv-python`, `numpy`, and `flask`
for the server scripts. `Jetson.GPIO` and the overlay are Jetson-specific; these
scripts are meant to run on the car, not a desktop.

## Pin overview

Motor control uses six GPIO pins in BCM numbering: two enable/PWM pins (one per
motor) and four direction pins (two per motor) driving the L298N inputs. The exact
assignments are defined at the top of each script and in `motor-gpio.dts`. One
early diagnostic (`ena_diagnostic.py`) uses a different enable pin while we were
tracking down a wiring issue; the driving scripts settled on a consistent set.

## video2_demo

A separate, self-contained demo that runs DeepLabV3 semantic segmentation
(pre-trained on Pascal VOC) on a webcam or still image. It highlights the
background/drivable-area class and was used to illustrate the segmentation concept
behind the main project. See `video2_demo/README.md` for setup and usage.
