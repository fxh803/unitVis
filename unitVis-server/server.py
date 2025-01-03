from flask import Flask,request, jsonify
import base64 
import json
import io
import random
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from utils.linearColor import linearColor
from utils.emitArea import emitArea
from utils.transparency import transparency
from utils.backgroundWhite import backgroundWhite
from utils.square import square
from utils.df_with_origin import df_with_origin
import os
import requests
import cairosvg
from flask_cors import *
from PIL import Image
from io import BytesIO
import io
import base64
import os
import torch
from outline_svg import outline_svg
from PNGmaskGenerate import maskGenerate
from types import SimpleNamespace
from shapecollage import ShapeCollage
import copy
import yaml
import re
import shutil
import threading
import os
app = Flask(__name__, template_folder='',static_folder="")
CORS(app, supports_credentials=True)


# 读取YAML文件
def load_yaml(filename):
    with open(filename, 'r') as file:
        data = yaml.safe_load(file)
    return data

# 指定要读取的YAML文件路径
yaml_file = './config.yaml'  # 请替换为实际的YAML文件路径
# 加载YAML文件内容为一个对象
config = SimpleNamespace(**load_yaml(yaml_file))

working = False# 运行状态
progress_data = {}  # 存储进度信息的全局字典
result_data = {} #存储结果的字典
stop_ids = []# 存储要停止的id
device = torch.device("cuda:0")

@app.route('/generateEmitArea', methods=['POST'])
def generateEmitArea():
    height = request.json['canvasHeight'] 
    width = request.json['canvasWidth'] 
    image = request.json['image'] 
    generateMask = request.json['generateMask'] 
    # 解码 Base64 数据为字节数据
    image_data = base64.b64decode(image)
    image_stream = io.BytesIO(image_data)
    image = Image.open(image_stream)
    if generateMask:
        shorterEdge =  width if width < height else height
        image = image.resize((shorterEdge, shorterEdge))
        # 创建一个空白画布，大小为 800x800（可以根据需求调整）
        blank_canvas = Image.new("RGBA", (width, height), (255,255,255,0))
        # 计算将图片放置在空白画布中心的位置
        x_offset = (blank_canvas.width - image.width) // 2
        y_offset = (blank_canvas.height - image.height) // 2

        # 将图片粘贴到空白画布的中心
        blank_canvas.paste(image, (x_offset, y_offset))
        image = blank_canvas
    else:
        image = image.resize((width, height))
    image.save('test2.png')
    boundary_points_list,points_list,boundary_index = emitArea(image)
    print(boundary_index)
    return jsonify({'status': 0,'boundary_points_list':boundary_points_list,'points_list':points_list,'boundary_index':boundary_index})    


@app.route('/preProcessUploadMask', methods=['POST'])
def preProcessUploadMask():
    image = request.json['image'] 
    # 解码 Base64 数据为字节数据
    image_data = base64.b64decode(image)
    image_stream = io.BytesIO(image_data)
    image = Image.open(image_stream)
    #透明化
    new_image = transparency(image)
    new_image.save('test.png')
    buffered = io.BytesIO()
    new_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return jsonify({'status': 0,'result':img_str},)    


@app.route('/collage', methods=['POST'])
def collage():
    print('process_data invoked')
    global working
    global config
    if working:
        print('working, return')
        return jsonify({'message': '正在执行，请稍后','status':'-1'})
    working = True

    height = request.json['canvasHeight'] 
    width = request.json['canvasWidth'] 
    mask_base64 = request.json['mask'] 
    emitDetail= request.json['emitDetail'] 
    lineDetail = request.json['lineDetail'] 
    id = request.json['processId'] 
    shape_class = 'open' if request.json['gravityEnable'] else 'closed'
    print(shape_class)
    try:
        os.makedirs(f"./workdir/{str(id)}", exist_ok=True)
        os.makedirs(f"./workdir/{str(id)}/outline_files", exist_ok=True)
        os.makedirs(f"./workdir/{str(id)}/images", exist_ok=True)
        os.makedirs(f"./workdir/{str(id)}/masks", exist_ok=True)
        os.makedirs(f"./workdir/{str(id)}/outline_targets", exist_ok=True)
        
        #保存mask
        mask = base64_to_image(mask_base64) 
        mask = mask.resize((width, height))
        mask = backgroundWhite(mask)
        mask = square(mask)
        cropped_width, cropped_height = mask.size
        result_data[str(id)] = {
        'width':cropped_width,
        'height':cropped_height,
        }
        mask.save(f'./workdir/{str(id)}/target_shape.png')
        
        #组合lineDetail和emitDetail
        allDetail = []
        for detail in emitDetail:
            if detail['type'] == 'point':
                for sub_detail in lineDetail:
                    if sub_detail['assignId'] == detail['assignId']:
                        allDetail.append({
                            'assignId':sub_detail['assignId'],
                            'lineId':sub_detail['lineId'],
                            'selectedData':sub_detail['filteredData'],
                            'trace':sub_detail['trace'],
                            'traceLastPoint':sub_detail['traceLastPoint'],
                            'assignPoint':detail['assignPoint'],
                            'img':detail['img'],
                            'renderHeight':detail['renderHeight'],
                            'renderWidth':detail['renderWidth'],
                            'type':'point',
                            'selectedVis':detail['selectedVis'],
                        })               
            else:
                allDetail.append(detail)
        print(allDetail)
        allDetail = sorted(allDetail, key=lambda x: 0 if x['type'] == 'point' else 1)

        # 打印排序后的 allDetail 列表
        print(allDetail)
        #解码elements
        #http转base64
        emitElements = []
        for index, detail in enumerate(allDetail):
            if detail['img'].startswith("http"):
                # 如果是 URL 路径
                response = requests.get(detail['img'])
                if response.status_code == 200:
                    svg_base64 = base64.b64encode(response.content).decode('utf-8')
                    # 更新 emitElement
                    allDetail[index]['img'] = "data:image/svg+xml;base64," + svg_base64
            emitElements.append(detail['img'])
        #如果有png就全部转png
        contains_png_image = any(element.startswith("data:image/png") for element in emitElements)
        # contains_png_image = True
        if contains_png_image:
            for index, emitElement in enumerate(emitElements):
                if emitElement.startswith("data:image/svg+xml"):
                    svg_data = base64.b64decode(emitElement.split(",")[1])
                    # 将 SVG 数据转换为 PNG 格式
                    png_data = cairosvg.svg2png(bytestring=svg_data)
                    png_base64 = base64.b64encode(png_data).decode('utf-8')
                    # 更新 emitElement
                    emitElements[index] = "data:image/png;base64," + png_base64
                    
        #weight_list生成(1维)
        weights_list = []    
        for detail in allDetail:
            if detail['selectedVis'] =='color':#如果是颜色
                weights = [ 1 for _ in range(len(detail['selectedData']))]#大小都为 1
                weights_list.extend(weights)
            elif detail['selectedVis'] =='size':#如果是尺寸
                if str(detail['selectedData'][0]).isdigit():#如果是数字数据，以它作为大小
                    random.shuffle(detail['selectedData'])#随机一下，好看点，反正是同类元素
                    for data in detail['selectedData']:
                        weights_list.append(int(data))
                else:
                    weights = [ 1 for _ in range(len(detail['selectedData']))]#否则全为1
                    weights_list.extend(weights)

        # 归一化
        min_val = min(weights_list)
        max_val = max(weights_list)

        # 检查最大值是否等于最小值
        if max_val == min_val:
            # 如果最大值和最小值相等，将所有值设置为 1.5
            weights_list = [1.5 for _ in weights_list]
        else:
            # 归一化计算公式
            weights_list = [(((x - min_val) / (max_val - min_val)) + 1) for x in weights_list]
        # print(weights_list)
        #决定模式
        primitive_class= 'any_shape_raster' if contains_png_image else 'any_shape_svg'
        result_data[str(id)]['type'] = 'png' if contains_png_image else 'svg'
        #保存outline目标文件
        for i,emitElement in enumerate(emitElements):
            
            if primitive_class=='any_shape_svg':#svg模式
                element = base64.b64decode(emitElement.split(",")[1])
                with open(f'./workdir/{str(id)}/outline_targets/{i+1}.svg', 'wb') as file:
                    file.write(element)
                # final_file_path = f'workdir/{str(id)}/final.svg'
            elif primitive_class=='any_shape_raster':#png模式
                    element = base64_to_image(emitElement.split(",")[1]) 
                    element.save(f'./workdir/{str(id)}/outline_targets/{i+1}.png')
                    maskGenerate(f'./workdir/{str(id)}/outline_targets/{i+1}.png',f'./workdir/{str(id)}/masks/{i+1}.png')
                    # final_file_path = f'workdir/{str(id)}/final.png'
        #配置项
        _config = copy.deepcopy(config)
        _config.primitive_dir= f"./workdir/{str(id)}"
        _config.primitive_class= primitive_class
        _config.target_shape_mask_dir= f'./workdir/{str(id)}/target_shape.png'
        _config.save_name= f'{str(id)}'
        _config.weights_list= weights_list  
        _config.shape_class = shape_class

        #生成outline文件的名称
        name_list = [] #有多组数据，如果selectedData的长度为2，3，4，那么namelist应该是1，3，6
        selectedData = [item['selectedData'] for item in allDetail]
        for i in range(len(selectedData)):
            name_list.append(1 + sum(len(item) for item in selectedData[:i]))

        #针对outline目标文件进行outline
        outline_svg(_config,device= device,progress_callback = progress_callback,stop_ids=stop_ids, id = str(id),name_list = name_list)

        #对outline文件进行复制
        type =  'png' if contains_png_image else 'svg'
        for i in range(len(selectedData)):
            target_file1 = f'./workdir/{str(id)}/outline_files/{name_list[i]}.json'
            target_file2 = f'./workdir/{str(id)}/outline_files/{name_list[i]}.png'
            target_file3 = f'./workdir/{str(id)}/outline_files/outline_{name_list[i]}.svg'

            
            for j in range(len(selectedData[i])-1):
                shutil.copy(target_file1, f'./workdir/{str(id)}/outline_files/{name_list[i]+j+1}.json')
                shutil.copy(target_file2, f'./workdir/{str(id)}/outline_files/{name_list[i]+j+1}.png')
                shutil.copy(target_file3, f'./workdir/{str(id)}/outline_files/outline_{name_list[i]+j+1}.svg')
        
        #对uniform图像进行处理
        for i, detail in enumerate(allDetail):
            file = f'./workdir/{str(id)}/outline_files/uniform_{name_list[i]}.{type}'#要处理的目标文件
            # 读取文件并转换为Base64
            with open(file, 'rb') as f:
                file_content = f.read()
                base64_encoded = base64.b64encode(file_content).decode('utf-8')
            if detail['selectedVis'] =='color':#如果是颜色
                elements = linearColor(base64_encoded,len(detail['selectedData']),type)#进行线性插值
                # 保存Base64数据为SVG或PNG文件
                for j, base64_data in enumerate(elements):
                    # 将Base64解码为二进制数据
                    file_data = base64.b64decode(base64_data)
                    # 保存文件
                    file_name = f'./workdir/{str(id)}/outline_files/uniform_{name_list[i]+j}.{type}'
                    with open(file_name, "wb") as f:
                        f.write(file_data)

            elif detail['selectedVis'] =='size':#如果是尺寸
                for j in range(len(detail['selectedData'])-1):
                    shutil.copy(file, f'./workdir/{str(id)}/outline_files/uniform_{name_list[i]+j+1}.{type}')
        
        #对png模式下的uniform元素进行变换处理
        if type =='png':
            files = os.listdir(f'./workdir/{str(id)}/outline_files')
            uniform_files = [f for f in files if f.startswith('uniform')]
            for i in range(len(uniform_files)):
                file_path = f'./workdir/{str(id)}/outline_files/uniform_{i+1}.png'
                trans_file_path = f'./workdir/{str(id)}/outline_files/trans_uniform_{i+1}.png'
                mask_path = f'./workdir/{str(id)}/outline_files/{i+1}.png'
                json_path = f'./workdir/{str(id)}/outline_files/{i+1}.json'
                # 读取 JSON 文件
                with open(json_path, 'r') as file:
                    data = json.load(file)
                    center = [int(data["center_x"]),data["center_y"]]
                image = Image.open(file_path).convert("RGBA")  # 确保图像有透明通道
                mask = Image.open(mask_path).convert("L")  # 将 mask 转换为灰度图像（黑白）
                # 计算裁剪区域的左上角和右下角坐标
                crop_box = ( center[0]-250, center[1]-250,center[0]+250, center[1]+250)
                # 裁剪原始图片
                cropped_image = image.crop(crop_box)
                cropped_mask = mask.crop(crop_box)
                # 创建透明遮罩
                # 将 mask 中黑色部分 (值为 0) 转换为透明，白色部分保持原样
                transparent_mask = cropped_mask.point(lambda p: 0 if p == 0 else 255)
                # 将 mask 应用于原图像，使黑色部分透明
                cropped_image.putalpha(transparent_mask)
                # 保存结果
                cropped_image.save(trans_file_path, "PNG")

        #对svg模式下的uniform元素进行变换处理
        if type =='svg':
            files = os.listdir(f'./workdir/{str(id)}/outline_files')
            uniform_files = [f for f in files if f.startswith('uniform')]
            for i in range(len(uniform_files)):
                file_path = f'./workdir/{str(id)}/outline_files/uniform_{i+1}.svg'
                trans_file_path = f'./workdir/{str(id)}/outline_files/trans_uniform_{i+1}.svg'
                json_path = f'./workdir/{str(id)}/outline_files/{i+1}.json'
                # 读取 JSON 文件
                with open(json_path, 'r') as file:
                    data = json.load(file)
                    center = [data["center_x"],data["center_y"]]
                tree = ET.parse(file_path)
                root = tree.getroot()

                # 添加viewBox属性到根元素
                viewbox_value = f" {center[0] - 50} {center[1] - 50} 100 100"  # 你想要设置的viewBox值
                root.set("viewBox", viewbox_value)

                # 保存修改后的SVG文件
                tree.write(trans_file_path)

        print("file prepared")

        #自定义初始化位置信息，以区域为单位
        custom_init_meg = []
        merged_dict = {}
        longer_edge = width if width > height else height
        for i,detail in enumerate(allDetail):
            type = detail["type"]
            if type == 'point':
                indices = [i for i in range(sum(len(item) for item in selectedData[:i]),sum(len(item) for item in selectedData[:i+1]))]
                center_offset_x = detail['traceLastPoint'][0]-width/2
                center_offset_y = detail['traceLastPoint'][1]-height/2
                new_x_in_1000 = (center_offset_x + longer_edge/2)/longer_edge*1000
                new_y_in_1000 = (center_offset_y + longer_edge/2)/longer_edge*1000
                
                custom_init_meg.append({
                'indices': indices,
                'init_points': [[new_x_in_1000,new_y_in_1000]]*len(indices),
                'type':type,
                'assignId':[detail["assignId"]]*len(indices),
                'lineId':[detail["lineId"]]*len(indices)
                })
                
            elif type == 'line':
                areaId = detail["areaId"]
                indices = [i for i in range(sum(len(item) for item in selectedData[:i]),sum(len(item) for item in selectedData[:i+1]))]
                if areaId not in merged_dict:
                    merged_dict[areaId] = {
                        'indices': indices,
                        'type':type,
                        'assignId':[detail["assignId"]]*len(indices),
                        'lineId':[None]*len(indices)
                    }
                else:
                    merged_dict[areaId]['indices'].extend(indices)
                    merged_dict[areaId]['assignId'].extend([detail["assignId"]]*len(indices))
                    merged_dict[areaId]['lineId'].extend([None]*len(indices))
                new_points_in_1000 = []
                for point in detail['areaPoints']:
                    center_offset_x = point[0]-width/2
                    center_offset_y = point[1]-height/2
                    new_x_in_1000 = (center_offset_x + longer_edge/2)/longer_edge*1000
                    new_y_in_1000 = (center_offset_y + longer_edge/2)/longer_edge*1000
                    new_points_in_1000.append([new_x_in_1000,new_y_in_1000])
                merged_dict[areaId]['init_points'] = sample_area_points(new_points_in_1000,len(merged_dict[areaId]['indices']))
                
            elif type == 'area' :
                # 创建一个白色背景的图片
                img = Image.new('RGB', (width, height), 'white')
                draw = ImageDraw.Draw(img)
                tuple_coordinates_list = [tuple(coord) for coord in detail["areaPoints"]]
            
                # 绘制黑色多边形
                draw.polygon(tuple_coordinates_list, outline='black', fill='black')
                img = square(img)
                # 保存图片到内存中
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                # 将图片编码为Base64字符串
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                areaId = detail["areaId"]
                indices = [i for i in range(sum(len(item) for item in selectedData[:i]),sum(len(item) for item in selectedData[:i+1]))]
                if areaId not in merged_dict:
                    merged_dict[areaId] = {
                        'indices': indices,
                        'init_mask': img_base64,
                        'type':'area',
                        'assignId':[detail["assignId"]]*len(indices),
                        'lineId':[None]*len(indices)
                    }
                else:
                    merged_dict[areaId]['indices'].extend([i for i in range(sum(len(item) for item in selectedData[:i]),sum(len(item) for item in selectedData[:i+1]))])
                    merged_dict[areaId]['assignId'].extend([detail["assignId"]]*len(indices))
                    merged_dict[areaId]['lineId'].extend([None]*len(indices))
        #对merged_dist中的面发射类进行距离场处理
        for key, value in merged_dict.items():
            if value['type'] == 'area':
                init_config = copy.copy(_config)
                # 将Base64字符串解码为字节流
                image_data = base64.b64decode(value["init_mask"])
                # 使用io.BytesIO创建一个BytesIO对象
                image_stream = io.BytesIO(image_data)
                init_config.target_shape_mask_dir= image_stream
                init_config.weights_list = [ weights_list[i] for i in value["indices"]]
                
                sc = ShapeCollage(init_config, device, progress_callback, stop_ids, str(id),fileIndices = value["indices"])
                size, _, pos = sc.init_shapes_properties()
                pos = [tensor.tolist() for tensor in pos]
                pos = [inner[0] for inner in pos]
                size = [tensor.tolist() for tensor in size]
                size = [inner[0] for inner in size]
                merged_dict[key]['init_points'] = pos
                
        #把所有的合并字典的值放到这个custom_init_meg
        custom_init_meg.extend(merged_dict.values())
        
        custom_init_indices = sum([item['indices'] for item in custom_init_meg], [])
        custom_init_pos = sum([item['init_points'] for item in custom_init_meg], []) 
        custom_init_assignId = sum([item['assignId'] for item in custom_init_meg], []) 
        custom_init_lineId = sum([item['lineId'] for item in custom_init_meg], []) 
        #把乱序的位置返回根据索引排好
        sorted_custom_init_pos = [file for _, file in sorted(zip(custom_init_indices, custom_init_pos))]
        sorted_custom_init_assignId = [file for _, file in sorted(zip(custom_init_indices, custom_init_assignId))]
        sorted_custom_init_lineId = [file for _, file in sorted(zip(custom_init_indices, custom_init_lineId))]
        result_data[str(id)]['assignId'] = sorted_custom_init_assignId
        result_data[str(id)]['lineId'] = sorted_custom_init_lineId
        primitive_mask_list = [f"./workdir/{str(id)}/outline_files/{i+1}.png" for i in range(len(weights_list))]
        primitive_json_list = [f"./workdir/{str(id)}/outline_files/{i+1}.json" for i in range(len(weights_list))]
        mask = f'./workdir/{str(id)}/target_shape.png'

        new_pos,new_size = df_with_origin (primitive_mask_list,mask,sorted_custom_init_pos,primitive_json_list,weights_list, _config.initialize_fill_ratio)
        print("start collage")
        def startCollage( _config, device, progress_callback, stop_ids, id, new_pos, new_size, render_every_step, result_callback):
            global working
            sc = ShapeCollage(_config, device, progress_callback, stop_ids, str(id), custom_init_pos = new_pos, custom_init_size = new_size , render_every_step = render_every_step, result_callback = result_callback)
            sc.shape_collage()
            working = False
        # 启动一个线程运行collage
        threading.Thread(target=startCollage, args=(_config, device, progress_callback, stop_ids, id, new_pos, new_size, False, result_callback), daemon=True).start()
        
        
        #获取现有结果
        result = copy.deepcopy(result_data.get(str(id), {}))
        result['origin_pos'] = []
        result['des_pos'] = []
        for i in range(len(sorted_custom_init_pos)):
            result['origin_pos'].append ([(sorted_custom_init_pos[i][0] / 1000) * result['width'] - (result['width'] / 2),(sorted_custom_init_pos[i][1] / 1000) * result['height'] - (result['height'] / 2)])
        for i in range(len(new_pos)):
            result['des_pos'].append([(new_pos[i][0] / 1000) * result['width'] - (result['width'] / 2),(new_pos[i][1] / 1000) * result['height'] - (result['height'] / 2)])

        result['assignId'] = sorted_custom_init_assignId
        result['lineId'] = sorted_custom_init_lineId
        result['des_size'] = new_size
        return jsonify({'message': '处理结束','status':0 ,'result':result})
    
        
    except Exception as e:
        error_message = str(e)
        print(error_message)
        return {'status': -2, 'message': error_message}
           

@app.route('/getProgress', methods=['GET'])
def getProgress():
    # 从请求参数中获取ID
    id = request.args.get('id')#str
    # 获取进度
    progress = progress_data.get(id,{})  # 默认进度为0
   
    #获取现有结果
    result = copy.deepcopy(result_data.get(id, {}))

    try:
        collage_result = False
        if os.path.exists(f"./workdir/{str(id)}/final.svg") or os.path.exists(f"./workdir/{str(id)}/final.png"):
            collage_result = True
        if 'pos' in result:
            for i in range(len(result['pos'])):
                result['pos'][i][0] = (result['pos'][i][0] / 1000) * result['width'] - (result['width'] / 2)
                result['pos'][i][1] = (result['pos'][i][1] / 1000) * result['height'] - (result['height'] / 2)
            return {'status': 0,'progress': progress,'result':result,'collage_result':collage_result}
        else:
            return {'status': 0,'progress': progress,'result':{},'collage_result':collage_result}
       
    except Exception as e:
        error_message = str(e)
        print(error_message)
        return {'status': -1, 'error': error_message}

@app.route('/stop_process' , methods=['POST'])
def stop_process():
    global stop_ids
    data = request.get_json()
    id = data['id']
    stop_ids.append(str(id))
    return jsonify({'message': 'Stop signal received','id':id})

@app.route('/get_working', methods=['GET'])
def get_working():
    global working
    # 构建返回的 JSON 数据
    response_data = {
        'working': working,
    }
    return response_data
    
def progress_callback(type, steps,totalSteps, task_id):
    global progress_data
    progress_data[task_id] = {
        'type':type,
        'steps':steps,
        'totalSteps':totalSteps
    }

def result_callback(pos, size,angle, task_id):
    global result_data
    result_data[task_id]['pos'] = pos
    result_data[task_id]['size'] = size
    result_data[task_id]['angle'] = angle

def base64_to_image(base64_data):
    image_data = base64.b64decode(base64_data)
    image = Image.open(BytesIO(image_data))
    return image
def sample_area_points(area_points, n):
    # 获取 areaPoints 的长度
    total_points = len(area_points)
    
    if total_points == 0 or n <= 0:
        return []  # 如果 areaPoints 为空或 n 小于等于0，返回空列表

    # 计算步长
    step = total_points / n

    sampled_points = []
    
    for i in range(n):
        # 计算当前采样点的位置
        index = int(i * step)  # 计算索引
        # 确保索引不超过原数组的范围
        if index < total_points:
            sampled_points.append(area_points[index])
    #打乱位置
    random.shuffle(sampled_points)
    return sampled_points

if __name__ == '__main__':
    app.run(debug = True,host = '0.0.0.0')