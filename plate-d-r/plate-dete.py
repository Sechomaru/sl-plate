import cv2
import hyperlpr3 as lpr3
import datetime
# 实例化识别对象
catcher = lpr3.LicensePlateCatcher()

# 打开视频文件
video_path = "images/testP.mp4"
cap = cv2.VideoCapture(video_path)

# 获取视频帧率
fps = cap.get(cv2.CAP_PROP_FPS)

# 创建输出文件
output_path = "license_plates.txt"
with open(output_path, "w", encoding="utf-8") as f:
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 计算当前时间（更精确的方式）
        # current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        current_time = datetime.datetime.now()

        try:
            # 进行车牌识别并处理空结果
            results = catcher(frame)

            # 解析结果结构（根据实际输出调整）
            for plate in results:
                # 新版数据结构可能需要这样访问：
                plate_number = plate[0]  # 车牌号在第一个位置
                confidence = plate[1]  # 置信度在第二个位置
                f.write(f"{current_time}s,{plate_number}\n")
                # f.write(f"{current_time:.2f}s, {plate_number}\n")

        except Exception as e:
            print(f"第 {frame_count} 帧处理出错: {str(e)}")

        # 进度显示优化
        print(f"已处理 {frame_count} 帧 | 最新时间戳: {current_time:.1f}s", end="\r")
        frame_count += 1

cap.release()
print("\n处理完成！结果保存至:", output_path)