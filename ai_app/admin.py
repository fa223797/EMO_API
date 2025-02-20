from django.contrib import admin
from .models import MediaResource, UserConversation, ModelInfo, CustomUser

# 使用装饰器注册模型并自定义 Admin 类
# 模型信息表
@admin.register(ModelInfo)
class ModelInfoAdmin(admin.ModelAdmin):
    """
    AI模型信息的Admin配置
    """
    # 在列表页显示的字段
    list_display = ('model', 'name', 'type', 'context', 'cost')

    # 添加搜索框，支持按模型标识和模型名称搜索
    search_fields = ('model', 'name')

    # 添加过滤器，支持按模型类型过滤
    list_filter = ('type',)

    # 设置默认排序规则（按模型名称升序）
    ordering = ('name',)

    # 在编辑页分组显示字段
    fieldsets = (
        ("基本信息", {
            "fields": ('model', 'name')
        }),
        ("详细信息", {
            "fields": ('type', 'context', 'cost')
        }),
    )

# 用户管理表
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'openid', 'avatar')
    search_fields = ('username', 'openid')
    list_filter = ('is_active',)

# 资源管理表
@admin.register(MediaResource)
class MediaResourceAdmin(admin.ModelAdmin):
    list_display = ('file', 'upload_time', 'user')
    list_filter = ('upload_time',)
    search_fields = ('user__username',)

# 对话存储表
@admin.register(UserConversation)
class UserConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'content')
