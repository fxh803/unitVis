from PIL import Image

def mask2mask(path1,path2):
    # 打开PNG图像文件
    image = Image.open(path1)

    # 确保图像具有四通道（RGBA）
    image = image.convert("RGBA")

    # 获取图像的宽度和高度
    width, height = image.size

    # 遍历图像的每个像素
    for x in range(width):
        for y in range(height):
            # 获取像素的RGBA值
            r, g, b, a = image.getpixel((x, y))

            # 检查是否为黑色或白色
            if (r, g, b) == (0, 0, 0):  # 黑色
                new_color = (255, 255, 255, a)  # 白色
            elif (r, g, b) == (255, 255, 255):  # 白色
                new_color = (0, 0, 0, a)  # 黑色
            else:
                new_color = (r, g, b, a)  # 其他颜色保持不变

            # 将像素设置为新的颜色
            image.putpixel((x, y), new_color)

    # 保存修改后的图像
    image.save(path2)

