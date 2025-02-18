from django.urls import path
from .views import (
    GLM4View, 
    GLM4VView, 
    GLMCogView, 
    CogVideoXView, 
    GLM4Voice,
    CozeChatView,
    api_docs,
    QwenChat,
    QwenChatFile,
    QwenChatToke,
    QwenOCR,
    Qwenomni,
    QwenAudio,
    AI_ALL,
)

urlpatterns = [
    path('', api_docs, name='api-docs'),
    path('GLM-4/', GLM4View.as_view(), name='glm-4-api'),
    path('GLM-4V/', GLM4VView.as_view(), name='glm-4v-api'),
    path('GLM-Cog/', GLMCogView.as_view(), name='glm-cog-api'),
    path('GLM-CogVideo/', CogVideoXView.as_view(), name='glm-cogvideo-api'),
    path('GLM-4-Voice/', GLM4Voice.as_view(), name='glm-4-voice-api'),
    path('CozeChat/', CozeChatView.as_view(), name='coze-chat-api'),
    path('QwenChat/', QwenChat.as_view(), name='qwen-chat-api'),
    path('QwenChatFile/', QwenChatFile.as_view(), name='qwen-chat-file-api'),
    path('QwenChatToke/', QwenChatToke.as_view(), name='qwen-chat-toke-api'),
    path('QwenOCR/', QwenOCR.as_view(), name='qwen-ocr-api'),
    path('Qwenomni/', Qwenomni.as_view(), name='qwen-omni-api'),
    path('QwenAudio/', QwenAudio.as_view(), name='qwen-audio-api'),
    path('AI_ALL/', AI_ALL.as_view(), name='ai-all-api'),
] 