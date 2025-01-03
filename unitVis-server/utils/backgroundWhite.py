from PIL import Image
def backgroundWhite(mask):

    # 将 alpha 通道为 0 的像素变为白色
    mask_data = mask.getdata()
    new_data = []
    for pixel in mask_data:
        if pixel[3] == 0:  # 检查 alpha 通道是否为 0
            new_data.append((255, 255, 255, 255))  # 将透明区域变为白色
        else:
            new_data.append(pixel)

    # 创建新的图像对象
    new_mask = Image.new("RGBA", mask.size)
    new_mask.putdata(new_data)
    return new_mask