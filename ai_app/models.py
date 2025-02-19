from django.db import models

class ModelInfo(models.Model):
    ''' 
    模型信息表，用于存储AI模型的基本信息
    '''
    MODEL_TYPES = (
        ('chat', '大语言模型'),
        ('vision', '多模态模型'),
        ('function', '功能模型')
    )

    model = models.TextField(verbose_name="模型标识")
    name = models.TextField(verbose_name="模型名称")
    type = models.CharField(
        max_length=20,
        choices=MODEL_TYPES,
        default='chat',
        verbose_name="模型类型"
    )
    context = models.TextField(verbose_name="模型描述")
    cost = models.TextField(verbose_name="费用说明")
    
    def __str__(self):
        return f"{self.name} - {self.model} - {self.type} - {self.context} - {self.cost}"
    
    class Meta:
        db_table = "ai_model_info"
        verbose_name = "AI模型信息"
        verbose_name_plural = verbose_name


