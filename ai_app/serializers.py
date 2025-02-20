from rest_framework import serializers
from .models import ModelInfo  # 导入你的实际模型

class ModelInfoSerializer(serializers.ModelSerializer):
    """
    AI模型信息的序列化器
    """
    class Meta:
        model = ModelInfo  # 指定模型为 ModelInfo
        fields = '__all__'  # 序列化所有字段