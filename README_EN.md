# Can You Be Faster?

A CS2 detection assistant based on YOLOv8 and OpenCV, developed in Python. For research and learning purposes only.

## 🚀 Key Features

- Real-time object detection and tracking
- Adaptive aim assistance
- Multiple mode switching
- Highly configurable parameters
- Scope detection support
- GPU acceleration (CUDA)
- Auto-adjustment for scoped/unscoped states
- Precise parameter control (0.01 precision)

## 🛠️ Core Features

- **Dual Mode System**
  - Radius Mode: Only aim at targets within specified radius
  - Force Mode: Aim at all targets in detection area (Default)

- **Smart Control**
  - Mouse4 button control (Optional)
  - CapsLock for mode switching
  - Insert for toggle always-on state

- **Auto Parameter Adjustment**
  - Auto Scale
    - Scoped: 2.20
    - Unscoped: 2.65
  - Auto Head Offset
    - Scoped: 12px
    - Unscoped: 6px

- **Precise Parameter Control**
  - Sensitivity: 0.00-10.00
  - Fire Rate: 0.00-2.00s
  - Confidence: 0.00-1.00
  - Head Offset: 0-20px

## 📋 System Requirements

- Windows 10/11
- Python 3.8+
- NVIDIA GPU (Recommended)
- CS2 Game

## 📦 Installation

1. Clone repository:
```bash
git clone https://github.com/s1lently/你可以再快一点吗.git
cd 你可以再快一点吗
```

2. Create and activate Conda environment:
```bash
conda create -n yolo-cs2 python=3.8
conda activate yolo-cs2
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download YOLOv8 model:
```bash
# Will be downloaded automatically, or manually download from:
# https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt
```

## 🎮 Usage

1. Start program:
```bash
python screen_detect.py
```

2. Hotkeys:
- `CapsLock`: Switch between Radius/Force mode
- `Insert`: Toggle Mouse4 requirement
- `Mouse4`: Hold to activate assistant (Optional)

3. Control Panel Parameters:
- **Aim Radius**: Aim radius (doubles when scoped)
- **Min Confidence**: Minimum confidence (Default: 0.70)
- **Mode**: Mode switch (Default: Force Mode)
- **Need Mouse4**: Mouse4 requirement (Default: Off)
- **Mouse Scale**: Mouse sensitivity (0.01 precision)
- **Auto Scale**: Auto sensitivity adjustment (Default: On)
  - Scoped: 2.20
  - Unscoped: 2.65
- **Head Offset**: Head offset pixels
- **Auto Head**: Auto head offset (Default: On)
  - Scoped: 12px
  - Unscoped: 6px
- **Max Fire Rate**: Maximum fire rate (Default: 0.10s)
- **Min ReShot Rate**: Minimum re-shot rate (Default: 0.10s)

4. Display Information:
- FPS
- Current mode status
- Mouse4 status
- All parameter real-time values

## ⚠️ Disclaimer

This project is for learning and research purposes only. Any consequences of using this project are the sole responsibility of the user.

## 📄 License

MIT License 