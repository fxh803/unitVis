import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely.geometry import Polygon, MultiPoint,Point

def find_extended_polygons(control_points,polygons,color=['orange','purple','yellow']):
    # 寻找包含控制点的多边形
    for i,point in enumerate(control_points):
        print(point)
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
# 生成固定的随机点

# 设置随机种子
# np.random.seed(42)
num_points = 300
ran_points = np.random.rand(num_points, 2)  # 在 [0, 1] 区域生成随机点
control_points = np.array([[0.2,0.2],[0.4,0.4],[0.6,0.6],[0.8,0.8]])
# 泰森多边形
vor = Voronoi(ran_points, furthest_site=False)
# 创建裁剪区域
clip_region = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
# 绘制结果
fig, ax = plt.subplots(figsize=(8, 8))
#绘制原始随机点
# ax.plot(ran_points[:, 0], ran_points[:, 1], 'o', color='black', label='Random Points')
#绘制控制点
ax.plot(control_points[:, 0], control_points[:, 1], 's', color='red', label='Random Points')
# 绘制裁剪区域
x, y = clip_region.exterior.xy
ax.fill(x, y, alpha=0.5, fc='gray', ec='black')
# 裁剪泰森多边形
clipped_polygons = []
poly_centers = []
for index,region in enumerate(vor.regions):
    if not -1 in region and len(region) > 0:
        polygon = Polygon([vor.vertices[i] for i in region])
        clipped = clip_region.intersection(polygon)
        if clipped.geom_type == 'Polygon':
            clipped_polygons.append(clipped)
            center_poly = np.array(clipped.centroid.xy).flatten()
            poly_centers.append(center_poly.tolist())
            
poly_centers = np.array(poly_centers)            

# 绘制泰森多边形
voronoi_plot_2d(vor, ax=ax, show_vertices=False, line_colors='orange', line_width=1.5, line_alpha=0.6)      
#绘制所有质心
ax.plot(poly_centers[:, 0], poly_centers[:, 1], 'o', color='black', label='Random Points' )


find_extended_polygons(control_points,clipped_polygons)    

# # 设置坐标轴范围
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.autoscale_view()
plt.show()