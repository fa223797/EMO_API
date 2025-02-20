from django.contrib import admin
from .models import UserConversation, ModelInfo, CustomUser, UploadedFile
from constance.admin import ConstanceAdmin, Config
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponse, HttpResponseRedirect
import os
from django.conf import settings

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

# 对话存储表
@admin.register(UserConversation)
class UserConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'content')

# 媒体资料列表
@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    """上传文件管理"""
    list_display = ('file_name', 'file_type', 'file_size_display', 'mime_type', 'upload_time', 'uploader', 'file_preview', 'file_actions')
    list_filter = ('file_type', 'upload_time', 'uploader')
    search_fields = ('file_name', 'uploader__username')
    readonly_fields = ('file_size', 'mime_type', 'upload_time', 'file_type')
    
    def get_queryset(self, request):
        # 按文件类型分组排序
        return super().get_queryset(request).order_by('file_type', '-upload_time')
    
    def file_size_display(self, obj):
        """格式化文件大小显示"""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size/1024:.2f} KB"
        elif obj.file_size < 1024 * 1024 * 1024:
            return f"{obj.file_size/(1024*1024):.2f} MB"
        return f"{obj.file_size/(1024*1024*1024):.2f} GB"
    
    file_size_display.short_description = '文件大小'

    def file_actions(self, obj):
        """文件操作按钮"""
        return format_html(
            '<a class="button" href="{}">下载</a>&nbsp;'
            '<button class="button" onclick="renameFile({})">重命名</button>&nbsp;'
            '<button class="button" onclick="deleteFile({})">删除</button>',
            obj.file.url,
            obj.pk,
            obj.pk
        )
    file_actions.short_description = '操作'

    def file_preview(self, obj):
        """文件预览"""
        if obj.file_type == 'image':
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:100px"/>',
                obj.file.url
            )
        elif obj.file_type == 'video':
            return format_html(
                '<video width="100" height="100" controls>'
                '<source src="{}" type="{}">不支持预览</video>',
                obj.file.url, obj.mime_type
            )
        elif obj.file_type == 'audio':
            return format_html(
                '<audio controls style="width:200px">'
                '<source src="{}" type="{}">不支持预览</audio>',
                obj.file.url, obj.mime_type
            )
        elif obj.file_type == 'document':
            if obj.file_name.lower().endswith(('.md', '.markdown')):
                return format_html(
                    '<a href="{}" target="_blank">预览Markdown</a>',
                    obj.file.url
                )
            return format_html(
                '<a href="{}" target="_blank">查看文档</a>',
                obj.file.url
            )
        return format_html('<a href="{}" target="_blank">下载文件</a>', obj.file.url)
    
    file_preview.short_description = '预览'

    def delete_file(self, request, file_id):
        """删除文件"""
        try:
            uploaded_file = self.get_object(request, file_id)
            if uploaded_file:
                # 删除物理文件
                file_path = os.path.join(settings.MEDIA_ROOT, str(uploaded_file.file))
                if os.path.exists(file_path):
                    os.remove(file_path)
                # 删除数据库记录
                uploaded_file.delete()
                return HttpResponse('文件删除成功')
            return HttpResponse('文件不存在', status=404)
        except Exception as e:
            return HttpResponse(f'删除失败: {str(e)}', status=500)

    def download_file(self, request, file_id):
        """下载文件"""
        uploaded_file = self.get_object(request, file_id)
        if uploaded_file is None:
            return HttpResponse('文件不存在', status=404)
            
        file_path = os.path.join(settings.MEDIA_ROOT, str(uploaded_file.file))
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type=uploaded_file.mime_type)
                response['Content-Disposition'] = f'attachment; filename={uploaded_file.file_name}'
                return response
        return HttpResponse('文件不存在', status=404)

    def rename_file(self, request, file_id):
        """重命名文件"""
        if request.method == 'POST':
            uploaded_file = self.get_object(request, file_id)
            new_name = request.POST.get('new_name')
            if uploaded_file and new_name:
                # 保持原扩展名
                old_ext = os.path.splitext(uploaded_file.file_name)[1]
                new_name = f"{new_name}{old_ext}"
                uploaded_file.file_name = new_name
                uploaded_file.save()
                self.message_user(request, '文件重命名成功')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        return HttpResponse('重命名失败', status=400)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:file_id>/delete/',
                self.admin_site.admin_view(self.delete_file),
                name='uploaded-file-delete',
            ),
            path(
                '<int:file_id>/rename/',
                self.admin_site.admin_view(self.rename_file),
                name='uploaded-file-rename',
            ),
            path(
                '<int:file_id>/download/',
                self.admin_site.admin_view(self.download_file),
                name='uploaded-file-download',
            ),
        ]
        return custom_urls + urls

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'admin/js/file_admin.js',
        )

