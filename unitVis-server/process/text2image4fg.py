import requests
import base64

def text2image4fg(prompt,controlNet_image=None):
    usingControlNet = False
    if(controlNet_image!=None):
        usingControlNet = True
        print("正在使用controlnet")
    url = "http://192.168.152.85:62001"
    data = {
        "prompt": prompt+"<lora:F2D:0.7>, flat color, isolated, (simple background:1.2), no face, (no shadow:1.2), (light fresh style:1.2), (minimalism:1.2), vector art, clean lines, illustration, graphic design ",
        "negative_prompt": "worst quality, low quality, text, watermark, signature, username, error, meme, poorly drawn, low-resolution, low-quality, blurry, glossy, overexposed, pattern",
        "steps": 20,
        "sampler_name": "DPM++ 2M SDE",#Sampling method
        "scheduler": "Karras",#Schedule type
        "enable_hr": True,
        "hr_upscaler": "R-ESRGAN 4x+",
        "hr_resize_x": 1024,
        "hr_resize_y": 1024,
        "hr_scale": 2,
        "denoising_strength": 0.7,
        "hr_second_pass_steps": 20,
        "override_settings": {
            "sd_model_checkpoint": "albedobaseXL_v21.safetensors [1718b5bb2d]",  # 指定大模型
        },

        "alwayson_scripts": {
                "controlnet":
                    {
                        "args": [
                            {
                                "enabled": usingControlNet,  # 启用
                                "module": "reference_only",  # 对应webui 的 Preprocessor
                                "weight": 1,  # 对应webui 的Control Weight
                                "resize_mode": "Crop and Resize",
                                "guidance_start": 0,  # 什么时候介入 对应webui 的 Starting Control Step
                                "guidance_end": 1,  # 什么时候退出 对应webui 的 Ending Control Step
                                "pixel_perfect": True,  # 像素完美
                                "processor_res": 512,  # 预处理器分辨率
                                "save_detected_map": False,  # 因为使用了 controlnet API会返回生成controlnet的效果图，默认是True，如何不需要，改成False
                                "image": controlNet_image,  # 图片 格式为base64

                            }
                        ]
                    }
            },

    }

    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=data)
    r = response.json()
    # print(r)

    return r['images'][0]