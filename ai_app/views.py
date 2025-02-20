from django.shortcuts import render  # 导入Django的render函数用于渲染页面模板
from rest_framework.views import APIView  # 导入DRF的APIView类，用于创建API视图
from rest_framework.response import Response  # 导入DRF的Response对象，用于构建HTTP响应
from rest_framework import status  # 导入DRF的状态码模块，便于返回标准HTTP状态码
import requests  # 导入requests库，用于发送HTTP请求
import json  # 导入json库，用于处理JSON数据
import base64  # 导入base64库，用于处理Base64编码
from zhipuai import ZhipuAI  # 导入ZhipuAI库，用于调用智谱AI的API
from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL
from dashscope import Generation 
from django.http  import StreamingHttpResponse, JsonResponse 
from openai import OpenAI
from pathlib import Path
import dashscope
import time
from .models import ModelInfo
from rest_framework import viewsets
from .serializers import ModelInfoSerializer



# 统一的API密钥配置
API_KEY = "98fd7efde5b04a9ab8ded261b0cd54e5.iSTkJXlCzxR1rMC9"#GLM的API密钥
COZE_API_TOKEN = 'pat_g29XD40XKp9DFbztQUVFzbbarqPceZ7jhIOGDkqeEHpcMYhL753COSdIF4xMLt6P'  # COZE的API令牌
COZE_BOT_ID = '7471264796252487689'  # COZE的机器人ID
COZE_BASE_URL = COZE_CN_BASE_URL  # COZE的基础URL
Qwen_APIKEY = "sk-e820da316ff34addb3c12d4be1461e96"# Qwen的秘钥
# 合体api
class AI_ALL(APIView):
    def post(self, request):
        try:
            # 获取通用参数
            model_name = request.POST.get('model', '')
            text = request.POST.get('text', '')
            file = request.FILES.get('file') 
            url = request.POST.get('url', '')
            voice = request.POST.get('voice', 'Cherry')
 
            # 参数验证 
            if not model_name:
                return JsonResponse({'error': 'model参数必填'}, status=400)
 
            # 根据模型类型处理输入
            content_type = self.detect_content_type(model_name) 
 
            # 处理文件上传
            file_data = None
            if file:
                file_data = base64.b64encode(file.read()).decode('utf-8') 
 
            # 构建消息内容
            messages = request.session.get(f'{model_name}_history', [])
            
            # 特殊处理视频生成模型
            if 'cogvideox' in model_name:
                try:
                    client = ZhipuAI(api_key=API_KEY)
                    
                    # 构建视频生成参数
                    generation_params = {
                        "model": model_name,  # 使用完整的模型名称
                        "prompt": text,
                        "quality": "quality",
                        "with_audio": True,
                        "size": "720x480",
                        "fps": 30
                    }
                    
                    # 添加图片URL（如果有）
                    if url:
                        generation_params["image_url"] = url
                    elif file_data:
                        generation_params["image_url"] = f"data:image/jpeg;base64,{file_data}"

                    def stream_generator():
                        try:
                            # 生成视频
                            response = client.videos.generations(**generation_params)
                            yield f"status:已获取任务ID: {response.id}\n"
                            
                            # 轮询检查结果
                            for _ in range(120):  # 最多等待120次
                                try:
                                    result = client.videos.retrieve_videos_result(id=response.id)
                                    yield f"status:{result.task_status}\n"
                                    
                                    if result.task_status == "SUCCESS" and hasattr(result, 'video_result'):
                                        video_url = result.video_result[0].url
                                        yield f"video_url:{video_url}\n"
                                        break
                                    elif result.task_status in ["FAIL", "failed", "error"]:
                                        yield f"error:视频生成失败\n"
                                        break
                                        
                                    time.sleep(20)  # 等待20秒再次查询
                                    
                                except Exception as e:
                                    yield f"error:检查结果失败: {str(e)}\n"
                                    break
                                    
                        except Exception as e:
                            yield f"error:生成视频失败: {str(e)}\n"

                    return StreamingHttpResponse(stream_generator(), content_type='text/plain; charset=utf-8')
                    
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)
            else:
                # 其他模型使用标准消息结构
                user_content = self.build_content(content_type, text, url, file_data)
                messages.append({"role": "user", "content": user_content})
 
            # 调用具体模型的API 
            response_generator = self.call_model_api(model_name, messages, voice)
 
            # 更新会话历史
            def stream_generator():
                assistant_response = []
                for chunk in response_generator:
                    content = self.process_chunk(chunk, model_name)
                    if content:
                        assistant_response.append(content) 
                        yield f"{content['type']}:{content['data']}\n"
                messages.append({"role": "assistant", "content": assistant_response})
                request.session[f'{model_name}_history'] = messages 
 
            return StreamingHttpResponse(stream_generator(), content_type='text/plain; charset=utf-8')
 
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
 
    def detect_content_type(self, model_name):
        """根据模型名称判断内容类型"""
        if 'cogvideox' in model_name:  # 修改为包含而不是完全匹配
            return 'video'
        if 'vl' in model_name or 'image' in model_name:
            return 'image'
        if 'audio' in model_name:
            return 'audio'
        return 'text'
 
    def build_content(self, content_type, text, url, file_data):
        """构建不同模型需要的内容结构"""
        content = []
        if content_type == 'text':
            content.append({"type": "text", "text": text})
        else:
            media_url = url or (f"data:{content_type};base64,{file_data}" if file_data else None)
            if not media_url:
                raise ValueError("需要提供url或文件")
            
            # 增加模型前缀判断
            is_qwen = any([model_prefix in self.model_name for model_prefix in ['qwen', 'wanx', 'deepseek']])
            
            if is_qwen:
                media_mapping = {
                    'image': {"type": "image_url", "image_url": {"url": media_url}},
                    'audio': {"type": "input_audio", "input_audio": {"data": media_url}},
                    'video': {"type": "video_url", "video_url": {"url": media_url}}
                }
            else:
                media_mapping = {
                    'image': {"type": "image_url", "image_url": {"url": media_url}},
                    'audio': {"type": "audio", "audio": media_url},
                    'video': {"type": "video", "video": media_url}
                }
            
            content.append(media_mapping[content_type])
            if text:
                content.append({"type": "text", "text": text})
        return content
 
    def call_model_api(self, model_name, messages, voice):
        """调用具体模型的API"""
        # 增加模型前缀判断
        if any([prefix in model_name for prefix in ['glm', 'cogview', 'cogvideox']]):
            client = ZhipuAI(api_key=API_KEY)
            return client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                **self.get_model_params(model_name, voice)
            )
        elif any([prefix in model_name for prefix in ['qwen', 'wanx', 'deepseek']]):
            # 统一处理通义系列模型
            if 'omni' in model_name:
                client = OpenAI(
                    api_key=Qwen_APIKEY,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    modalities=["text", "audio"],
                    audio={"voice": voice, "format": "wav", "rate": 24000}
                )
            elif 'audio' in model_name:
                return dashscope.MultiModalConversation.call(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    incremental_output=True,
                    result_format="message"
                )
            else:
                client = OpenAI(
                    api_key=Qwen_APIKEY,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True
                )
        elif 'coze' in model_name:
            coze = Coze(auth=TokenAuth(token=COZE_API_TOKEN), base_url=COZE_BASE_URL)
            return coze.chat.stream(bot_id=COZE_BOT_ID, user_id="default_user", additional_messages=messages)
        else:
            raise ValueError(f"未知模型: {model_name}")
 
    def get_model_params(self, model_name, voice):
        """获取不同模型的特殊参数"""
        params = {}
        if 'omni' in model_name:
            params.update({
                "tools": [
                    {
                        "type": "text_to_speech",
                        "voice": voice,
                        "format": "wav",
                        "rate": 24000
                    }
                ],
                "tool_choice": "text_to_speech"
            })
        return params
 
    def process_chunk(self, chunk, model_name):
        """处理不同模型的响应块"""
        if 'dashscope' in str(type(chunk)):
            if 'audio' in model_name:
                # 处理音频模型响应
                if hasattr(chunk, 'output') and hasattr(chunk.output, 'choices'):
                    for choice in chunk.output.choices:
                        if hasattr(choice.message, 'content'):
                            return {"type": "text", "data": choice.message.content}
            else:
                # 处理其他通义千问响应
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta'):
                        delta = choice.delta
                        if hasattr(delta, 'content') and delta.content:
                            return {"type": "text", "data": delta.content}
                        elif hasattr(delta, 'audio') and delta.audio:
                            return {"type": "audio", "data": delta.audio}
        elif hasattr(chunk.choices[0].delta, "content"):
            return {"type": "text", "data": chunk.choices[0].delta.content}
        elif hasattr(chunk.choices[0].delta, "audio"):
            return {"type": "audio", "data": chunk.choices[0].delta.audio['data']}
        return None
# 说明文档页面
def api_docs(request):
    """API文档页面"""
    models = ModelInfo.objects.all()
    return render(request, 'api_docs.html', {'models': models})

# REST framework视图
class ModelListView(APIView):
    def get(self, request):
        queryset = ModelInfo.objects.all() 
        serializer = ModelInfoSerializer(queryset, many=True)
        return Response(serializer.data) 



# 模型接口
# GLM模型
# GLM语言模型chat类型，glm-4
class GLM4View(APIView):
    def post(self, request):
        """
        处理POST请求，调用GLM（Generative Language Model）服务并返回结果。
        """
        # 定义GLM服务的URL地址
        glm_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        # 从请求的数据中获取用户的问题，默认为空字符串
        question = request.data.get('question', '')
        
        # 从请求的数据中获取要使用的模型名称
        model_name = request.data.get('model')  # 直接使用传入的模型名称
        
        # 如果问题为空，则返回错误信息并设置HTTP状态码为400 Bad Request
        if not question:
            return Response({"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 构造发送到GLM API的头部信息，包括授权和内容类型
        headers = {
            "Authorization": f"Bearer {API_KEY}",  # 使用API密钥进行身份验证
            "Content-Type": "application/json",     # 指定请求体的内容类型为JSON
        }
        
        # 构建发送给GLM API的请求数据
        data = {
            "model": model_name,  # 请求中指定要使用的模型名称
            
            # 用户的消息部分，包含角色（这里是用户）和具体问题内容
            "messages": [{"role": "user", "content": question}],
            
            # 工具配置：这里指定了一个检索工具
            "tools": [
                {
                    "type": "retrieval",  # 工具类型是"检索"
                    
                    # 具体的检索配置：
                    "retrieval": {
                        "knowledge_id": "1880239333915635712",  # 知识库ID
                        
                        # 提示模板，告诉模型如何处理检索到的信息
                        "prompt_template": (
                            "从文档\n\"\"\"\n{{knowledge}}\n\"\"\"\n中找问题\n\"\"\"\n{{question}}\n\"\"\"\n的答案，"
                            "找到答案就仅使用文档语句回答问题，找不到答案就用自身知识回答。\n"
                            "不要复述问题，直接开始回答。"
                        )
                    }
                }
            ]
        }

        try:
            # 尝试通过requests库发起一个POST请求到GLM API服务器
            response = requests.post(glm_url, headers=headers, json=data)
            
            # 检查API响应的状态码是否在成功范围内（如2xx）。如果不是，则引发HTTPError异常
            response.raise_for_status()
            
            # 返回API的成功响应数据，并将HTTP状态码设为200 OK
            return Response(response.json(), status=status.HTTP_200_OK)
        
        except requests.exceptions.RequestException as e:
            # 如果发生任何与网络请求相关的错误（例如连接失败、超时等），捕获这些异常并返回详细的错误信息，
            # 同时设置HTTP状态码为503 Service Unavailable表示临时不可用的服务端问题。
            return Response(
                {"error": f"API request failed: {str(e)}"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except json.JSONDecodeError:
            # 当API返回的数据不是有效的JSON格式时，会抛出json.JSONDecodeError异常；
            # 这里我们捕捉此异常，并告知客户端API响应格式无效，同时设置HTTP状态码为502 Bad Gateway表示网关或代理收到上游服务器的有效响应但是无法解析它。
            return Response(
                {"error": "Invalid API response format"}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
# GLM语言模型多模态识别glm-4v模型
class GLM4VView(APIView):
    def post(self, request):
        glm_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        # 直接获取完整的messages结构
        messages = request.data.get('messages', [])
        model_name = request.data.get('model', 'glm-4v-flash')

        # 基本验证
        if not messages:
            return Response({"error": "messages is required"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": model_name,
            "messages": messages  # 直接使用客户端传来的messages结构
        }

        try:
            response = requests.post(glm_url, headers=headers, json=data)
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except json.JSONDecodeError:
            return Response({"error": "Invalid API response format"}, status=status.HTTP_502_BAD_GATEWAY)
# GLM文生图模型glm-CogView
class GLMCogView(APIView):
    def post(self, request):
        cog_url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
        
        # 获取参数
        model_name = request.data.get('model', 'cogview-3')
        prompt = request.data.get('prompt', '')
        size = request.data.get('size', '1024x1024')  # 默认尺寸
        user_id = request.data.get('user_id', '')  # 可选参数
        
        # 基本验证
        if not prompt:
            return Response({"error": "prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": model_name,
            "prompt": prompt
        }
        
        # 添加可选参数
        if size:
            data["size"] = size
        if user_id:
            data["user_id"] = user_id

        try:
            response = requests.post(cog_url, headers=headers, json=data)
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except json.JSONDecodeError:
            return Response({"error": "Invalid API response format"}, status=status.HTTP_502_BAD_GATEWAY)
# GLM文生视频模型CogVideoX
class CogVideoXView(APIView):
    def post(self, request):
        """生成视频请求"""
        try:
            # 初始化智谱AI客户端
            client = ZhipuAI(api_key=API_KEY)
            
            if request.data.get('action') == 'check_status':
                # 查询任务状态
                task_id = request.data.get('task_id')
                if not task_id:
                    return Response({"error": "task_id is required"}, status=status.HTTP_400_BAD_REQUEST)
                    
                response = client.videos.retrieve_videos_result(id=task_id)
                
                # 直接返回视频结果对象的所有属性
                return Response({
                    "task_status": response.task_status,
                    "video_result": [
                        {
                            "url": video.url,
                            "cover_image_url": video.cover_image_url
                        } for video in response.video_result
                    ] if hasattr(response, 'video_result') else []
                }, status=status.HTTP_200_OK)
            else:
                # 生成视频
                # 获取参数
                model_name = request.data.get('model', 'cogvideox-flash')
                prompt = request.data.get('prompt')
                image_url = request.data.get('image_url')
                quality = request.data.get('quality', 'quality')
                with_audio = request.data.get('with_audio', True)
                size = request.data.get('size', '720x480')
                fps = request.data.get('fps', 30)
                
                # 基本验证
                if not prompt:
                    return Response({"error": "prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
                
                # 生成视频
                response = client.videos.generations(
                    model=model_name,
                    prompt=prompt,
                    image_url=image_url,
                    quality=quality,
                    with_audio=with_audio,
                    size=size,
                    fps=fps
                )
                return Response({"task_id": response.id}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
# GLM语音对话模型GLM-4-Voice
class GLM4Voice(APIView):
    def post(self, request):
        """生成语音请求"""
        try:
            # 初始化智谱AI客户端
            client = ZhipuAI(api_key=API_KEY)
            
            # 获取参数
            model_name = request.data.get('model', 'glm-4-voice')
            messages = request.data.get('messages', [])
            do_sample = request.data.get('do_sample', True)
            stream = request.data.get('stream', False)
            temperature = request.data.get('temperature', 0.8)
            top_p = request.data.get('top_p', 0.6)
            max_tokens = request.data.get('max_tokens', 1024)
            stop = request.data.get('stop')
            user_id = request.data.get('user_id')
            request_id = request.data.get('request_id')
            
            # 基本验证
            if not messages:
                return Response({"error": "messages is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 调用API
            kwargs = {
                "model": model_name,
                "messages": messages,
                "do_sample": do_sample,
                "stream": stream,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens
            }
            
            # 添加可选参数
            if stop:
                kwargs["stop"] = stop
            if user_id:
                kwargs["user_id"] = user_id
            if request_id:
                kwargs["request_id"] = request_id
            
            response = client.chat.completions.create(**kwargs)
            
            # 构造响应
            result = {
                "id": response.id,
                "created": response.created,
                "model": response.model,
                "choices": [{
                    "index": choice.index,
                    "finish_reason": choice.finish_reason,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                    }
                } for choice in response.choices],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            # 如果有音频数据，添加到结果中
            if hasattr(response.choices[0].message, "audio"):
                result["choices"][0]["message"]["audio"] = response.choices[0].message.audio
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# COZE对话模型
class CozeChatView(APIView):
    def post(self, request):
        """生成对话请求"""
        try:
            # 获取参数，api_token和bot_id使用默认配置值，但user_id必须由前端提供
            coze_api_token = request.data.get('api_token', COZE_API_TOKEN)
            bot_id = request.data.get('bot_id', COZE_BOT_ID)
            user_id = request.data.get('user_id')
            question = request.data.get('question')
            
            # 基本验证
            if not question:
                return Response({"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not user_id:
                return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 初始化Coze客户端
            coze = Coze(
                auth=TokenAuth(token=coze_api_token), 
                base_url=COZE_BASE_URL
            )
            
            content = ""
            token_count = 0
            
            # 使用stream方式调用API
            for event in coze.chat.stream(
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(question),
                ]
            ):
                # 实时处理消息增量
                if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    content += event.message.content
                
                # 完成时获取token用量
                if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                    token_count = event.chat.usage.token_count
            
            # 构造响应
            result = {
                "content": content,
                "token_count": token_count
            }
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# Qwen模型
# 大语言模型-单轮对话
class QwenChat(APIView):
    def post(self, request):
        content = request.POST.get('content', '')
        system_role = request.POST.get('system_role', '你是一名专业的心里医生')
        model = request.POST.get('model', 'qwen2.5-1.5b-instruct')  # 默认模型，可由前端指定
        
        messages = [
            {'role': 'system', 'content': system_role},
            {'role': 'user', 'content': content}
        ]
 
        def stream_generator():
            response = Generation.call( 
                api_key=Qwen_APIKEY,
                model=model,  # 使用前端传入的模型
                messages=messages,
                result_format="message",
                stream=True 
            )
            for chunk in response:
                if chunk.output and chunk.output.choices: 
                    for choice in chunk.output.choices: 
                        if choice.message and choice.message.content: 
                            yield choice.message.content  
 
        return StreamingHttpResponse(stream_generator())
# 大语言模型-长文本对话
class QwenChatFile(APIView):
    def post(self, request):
        try:
            client = OpenAI(
                api_key=Qwen_APIKEY,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1" 
            )
            
            # 处理文件上传 
            uploaded_file = request.FILES.get('file') 
            if not uploaded_file:
                return JsonResponse({'error': '未上传文件'}, status=400)
                
            # 保存临时文件 
            temp_path = Path(f"/tmp/{uploaded_file.name}") 
            temp_path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
            
            with open(temp_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks(): 
                    destination.write(chunk) 
                    
            try:
                # 创建文件对象 
                file_object = client.files.create(file=temp_path, purpose="file-extract")
                
                # 处理问题参数 
                question = request.POST.get('question', '')
                if not question:
                    return JsonResponse({'error': '问题不能为空'}, status=400)
                    
                messages = [
                    {'role': 'system', 'content': f'fileid://{file_object.id}'}, 
                    {'role': 'user', 'content': question}
                ]
                
                completion = client.chat.completions.create( 
                    model="qwen-long",
                    messages=messages,
                    stream=False 
                )
                
                return JsonResponse({
                    'response': completion.choices[0].message.content
                })
                
            finally:
                # 清理临时文件和文件对象
                if temp_path.exists():
                    temp_path.unlink()
                if 'file_object' in locals():
                    client.files.delete(file_object.id)
                    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
# 大语言模型-多轮对话
class QwenChatToke(APIView):
    def post(self, request):
        messages = request.session.get('dialog_history',  [
            {"role": "system", "content": "你是一名专业心理医生"}
        ])
        
        user_input = request.POST.get('content', '')
        model = request.POST.get('model', 'qwen2.5-1.5b-instruct')  # 默认模型，可由前端指定
        messages.append({"role": "user", "content": user_input})
 
        response = Generation.call( 
            api_key=Qwen_APIKEY,
            model=model,  # 使用前端传入的模型
            messages=messages,
            result_format="message",
            stream=True 
        )
 
        full_content = ""
        def stream_generator():
            nonlocal full_content 
            for chunk in response:
                if chunk.output  and chunk.output.choices: 
                    for choice in chunk.output.choices: 
                        if choice.message  and choice.message.content: 
                            content = choice.message.content  
                            full_content += content 
                            yield content 
            messages.append({"role":  "assistant", "content": full_content})
            request.session['dialog_history']  = messages 
 
        return StreamingHttpResponse(stream_generator())
# 图像识别OCR
class QwenOCR(APIView):
    def post(self, request):
        try:
            client = OpenAI(
                api_key=Qwen_APIKEY,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            uploaded_file = request.FILES.get('file')
            question = request.POST.get('question', '提取所有图中文字')
            if not uploaded_file:
                return JsonResponse({'error': '未上传文件'}, status=400)
            
            # 读取并编码文件
            file_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
            
            completion = client.chat.completions.create(
                model="qwen-vl-ocr",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{file_data}"},
                                "min_pixels": 28 * 28 * 4,
                                "max_pixels": 28 * 28 * 1280
                            },
                            {"type": "text", "text": question},
                        ],
                    }
                ]
            )
            
            return JsonResponse({
                'response': completion.choices[0].message.content
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
# 多模态语音对话
class Qwenomni(APIView):
    def post(self, request):
        try:
            client = OpenAI(
                api_key=Qwen_APIKEY,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            # 获取参数
            content_type = request.POST.get('type', 'text')  # text/image/audio/video
            text = request.POST.get('text', '')
            voice = request.POST.get('voice', 'Cherry')
            url = request.POST.get('url', '')  # 获取URL参数
            
            # 获取对话历史
            messages = request.session.get('omni_dialog_history', [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant."}]
                }
            ])
            
            # 构建消息内容
            if content_type == 'text':
                user_content = [{"type": "text", "text": text}]
            elif url:  # 处理URL方式
                if content_type == 'image':
                    user_content = [
                        {"type": "image_url", "image_url": {"url": url}},
                        {"type": "text", "text": text}
                    ]
                elif content_type == 'audio':
                    user_content = [
                        {"type": "input_audio", "input_audio": {"data": url, "format": "mp3"}},
                        {"type": "text", "text": text}
                    ]
                elif content_type == 'video':
                    user_content = [
                        {"type": "video_url", "video_url": {"url": url}},
                        {"type": "text", "text": text}
                    ]
            else:  # 处理文件上传方式
                file = request.FILES.get('file')
                if not file:
                    return JsonResponse({'error': '未上传文件'}, status=400)
                
                file_data = base64.b64encode(file.read()).decode('utf-8')
                
                if content_type == 'image':
                    user_content = [
                        {"type": "image_url", 
                         "image_url": {"url": f"data:image/jpeg;base64,{file_data}"}},
                        {"type": "text", "text": text}
                    ]
                elif content_type == 'audio':
                    user_content = [
                        {"type": "input_audio", 
                         "input_audio": {"data": f"data:;base64,{file_data}", "format": "mp3"}},
                        {"type": "text", "text": text}
                    ]
                elif content_type == 'video':
                    user_content = [
                        {"type": "video_url",
                         "video_url": {"url": f"data:;base64,{file_data}"}},
                        {"type": "text", "text": text}
                    ]
            
            # 添加用户消息到历史
            messages.append({"role": "user", "content": user_content})
            
            def stream_generator():
                completion = client.chat.completions.create(
                    model="qwen-omni-turbo",
                    messages=messages,
                    modalities=["text", "audio"],
                    audio={"voice": voice, "format": "wav"},
                    stream=True
                )
                
                assistant_response = []
                for chunk in completion:
                    if hasattr(chunk.choices[0].delta, "audio"):
                        try:
                            audio_data = chunk.choices[0].delta.audio['data']
                            assistant_response.append({"type": "audio", "audio": {"data": audio_data}})
                            yield f"audio:{audio_data}\n"
                        except Exception as e:
                            transcript = chunk.choices[0].delta.audio['transcript']
                            assistant_response.append({"type": "text", "text": transcript})
                            yield f"text:{transcript}\n"
                    elif hasattr(chunk.choices[0].delta, "content"):
                        content = chunk.choices[0].delta.content
                        if content:
                            assistant_response.append({"type": "text", "text": content})
                            yield f"text:{content}\n"
                
                # 添加助手回复到历史
                messages.append({"role": "assistant", "content": assistant_response})
                request.session['omni_dialog_history'] = messages
            
            return StreamingHttpResponse(stream_generator(), content_type='text/plain; charset=utf-8')
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
# Qwen 音频理解
class QwenAudio(APIView):
    def post(self, request):
        try:
            # 获取参数
            audio_source = request.POST.get('audio_source', '')  # 音频URL或base64
            question = request.POST.get('question', '')  # 问题文本
            
            # 获取对话历史
            messages = request.session.get('audio_dialog_history', [])
            
            # 处理音频文件上传
            if not audio_source and request.FILES.get('file'):
                file = request.FILES.get('file')
                file_data = base64.b64encode(file.read()).decode('utf-8')
                audio_source = f"data:audio/wav;base64,{file_data}"
            
            if not audio_source:
                return JsonResponse({'error': '未提供音频数据'}, status=400)
            
            # 构造消息内容
            content = [{"audio": audio_source}]
            if question:
                content.append({"text": question})
            
            # 添加用户消息到历史
            messages.append({
                "role": "user",
                "content": content
            })
            
            def stream_generator():
                response = dashscope.MultiModalConversation.call(
                    model="qwen-audio-turbo-latest",
                    messages=messages,
                    stream=True,
                    incremental_output=True,
                    result_format="message"
                )
                
                assistant_response = []
                for chunk in response:
                    if hasattr(chunk, 'output') and hasattr(chunk.output, 'choices'):
                        for choice in chunk.output.choices:
                            if hasattr(choice.message, 'content'):
                                content = choice.message.content
                                assistant_response.append({"type": "text", "text": content})
                                yield f"text:{content}\n"
                
                # 添加助手回复到历史
                messages.append({"role": "assistant", "content": assistant_response})
                request.session['audio_dialog_history'] = messages
            
            return StreamingHttpResponse(stream_generator(), content_type='text/plain; charset=utf-8')
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class ModelInfoViewSet(viewsets.ModelViewSet):
    queryset = ModelInfo.objects.all()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.model = request.data.get('model', instance.model)
        instance.name = request.data.get('name', instance.name)
        instance.type = request.data.get('type', instance.type)
        instance.context = request.data.get('context', instance.context)
        instance.cost = request.data.get('cost', instance.cost)
        instance.save()
        
        return Response({
            'id': instance.id,
            'model': instance.model,
            'name': instance.name,
            'type': instance.type,
            'type_display': instance.get_type_display(),
            'context': instance.context,
            'cost': instance.cost
        })

    def create(self, request, *args, **kwargs):
        instance = ModelInfo.objects.create(
            model=request.data.get('model'),
            name=request.data.get('name'),
            type=request.data.get('type'),
            context=request.data.get('context'),
            cost=request.data.get('cost')
        )
        
        return Response({
            'id': instance.id,
            'model': instance.model,
            'name': instance.name,
            'type': instance.type,
            'type_display': instance.get_type_display(),
            'context': instance.context,
            'cost': instance.cost
        })


