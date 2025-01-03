from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt
import json
from tqdm import tqdm
# 读取shape图像，并转换为二值图像，白色为1，黑色为0
def load_shape_image(image_path,global_scale,weight):
    shape_img = Image.open(image_path).convert('L')
    
    shape_img = shape_img.resize((int(shape_img.width*global_scale*weight),int(shape_img.height*global_scale*weight)))
    
    return shape_img

# 寻找离初始点最近的可放置位置
def find_nearest_position(mask, start_position):
    distance_map = distance_transform_edt(mask)

    candidate_positions = np.argwhere(distance_map > 10)
    if len(candidate_positions)>0:
        # 计算每个候选位置与 start_position 的欧几里得距离
        distances = np.linalg.norm(candidate_positions - np.array(start_position), axis=1)

        # 按距离升序排序，最接近 start_position 的位置会排在最前面
        sorted_indices = np.argsort(distances)

        final_position = candidate_positions[sorted_indices[0]]
        i, j = final_position
            
        return (i, j) , distance_map
    else:
        return (-1, -1) , distance_map

def df_with_origin(elements_dir,mask_dir,pos,json_dir,weights_list, fill_ratio):
    all_area = 0
    centroid_list = []
    primitive_area_list = []
    for i in range(len(elements_dir)):
        with open(json_dir[i], 'r') as file:
                    data = json.load(file)
                    centroid_list.append((data["center_x"],data["center_y"]))
                    primitive_area_list.append(data["area"])
        all_area+= primitive_area_list[i]*weights_list[i]*weights_list[i]
    background = Image.open(mask_dir).convert('L').resize((1000,1000))
    binary_image = np.array(background) < 128
    shape_area = np.sum(binary_image == True)
    global_scale = (fill_ratio*shape_area/all_area)**(1/2)
        
    # 读取主图像并转换为灰度图像
    image = Image.open(mask_dir).resize((1000,1000))  # 'L' 表示灰度图像
    # 读取多个shape图像
    shape_files = elements_dir
    shapes = [load_shape_image(shape_file,global_scale,weights_list[i]) for i,shape_file in enumerate(shape_files)]
    new_pos = []
    new_size = []
    # 逐个寻找最近的可放置位置并放置
    with tqdm(total=len(shapes), desc="df_with_origin", unit="shape") as pbar:
        for i in range(len(shapes)):
            image = image.convert('L')
            binary_image = image.point(lambda p: 255 if p > 128 else 0)
            # 将图像转换为 numpy 数组
            image_array = np.array(binary_image)
            # 创建掩膜，黑色区域的值为0，表示可以放置的区域
            mask = (image_array <128).astype(np.uint8)
            start_positon = (int(pos[i][1]),int(pos[i][0]))
            nearest_position,distance_map = find_nearest_position(mask, start_positon)
            new_pos.append([nearest_position[1],nearest_position[0]])
            new_size.append(global_scale*weights_list[i])
            # 显示原始图像和距离场
            # plt.figure(figsize=(12, 6))
            # plt.subplot(1, 2, 1)
            # plt.title('Binary Image')
            # plt.imshow(image, cmap='gray')
            # plt.subplot(1, 2, 2)
            # plt.title('Distance Field')
            # plt.imshow(distance_map, cmap='jet')
            # plt.colorbar()
            # plt.show()
            position = (int(nearest_position[1]-global_scale*weights_list[i]*centroid_list[i][0]),int(nearest_position[0]-global_scale*weights_list[i]*centroid_list[i][1]))
            image.paste(shapes[i],position,shapes[i])
            image.save('test3.png')
            pbar.update(1)
    return new_pos,new_size
        
       