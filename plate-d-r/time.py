import cv2
from ultralytics import YOLO
from datetime import datetime
import hyperlpr3 as lpr3

# 初始化模型
vehicle_model = YOLO('yolov8s.pt')  # 加载车辆检测模型
catcher = lpr3.LicensePlateCatcher()  # 初始化HyperLPR3

# 停止线配置
STOP_LINE = [(83, 168), (357, 160)]

# 车辆跟踪管理
vehicle_history = {}


def cross(p1, p2, point):
    """计算叉积判断车辆与停止线位置关系"""
    return (p2[0] - p1[0]) * (point[1] - p1[1]) - (p2[1] - p1[1]) * (point[0] - p1[0])


def safe_crop(frame, center_x, center_y, width, height):
    """安全截取车辆区域"""
    h, w = frame.shape[:2]
    y1 = max(0, int(center_y - height / 2))
    y2 = min(h, int(center_y + height / 2))
    x1 = max(0, int(center_x - width / 2))
    x2 = min(w, int(center_x + width / 2))
    return frame[y1:y2, x1:x2] if y2 > y1 and x2 > x1 else None


def recognize_plate(roi):
    """使用HyperLPR3识别车牌"""
    if roi is None or roi.size == 0:
        return None
    results = catcher(roi)
    return max(results, key=lambda x: x[1])[0] if results else None


# 视频处理流程
cap = cv2.VideoCapture('images/testP.mp4')
with open('output.txt', 'w') as log_file:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # 车辆检测与跟踪
        results = vehicle_model.track(frame, persist=True, tracker="bytetrack.yaml")
        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist() if results[0].boxes.id else []
        classes = results[0].boxes.cls.int().cpu().tolist()

        for box, track_id, cls in zip(boxes, track_ids, classes):
            if cls == 2:  # 过滤汽车类别（COCO数据集）
                x, y, w, h = box.tolist()
                current_sign = cross(STOP_LINE[0], STOP_LINE[1], (x, y))

                # 初始化车辆记录
                if track_id not in vehicle_history:
                    vehicle_history[track_id] = {
                        'last_sign': current_sign,
                        'recorded': False
                    }
                    continue

                # 检测过线行为
                if vehicle_history[track_id]['last_sign'] * current_sign < 0 \
                        and not vehicle_history[track_id]['recorded']:

                    # 截取车辆区域识别车牌
                    vehicle_roi = safe_crop(frame, x, y, w, h)
                    plate_number = recognize_plate(vehicle_roi)

                    if plate_number:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_file.write(f"{plate_number} {timestamp}\n")
                        vehicle_history[track_id]['recorded'] = True

                # 更新位置状态
                vehicle_history[track_id]['last_sign'] = current_sign

cap.release()