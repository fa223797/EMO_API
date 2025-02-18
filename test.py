import requests
import json
from pathlib import Path
import re
import base64
import numpy as np
import soundfile as sf
import pyaudio
import time

# 测试基础配置
BASE_URL = "http://localhost:8000/AI_ALL/"
VOICE = "Chelsie"  # 固定使用 Chelsie 音色

def play_audio(audio_string):
    """播放音频响应"""
    if audio_string:
        try:
            wav_bytes = base64.b64decode(audio_string)
            audio_np = np.frombuffer(wav_bytes, dtype=np.int16)
            sf.write('audio_response.wav', audio_np, samplerate=24000)
            
            # 播放音频
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
            stream.write(audio_np.tobytes())
            time.sleep(0.8)
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            print(f"音频播放失败: {e}")

def test_model(text, file_path=None, url=None):
    """测试通义千问多模态模型"""
    session = requests.Session()
    data = {
        'model': 'qwen-omni-turbo',  # 使用通义千问多模态模型
        'text': text,
        'voice': VOICE
    }
    
    if url:
        data['url'] = url
        
    files = None
    if file_path:
        try:
            files = {'file': open(file_path, 'rb')}
        except Exception as e:
            print(f"打开文件失败: {e}")
            return
    
    try:
        print(f"\n=== 测试 qwen-omni-turbo ===")
        print(f"输入: {text}")
        if url:
            print(f"URL: {url}")
        if file_path:
            print(f"文件: {file_path}")
            
        response = session.post(BASE_URL, data=data, files=files, stream=True)
        
        if response.status_code == 200:
            print("\nAI回复:")
            audio_string = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('audio:'):
                        audio_string += line[6:]
                    elif line.startswith('text:'):
                        text_content = line[5:]
                        print(text_content, end='', flush=True)
            
            print("\n")
            # 播放音频响应
            if audio_string:
                print("\n正在播放音频响应...")
                play_audio(audio_string)
                time.sleep(1)  # 等待音频播放完成
        else:
            print(f"请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")
    finally:
        if files and 'file' in files:
            files['file'].close()

def run_all_tests():
    """运行所有测试"""
    print("\n=== 开始自动测试 ===")
    
    # 1. 文本测试
    print("\n=== 测试1：文本对话 ===")
    test_model("你好")
    time.sleep(2)
    
    # 2. URL测试
    print("\n=== 测试2：URL多媒体测试 ===")
    
    # 图片URL测试
    test_model("这张图片是什么内容？",
              url="http://obs.roseyy.cn/test.jpg")
    time.sleep(2)
    
    # 音频URL测试
    test_model("这段音频说了什么内容？",
              url="https://obs.roseyy.cn/test.wav")
    time.sleep(2)
    
    # 视频URL测试
    test_model("这个视频怎么样？",
              url="https://obs.roseyy.cn/test.mp4")
    time.sleep(2)
    
    # 3. 本地文件测试
    print("\n=== 测试3：本地文件测试 ===")
    
    # 本地图片测试
    test_model("这张图片怎么办？",
              file_path=r"C:\Users\58300\Desktop\rag\test.jpg")
    time.sleep(2)
    
    # 本地音频测试
    test_model("这段音频怎么办？",
              file_path=r"C:\Users\58300\Desktop\rag\test.wav")
    time.sleep(2)
    
    # 本地视频测试
    test_model("这个视频怎么办？",
              file_path=r"C:\Users\58300\Desktop\rag\test.mp4")
    
    print("\n=== 自动测试完成 ===")

if __name__ == "__main__":
    run_all_tests()