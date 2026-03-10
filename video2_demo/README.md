# Video 2 — DeepLabV3+ Segmentation Demo

Runs DeepLabV3+ semantic segmentation (pre-trained on COCO) on webcam or images.
COCO includes road/sidewalk/floor classes — same drivable-area concept as our RC car project.

## Setup
```bash
conda env create -f environment.yml
conda activate cvProject
```

## Run on webcam
```bash
python segmentation_demo.py --input webcam
```

## Run on an image
```bash
python segmentation_demo.py --input sample_images/hallway.jpg
```

## Notes
- First run downloads the model weights (~40MB). Needs internet.
- If your USB camera isn't detected, try: `--camera-id 2` or `--camera-id 1` at the end of the python command. 
- Press `q` to quit, `s` to save a screenshot.
