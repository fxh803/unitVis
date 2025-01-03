from torchvision import transforms
import torch
import pydiffvg
import torch.nn.functional as F
from torchvision.transforms.functional import rgb_to_grayscale
import numpy as np
from PIL import Image, ImageDraw, ImageFont,ImageFilter
from skimage.morphology import medial_axis
from scipy.ndimage import distance_transform_edt
import json
import matplotlib.pyplot as plt
import os
import glob
from natsort import natsorted
import cv2
import string
import math
def mask2targetimg(mask_dir,device,img_size=1000):
    # 目标图像
    image = Image.open(mask_dir).convert("L").resize([img_size,img_size])
    rgb_image = image.convert("RGB")
    width, height = rgb_image.size

    for x in range(width):
        for y in range(height):
            gray_value = image.getpixel((x, y))
            
            # 如果灰度值小于10，将其RGB值设置为(178, 178, 178)
            if gray_value < 128:
                rgb_image.putpixel((x, y), (178, 178, 178))
            else:
                rgb_image.putpixel((x, y), (255, 255, 255))
    target_img = transforms.ToTensor()(rgb_image)
    target_img = target_img.to(device)

    # 掩码图像
    binary_image = np.array(image) > 128
    binary_image = binary_image.astype(int)
    mask_img = torch.tensor(binary_image,device=device,dtype=torch.float32,requires_grad=False)

    return target_img,mask_img

def init_primitive_pos_by_distance_field(weights_list,
                                         target_shape_mask_dir,
                                         primitive_mask_list=None,
                                         centroid_list = None,
                                         primitive_area_list = None,
                                         global_scale=1,
                                         img_size=1000):
    area_list = []
    for i in range(len(weights_list)):
        area_list.append(primitive_area_list[i]*weights_list[i]*weights_list[i])
    sorted_indices = [index for index, value in sorted(enumerate(area_list), key=lambda x: x[1], reverse=True)]

    background = Image.open(target_shape_mask_dir).resize((img_size,img_size))

    init_pos_list = []
    for i in sorted_indices:
        background = background.convert("RGBA")
        image = background.convert('L')
        binary_image = np.array(image) < 128
        # 计算距离场
        distance_field = distance_transform_edt(binary_image)

        # 计算距离场最大的坐标
        distance_field = torch.tensor(distance_field)
        max_index = torch.argmax(distance_field)
        max_index = np.unravel_index(max_index.item(), distance_field.shape)
        overlay_rgba = primitive_mask_list[i]
        overlay_rgba = overlay_rgba.resize((int(overlay_rgba.width*global_scale*weights_list[i]),int(overlay_rgba.height*global_scale*weights_list[i])))
        position = (max_index[1]-global_scale*weights_list[i]*centroid_list[i][0], max_index[0]-global_scale*weights_list[i]*centroid_list[i][1])
        position = (int(position[0]),int(position[1]))
        background.paste(overlay_rgba, position, overlay_rgba)
        background.save('test4.png')
        position1 = (max_index[1], max_index[0])
        init_pos_list.append(position1)

        # 显示原始图像和距离场
        # plt.figure(figsize=(12, 6))
        # plt.subplot(1, 2, 1)
        # plt.title('Binary Image')
        # plt.imshow(binary_image, cmap='gray')
        # plt.subplot(1, 2, 2)
        # plt.title('Distance Field')
        # plt.imshow(distance_field, cmap='jet')
        # plt.colorbar()
        # plt.show()
    def sort_by_indices(values, indices):
        # 获取排序后的索引列表
        sorted_indices_with_values = sorted(enumerate(indices), key=lambda x: x[1])
        # 提取排序后的原始列表和索引
        sorted_values = [values[i] for i, _ in sorted_indices_with_values]
        sorted_indices = [index for _, index in sorted_indices_with_values]
        return sorted_values, sorted_indices

    init_pos_list, sorted_indices = sort_by_indices(init_pos_list, sorted_indices)

    return init_pos_list

def init_primitive_pos_by_medial_axis(target_shape_mask_dir,points_num=100,img_size=1000):
    # 打开PNG图像
    image = Image.open(target_shape_mask_dir).resize([img_size,img_size]).convert("L")
    image = np.array(image)
    binary_image = image < 128
    # 进行中轴变换
    skel, distance = medial_axis(binary_image, return_distance=True)
    medial_axis_index = np.where(skel)

    # 获取中轴线上的点和宽度
    medial_axis_distance = np.zeros((len(medial_axis_index[0]), 3))
    for i in range(len(medial_axis_index[0])):
        x = medial_axis_index[0][i]
        y = medial_axis_index[1][i]
        medial_axis_distance[i,:] = np.array([x,y,distance[x,y]])
    if len(medial_axis_distance)<points_num:
        raise Exception("The current shape is not suitable for initialization with a medial axis transformation!")
    # 随机选点
    indices = np.random.choice(medial_axis_distance.shape[0], size=points_num, replace=False)
    random_selected_array = medial_axis_distance[indices]
    # 根据中轴宽度进行排序
    sorted_indices = np.argsort(random_selected_array[:, 2])
    sorted_array = random_selected_array[sorted_indices]
    sorted_array = [(x[1],x[0]) for x in sorted_array]
    return sorted_array

def init_primitive_pos_by_random_within_shape(weights_list,
                                         target_shape_mask_dir,
                                         primitive_mask_list=None,
                                         centroid_list = None,
                                         global_scale=1,
                                         img_size=1000):
    background = Image.open(target_shape_mask_dir).resize((img_size,img_size))
    init_pos_list = []
    for i in range(len(weights_list)):
        background = background.convert("RGBA")
        image = background.convert('L')
        binary_image = np.array(image) < 128
        # 获取所有 True 值的位置
        true_positions = np.argwhere(binary_image)
        # 随机选择一个位置
        random_index = np.random.choice(len(true_positions))
        random_position = true_positions[random_index]
        overlay_rgba = primitive_mask_list[i]
        overlay_rgba = overlay_rgba.resize((int(overlay_rgba.width*global_scale*weights_list[i]),int(overlay_rgba.height*global_scale*weights_list[i])))
        position = (random_position[1]-global_scale*weights_list[i]*centroid_list[i][0], random_position[0]-global_scale*weights_list[i]*centroid_list[i][1])
        position = (int(position[0]),int(position[1]))
        background.paste(overlay_rgba, position, overlay_rgba)
        # background.save('test2.png')
        position1 = (random_position[1], random_position[0])
        init_pos_list.append(position1)
    return init_pos_list


def get_photo_list(photos):
    png_files = glob.glob(os.path.join(photos, '*.png'))
    jpg_files = glob.glob(os.path.join(photos, '*.jpg'))
    jpeg_files = glob.glob(os.path.join(photos, '*.jpeg'))
    image_files = png_files + jpg_files + jpeg_files
    image_files = natsorted(image_files, key=lambda x: os.path.basename(x).lower())
    img_list = []
    for img in image_files:
        img = Image.open(img).convert("RGB")
        img_list.append(img)
    return img_list

def get_words(word,font_path,word_color):
    word_color = tuple([int(x) for x in word_color])
    # 获取小写字母
    lowercase_letters = list(string.ascii_lowercase)
    # 获取大写字母
    uppercase_letters = list(string.ascii_uppercase)
    letters = lowercase_letters+uppercase_letters
    width_dict = {}
    upper_dict = {}
    lower_dict = {}
    font = ImageFont.truetype(font_path, 200)
    for letter in letters:
        image = Image.new('RGBA', (150,200), color=(255,255,255,0))

        # 创建绘图对象
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), letter, font=font, fill=(0,0,0,255))
        # 获取 alpha 通道
        alpha_channel = image.split()[-1]
        # 计算透明度不为 0 的边界框
        bbox = alpha_channel.getbbox()
        left, upper, right, lower = bbox
        width_dict[letter] = right-left
        upper_dict[letter] = upper
        lower_dict[letter] = lower      

    word_img = Image.new('RGBA', ((len(word)*150),200), color=(0, 0, 0, 0))
    mask_img = Image.new('RGBA', ((len(word)*150),200), color=(0, 0, 0, 0))

    # 创建绘图对象
    word_draw = ImageDraw.Draw(word_img)
    mask_draw = ImageDraw.Draw(mask_img)
    # 在图像上绘制文本
    word_draw.text((10, 10), word, font=font, fill=word_color)
    # image.show()
    image = word_img.copy()
    max_y = 0
    min_y = 9999
    for letter in word:
        max_y = max_y if max_y >= lower_dict[letter] else lower_dict[letter]
        min_y = min_y if min_y <= upper_dict[letter] else upper_dict[letter]
    left2 = 0
    upper2 = 0
    points = []
    min_x = -1
    bbox_area = 0
    for letter in word:
        alpha_channel = image.split()[-1]
        bbox = alpha_channel.getbbox()
        left, upper, right, lower = bbox
        if min_x==-1:
            min_x = left
            bbox_area = (right-left)*(lower-upper)*0.95
        left1=left+width_dict[letter]
        mask_draw.rectangle([(left, upper_dict[letter]), (left1, max_y)], fill=(123, 232, 65, 255))
        if left2 == 0:
            points.append(((left, upper_dict[letter])))
        if left2>0:
            mask_draw.polygon([(left2, max(upper2,upper_dict[letter])), (left, max(upper2,upper_dict[letter])), (left, max_y), (left2, max_y)], fill=(123, 232, 65, 255))
            if abs(upper2-upper_dict[letter]) >=5:
                if upper2>=upper_dict[letter]:
                    points.append((left,upper2))
                    points.append((left,upper_dict[letter]))
                else:
                    points.append((left2,upper2))
                    points.append((left2,upper_dict[letter]))

        # print(left)
        data = np.array(image)
        # 将左侧宽度为 10 像素的区域的 alpha 通道设置为 0
        data[:, :left1, 3] = 0
        # 将 numpy 数组转换回 Pillow 图像
        image = Image.fromarray(data, "RGBA")
        left2 = left1
        upper2 = upper_dict[letter]
    points.append((left2,upper2))
    # points.append((left2,max_y)) 
    # points.append((left2,max_y))   
    x_values = np.linspace(left2, min_x, 32-len(points)) 
    y_values = np.linspace(max_y, max_y, 32-len(points))  
    add_points = list(zip(x_values, y_values))
    for point in add_points:
        points.append(point)
    centroid = ((min_x+right)/2,(min_y+max_y)/2)
    # word_img.show()
    # mask_img.show()
    return word_img,mask_img,points,centroid,bbox_area


def post_photos(shapes, photo_list, canvas_size, file_name):
    canvas = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255
    
    for i, shape in enumerate(shapes):
        image = photo_list[i]
        overlay_image = np.array(image)
        overlay_image = cv2.cvtColor(overlay_image, cv2.COLOR_RGB2BGR)
        
        overlay_points = np.float32([[0, 0], [overlay_image.shape[1], 0], [overlay_image.shape[1], overlay_image.shape[0]], [0, overlay_image.shape[0]]])
        
        target_points = np.float32([shape.points[0].tolist(), shape.points[1].tolist(), shape.points[2].tolist(), shape.points[3].tolist()])
        M = cv2.getPerspectiveTransform(overlay_points, target_points)
        warped_image = cv2.warpPerspective(overlay_image, M, (canvas.shape[1], canvas.shape[0]))

        mask = np.ones_like(overlay_image, dtype=np.uint8) * 255
        warped_mask = cv2.warpPerspective(mask, M, (canvas.shape[1], canvas.shape[0]))
        _, warped_mask = cv2.threshold(warped_mask, 200, 255, cv2.THRESH_BINARY)
        inverted_warped_mask = cv2.bitwise_not(warped_mask)
        
        canvas = warped_mask.astype(np.float32)*warped_image.astype(np.float32)+inverted_warped_mask.astype(np.float32)*canvas.astype(np.float32)
        canvas = (canvas/255).astype(np.uint8)
        # # 显示中间结果
        # cv2.imshow('Result', canvas)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
    
    final_image = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    final_image.save(f"{file_name}.png")

# 贴上svg
def post_svgs(size_tensor,angle_tensor,pos_tensor,global_size,svg_num,original_svg_dir_list,svg_json_list,is_global_size,file_name):
    shapes1 = []
    shape_groups1 = []
    count = 0
    size_tensor = size_tensor.to(torch.device('cpu'))
    angle_tensor = angle_tensor.to(torch.device('cpu'))
    pos_tensor = pos_tensor.to(torch.device('cpu'))
    global_size = global_size.to(torch.device('cpu'))

    size_tensor = size_tensor.view(svg_num)
    angle_tensor = angle_tensor.view(svg_num)
    pos_tensor = pos_tensor.view(svg_num,2)
    
    for i,svg_dir in enumerate(original_svg_dir_list):
        _, _, shapes, shape_groups = pydiffvg.svg_to_scene(svg_dir)
        for j,shape in enumerate(shapes):
            with open(svg_json_list[i], 'r') as file:
                data = json.load(file)
                center = torch.tensor([data["center_x"],data["center_y"]])
            if is_global_size:
                points_1 = (shape.points-center)*size_tensor[i]*global_size
            else:    
                points_1 = (shape.points-center)*size_tensor[i]
            points_2 = torch.zeros_like(points_1)
            points_2[:,0] = points_1[:,0] * torch.cos(angle_tensor[i]) - points_1[:,1] * torch.sin(angle_tensor[i])
            points_2[:,1] = points_1[:,0] * torch.sin(angle_tensor[i]) + points_1[:,1] * torch.cos(angle_tensor[i])
            points_2 = points_2+pos_tensor[i]
            shape.points = points_2
            shapes1.append(shape)
            shape_groups[j].shape_ids=torch.LongTensor([count])
            count+=1
            shape_groups1.append(shape_groups[j])
    
    pydiffvg.save_svg(f"{file_name}.svg",
                            1000,
                            1000,
                            shapes1,
                            shape_groups1)

def post_raster(size_tensor,angle_tensor,pos_tensor,global_size,primitive_num,original_primitive_dir_list,mask_dir_list,json_list,is_global_size,canvas_size,file_name):
    # size_tensor = size_tensor.to(torch.device('cpu'))
    # angle_tensor = angle_tensor.to(torch.device('cpu'))
    # pos_tensor = pos_tensor.to(torch.device('cpu'))
    # global_size = global_size.to(torch.device('cpu'))

    # size_tensor = size_tensor.view(primitive_num)
    # angle_tensor = angle_tensor.view(primitive_num)
    # pos_tensor = pos_tensor.view(primitive_num,2)
    # vertex = torch.tensor([[0,0],[500,0],[500,500],[0,500]])
    # canvas = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255
    # for i in range(primitive_num):
    #     with open(json_list[i], 'r') as file:
    #         data = json.load(file)
    #         center = torch.tensor([data["center_x"],data["center_y"]])
    #     if is_global_size:
    #         points_1 = (vertex-center)*size_tensor[i]*global_size
    #     else:    
    #         points_1 = (vertex-center)*size_tensor[i]
    #     points_2 = torch.zeros_like(points_1)
    #     points_2[:,0] = points_1[:,0] * torch.cos(angle_tensor[i]) - points_1[:,1] * torch.sin(angle_tensor[i])
    #     points_2[:,1] = points_1[:,0] * torch.sin(angle_tensor[i]) + points_1[:,1] * torch.cos(angle_tensor[i])
    #     vertex_transform = points_2+pos_tensor[i]

    #     original_primitive = cv2.imread(original_primitive_dir_list[i])
    #     original_mask = cv2.imread(mask_dir_list[i])

    #     target_points = vertex_transform.detach().numpy().astype(np.float32)
    #     overlay_points = np.float32([[0, 0], [500, 0], [500, 500], [0, 500]])

    #     # 计算透视变换矩阵
    #     M = cv2.getPerspectiveTransform(overlay_points, target_points)
    #     # 对源图像应用透视变换
    #     warped_image = cv2.warpPerspective(original_primitive, M, (canvas.shape[1], canvas.shape[0]))
    #     warped_mask = cv2.warpPerspective(original_mask, M, (canvas.shape[1], canvas.shape[0]))
    #     _, warped_mask = cv2.threshold(warped_mask, 200, 255, cv2.THRESH_BINARY)
    #     inverted_warped_mask = cv2.bitwise_not(warped_mask)
        
    #     canvas = warped_mask.astype(np.float32)*warped_image.astype(np.float32)+inverted_warped_mask.astype(np.float32)*canvas.astype(np.float32)
    #     canvas = (canvas/255).astype(np.uint8)
    #     # 显示中间结果
    #     # cv2.imshow('Result', canvas)
    #     # cv2.waitKey(0)
    #     # cv2.destroyAllWindows()
    
    # # 将最终结果保存为图像
    # final_image = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    # final_image.save(f"{file_name}.png")

################################################################################################
    size_tensor2 = size_tensor.to(torch.device('cpu'))
    angle_tensor2 = angle_tensor.to(torch.device('cpu'))
    pos_tensor2 = pos_tensor.to(torch.device('cpu'))
    global_size2 = global_size.to(torch.device('cpu'))

    size_tensor2 = size_tensor2.view(primitive_num).tolist()
    angle_tensor2 = angle_tensor2.view(primitive_num).tolist()
    pos_tensor2 = pos_tensor2.view(primitive_num,2).tolist()
    # 创建一个空白图像，大小与背景图像相同
    # canvas = Image.new("RGBA", (canvas_size,canvas_size),'white')
    canvas = Image.new("RGBA", (canvas_size,canvas_size))
    for i in range(primitive_num):
        with open(json_list[i], 'r') as file:
            data = json.load(file)
            center = [int(data["center_x"]),data["center_y"]]
        
        original_primitive = cv2.imread(original_primitive_dir_list[i])
        original_mask = cv2.imread(mask_dir_list[i])
        
        mask = cv2.inRange(original_mask[:, :, :3], (255, 255, 255), (255, 255, 255))
        
        # 将 OpenCV 图像转换为 PIL 图像
        original_primitive = Image.fromarray(cv2.cvtColor(original_primitive, cv2.COLOR_BGR2RGB))
        mask = Image.fromarray(mask)

        # 计算裁剪区域的左上角和右下角坐标
        crop_box = ( center[0]-250, center[1]-250,center[0]+250, center[1]+250)
        # 裁剪原始图片
        cropped_image = original_primitive.crop(crop_box)
        cropped_mask = mask.crop(crop_box)
        #放大
        if is_global_size:
            scale = size_tensor2[i]*global_size2
        else:    
            scale = size_tensor2[i]
        
        new_width = int(cropped_image.size[0] * scale)  
        new_height = int(cropped_image.size[1] * scale)  
        new_size = (new_width, new_height) 
        resized_image = cropped_image.resize(new_size, resample=Image.BICUBIC) 
        resized_mask = cropped_mask.resize(new_size, resample=Image.BICUBIC) 

        # 旋转
        rotated_image = resized_image.rotate(-math.degrees(angle_tensor2[i]), resample=Image.BICUBIC, expand=True)
        rotated_mask = resized_mask.rotate(-math.degrees(angle_tensor2[i]), resample=Image.BICUBIC, expand=True)
        # 将裁剪后的图片粘贴到新图片中
        paste_position = (int(pos_tensor2[i][0]/1000*canvas_size - rotated_image.width/2), int(pos_tensor2[i][1]/1000*canvas_size - rotated_image.height / 2))
        
        canvas.paste(rotated_image, paste_position,rotated_mask)

    # 对图片进行抗锯齿处理
    # 转换图像为RGB模式
    canvas = canvas.convert('RGBA')
    # 将最终结果保存为图像
    canvas.save(f"{file_name}.png")
        


def post_words(size_tensor,angle_tensor,pos_tensor,global_size,primitive_num,wordimg_list,center_list,is_global_size,canvas_size,file_name):
    size_tensor = size_tensor.to(torch.device('cpu'))
    angle_tensor = angle_tensor.to(torch.device('cpu'))
    pos_tensor = pos_tensor.to(torch.device('cpu'))
    global_size = global_size.to(torch.device('cpu'))

    size_tensor = size_tensor.view(primitive_num)
    angle_tensor = angle_tensor.view(primitive_num)
    pos_tensor = pos_tensor.view(primitive_num,2)
    # 创建白色画布
    canvas1 = Image.new('RGBA', (canvas_size,canvas_size), color=(255, 255, 255, 255))
    canvas = np.ones((canvas_size, canvas_size, 3), dtype=np.uint8) * 255
    
    for i in range(primitive_num):
        center = torch.tensor(center_list[i])
        vertex = torch.tensor([[0,0],[wordimg_list[i].width,0],[wordimg_list[i].width,wordimg_list[i].height],[0,wordimg_list[i].height]])
        if is_global_size:
            points_1 = (vertex-center)*size_tensor[i]*global_size
        else:    
            points_1 = (vertex-center)*size_tensor[i]
        points_2 = torch.zeros_like(points_1)
        points_2[:,0] = points_1[:,0] * torch.cos(angle_tensor[i]) - points_1[:,1] * torch.sin(angle_tensor[i])
        points_2[:,1] = points_1[:,0] * torch.sin(angle_tensor[i]) + points_1[:,1] * torch.cos(angle_tensor[i])
        vertex_transform = points_2+pos_tensor[i]
        word_img = np.array(wordimg_list[i])
        word_img = cv2.cvtColor(word_img, cv2.COLOR_RGBA2BGRA)

        target_points = vertex_transform.detach().numpy().astype(np.float32)
        overlay_points = np.float32([[0,0],[wordimg_list[i].width,0],[wordimg_list[i].width,wordimg_list[i].height],[0,wordimg_list[i].height]])
        # 计算透视变换矩阵
        M = cv2.getPerspectiveTransform(overlay_points, target_points)
        # 对源图像应用透视变换
        warped_image = cv2.warpPerspective(word_img, M, (canvas.shape[1], canvas.shape[0]),flags=cv2.INTER_LANCZOS4)
        warped_image = Image.fromarray(warped_image)
        canvas1.paste(warped_image, (0,0), warped_image)
    
    # 将最终结果保存为图像
    # final_image = Image.fromarray(cv2.cvtColor(canvas1, cv2.COLOR_BGR2RGB))
    canvas1.save(f"{file_name}.png")

# 可微分的渲染svg
def svg_to_img(shapes, shape_groups, width, height):
    scene_args = pydiffvg.RenderFunction.serialize_scene(
    width, height, shapes, shape_groups
    )
    _render = pydiffvg.RenderFunction.apply
    img = _render(width,  # width
                height,  # height
                2,  # num_samples_x
                2,  # num_samples_y
                0,  # seed
                None,
                *scene_args)
    para_bg = torch.tensor([1., 1., 1.], requires_grad=False, device=img.device)
    img = img[:, :, 3:4] * img[:, :, :3] + para_bg * (1 - img[:, :, 3:4])
    img = img.permute(2, 0, 1)
    return img
             