# ========== 0. 项目目录 ==========
PS D:\python代码\Django\EMO_API> tree /F
卷   的文件夹 PATH 列表
卷序列号为 FC60-533D
D:.
│  db.sqlite3
│  manage.py
│  readme.md
│  requirements.txt
│  test.ipynb
│  test.py
│
├─ai_app
│  │  admin.py
│  │  apps.py
│  │  models.py
│  │  tests.py
│  │  urls.py
│  │  views.py
│  │  __init__.py
│  │
│  ├─migrations
│  │  │  0001_initial.py
│  │  │  0002_models_delete_ai_model.py
│  │  │  0003_rename_上下文_models_context_rename_名称_models_cost_and_more.py
│  │  │  0004_rename_models_modelinfo.py
│  │  │  0005_aiconfig.py
│  │  │  0006_delete_aiconfig.py
│  │  │  0007_alter_modelinfo_options_alter_modelinfo_context_and_more.py
│  │  │  0008_alter_modelinfo_type.py
│  │  │  0009_alter_modelinfo_options_alter_modelinfo_context_and_more.py
│  │  │  __init__.py
│  │  │
│  │  └─__pycache__
│  │          0001_initial.cpython-312.pyc
│  │          0002_models_delete_ai_model.cpython-312.pyc
│  │          0003_rename_上下文_models_context_rename_名称_models_cost_and_more.cpython-312.pyc
│  │          0004_rename_models_modelinfo.cpython-312.pyc
│  │          0005_aiconfig.cpython-312.pyc
│  │          0006_delete_aiconfig.cpython-312.pyc
│  │          0007_alter_modelinfo_options_alter_modelinfo_context_and_more.cpython-312.pyc
│  │          0008_alter_modelinfo_type.cpython-312.pyc
│  │          0009_alter_modelinfo_options_alter_modelinfo_context_and_more.cpython-312.pyc
│  │          __init__.cpython-312.pyc
│  │
│  ├─templates
│  │      api_docs.html
│  │
│  └─__pycache__
│          admin.cpython-312.pyc
│          apps.cpython-312.pyc
│          models.cpython-312.pyc
│          urls.cpython-312.pyc
│          views.cpython-312.pyc
│          __init__.cpython-312.pyc
│
└─config
    │  asgi.py
    │  settings.py
    │  urls.py
    │  wsgi.py
    │  __init__.py
    │
    └─__pycache__
            settings.cpython-312.pyc
            urls.cpython-312.pyc
            wsgi.cpython-312.pyc
            __init__.cpython-312.pyc

方法：
# ========== 1. 初始化Django项目 ==========
django-admin startproject config .

# ========== 2. 创建RDF应用 ==========
python manage.py startapp ai_app

# ========== 3. 安装依赖 ==========
pip install django python-decouple mysqlclient pymysql
pip freeze > requirements.txt

# ========== 4. 数据库迁移 ==========
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser #超级管理员

# ========== 5. 启动验证 ==========
python manage.py runserver

# ========== 6. 设置settings.py和urls.py ==========
设置ettings.py
LANGUAGE_CODE = 'zh-Hans'
TIME_ZONE = 'Asia/Shanghai'

INSTALLED_APPS = [
    'rest_framework',
    'ai_app',
]

# ========== 7. AI相关路由和视图函数 ==========
主路由config/urls.py添加admin和ai_app里面的路由
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ai_app.urls')),
]

创建ai_app/urls.py
先创建glm_4_flash路由（最基本的）
urlpatterns = [
    path('glm_4_flash/', glm_4_flash.as_view(), name='glm-4-flash'),
 ]

 创建ai_app/views.py
 具体参考代码即可，test.py是测试代码只测试glm_4_flash路由和返回的json格式
 # ========== 8. AI接口相关视图里面的注意 ==========
 0、..\EMO_API\ai_app\templates\api_docs.html是api文档页面，可以参考修改

 1、views.py里面的model是空的，需要手动传入，所以test.py是手动输入名称的，但是名称不能写错，没有校验机制

 2、glm模型名称包括（views.py）里面单独修改自己的api_key
    语言模型：
    glm-4-plus、glm-4-air、glm-4-air-0111、glm-4-airx、glm-4-long 、glm-4-flashx 、glm-4-flash；
    图/视频理解：
    glm-4v-plus-0111、glm-4v-plus 、glm-4v、glm-4v-flash；
    图像生成：
    cogview-4、cogview-3-flash、cogview-3；
    视频生成：
    cogvideox-2、cogvideox-flash；

3、coze参考CozeChatView；但这里最重要的就是access_token，需要30天更换一次；这个现在是卸载了传输段

4、qwen免费模型
    chat类
    qwen2.5-1.5b-instruct
    qwen-1.8b-longcontext-chat
    视觉类
    qwen2-vl-2b-instruct免费视觉
    功能类
    qwen2.5-math-1.5b-instruct数学解题
    qwen2.5-coder-3b-instruct代码变成，也可以使用更轻量级的1.5；0.5
    deepseek类
    deepseek-r1-distill-qwen-1.5b；deepseek-r1-distill-llama-8b；deepseek-r1-distill-llama-70b；
    wanx-ast图上加文字
    facechain-facedetect人物图像检测
    video-style-transform视频风格重绘：
    gte-rerank文本排序

 # ========== 9. 配置远程数据库 ==========
 1、数据库的安装配置：
    首先一定是8.0以上的mysql（我现在的操作系统是almalinux9.0）
    然后在宝塔里面安装mysql以及phpmyadmin,这两个设置的时候数据库要选择对所有人，phpmyadmin要白版选择安装
    如果不改动则MySQL会选择3306端口，phpmyadmin选择的是80端口
    一定要回到服务器里面去修改安全组，放行3306端口（Sys-WebServer安全组里面的出入方向都添加，TCP，3306，0.0.0.0/0）；多个数据库都是一样的3306端口
    如果想检查宝塔的虚拟环境则vscode连接ssl：root@123.249.67.69；然后进入cd /www/server/panel下后source pyenv/bin/activate激活虚拟环境deactivate退出虚拟环境;
2、
 config/settings.py里面修改数据库
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'emo',
            'USER': 'fa223797',
            'PASSWORD': 'Yd011987..',
            'HOST': '123.249.67.69',
            'PORT': '3306',
        }
    }
    同时下面的设置里面子应用要添加到INSTALLED_APPS里面，要不相对应的数据库不会迁移也不显示表

3.在app里面的models.py创建模型，然后迁移（所谓模型就是数据库的表）
    模型样例：
    class ModelInfo(models.Model):
        model = models.TextField()
        name = models.TextField()
        type = models.TextField()
        context = models.TextField()
        cost = models.TextField()
        def __str__(self):
            return f"{self.model} - {self.name} - {self.type} - {self.context} - {self.cost}"
    迁移：
    python manage.py makemigrations
    python manage.py migrate

4.在admin.py里面注册模型
    from django.contrib import admin
    from .models import ModelInfo
    admin.site.register(ModelInfo)

5.在apps.py里面注册应用并且显示中文
    name = 'ai_app'
    verbose_name = "AI-应用"

# ========== 10. 使用数据库案例 ==========
 1、把数据库导入到docs里面，先修改views.py增删改查的方法，增加models.py的内容，然后修改docs.html
 2、增删改查功能，则除了views.py里面添加了新的功能，同时urls.py里面和settings.py里面也要修改

# ========== 11. 搭建基础框架simpleui ==========
simpleui的配置：
1、安装依赖：pip install django-simpleui
2、添加应用：settings.py里面INSTALLED_APPS = ['simpleui',]
增加REST framework的视图及关系
3、手动添加serializers.py文件，文件内容参考文件，主要功能是序列化模型成为json格式
4、更新视图views.py，添加ModelInfoViewSet视图，用于管理模型信息；class ModelListView(APIView)，用于后台基础看框架
5、配置路由path('ModelListView/', ModelListView.as_view(),  name='ModelListView'),#framework视图

# ========== 12. 增加数据库表 ==========
1、在models.py里面增加新的模型，包括用户管理表、资源管理表、对话存储表
2、在admin.py里面注册模型,用@方式

# ========== 13. 动态配置参数管理django-constance ==========
1、pip install django-constance[database]
2、settings.py中添加：
    INSTALLED_APPS += ['constance']
    CONSTANCE_CONFIG = {
        'WECHAT_APP_ID': ('', '微信AppID'),
        'API_TIMEOUT': (30, '接口超时时间（秒）'),
    }
3、admin.py里面class CustomConstanceAdmin(ConstanceAdmin)是汉化用的，下面的是对站点标题汉化设置
4、对views.py里面的配置文件进行动态迁移

# ========== 14. 文件存储 ==========
1、安装依赖：pip install django-storages
   在views.py里面有上传接口，admin里面有“文件上传列表”
2、使用方法
    上传文件：
    POST /api/upload/
    Content-Type: multipart/form-data
    file: <文件数据>
    获取文件列表：
    GET /api/upload/
3、修改完迁移数据库和静态文件收集
    python manage.py makemigrations
    python manage.py migrate
    python manage.py collectstatic
4、media是上传文件的目录
5、static\admin\js\file_admin.js是上传页面的js文件，可以修改
6、staticfiles 文件夹说明：这是Django用来收集所有静态文件的目录
