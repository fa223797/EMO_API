from django.contrib import admin
from .models import MediaResource, UserConversation, ModelInfo, CustomUser
from constance.admin import ConstanceAdmin, Config
from django.utils.translation import gettext_lazy as _

# 自定义 Constance 的 Admin 配置
class CustomConstanceAdmin(ConstanceAdmin):
    def get_changelist_form(self, request, **kwargs):
        form = super().get_changelist_form(request, **kwargs)
        try:
            if 'WECHAT_APP_ID' in form.base_fields:
                form.base_fields['WECHAT_APP_ID'].label = "微信小程序 AppID"
            if 'API_TIMEOUT' in form.base_fields:
                form.base_fields['API_TIMEOUT'].label = "接口超时时间（秒）"
            if 'GLM_API_KEY' in form.base_fields:
                form.base_fields['GLM_API_KEY'].label = "智谱AI API密钥"
            if 'COZE_API_TOKEN' in form.base_fields:
                form.base_fields['COZE_API_TOKEN'].label = "COZE API令牌"
            if 'COZE_BOT_ID' in form.base_fields:
                form.base_fields['COZE_BOT_ID'].label = "COZE 机器人ID"
            if 'QWEN_API_KEY' in form.base_fields:
                form.base_fields['QWEN_API_KEY'].label = "通义千问 API密钥"
            if 'DEFAULT_VOICE' in form.base_fields:
                form.base_fields['DEFAULT_VOICE'].label = "默认语音角色"
            if 'DEFAULT_VIDEO_SIZE' in form.base_fields:
                form.base_fields['DEFAULT_VIDEO_SIZE'].label = "默认视频尺寸"
            if 'DEFAULT_VIDEO_FPS' in form.base_fields:
                form.base_fields['DEFAULT_VIDEO_FPS'].label = "默认视频帧率"
            if 'MAX_TOKENS' in form.base_fields:
                form.base_fields['MAX_TOKENS'].label = "最大Token数量"
        except KeyError as e:
            print(f"字段不存在: {e}")
        return form
admin.site.unregister([Config])
admin.site.register([Config], CustomConstanceAdmin)

# 修改 admin 站点标题
admin.site.site_header = '玫云科技AI管理后台'
admin.site.site_title = '系统管理'
admin.site.index_title = '系统管理'
admin.site.empty_value_display = '无数据'#空数据显示内容


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
