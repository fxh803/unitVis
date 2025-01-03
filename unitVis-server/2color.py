from PIL import Image

# 打开图片并转换为灰度图
image = Image.open('OIP.png').convert('L')

# 定义阈值化函数
threshold = 127
image = image.point(lambda p: 255 if p >= threshold else 0)

# 将图像转换为 RGB 模式
image_rgb = image.convert('RGB')

# 添加透明度通道（A 通道）并设置透明度为 255
image_rgba = image_rgb.convert('RGBA')
pixels = image_rgba.load()

# 设置所有像素的 Alpha 通道为 255（完全不透明）
for y in range(image_rgba.height):
    for x in range(image_rgba.width):
        r, g, b, _ = pixels[x, y]  # 获取当前像素的 RGB 值（忽略 A 通道）
        pixels[x, y] = (r, g, b, 255)  # 设置 A 通道为 255

# 保存结果
image_rgba.save('OIP.png')
