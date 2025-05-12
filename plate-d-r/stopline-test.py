import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont  # 新增PIL相关导入


# ================== 中文渲染函数 ==================
def cv2_puttext_chinese(img, text, position, color, font_size=20):
    """
    使用PIL在OpenCV图像上绘制中文
    参数：
    - img: OpenCV图像（BGR格式）
    - text: 要绘制的中文文本
    - position: (x, y) 文本起始坐标（左上角）
    - color: (B, G, R) 颜色值
    - font_size: 字体大小
    """
    # 转换颜色格式为RGB元组
    color_rgb = tuple(color[::-1])

    # 将OpenCV图像转换为PIL格式
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    # 加载中文字体（需要确保字体文件存在）
    try:
        font = ImageFont.truetype("simhei.ttf", font_size)  # 字体文件需放在项目目录
    except IOError:
        font = ImageFont.load_default()
        print("警告：未找到中文字体，已使用默认字体")

    # 绘制文本
    draw.text(position, text, font=font, fill=color_rgb)

    # 转换回OpenCV格式
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ================== 主程序 ==================
stop_lines = []  # 存储两条停止线坐标
current_line = []  # 临时存储当前绘制的线段


def mouse_callback(event, x, y, flags, param):
    global current_line, stop_lines
    if event == cv2.EVENT_LBUTTONDOWN:
        current_line.append((x, y))
        print(f"记录坐标点 ({x}, {y})")

        if len(current_line) == 2:
            stop_lines.append(current_line.copy())
            current_line.clear()
            print(f"停止线已添加：{stop_lines[-1]}")


def main():
    global stop_lines, current_line

    # 读取视频文件
    cap = cv2.VideoCapture('images/testP.mp4')
    if not cap.isOpened():
        print("错误：无法打开视频文件")
        return

    ret, frame = cap.read()
    if not ret:
        print("错误：无法读取视频帧")
        cap.release()
        return

    # 创建交互窗口
    cv2.namedWindow('line-drawing')
    cv2.setMouseCallback('line-drawing', mouse_callback)

    # 用户交互标注界面
    print("请依次标注两条停止线（每条线需要点击两个点）")
    while True:
        display_frame = frame.copy()

        # 绘制已完成的停止线
        for i, line in enumerate(stop_lines):
            color = (0, 0, 255) if i == 0 else (0, 128, 255)  # 红和浅红
            cv2.line(display_frame, line[0], line[1], color, 2)

        # 绘制当前正在标注的点
        if len(current_line) > 0:
            cv2.circle(display_frame, current_line[0], 5, (0, 255, 0), -1)

        # 添加中文状态提示
        status_text = f"需要标注 {2 - len(stop_lines)} 条停止线" if len(stop_lines) < 2 else "按回车继续"
        display_frame = cv2_puttext_chinese(
            display_frame,
            status_text,
            (10, 30),  # 文字位置（左上角开始）
            (255, 255, 255),  # 白色文字
            20  # 字体大小
        )

        cv2.imshow('line-drawing', display_frame)

        # 键盘操作检测
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # 回车键
            if len(stop_lines) == 2:
                break
            else:
                print("请先完成两条停止线的标注")
        elif key == 27:  # ESC键
            cap.release()
            cv2.destroyAllWindows()
            return

    cv2.destroyAllWindows()

    # 输出坐标信息
    print("\n最终停止线坐标：")
    for i, line in enumerate(stop_lines):
        print(f"停止线 {i + 1}: ({line[0][0]}, {line[0][1]}) - ({line[1][0]}, {line[1][1]})")

    # 配置视频输出参数
    frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('output_with_lines.mp4', fourcc, fps, frame_size)

    # 处理视频流
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 绘制停止线
        for i, line in enumerate(stop_lines):
            color = (0, 0, 255) if i == 0 else (0, 128, 255)
            cv2.line(frame, line[0], line[1], color, 2)

        # 添加处理进度提示
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        progress_text = f"处理进度：{current_frame}/{total_frames}"
        frame = cv2_puttext_chinese(frame, progress_text, (10, 60), (255, 255, 255), 20)

        out.write(frame)

        # 实时预览（按ESC可跳过）
        cv2.imshow('处理中', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # 释放资源
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"\n处理完成！输出视频已保存至：output_with_lines.mp4")


if __name__ == "__main__":
    main()