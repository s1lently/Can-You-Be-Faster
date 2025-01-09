import numpy as np
import time
import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll
import cv2
from ultralytics import YOLO
import torch
from win32api import GetAsyncKeyState
from win32con import VK_CAPITAL, VK_INSERT, VK_XBUTTON1  # 使用Caps Lock作为切换键
from math import sqrt

def find_cs2_window():
    """查找CS2窗口"""
    hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
    if not hwnd:
        return None
    
    # 获取窗口客户区位置
    rect = win32gui.GetClientRect(hwnd)
    pos = win32gui.ClientToScreen(hwnd, (0, 0))
    
    return {
        "hwnd": hwnd,
        "left": pos[0],
        "top": pos[1],
        "width": rect[2],
        "height": rect[3]
    }

def grab_window(region):
    """使用win32gui截图"""
    hwnd = region["hwnd"]
    width = region["width"]
    height = region["height"]
    
    # 创建设备上下文
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    
    # 创建位图对象
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)
    
    # 复制窗口内容到位图
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
    
    # 获取位图数据
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    
    # 转换为numpy数组
    img = np.frombuffer(bmpstr, dtype=np.uint8)
    img.shape = (height, width, 4)
    
    # 清理资源
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    
    return img

def get_center_region(img, width=200, height=150):
    """获取图像中心区域"""
    h, w = img.shape[:2]
    x = w // 2 - width // 2
    y = h // 2 - height // 2
    return img[y:y+height, x:x+width], (x, y)

def move_mouse(dx, dy):
    """相对移动鼠标"""
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)

def is_scoped(img):
    """检测是否开镜（通过检测边缘区域的亮度）"""
    h, w = img.shape[:2]
    # 检查四个角的区域
    regions = [
        img[0:50, 0:50],          # 左上
        img[0:50, w-50:w],        # 右上
        img[h-50:h, 0:50],        # 左下
        img[h-50:h, w-50:w]       # 右下
    ]
    # 计算平均亮度
    avg_brightness = np.mean([np.mean(region) for region in regions])
    return avg_brightness < 50  # 如果亮度小于50认为是开镜状态

def is_box_circle_overlap(box, circle_center, radius, force_mode=False):
    """检测框的上1/4部分是否与圆形区域重叠"""
    # 获取框的坐标
    x1, y1, x2, y2 = box
    
    # 计算框的宽度和高度
    width = x2 - x1
    height = y2 - y1
    
    # 如果高度不大于宽度的1.5倍，返回False
    if height <= width * 1.5:
        return False
    
    # 在死手模式下，所有检测到的目标都在范围内
    if force_mode:
        return True
    
    # 只取上1/4部分
    y2 = y1 + height/4
    
    # 计算框的中心点
    box_center = np.array([(x1 + x2)/2, (y1 + y2)/2])
    circle_center = np.array(circle_center)
    
    # 计算框的半宽和半高
    half_width = (x2 - x1) / 2
    half_height = (y2 - y1) / 2
    
    # 计算圆心到框中心的距离
    dx = abs(circle_center[0] - box_center[0])
    dy = abs(circle_center[1] - box_center[1])
    
    # 如果圆心在框外，计算到框边缘的最短距离
    if dx > half_width:
        dx = dx - half_width
    else:
        dx = 0
        
    if dy > half_height:
        dy = dy - half_height
    else:
        dy = 0
    
    # 如果最短距离小于圆的半径，则重叠
    return (dx * dx + dy * dy) <= (radius * radius)

def draw_detections(img, results, circle_center, threshold_radius, force_mode=False, color=(0, 255, 0)):
    """只绘制人物检测框并返回最近目标的头部位置"""
    target_pos = None
    min_dist = float('inf')
    img_center = np.array([img.shape[1]/2, img.shape[0]/2])
    
    # 获取头部偏移值
    head_offset = cv2.getTrackbarPos('Head Offset', 'Controls')
    
    for box in results[0].boxes:
        # 只处理人物类别(class 0)
        if box.cls.cpu().numpy()[0] == 0:
            # 获取坐标
            x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]
            
            # 计算框的宽度和高度
            width = x2 - x1
            height = y2 - y1
            
            # 只处理竖直框（高度大于宽度）
            if height > width:
                # 检查框的上1/4部分是否与圆重叠
                if is_box_circle_overlap([x1, y1, x2, y2], circle_center, threshold_radius, force_mode):
                    # 计算头部位置（框顶部往下head_offset像素）
                    head_x = (x1 + x2) / 2
                    head_y = y1 + head_offset
                    head_pos = np.array([head_x, head_y])
                    
                    # 计算到中心点的距离
                    dist = np.linalg.norm(head_pos - img_center)
                    
                    # 如果这个目标更近，更新目标位置
                    if dist < min_dist:
                        min_dist = dist
                        target_pos = head_pos
                
                # 绘制完整矩形框
                cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                # 绘制上1/4部分的框（用不同颜色）
                cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y1 + height/4)), (0, 0, 255), 1)
                # 绘制头部位置
                cv2.circle(img, (int((x1+x2)/2), int(y1+head_offset)), 2, (0, 0, 255), -1)
                # 显示置信度
                conf = float(box.conf.cpu().numpy()[0])
                cv2.putText(img, f"{conf:.2f}", (int(x1), int(y1)-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
    return img, target_pos

def create_control_window():
    """创建控制窗口和滑动条"""
    cv2.namedWindow('Controls')
    # 创建滑动条
    cv2.createTrackbar('Aim Radius', 'Controls', 30, 100, lambda x: None)  # 默认30，最大100
    cv2.createTrackbar('Min Confidence', 'Controls', 70, 100, lambda x: None)  # 默认0.70，最大1.0
    # 创建模式开关（0: 半径模式, 1: 死守模式）
    cv2.createTrackbar('Mode', 'Controls', 1, 1, lambda x: None)  # 默认死守模式
    # 创建Mouse4需求开关（0: 不需要, 1: 需要）
    cv2.createTrackbar('Need Mouse4', 'Controls', 0, 1, lambda x: None)  # 默认不需要Mouse4
    # 创建按键状态显示（0: 关闭, 1: 开启）
    cv2.createTrackbar('Key Active', 'Controls', 0, 1, lambda x: None)  # 默认关闭
    # 创建射击频率控制
    cv2.createTrackbar('Max Fire Rate', 'Controls', 10, 200, lambda x: None)  # 默认0.10秒 (10*0.01)
    cv2.createTrackbar('Min ReShot Rate', 'Controls', 10, 200, lambda x: None)  # 默认0.10秒 (10*0.01)
    # 创建灵敏度控制
    cv2.createTrackbar('Mouse Scale', 'Controls', 265, 1000, lambda x: None)  # 默认2.65 (265*0.01)
    # 创建自动灵敏度开关
    cv2.createTrackbar('Auto Scale', 'Controls', 1, 1, lambda x: None)  # 默认开启
    # 创建攻击位置控制
    cv2.createTrackbar('Head Offset', 'Controls', 7, 20, lambda x: None)  # 默认7像素
    # 创建自动头部偏移开关
    cv2.createTrackbar('Auto Head', 'Controls', 1, 1, lambda x: None)  # 默认开启

# 检查CUDA
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"使用设备: {device}")
if device == 'cuda':
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# 加载YOLO模型
model = YOLO('yolov8s.pt')
model.to(device)

# 查找CS2窗口
region = find_cs2_window()
if not region:
    print("未找到CS2窗口!")
    exit()

print(f"找到CS2窗口: {region['width']}x{region['height']}")
print(f"窗口位置: ({region['left']}, {region['top']})")

# FPS计算变量
fps_array = []
last_time = time.perf_counter()

print("开始检测...")

# 在主循环之前创建控制窗口
create_control_window()

# 在主循环之前初始化状态
force_mode = True  # 初始为死守模式
key_active = False  # 按键激活状态
caps_pressed = False  # Caps Lock状态
ins_pressed = False  # INS状态
require_mouse4 = True  # 是否需要按下mouse4才开锁
last_shot_time = 0  # 上次开枪时间
last_target_pos = None  # 上次目标位置

def move_mouse_and_shoot(dx, dy, target_pos):
    """移动鼠标并在移动距离较大时自动开枪"""
    global last_shot_time, last_target_pos
    current_time = time.time()
    
    # 获取射击频率设置（将滑动条值转换为秒）
    max_fire_rate = cv2.getTrackbarPos('Max Fire Rate', 'Controls') * 0.01  # 转换为秒
    min_reshot_rate = cv2.getTrackbarPos('Min ReShot Rate', 'Controls') * 0.01  # 转换为秒
    
    # 计算移动距离
    distance = sqrt(dx*dx + dy*dy)
    
    # 执行鼠标移动
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
    
    # 如果移动距离大于阈值（10像素），则立即开枪
    if distance > 10:
        if current_time - last_shot_time > max_fire_rate:
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            last_shot_time = current_time
            last_target_pos = target_pos
    # 如果准心已经在目标头部附近（小范围移动）
    elif distance <= 5:  # 如果移动距离很小，说明准心基本在目标头部
        # 如果是新目标或者距离上次开枪超过设定时间
        if (last_target_pos is None or 
            current_time - last_shot_time > min_reshot_rate):
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            last_shot_time = current_time
            last_target_pos = target_pos
    # 如果准心偏离了当前目标，重置上次目标位置
    elif distance > 5:
        last_target_pos = None

try:
    while True:
        # 检测Caps Lock状态变化（切换模式）
        if GetAsyncKeyState(VK_CAPITAL) & 0x8000:
            if not caps_pressed:
                force_mode = not force_mode
                cv2.setTrackbarPos('Mode', 'Controls', 1 if force_mode else 0)
                caps_pressed = True
        else:
            caps_pressed = False
        
        # 检测INS状态变化（切换是否需要mouse4）
        if GetAsyncKeyState(VK_INSERT) & 0x8000:
            if not ins_pressed:
                require_mouse4 = not require_mouse4
                cv2.setTrackbarPos('Need Mouse4', 'Controls', 1 if require_mouse4 else 0)
                ins_pressed = True
        else:
            ins_pressed = False
        
        # 从控制窗口获取Mouse4需求状态
        require_mouse4 = cv2.getTrackbarPos('Need Mouse4', 'Controls') == 1
        
        # 检测Mouse4状态（按键模式）
        if GetAsyncKeyState(VK_XBUTTON1) & 0x8000:
            key_active = True
            cv2.setTrackbarPos('Key Active', 'Controls', 1)
        else:
            key_active = False
            cv2.setTrackbarPos('Key Active', 'Controls', 0)
        
        # 根据require_mouse4的状态决定是否激活
        aim_active = key_active if require_mouse4 else True
        
        # 截图
        screen = grab_window(region)
        screen_bgr = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
        
        # 获取滑动条的值
        aim_radius = cv2.getTrackbarPos('Aim Radius', 'Controls')
        min_conf = cv2.getTrackbarPos('Min Confidence', 'Controls') / 100.0  # 转换到0-1范围
        
        # 检测是否开镜
        scoped = is_scoped(screen_bgr)
        # 根据开镜状态设置阈值半径
        threshold_radius = aim_radius * 2 if scoped else aim_radius
        
        # 自动调节灵敏度
        auto_scale = cv2.getTrackbarPos('Auto Scale', 'Controls') == 1
        if auto_scale:
            if scoped:
                cv2.setTrackbarPos('Mouse Scale', 'Controls', 220)  # 开镜时设置为2.20
            else:
                cv2.setTrackbarPos('Mouse Scale', 'Controls', 265)  # 未开镜时设置为2.65
        
        # 自动调节头部偏移
        auto_head = cv2.getTrackbarPos('Auto Head', 'Controls') == 1
        if auto_head:
            if scoped:
                cv2.setTrackbarPos('Head Offset', 'Controls', 12)  # 开镜时设置为12
            else:
                cv2.setTrackbarPos('Head Offset', 'Controls', 6)   # 未开镜时设置为6
        
        # 获取中心区域（改为600x300）
        center_region, (cx, cy) = get_center_region(screen_bgr, 600, 300)
        
        # YOLO检测
        results = model(center_region, verbose=False, conf=min_conf)
        
        # 在原始图像上绘制中心区域框和阈值圆
        cv2.rectangle(screen_bgr, (cx, cy), (cx+600, cy+300), (0, 255, 0), 2)
        circle_center = (cx + 300, cy + 150)  # 检测区域中心
        cv2.circle(screen_bgr, circle_center, threshold_radius, (255, 0, 0), 1)
        
        # 如果检测到人物，在中心区域内绘制并移动鼠标
        if len(results[0].boxes) > 0:
            center_with_boxes = center_region.copy()
            center_with_boxes, target_pos = draw_detections(center_with_boxes, results, 
                                                          (300, 150), threshold_radius, force_mode)
            screen_bgr[cy:cy+300, cx:cx+600] = center_with_boxes
            
            # 只在激活状态下移动鼠标
            if target_pos is not None and aim_active:
                center_x = 300
                center_y = 150
                offset_x = target_pos[0] - center_x
                offset_y = target_pos[1] - center_y
                
                # 获取灵敏度设置
                scale = cv2.getTrackbarPos('Mouse Scale', 'Controls') * 0.01
                dx = int(offset_x * scale)
                dy = int(offset_y * scale)
                move_mouse_and_shoot(dx, dy, target_pos)
        
        # 获取当前设置值用于显示
        scale = cv2.getTrackbarPos('Mouse Scale', 'Controls') * 0.01
        max_fire_rate = cv2.getTrackbarPos('Max Fire Rate', 'Controls') * 0.01
        min_reshot_rate = cv2.getTrackbarPos('Min ReShot Rate', 'Controls') * 0.01
        head_offset = cv2.getTrackbarPos('Head Offset', 'Controls')
        
        # 显示当前模式和状态
        mode_text = "Force Mode" if force_mode else "Radius Mode"
        mouse4_text = "Need Mouse4" if require_mouse4 else "Always Active"
        key_text = "Key Active" if aim_active else "Key Inactive"
        cv2.putText(screen_bgr, f"{mode_text} | {mouse4_text} | {key_text}", (10, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 显示当前设置
        cv2.putText(screen_bgr, f"Radius: {threshold_radius}", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(screen_bgr, f"Conf: {min_conf:.2f}", (10, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(screen_bgr, f"Scale: {scale:.2f}", (10, 180), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(screen_bgr, f"Auto Scale: {'On' if auto_scale else 'Off'}", (10, 210), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(screen_bgr, f"Head Offset: {head_offset}px", (10, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(screen_bgr, f"Auto Head: {'On' if auto_head else 'Off'}", (10, 270), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(screen_bgr, f"Fire Rate: {max_fire_rate:.2f}/{min_reshot_rate:.2f}", (10, 300), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 计算和显示FPS
        current_time = time.perf_counter()
        fps = 1.0 / (current_time - last_time)
        last_time = current_time
        
        fps_array.append(fps)
        if len(fps_array) > 30:
            fps_array.pop(0)
        avg_fps = sum(fps_array) / len(fps_array)
        
        cv2.putText(screen_bgr, f"FPS: {avg_fps:.1f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 显示结果
        cv2.imshow("YOLOv8 Detection", screen_bgr)
        
        # 按'q'退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
except KeyboardInterrupt:
    pass

cv2.destroyAllWindows() 