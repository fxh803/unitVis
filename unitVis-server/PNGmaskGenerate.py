import cv2
import numpy as np
from PIL import Image

def maskGenerate(input_path, output_path,padding = 1):

    # 读取PNG图像
    image = Image.open(input_path)

    # 获取图像的透明通道（如果有的话）
    alpha = image.getchannel('A')

    # 创建一个新的掩码，将透明度为0的位置变为白色
    mask_data = [(255 if p == 0 else 0) for p in alpha.getdata()]
    mask = Image.new('L', image.size)
    mask.putdata(mask_data)
    # 转换 PIL Image 为 OpenCV 格式
    mask_cv = np.array(mask)
    mask_gray = cv2.cvtColor(mask_cv, cv2.COLOR_GRAY2BGR)

    # 定义膨胀核大小和形状
    kernel = np.ones((padding, padding), np.uint8)  # 可调整核的大小
    erode_mask = cv2.erode(mask_gray, kernel, iterations=2)

    # 将膨胀后的图像转换回 PIL Image 格式
    erode_mask = Image.fromarray(erode_mask)

    # 保存掩码
    erode_mask.save(output_path)