import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from shapely.geometry import Polygon, MultiPoint,Point
from PIL import Image
import random
def find_extended_polygons(control_points,polygons,color=['orange','purple','yellow']):
    # 寻找包含控制点的多边形
    for i,point in enumerate(control_points):
        
        control_point_polygons = []
        for poly in polygons:
            if poly.contains(Point(point)):
                control_point_polygons.append(poly)
        
        # 横向扩展：寻找质心横坐标接近的多边形
        threshold = 0.1  # 横向距离阈值
        center_control = np.array(control_point_polygons[0].centroid.xy).flatten()  # 控制多边形质心
        extended_polygons = []

        for poly in polygons:
            center_poly = np.array(poly.centroid.xy).flatten()
            if abs(center_poly[0] - center_control[0]) < threshold:
                extended_polygons.append(poly)
        # #控制点所在多边形
        # for poly in control_point_polygons:
        #     x, y = poly.exterior.xy
        #     ax.fill(x, y, alpha=0.5, fc='red', ec='black')

        # 绘制横向扩展的多边形
        for poly in extended_polygons:
            x, y = poly.exterior.xy
            ax.fill(x, y, alpha=0.5, fc=color[i%len(color)], ec='black', label='Extended Polygons')

background = Image.open('./bottle.png').convert('L')
binary_image = np.array(background) < 128
# 1. 生成随机点    
n_points = 200  # 随机点的数量
random_points = []
while  len(random_points) < n_points:
    x = random.randint(0, binary_image.shape[1] - 1)
    y = random.randint(0, binary_image.shape[0] - 1)
    if binary_image[y, x]:
       # 翻转 y 坐标
        y_flipped = binary_image.shape[0] - y - 1
        # 缩放到 [0, 1] 的范围
        x_normalized = x / binary_image.shape[1]
        y_normalized = y_flipped / binary_image.shape[0]
        random_points.append([x_normalized, y_normalized])
random_points = np.array(random_points)
control_points = np.array([[0.5,0.5]])
# 2. 添加四个边界点
boundary_points = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
# points = np.vstack([random_points, boundary_points])  # 合并随机点和边界点

# 3. 进行三角剖分
tri = Delaunay(random_points)
polygons = []
for index,polygon in enumerate(tri.simplices):
    polygon = Polygon([tri.points[i] for i in polygon])
    polygons.append(polygon)
# 4. 可视化
# 绘制结果
fig, ax = plt.subplots(figsize=(8, 8))
# 可视化二值化后的图像
plt.imshow(binary_image, cmap='gray', origin='upper', extent=[0, 1, 0, 1])
plt.triplot(random_points[:, 0], random_points[:, 1], tri.simplices, color='blue', linewidth=0.5)
plt.scatter(random_points[:, 0], random_points[:, 1], color='red', s=10)
find_extended_polygons(control_points,polygons)
plt.gca().set_aspect('equal')
plt.title("Triangulation with Boundary Points")

plt.show()
