import numpy as np  # 导入NumPy库，用于数值计算
import requests  # 导入requests库，用于发送HTTP请求
import json  # 导入json库，用于处理JSON数据
import base64  # 导入base64库，用于编码和解码base64格式的数据
import os  # 导入os库，用于文件和目录操作
import argparse  # 导入argparse库，用于解析命令行参数

# 定义一个将字符串转换为布尔值的函数
def str2bool(v):
    return v.lower() in ("true", "t", "1")

# 创建一个命令行参数解析器，并定义参数
parser = argparse.ArgumentParser(description="args for paddleserving")
parser.add_argument("--image_dir", type=str, default="D:/ppocr_img/ppocr_img/imgs/")  # 定义图像目录参数(可单图，可指定文件夹内多图)
parser.add_argument("--det", type=str2bool, default=True)  # 定义文本检测参数
parser.add_argument("--rec", type=str2bool, default=True)  # 定义文本识别参数
args = parser.parse_args()  # 解析命令行参数

# 定义一个函数，将图像数据转换为base64编码的字符串
def cv2_to_base64(image):
    return base64.b64encode(image).decode("utf8")

# 定义一个函数，用于检查文件是否为图像文件
def _check_image_file(path):
    img_end = {"jpg", "bmp", "png", "jpeg", "rgb", "tif", "tiff", "gif"}  # 定义图像文件的扩展名集合
    return any([path.lower().endswith(e) for e in img_end])  # 检查文件扩展名是否在集合中

url = "http://8.138.145.157:9998/ocr/prediction"  # OCR服务器的URL
test_img_dir = args.image_dir  # 从命令行参数中获取图像目录

test_img_list = []  # 初始化图像文件列表
# 如果路径是文件并且是图像文件，则将其添加到列表中
if os.path.isfile(test_img_dir) and _check_image_file(test_img_dir):
    test_img_list.append(test_img_dir)
# 如果路径是目录，则遍历目录中的文件并检查是否为图像文件
elif os.path.isdir(test_img_dir):
    for single_file in os.listdir(test_img_dir):
        file_path = os.path.join(test_img_dir, single_file)  # 获取文件的完整路径
        if os.path.isfile(file_path) and _check_image_file(file_path):  # 如果是文件并且是图像文件，则添加到列表中
            test_img_list.append(file_path)
# 如果列表为空，抛出异常
if len(test_img_list) == 0:
    raise Exception("not found any img file in {}".format(test_img_dir))

# 遍历图像文件列表，逐个处理
for idx, img_file in enumerate(test_img_list):
    with open(img_file, "rb") as file:  # 以二进制模式打开图像文件
        image_data1 = file.read()  # 读取图像数据
    print("{}{}{}".format("-" * 10, img_file, "-" * 10))  # 打印分隔符和文件名

    image = cv2_to_base64(image_data1)  # 将图像数据转换为base64编码
    data = {"key": ["image"], "value": [image]}  # 准备发送到服务器的请求数据
    
    r = requests.post(url=url, data=json.dumps(data))  # 向OCR服务器发送POST请求
    print("服务器响应状态码:", r.status_code)  # 打印服务器响应的状态码
    
    try:
        result = r.json()  # 尝试解析服务器返回的JSON数据
    except json.JSONDecodeError as e:  # 如果解析失败，捕获异常
        print("JSON decode error:", e)  # 打印异常信息
        print("erro_no:{}, err_msg:{}".format(result["err_no"], result["err_msg"]))  # 打印错误信息
        continue  # 继续处理下一张图像
    
    # 如果OCR识别成功
    if result["err_no"] == 0:
        ocr_result = result["value"][0]  # 获取OCR识别结果
        if not args.det:  # 如果不需要文本检测，直接打印结果
            print(ocr_result)
        else:
            try:
                text_lines = []  # 初始化存储文本的列表
                for item in eval(ocr_result):  # 解析OCR结果
                    text = item[0][0]  # 只提取文本部分
                    text_lines.append(text)  # 添加到文本列表中
                    
                    print(text)  # 打印识别出的文本
                #print(text_lines)  # 打印所有文本行
            except Exception as e:  # 捕获可能的异常
                print(ocr_result)  # 打印原始OCR结果
                print("未检测到文本，请检查图片是否包含文字以及清晰度是否达标")  # 打印错误提示
                continue  # 继续处理下一张图像
    else:
        print("查看更多错误信息于： PipelineServingLogs/pipeline.log")  # 如果有错误，提示查看日志
print("==> 处理图片数量: ", len(test_img_list))  # 打印处理的图像数量
