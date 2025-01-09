# YOLOv8 CS2 目标检测助手

基于 YOLOv8 和 OpenCV 的 CS2 目标检测项目，使用 Python 开发。该项目仅用于研究和学习目的。

## 🚀 主要特性

- 实时目标检测和追踪
- 自适应瞄准辅助
- 多种模式切换
- 高度可配置的参数控制
- 支持开镜检测
- GPU 加速支持 (CUDA)
- 自动调节开镜/非开镜参数
- 精确的参数控制（支持0.01精度）

## 🛠️ 核心功能

- **双模式系统**
  - 半径模式：只在指定半径内瞄准目标
  - 死守模式：瞄准检测区域内的所有目标（默认）

- **智能控制**
  - Mouse4 按键控制（可选）
  - CapsLock 切换模式
  - Insert 切换常驻状态

- **自动参数调节**
  - 自动灵敏度调节（Auto Scale）
    - 开镜：2.20
    - 未开镜：2.65
  - 自动头部偏移（Auto Head）
    - 开镜：12像素
    - 未开镜：6像素

- **精确参数控制**
  - 灵敏度：0.00-10.00
  - 射击频率：0.00-2.00秒
  - 置信度：0.00-1.00
  - 头部偏移：0-20像素

## 📋 系统要求

- Windows 10/11
- Python 3.8+
- NVIDIA GPU (推荐)
- CS2 游戏

## 📦 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/s1lently/cs2_yolo_proj.git
cd cs2_yolo_proj
```

2. 创建并激活 Conda 环境：
```bash
conda create -n yolo-cs2 python=3.8
conda activate yolo-cs2
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 下载 YOLOv8 模型：
```bash
# 程序会自动下载，也可以手动下载放在同目录
# https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt
```

## 🎮 使用说明

1. 启动程序：
```bash
python screen_detect.py
```

2. 快捷键控制：
- `CapsLock`: 切换半径/死守模式
- `Insert`: 切换是否需要 Mouse4 激活
- `Mouse4`: 按住启动辅助（可选）

3. 控制面板参数：
- **Aim Radius**: 瞄准范围半径（开镜时自动翻倍）
- **Min Confidence**: 最低置信度（默认0.70）
- **Mode**: 模式切换（默认死守模式）
- **Need Mouse4**: 是否需要按住Mouse4（默认关闭）
- **Mouse Scale**: 鼠标灵敏度（支持0.01精度）
- **Auto Scale**: 自动灵敏度调节（默认开启）
  - 开镜: 2.20
  - 未开镜: 2.65
- **Head Offset**: 头部偏移像素
- **Auto Head**: 自动头部偏移（默认开启）
  - 开镜: 12px
  - 未开镜: 6px
- **Max Fire Rate**: 最高开火频率（默认0.10秒）
- **Min ReShot Rate**: 最低再次射击频率（默认0.10秒）

4. 显示信息：
- FPS
- 当前模式状态
- Mouse4 状态
- 所有参数实时值

## ⚠️ 免责声明

本项目仅供学习和研究目的使用。使用本项目产生的任何后果由使用者自行承担。

## 📄 许可证

MIT License 