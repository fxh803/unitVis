# def uploadMask():
    # height = request.json['canvasHeight'] 
    # width = request.json['canvasWidth'] 
    # image = request.json['image'] 
    # points = request.json['points']
    # control_image = None
    # mask_image = None
    # if points != []:
    #     # 创建单通道空白画布
    #     pointsImage = np.ones((height, width,3), dtype=np.uint8)*255
    #     masksImage = np.ones((height, width,3), dtype=np.uint8)*255
    #     # 解析线条数据
    #     for _points in points:
    #         points_array = np.array([(point['x'], point['y']) for point in _points], dtype=np.int32)
    #         # 绘制线段
    #         cv2.polylines(pointsImage, [points_array], isClosed=False, color=(0, 0, 0), thickness=1)
    #     for _points in points:
    #         points_array = np.array([(point['x'], point['y']) for point in _points], dtype=np.int32)
    #         # 绘制多边形
    #         cv2.fillPoly(masksImage, [points_array], color=(0, 0, 0))
    #     control_image = Image.fromarray(cv2.cvtColor(pointsImage, cv2.COLOR_BGR2RGB))
    #     control_image =  crop_to_square(control_image)
    #     mask_image = Image.fromarray(cv2.cvtColor(masksImage, cv2.COLOR_BGR2RGB))
    #     mask_image =  crop_to_square(mask_image)
    #     mask_image = erode(mask_image)

    # #前景和背景的prompt
    # background_prompt = "a flat style empty water bottle"
    # foreground_prompt = "one flat style waterDrop"
    # main(background_prompt,foreground_prompt,control_image = control_image,mask_image = mask_image)

    # return jsonify({'message': 'Image uploaded successfully','status':0})