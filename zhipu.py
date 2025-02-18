import base64
import time
import requests

API_URL = "http://localhost:8000/AI_ALL/"
HEADERS = {"Content-Type": "application/json"}    # 改回 json 格式

def test_generate_video(prompt, image_input=None, model="cogvideox-flash"):
    """
    测试视频生成
    :param prompt: 文本描述
    :param image_input: 图片输入（可选，支持URL或本地路径）
    :param model: 模型名称
    :return: 生成的视频URL
    """
    data = {
        'model': model,
        'text': prompt
    }

    try:
        # 处理请求
        if image_input:
            if image_input.startswith(('http://', 'https://')):
                data['url'] = image_input
                response = requests.post(API_URL, data=data)
            else:
                with open(image_input, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(API_URL, data=data, files=files)
        else:
            response = requests.post(API_URL, data=data)

        if response.status_code != 200:
            print(f"请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None

        # 处理流式响应
        video_url = None
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(f"收到响应: {line}")  # 调试输出
                type_data = line.split(':', 1)
                if len(type_data) == 2:
                    content_type, content_data = type_data
                    if content_type == 'video_url':
                        video_url = content_data.strip()
                        print(f"获取到视频URL: {video_url}")
                    elif content_type == 'status':
                        print(f"当前状态: {content_data}")
                    elif content_type == 'error':
                        print(f"错误: {content_data}")
                        return None

        return video_url

    except Exception as e:
        print(f"请求失败: {e}")
        return None

def check_video_result(task_id, interval=20, max_retries=120):
    """检查视频生成结果"""
    for _ in range(max_retries):
        try:
            # 构建状态查询请求
            check_payload = {
                "action": "check_status",
                "task_id": task_id
            }
            
            response = requests.post(API_URL, json=check_payload, headers=HEADERS)
            if response.status_code != 200:
                print(f"检查任务状态失败: {response.json().get('error', '未知错误')}")
                continue
                
            result = response.json()
            status = result.get('task_status')
            print(f"当前状态: {status}")
            
            if status == "SUCCESS":
                video_result = result.get('video_result', [])
                if not video_result:
                    print("无视频结果")
                    return None
                    
                first_video = video_result[0]
                return {
                    "video_url": first_video.get('url'),
                    "cover_url": first_video.get('cover_image_url')
                }
            elif status in ["FAIL", "failed", "error"]:
                print("视频生成失败")
                return None
                
            time.sleep(interval)
            
        except Exception as e:
            print(f"检查结果失败: {e}")
            time.sleep(interval)
    
    print("等待超时")
    return None

if __name__ == "__main__":
    # 测试用例1：文生视频
    print("\n=== 测试用例1：文生视频 ===")
    result1 = test_generate_video(
        prompt="一朵盛开的红玫瑰",
        model="cogvideox-flash"
    )
    print("生成结果:", result1)
    
    # 测试用例2：图片URL生成
    print("\n=== 测试用例2：图片URL生成 ===")
    result2 = test_generate_video(
        prompt="让这朵花绽放",
        image_input="http://obs.roseyy.cn/test.jpg",
        model="cogvideox-flash"
    )
    print("生成结果:", result2)
    
    # 测试用例3：本地图片生成
    print("\n=== 测试用例3：本地图片生成 ===")
    result3 = test_generate_video(
        prompt="让图片动起来",
        image_input="C:/Users/58300/Desktop/rag/test.jpg",
        model="cogvideox-flash"
    )
    print("生成结果:", result3) 