from django.contrib.auth.models import User, AbstractUser
from django.db import models
# 模型信息表
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

# 用户管理表
class CustomUser(AbstractUser):
    """
    用户管理表，用于存储用户的基本信息
    """
    openid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="微信OpenID"
    )
    avatar = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="用户头像"
    )

    # 添加 related_name 来解决冲突
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="customuser",
    )

    class Meta:
        db_table = "custom_user"
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.username}"

    # 定义必需字段
    REQUIRED_FIELDS = ['email']  # 添加必需字段

# 资源管理表
class MediaResource(models.Model):
    """
    资源管理表，用于存储图片、音视频等资源
    """
    file = models.FileField(
        upload_to='media/',
        verbose_name="文件"
    )
    upload_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="上传时间"
    )
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        verbose_name="所属用户"
    )

    class Meta:
        db_table = "media_resource"  # 数据库表名
        verbose_name = "媒体资源"  # 模型名称（单数）
        verbose_name_plural = "媒体资源"  # 模型名称（复数）

    def __str__(self):
        return f"{self.file.name} - {self.user.username}"

# 对话存储表
class UserConversation(models.Model):
    """
    对话存储表，用于存储用户的对话记录
    """
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        verbose_name="用户"
    )
    content = models.TextField(
        verbose_name="对话内容"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )

    class Meta:
        db_table = "user_conversation"  # 数据库表名
        verbose_name = "用户对话"  # 模型名称（单数）
        verbose_name_plural = "用户对话"  # 模型名称（复数）

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"