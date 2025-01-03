import torch
import pydiffvg
from utils.image_process import *
from torchvision.transforms import ToPILImage
import cv2
import os
from scipy.ndimage import center_of_mass
import argparse
import yaml
from utils.svg_process import init_diffvg
from tqdm import tqdm


def insert_point_to_longest_segment(points,num_segments=20):
    def distance(point1, point2):
        return np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
    # 找到最长线段
    max_length = 0
    longest_segment = None
    for i in range(len(points) - 1):
        dist = distance(points[i], points[i + 1])
        if dist > max_length:
            max_length = dist
            longest_segment = (i, i + 1)
    
    if longest_segment is None:
        return points
    
    # 计算最长线段的中心点
    start_idx, end_idx = longest_segment
    start_point = points[start_idx]
    end_point = points[end_idx]
    center_point = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2)
    
    # 插入中心点到最长线段的位置
    new_points = np.insert(points, end_idx, center_point, axis=0)
    
    # 如果需要8个点，继续插入新点
    if len(new_points) == num_segments:
        return new_points
    # 递归调用直到插入到8个点
    return insert_point_to_longest_segment(new_points,num_segments)


# 在每个线段中插入新点
def insert_points_in_segments(points, num_interpolations=2):
    # 线性插值函数
    def interpolate_points(point1, point2, num_interpolations):
        # 生成 num_interpolations 个插入点
        x_values = np.linspace(point1[0], point2[0], num=num_interpolations + 2)[1:-1]
        y_values = np.linspace(point1[1], point2[1], num=num_interpolations + 2)[1:-1]
        interpolated_points = np.column_stack((x_values, y_values))
        return interpolated_points
    new_points = []
    for i in range(len(points) - 1):
        point1 = points[i]
        point2 = points[i + 1]
        # 将原始点加入新点集
        new_points.append(point1)
        # 在当前线段中插入新点
        interpolated_points = interpolate_points(point1, point2, num_interpolations)
        new_points.extend(interpolated_points)
    # 将最后一个原始点加入新点集
    new_points.append(points[-1])
    
    return np.array(new_points)

def uniform_size(svg_dir,save_dir,fixed_size=80,margin=10,index=0):
    _, _, shapes, shape_groups = pydiffvg.svg_to_scene(svg_dir)
    shape = shapes[0]
    min_values, _ = torch.min(shape.points, dim=0)
    max_values, _ = torch.max(shape.points, dim=0)
    min_x,min_y = min_values[0],min_values[1]
    max_x,max_y = max_values[0],max_values[1]
    for shape in shapes:
        min_values, _ = torch.min(shape.points, dim=0)
        max_values, _ = torch.max(shape.points, dim=0)
        min_x =  min_values[0] if min_values[0] < min_x else min_x
        min_y = min_values[1] if min_values[1] < min_y else min_y
        max_x =  max_values[0] if max_values[0] > max_x else max_x
        max_y = max_values[1] if max_values[1] > max_y else max_y
    # fixed_size = 80 
    scaling_ratio = fixed_size/max(max_x-min_x,max_y-min_y)
    for shape in shapes:
        shape.points[:,0] = shape.points[:,0]-min_x
        shape.points[:,1] = shape.points[:,1]-min_y
        shape.points = shape.points*scaling_ratio
        shape.points[:,0] = shape.points[:,0]+margin
        shape.points[:,1] = shape.points[:,1]+margin

    pydiffvg.save_svg(f"{save_dir}/uniform_{index}.svg",
                        100,
                        100,
                        shapes,
                        shape_groups)
    return shapes

# def uniform_image_size(raster_img_dir,mask_img_dir,img_size,save_dir,index):
#     mask_image = cv2.imread(mask_img_dir, cv2.IMREAD_GRAYSCALE)
#     raster_img = cv2.imread(raster_img_dir)
#     height, width, = mask_image.shape
#     inverted_mask_image = cv2.bitwise_not(mask_image)

#     num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inverted_mask_image, connectivity=8)
#     new_binary_image = np.zeros_like(mask_image)
#     for i in range(1, num_labels):
#         area = stats[i, cv2.CC_STAT_AREA]
#         if area >= 50:
#             new_binary_image[labels == i] = 255

#     coords = cv2.findNonZero(new_binary_image)
#     x, y, w, h = cv2.boundingRect(coords)

#     scale = img_size*0.8/max(w,h)

#     image = cv2.resize(new_binary_image, (int(width*scale), int(height*scale)))
#     raster_img = cv2.resize(raster_img, (int(width*scale), int(height*scale)))
#     x = int(x*scale)
#     y = int(y*scale)

#     margin = int(img_size/10)
#     if x >= margin:
#         image = image[:, x-margin:]
#         raster_img = raster_img[:, x-margin:]
#         x = margin
#     if y >= margin:
#         image = image[y-margin:,:]
#         raster_img = raster_img[y-margin:,:]
#         y = margin
#     if image.shape[1] >= 500:
#         image = image[:,:500]
#         raster_img = raster_img[:,:500]
#     if image.shape[0] >= 500:
#         image = image[:500,:]
#         raster_img = raster_img[:500,:]
#     # top, bottom, left, right
#     mask_image = cv2.copyMakeBorder(image, margin-y, 500-image.shape[0]-(margin-y), margin-x, 500-image.shape[1]-(margin-x), cv2.BORDER_CONSTANT, value=[0, 0, 0])
#     raster_image = cv2.copyMakeBorder(raster_img, margin-y, 500-image.shape[0]-(margin-y), margin-x, 500-image.shape[1]-(margin-x), cv2.BORDER_CONSTANT, value=[0, 0, 0])
    
#     cv2.imwrite(f'{save_dir}/{index}.png', mask_image)
#     cv2.imwrite(f'{save_dir}/uniform_{index}.png', raster_image)
#     _, binary_image = cv2.threshold(mask_image, 0, 255, cv2.THRESH_BINARY)
#     binary_image = cv2.bitwise_not(binary_image)
#     target_img = Image.fromarray(binary_image)
#     return target_img

def uniform_image_size(raster_img_dir,mask_img_dir,img_size,save_dir,index):
    mask_image = cv2.imread(mask_img_dir, cv2.IMREAD_GRAYSCALE)
    raster_img = cv2.imread(raster_img_dir)
    height, width, = mask_image.shape
    inverted_mask_image = cv2.bitwise_not(mask_image)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inverted_mask_image, connectivity=8)
    new_binary_image = np.zeros_like(mask_image)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= 50:
            new_binary_image[labels == i] = 255

    coords = cv2.findNonZero(new_binary_image)
    x, y, w, h = cv2.boundingRect(coords)

    scale = img_size*0.8/max(w,h)

    image = cv2.resize(new_binary_image, (int(width*scale), int(height*scale)))
    raster_img = cv2.resize(raster_img, (int(width*scale), int(height*scale)))
    x = int(x*scale)
    y = int(y*scale)

    margin = int(img_size/10)
    if x >= margin:
        image = image[:, x-margin:]
        raster_img = raster_img[:, x-margin:]
        x = margin
    else:
        image = cv2.copyMakeBorder(image, 0, 0, margin-x, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        raster_img = cv2.copyMakeBorder(raster_img, 0, 0, margin-x, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    if y >= margin:
        image = image[y-margin:,:]
        raster_img = raster_img[y-margin:,:]
        y = margin
    else:
        image = cv2.copyMakeBorder(image, margin-y, 0, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        raster_img = cv2.copyMakeBorder(raster_img, margin-y, 0, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    if image.shape[1] >= 500:
        image = image[:,:500]
        raster_img = raster_img[:,:500]
    else:
        image = cv2.copyMakeBorder(image, 0, 0, 0, 500-image.shape[1], cv2.BORDER_CONSTANT, value=[0, 0, 0])
        raster_img = cv2.copyMakeBorder(raster_img, 0, 0, 0, 500-raster_img.shape[1], cv2.BORDER_CONSTANT, value=[0, 0, 0])
    if image.shape[0] >= 500:
        image = image[:500,:]
        raster_img = raster_img[:500,:]
    else:
        image = cv2.copyMakeBorder(image, 0, 500-image.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        raster_img = cv2.copyMakeBorder(raster_img, 0, 500-raster_img.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        
    # top, bottom, left, right
    mask_image = image
    cv2.imwrite(f'{save_dir}/{index}.png', mask_image)
    cv2.imwrite(f'{save_dir}/uniform_{index}.png', raster_img)
    _, binary_image = cv2.threshold(mask_image, 0, 255, cv2.THRESH_BINARY)
    binary_image = cv2.bitwise_not(binary_image)
    target_img = Image.fromarray(binary_image)
    return target_img


def get_target_img(shapes,img_size=100):
    path_groups = []
    for i in range(len(shapes)):
        path_group = pydiffvg.ShapeGroup(
                                shape_ids=torch.LongTensor([i]),
                                fill_color=torch.FloatTensor([0,0,0,1]),
                                stroke_color=torch.FloatTensor([0,0,0,1])
                            )
        path_groups.append(path_group)

    target_img =  svg_to_img(shapes,path_groups,img_size,img_size)
    image = ToPILImage()(target_img.detach())
    return image

def init_shapes(image,num_segments=20):
    binary_image = np.array(image.convert('L'))
    binary_image = binary_image < 128
    binary_image = np.uint8(binary_image) * 255
    # 查找二值图像中的轮廓
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # # Create an image to draw the contours on
    # contour_image = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    # # Draw the contours on the image
    # cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)  # Draw all contours in green color
    # # Display the original binary image and the image with contours
    # cv2.imshow('Binary Image', binary_image)
    # cv2.imshow('Contours', contour_image)
    # # Wait until a key is pressed and close the display windows
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


    kernel_size=1
    while len(contours)>1:
        kernel_size+=1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)  # 5x5的矩形核
        dilated_image = cv2.dilate(binary_image, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = contours[0]

    simplified_contour = [1]*100
    epsilon = 0
    while len(simplified_contour)>num_segments:
        epsilon+=1
        # 进行轮廓近似，根据不同的阈值进行简化
        simplified_contour = cv2.approxPolyDP(contour, epsilon, closed=True)
    if len(simplified_contour) == num_segments:
        simplified_contour = simplified_contour[:,0,:]
    elif len(simplified_contour)<=num_segments-1:
        simplified_contour = insert_point_to_longest_segment(simplified_contour[:,0,:],num_segments)
    
    points = simplified_contour
    points = np.vstack((points, points[0]))
    points = insert_points_in_segments(points, num_interpolations=2)
    points = points[:-1]
    points = torch.FloatTensor(points)
    num_control_points = [2] * num_segments
    path = pydiffvg.Path(
                        num_control_points=torch.LongTensor(num_control_points),
                        points=points,
                        stroke_width=torch.tensor(0.0),
                        is_closed=True
                    )
    return path

def svg_optimize_img(img_size, shapes, shape_groups,image_taregt,device,save_svg_path,num_iters=1000,svg_i=0):
    image_taregt = image_taregt.convert('RGB')

    mask_img = image_taregt.convert("L")
    mask_img = np.array(mask_img) < 128
    mask_img = (mask_img*255).astype(np.uint8)
    mask_img = Image.fromarray(mask_img)
    mask_img.save(f"{save_svg_path}/{svg_i}.png")

    image_taregt = transforms.ToTensor()(image_taregt)
    image_taregt = image_taregt.to(device)

    # 设置优化器
    params = {}
    points_vars = []
    for i, path in enumerate(shapes):
        path.id = i  # set point id
        path.points.requires_grad = True
        points_vars.append(path.points)

    params = {}
    params['point'] = points_vars
    lr_base = {
        "point": 1,
    }
    learnable_params = [
        {'params': params[ki], 'lr': lr_base[ki], '_id': str(ki)} for ki in sorted(params.keys())
    ]
    svg_optimizer = torch.optim.Adam(learnable_params, betas=(0.9, 0.9), eps=1e-6)
    with tqdm(total=num_iters, desc="Processing value", unit="value") as pbar:
        for i in range(num_iters):
            img = svg_to_img(shapes, shape_groups,img_size,img_size)
            image_loss = F.mse_loss(img, image_taregt)
            loss = image_loss
            svg_optimizer.zero_grad()
            loss.backward()
            svg_optimizer.step()
            pbar.update(1)
            # pbar.set_description(f"epoch:{i}")
    pydiffvg.save_svg(f"{save_svg_path}/outline_{svg_i}.svg",
                    img_size,
                    img_size,
                    shapes,
                    shape_groups)

def get_area_centroid(target_img,save_svg_path,svg_i):
    # 打开图像并转换为灰度图
    image = target_img.convert('L')
    
    # 将灰度图像转换为二值图像（0 或 1）
    binary_image = np.array(image) < 128
    binary_image_uint8 = binary_image.astype(np.uint8) * 255
    # cv2.imwrite(f"{save_svg_path}/fuck{svg_i}.png", binary_image_uint8)
    area = np.sum(binary_image == True)
    # 计算质心
    centroid = center_of_mass(binary_image)
    data = {
        "center_x": int(centroid[1]),
        "center_y": int(centroid[0]),
        "area": int(area),
    }
    with open(f"{save_svg_path}/{svg_i}.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

def outline_svg(args,device,progress_callback = None,stop_ids = None,id = None,name_list =None):
    primitive_files=[]
    if args.primitive_class=="any_shape_svg":
        svg_files = glob.glob(os.path.join(f"{args.primitive_dir}/outline_targets", '*.svg'))
        primitive_files = natsorted(svg_files, key=lambda x: os.path.basename(x).lower())
    elif args.primitive_class=="any_shape_raster":
        png_files = glob.glob(os.path.join(f"{args.primitive_dir}/outline_targets", '*.png'))
        jpg_files = glob.glob(os.path.join(f"{args.primitive_dir}/outline_targets", '*.jpg'))
        jpeg_files = glob.glob(os.path.join(f"{args.primitive_dir}/outline_targets", '*.jpeg'))
        image_files = png_files+jpg_files+jpeg_files
        primitive_files = natsorted(image_files, key=lambda x: os.path.basename(x).lower())

        png_files = glob.glob(os.path.join(f"{args.primitive_dir}/masks", '*.png'))
        jpg_files = glob.glob(os.path.join(f"{args.primitive_dir}/masks", '*.jpg'))
        jpeg_files = glob.glob(os.path.join(f"{args.primitive_dir}/masks", '*.jpeg'))
        mask_files = png_files+jpg_files+jpeg_files
        mask_files = natsorted(mask_files, key=lambda x: os.path.basename(x).lower())

    os.makedirs(f"{args.primitive_dir}/outline_files", exist_ok=True)

    with tqdm(total=len(primitive_files), desc="Processing value", unit="value") as pbar:
        for i,primitive_file in enumerate(primitive_files):
            if  progress_callback!= None and id!= None:
                progress_callback(0,i+1,len(primitive_files),id)
            if  stop_ids!= None and id!= None:
                if id in stop_ids:
                    print("stop!!!")
                    return
            
            img_size = 0
            if args.primitive_class=="any_shape_svg":
                shapes = uniform_size(primitive_file,fixed_size=args.svg_normalized_size*0.8,margin=args.svg_normalized_size*0.1,save_dir=f"{args.primitive_dir}/outline_files",index=name_list[i])
                target_img = get_target_img(shapes,args.svg_normalized_size)
                img_size = args.svg_normalized_size
            elif args.primitive_class=="any_shape_raster":
                target_img = uniform_image_size(primitive_file,mask_files[i],args.raster_normalized_size,save_dir=f"{args.primitive_dir}/outline_files",index=name_list[i])
                img_size = args.raster_normalized_size
            path = init_shapes(target_img,num_segments=args.outline_num_segments)
            path_group = pydiffvg.ShapeGroup(
                                    shape_ids=torch.LongTensor([0]),
                                    fill_color=torch.FloatTensor([0,0,0,1]),
                                    stroke_color=torch.FloatTensor([0,0,0,1])
                                )
            svg_optimize_img(img_size,[path],[path_group],target_img,device,save_svg_path=f"{args.primitive_dir}/outline_files",num_iters=10,svg_i=name_list[i])
            get_area_centroid(target_img,f"{args.primitive_dir}/outline_files",svg_i=name_list[i])
            pbar.update(1)
            pbar.set_description(f"Number of primitives:{len(primitive_files)}")


def load_config(file_path,args):
    with open(file_path, 'r') as file:
        config =  yaml.safe_load(file)
        for key, value in config.items():
            setattr(args, key, value)
    return args


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="collage",
    )
    # config
    parser.add_argument("-c", "--config", type=str,default="./data/config.yaml",help="YAML/YML file for configuration.")
    # 填充单元类型
    parser.add_argument("-pc", "--primitive_class", type=str, choices=["any_shape_raster","any_shape_svg"], default="any_shape_svg",
                        help="Specify the primitive class (any_shape_raster,any_shape_svg).")

    args = parser.parse_args()
    args = load_config(args.config,args)
    device = torch.device("cuda:0")
    init_diffvg(device)
    outline_svg(args,device=device)
