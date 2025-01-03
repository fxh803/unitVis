import base64 
import io 
from PIL import Image
import numpy as np
import copy
import requests
import xml.etree.ElementTree as ET
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
def generate_interpolated_colors(color, n):
    if color.startswith('#'):
        color = hex_to_rgb(color)
        r, g, b = color
    elif color.startswith('rgba'):
        # 去除字符串中的多余字符，仅保留数字部分
        color_str = color.replace("rgba(", "").replace(")", "")
        # 将字符串拆分为R、G、B值
        r, g, b = map(int, color_str.split(", "))
    else:
        # 去除字符串中的多余字符，仅保留数字部分
        color_str = color.replace("rgb(", "").replace(")", "")
        # 将字符串拆分为R、G、B值
        r, g, b = map(int, color_str.split(", "))

    # Calculate step size for each color channel
    step_r = (255 - r) / (n )
    step_g = (255 - g) / (n )
    step_b = (255 - b) / (n )

    # Generate interpolated colors
    interpolated_colors = [(int(r + step_r * i), int(g + step_g * i), int(b + step_b * i)) for i in range(0, n)]

    return interpolated_colors
# 复制 SVG 根元素和整个 SVG 树
def deep_copy_element(elem):
    copy_elem = copy.deepcopy(elem)
    for child in elem:
        copied_child = deep_copy_element(child)
        copy_elem.append(copied_child)
    return copy_elem
#解码elements
def linearColor(emitElement,num,type):
        if type == "png":
            # 解码 Base64 数据
            ele_data = base64.b64decode(emitElement)
            ele_stream = io.BytesIO(ele_data)
            ele = Image.open(ele_stream)
            # 将图像转换为RGB格式
            ele_rgb = ele.convert("RGB")
            # 获取图像的像素数据
            pixels = np.array(ele_rgb)
            # 将图像数据转换为一维数组
            image_flat = pixels.reshape((-1, 3))
            # 提取唯一的颜色值
            unique_colors = np.unique(image_flat, axis=0).tolist()

            # 一个dict存储插值颜色
            colors_dict = {}

            # 提取原始的 fill 颜色并修改颜色
            for color in unique_colors:
                color_str = f"rgb({color[0]}, {color[1]}, {color[2]})"
                # print(color_str)
                new_colors = generate_interpolated_colors(color_str,num)
                colors_dict[color_str] = new_colors

            copied_pngs = []
            pngs_base64 = []
            for i in range(num):
                copied_png = ele.copy()
                    # 将插值颜色赋予回 copied_png
                data = np.array(copied_png)
                # 遍历data中的每个像素
                for x in range(data.shape[0]):
                    for y in range(data.shape[1]):
                        pixel_color = tuple(data[x, y, :3])  # 提取像素的RGB颜色值
                        pixel_color_str = f"rgb({pixel_color[0]}, {pixel_color[1]}, {pixel_color[2]})"

                        # 检查颜色是否在colors_dict中，如果是，则替换为对应的插值颜色
                        if pixel_color_str in colors_dict:
                            new_pixel_color = colors_dict[pixel_color_str][i]
                            data[x, y, :3] = new_pixel_color  # 将原始颜色替换为插值颜色
                
                copied_png = Image.fromarray(data)
                
                copied_pngs.append(copied_png)
            for copied_png in copied_pngs:
                # 将 Image 对象转换为字节序列
                output =  io.BytesIO() 
                copied_png.save(output, format="PNG")
                png_bytes = output.getvalue()
                png_base64 =  base64.b64encode(png_bytes).decode('utf-8')
                pngs_base64.append(png_base64)

            return pngs_base64

        #否则为svg
        elif type == "svg":
            # 解码 Base64 数据
            decoded_data = base64.b64decode(emitElement).decode('utf-8')
            # 进行相应操作，比如解析 SVG
            svg_root = ET.fromstring(decoded_data)

            # 一个dict存储插值颜色
            colors_dict = {}

            # 提取原始的 fill 颜色并修改颜色
            for elem in svg_root.iter():
                if 'fill' in elem.attrib:
                    # print(elem.attrib['fill'])
                    colors = generate_interpolated_colors(elem.attrib['fill'],num)
                    colors_dict[elem.attrib['fill']] = colors
            
            copied_svgs = []
            svgs_base64 = []
            for i in range(num):
                copied_svg = deep_copy_element(svg_root)
                for elem in copied_svg.iter():
                    if elem.attrib.get('fill') in colors_dict:
                        interpolated_color = colors_dict[elem.attrib['fill']][i]
                        elem.set('fill', f'rgb{interpolated_color}')
                
                copied_svgs.append(copied_svg)
            
            for copied_svg in copied_svgs:
                # 创建一个字符串缓冲区
                xml_str = io.BytesIO()
                # 将 SVG 树写入字符串缓冲区
                ET.ElementTree(copied_svg).write(xml_str, encoding='utf-8', xml_declaration=True)
                xml_bytes = xml_str.getvalue()
                svg_base64 =  base64.b64encode(xml_bytes).decode('utf-8')
                svgs_base64.append(svg_base64)
                
            return svgs_base64
