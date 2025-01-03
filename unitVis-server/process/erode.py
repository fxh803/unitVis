import cv2
import numpy as np
from PIL import Image
def erode(image):
    # 将 PIL 图像转换为 OpenCV 图像
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # 提取黑色区域
    black_mask = cv2.inRange(image, (0, 0, 0), (50, 50, 50))  # 定义黑色的阈值范围
    # 设置腐蚀核
    kernel = np.ones((5, 5), np.uint8)

    # 对黑色区域进行腐蚀操作
    eroded_black_mask = cv2.erode(black_mask, kernel, iterations=4)
  
    # 将腐蚀后的黑色区域应用到原始图像
    result = image.copy()
    result[eroded_black_mask != 255] = (255, 255, 255)
    # 将 OpenCV 图像转换为 PIL 图像
    result_pil = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    # 将 RGB 图像转换为 RGBA 格式
    result_pil = result_pil.convert('RGBA')
    return result_pil

