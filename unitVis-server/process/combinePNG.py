from PIL import Image
import cv2
import numpy as np
import cv2
import numpy as np

def add_alpha_channel(image):
   
    image_rgb = image[:, :, :3]
    image_alpha = np.ones((image.shape[0], image.shape[1], 1), dtype=np.uint8) * 255
    return np.concatenate([image_rgb, image_alpha], axis=2)

def remove_background_with_transparency(input_path, output_path, target_color=(255, 255, 255)):
   
    # 读取PNG图像，确保保留 Alpha 通道信息
    image = cv2.imread(input_path)
    
    # 为图像添加一个 Alpha 通道
    image = add_alpha_channel(image)

    # 将RGB颜色转换为BGR颜色
    target_color_bgr = target_color[::-1]

    # 创建掩膜，将目标颜色区域设置为白色（255），其他区域设置为黑色（0）
    mask = cv2.inRange(image[:, :, :3], target_color_bgr, target_color_bgr)
    cv2.imwrite('text1.png',mask)
    # 定义腐蚀核和膨胀核
    kernel = np.ones((2, 2), np.uint8)
    # 进行腐蚀操作
    eroded = cv2.erode(mask, kernel, iterations=2)
    # 进行膨胀操作
    mask = cv2.dilate(eroded, kernel, iterations=2)
    cv2.imwrite('text2.png',mask)
    # 将透明度信息的 Alpha 通道应用到原始图像上
    image[:, :, 3] = np.where(mask > 127, 0, image[:, :, 3])
    
    # 保存处理后的图像
    cv2.imwrite(output_path, image)


def composite_images(foreground_path, background_path, output_path, target_size=(512, 512)):
    
    # 打开背景图像
    background = Image.open(background_path).convert("RGBA")
    background = background.resize(target_size)
    # 打开前景图像并调整大小
    foreground = Image.open(foreground_path).convert("RGBA")
    foreground = foreground.resize(target_size)

    # 创建一个空白图像，大小与背景图像相同
    composite = Image.new("RGBA", target_size)

    # 粘贴背景图像到空白图像上
    composite.paste(background, (0, 0))

    # 粘贴前景图像到指定位置，使用前景图像的 alpha 通道作为掩码
    composite.paste(foreground, (0, 0), foreground)

    # 保存合成图像并调整大小
    # composite = composite.resize(target_size)
    composite.save(output_path, format="PNG")


def combinePNG(path1,path2,output_path):
    temp_path = 'test.png'
    remove_background_with_transparency(path1, temp_path)
    composite_images(temp_path, path2, output_path,target_size=(1000,1000))
