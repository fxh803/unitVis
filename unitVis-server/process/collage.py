import requests
import base64
from PIL import Image
import time
import base64
import io
import threading
# 创建一个全局标志
stop_event = threading.Event()
address = 'http://192.168.152.85:62002'
def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        # 读取图像文件内容
        img_data = img_file.read()
        # 将图像内容编码为Base64格式
        encoded_image = base64.b64encode(img_data).decode('utf-8')
    
    return encoded_image

def send_get_request(id):
    global stop
    while not stop_event.is_set():
        response = requests.get(f'{address}/get_progress?id={id}')
        print(response.json())
        time.sleep(3)
 
def decode_base64_to_png(base64_string, output_path):
    # 解码base64字符串为字节数据
    image_data = base64.b64decode(base64_string)

    # 创建BytesIO对象并将解码后的数据写入其中
    image_stream = io.BytesIO(image_data)

    # 打开Image对象
    image = Image.open(image_stream)
    # 转换图像为RGB模式
    image = image.convert('RGBA')
    # 保存图像为PNG格式
    image.save(output_path, 'PNG')

def collage(ele_path,mask_path,output_path):
    
    # 本地图像文件路径
    elements_base64 = [image_to_base64(ele_path)]*5
    mask_base64 = image_to_base64(mask_path)
    id = str(int(time.time()))
    # 启动一个线程来定时发送 GET 请求
    thread = threading.Thread(target=send_get_request, args=(id,), daemon=True)
    thread.start()

    # 构造数据
    data = {
        'elements_class': 'any_shape_raster',#any_shape_raster或any_shape_svg
        'elements': elements_base64,  # 请替换为实际的base64图像数据
        'mask': mask_base64,  # 请替换为实际的base64掩模图像数据
        'multiple':4,
        'weights_list':[1,1.2,1.3,1.4,1.5],
        'id': id,  # 使用当前时间戳作为ID
        'shape_class':'closed'
    }
    # 发送POST请求
    response = requests.post(f'{address}/process_data', json=data)
    r = response.json()
    print(r["message"])
    decode_base64_to_png(r["result"],output_path)
    # 停止线程
    stop_event.set()
    thread.join()
    stop_event.clear()
    
