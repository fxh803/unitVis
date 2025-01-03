import requests
import base64
def sam(prompt,image_base64):
    url = "http://192.168.152.85:62001"
    data = {
        "sam_model_name": "sam_vit_b_01ec64.pth",  # 蒙版模型名称
        "input_image": image_base64,  # 图像base64
        "sam_negative_points": [],  # 反选中坐标点
        "dino_enabled": True,  # 开启文字识别 例如一只猫在草坪上，想要得到猫的蒙版 可以使用 cat 会自动识别物品
        "dino_model_name": "GroundingDINO_SwinT_OGC (694MB)",  # 文字识别模型
        "dino_text_prompt": prompt,  # 文字（要英语）例如 cat
    }

    response = requests.post(url=f'{url}/sam/sam-predict', json=data)
    r = response.json() # dict_keys(['msg', 'blended_images', 'masks', 'masked_images'])
    # print(r)
    return r["blended_images"][0],r["masks"][0],r["masked_images"][0]