from PIL import Image, ImageOps

def crop_to_square(image,padding = 100):
    # 转换为RGBA模式
    image = image.convert("RGBA")
    
    # 获取图像的尺寸
    width, height = image.size
  
    # 创建一个新的图像，用于标识黑色区域
    black_mask = Image.new("L", (width, height), 0)
    
    # 遍历图像像素，标识非黑色区域
    for y in range(height):
        for x in range(width):
            r, g, b, a = image.getpixel((x, y))
            if (r == 0 and g == 0 and b == 0):  # 非黑色
                black_mask.putpixel((x, y), 255)
        
        # 获取非黑色区域的边界框
        bbox = black_mask.getbbox()
    
    if bbox:
        # 计算中心点
        center_x = (bbox[2] + bbox[0]) // 2
        center_y = (bbox[3] + bbox[1]) // 2
        size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        
        # 计算裁剪框的左上角和右下角坐标
        left = center_x - size // 2
        top = center_y - size // 2
        right = center_x + size // 2
        bottom = center_y + size // 2

        # 裁剪成正方形
        square_image = image.crop((left, top, right, bottom))
        # 在裁剪后的图像上添加填充
        padded_image = ImageOps.expand(square_image, border=padding, fill=(255, 255, 255, 255))  
           
    else:

        padded_image = image
    
    return padded_image