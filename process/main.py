import base64
import time
import os
from sam import sam
from text2image import text2image
def image_to_base64(image_path):
    try:
        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        return base64_image
    except FileNotFoundError:
        return "File not found. Please check the path and try again."

#新建处理文件夹
start_time = int(time.time())
folder_path =f'result/{start_time}'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
#前景和背景的prompt
background_prompt = "a glass bottle to fill coffee bean"
foreground_prompt = "a coffee bean"
#生成背景
background_image = text2image(background_prompt)
with open(f"result/{start_time}/background_image.png", 'wb') as f:
        f.write(base64.b64decode(background_image))

#将生成的背景的目标物抠出来
blend_img, mask, masked_img = sam(background_prompt,background_image)
with open(f"result/{start_time}/blend_img1.png", 'wb') as f:
        f.write(base64.b64decode(blend_img))
with open(f"result/{start_time}/mask_png1.png", 'wb') as f:
        f.write(base64.b64decode(mask))        
with open(f"result/{start_time}/masked_background.png", 'wb') as f:
        f.write(base64.b64decode(masked_img))

#生成前景
foreground_image = text2image(foreground_prompt,masked_img)
with open(f"result/{start_time}/foreground_image.png", 'wb') as f:
        f.write(base64.b64decode(foreground_image))

#把前景的目标抠出来
blend_img, mask, masked_img = sam(foreground_prompt,foreground_image)
with open(f"result/{start_time}/blend_img2.png", 'wb') as f:
        f.write(base64.b64decode(blend_img))
with open(f"result/{start_time}/mask_png2.png", 'wb') as f:
        f.write(base64.b64decode(mask))        
with open(f"result/{start_time}/masked_foreground.png", 'wb') as f:
        f.write(base64.b64decode(masked_img))

end_time = int(time.time())

execution_time = end_time - start_time  # 计算运行时间，以秒为单位
execution_time_minutes = int(execution_time / 60)
execution_time_seconds = execution_time % 60
print(f"代码运行时间：{execution_time_minutes}分钟,{execution_time_seconds}秒")




