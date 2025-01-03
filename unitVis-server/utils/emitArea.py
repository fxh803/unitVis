import numpy as np
import cv2
def angle(pt1, pt2, pt3 ,pt4):
    # 将点转换为向量
    v1 = np.array(pt1) - np.array(pt2)
    v2 = np.array(pt4) - np.array(pt3)
    
    # 计算两个向量之间的角度余弦值
    cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
    
    # 返回角度（单位为度）
    return np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))
def custom_approxPolyDP(contour, distance_threshold):
    points = contour.squeeze()
    approx_points = [points[0]]  # 初始化逼近后的点集，将第一个点添加到集合中

    for i in range(1, len(points)):
        if np.linalg.norm(points[i] - approx_points[-1]) > distance_threshold:
            # 如果当前点与上一个逼近点的距离大于阈值，则将当前点添加到逼近点集合中
            approx_points.append(points[i])

    return np.array(approx_points)

def emitArea(image):
    # 确保图像的模式为RGBA（如果不是）
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    # 将图像转换为 numpy 数组（OpenCV 处理图像数据）
    image_np = np.array(image)
    # 将图像转换为灰度图
    # 提取 Alpha 通道作为灰度图像
    alpha_channel = image_np[:, :, 3]
    # 查找轮廓
    contours, _ = cv2.findContours(alpha_channel, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # 获取每个轮廓的边界点
    boundary_points_list = [] #分割的轮廓
    points_list = [] #不分割的轮廓
    boundary_index = []#记录分割轮廓从属于完整轮廓的索引
    for index,contour in enumerate(contours):
        flags = [0]
        approx = custom_approxPolyDP(contour, distance_threshold=10)
        # epsilon = 0.001 * cv2.arcLength(contour, True)
        # approx = cv2.approxPolyDP(contour, epsilon, True)
        points = np.array(approx).reshape(-1, 2).tolist()
        points_list.append(points)
        i = 0
        while i < len(points):
            pt1 = points[i-2]
            pt2 = points[i-1]
            pt3 = points[i]
            pt4 = points[(i+1) % len(points)]
            if angle(pt1, pt2, pt3, pt4) < 120 :
                flags.append(i)
                i += 2
            else:
                i += 1
        # 切割并添加到 boundary_points_list
        for i, flag in enumerate(flags):
            if i == len(flags)-1:
                end_idx = len(points)
            else:
                end_idx = flags[i+1]
            start_idx = flags[i]
            if len(points[start_idx:end_idx])>=3:
                boundary_points_list.append(points[start_idx:end_idx])
                boundary_index.append(index)
    
    copy_img = image_np.copy()
    for points in points_list:
        for i,point in enumerate(points):
            x, y = point
            cv2.circle(copy_img, (x, y),6, (255,0,0,255), -1)  # 绘制一个像素大小的圆点
            cv2.putText(copy_img, f'{i}', (x+10, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0,255), 1, cv2.LINE_AA) 
    
    cv2.imwrite('points_list.png', copy_img)

    copy_img2 = image_np.copy()
    colors = [(255,0,255,255),(255,255,0,255),(0,255,255,255),(255,0,0,255),(0,255,0,255),(0,0,255,255)]
    for i, boundary_points in enumerate(boundary_points_list):
        for boundary_point in boundary_points:
            x, y = boundary_point
            cv2.circle(copy_img2, (x, y),6, colors[i%6], -1)  # 绘制一个像素大小的圆点
    
    cv2.imwrite('boundary_points_list.png', copy_img2)
    return boundary_points_list,points_list,boundary_index