from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
def cluster_and_find_least_common_color(image_path, num_clusters=5):
    # 打开图像
    image = Image.open(image_path)
    image = image.convert('RGB')  # 确保图像为RGB格式
    
    # 将图像数据转换为numpy数组
    data = np.array(image)
    width, height, _ = data.shape
    
    # 将图像数据重塑为二维数组，每行代表一个像素的RGB值
    pixels = data.reshape(-1, 3)
    
    # 使用K-means聚类
    kmeans = KMeans(n_clusters=num_clusters)
    kmeans.fit(pixels)
    
    # 获取每个像素的聚类标签
    labels = kmeans.labels_
    
    # 获取每个聚类中心的颜色
    cluster_centers = kmeans.cluster_centers_
    
    # 计算每个聚类中像素的数量
    counts = np.bincount(labels)
    
    # 找到像素最少的聚类的索引
    least_common_cluster_index = np.argmin(counts)
    
    # 获取像素最少的聚类中心的颜色
    least_common_color = cluster_centers[least_common_cluster_index]
    
    # 将颜色转换为整数RGB值
    least_common_color = tuple(map(int, least_common_color))
    
    return least_common_color
def colorize(image_path, target_color, output_path):
    # 打开图像
    image = Image.open(image_path).convert('RGBA')
    
    # 将图像转换为numpy数组
    data = np.array(image)
    
    # 获取图像的alpha通道
    alpha = data[:, :, 3]
    
    # 将图像的RGB颜色转换为浮点数
    rgb = data[:, :, :3].astype(float)
    
    # 计算颜色差异
    target_rgb = np.array(target_color).astype(float)
    diff = target_rgb - rgb
    
    # 将颜色向目标颜色靠近
    factor = 0.5  # 控制靠近的程度，0.0到1.0之间
    new_rgb = rgb + diff * factor
    
    # 确保RGB值在0-255之间
    new_rgb = np.clip(new_rgb, 0, 255).astype(np.uint8)
    
    # 组合新的RGB和原来的alpha通道
    new_data = np.dstack((new_rgb, alpha))
    
    # 创建新图像并保存
    new_image = Image.fromarray(new_data, 'RGBA')
    new_image.save(output_path)
def visualize_color(color):
    plt.figure(figsize=(2, 2))
    plt.axis('off')
    plt.imshow([[color]])
    plt.show()

input_image_path = r'result\1721202777\masked_background.png'
num_clusters = 5
least_common_color = cluster_and_find_least_common_color(input_image_path, num_clusters)
print(f'Least common cluster color: {least_common_color}')
# 可视化最少像素聚类的颜色
visualize_color(least_common_color)
# 使用示例
input_image_path = r'result\1721202777\masked_foreground.png'
output_image_path = 'output.png'
target_color = least_common_color  # 目标颜色，红色
colorize(input_image_path, target_color, output_image_path)