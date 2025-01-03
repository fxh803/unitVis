import base64
import time
import os
import io
from PIL import Image
from process.erode import erode
from process.sam import sam
from process.text2image4bg import text2image4bg
from process.text2image4fg import text2image4fg
from process.collage import collage
from process.mask2mask import mask2mask
from process.combinePNG import combinePNG
def image_to_base64(image_path):
    try:
        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        return base64_image
    except FileNotFoundError:
        return "File not found. Please check the path and try again."
	
def main(background_prompt,foreground_prompt,control_image= None,mask_image = None):

	start_time = int(time.time())
	#新建处理文件夹
	folder_path =f'result/{background_prompt}&{foreground_prompt}_{start_time}'
	if not os.path.exists(folder_path):
		os.makedirs(folder_path)
	#保存控制图片
	base64_control_image = None
	if control_image!=None:
		control_image.save(os.path.join(folder_path,"control_image.png"))
		# 将控制图片编码为base64字符串
		img_byte_arr = io.BytesIO()
		control_image.save(img_byte_arr, format='PNG') 
		img_byte_arr = img_byte_arr.getvalue()
		base64_control_image = base64.b64encode(img_byte_arr).decode('utf-8')
	#保存自定义mask
	if mask_image !=None:
		mask_image.save(os.path.join(folder_path,"target_shape.png"))

	#生成背景
	print("正在生成背景")
	background_image = text2image4bg(background_prompt,base64_control_image)
	with open(os.path.join(folder_path,"background_image.png"), 'wb') as f:
			f.write(base64.b64decode(background_image))

	#将生成的背景的目标物抠出来
	print("正在分割背景")
	blend_img, mask, masked_img = sam(background_prompt,background_image)
	# with open(os.path.join(folder_path,"blend_img1.png"), 'wb') as f:
	# 		f.write(base64.b64decode(blend_img))
	with open(os.path.join(folder_path,"background_mask.png"), 'wb') as f:
			f.write(base64.b64decode(mask))        
	with open(os.path.join(folder_path,"masked_background.png"), 'wb') as f:
			f.write(base64.b64decode(masked_img))

	#生成前景
	print("正在生成前景")
	foreground_image = text2image4fg(foreground_prompt,masked_img)
	with open(os.path.join(folder_path,"foreground_image.png"), 'wb') as f:
			f.write(base64.b64decode(foreground_image))

	#把前景的目标抠出来
	print("正在分割前景")
	blend_img, mask, masked_img = sam(foreground_prompt,foreground_image)
	# with open(os.path.join(folder_path,"blend_img2.png"), 'wb') as f:
	# 		f.write(base64.b64decode(blend_img))
	with open(os.path.join(folder_path,"foreground_mask.png"), 'wb') as f:
			f.write(base64.b64decode(mask))        
	with open(os.path.join(folder_path,"masked_foreground.png"), 'wb') as f:
			f.write(base64.b64decode(masked_img))

	end_time = int(time.time())

	execution_time = end_time - start_time  # 计算运行时间，以秒为单位
	execution_time_minutes = int(execution_time / 60)
	execution_time_seconds = execution_time % 60
	print(f"生成运行时间：{execution_time_minutes}分钟,{execution_time_seconds}秒")

	if mask_image==None:
		#mask反色
		mask2mask(f'{folder_path}/background_mask.png',f'{folder_path}/target_shape.png')
		image = Image.open(f'{folder_path}/target_shape.png')
		image = erode(image)
		image.save(f'{folder_path}/target_shape.png')
		print("反色完成")
	#开始collage
	collage(f'{folder_path}/masked_foreground.png',f'{folder_path}/target_shape.png',f'{folder_path}/collage.png')
	print("拼贴完成")
	#合成
	combinePNG(f'{folder_path}/collage.png',f'{folder_path}/background_image.png',f'{folder_path}/result.png')
	print("合成完成")



