from PIL import Image
def square(original_img):
    # 获取原始图片的宽度和高度
    width, height = original_img.size

    # 确定较长的一边作为正方形的边长
    side_length = max(width, height)

    # 创建白色正方形底图
    square_bg = Image.new('RGB', (side_length, side_length), 'white')

    # 计算将原始图片居中贴在正方形底图中的位置
    x_offset = (side_length - width) // 2
    y_offset = (side_length - height) // 2

    # 将原始图片贴在正方形底图中心
    square_bg.paste(original_img, (x_offset, y_offset))

    return square_bg