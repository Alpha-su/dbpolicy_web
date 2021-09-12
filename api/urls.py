from django.urls import path, re_path
from .apis import user, auth, targetUrls, dataLinks, esLinks


urlpatterns = [
    path('users/', user.UsersApi.as_view()),
    path('user/auth/',auth.AuthApi.as_view()),
    path('users/info/',user.UserHandler.as_view()),
    path('users/update/',user.UserHandler.as_view()),
    path('users/delete/',user.UserHandler.as_view()),
    path('users/create/',user.UserHandler.as_view()),
    re_path('user/info/$', user.get_user_info),
    path('user/pwd/', user.changePwd.as_view()),
    # 以下都是对配置文件表的操作
    path('targetUrls/info/', targetUrls.targetUrlsApi.as_view()),
    path('targetUrl/status/', targetUrls.ConfigHandle.as_view()),
    path('targetUrl/create/', targetUrls.ConfigHandle.as_view()),
    path('targetUrl/info/', targetUrls.ConfigHandle.as_view()),
    path('targetUrl/delete/', targetUrls.ConfigHandle.as_view()),
    path('targetUrl/update/', targetUrls.Configupdate.as_view()),
    path('targetUrl/testCreate/', targetUrls.ConfigTestCreate.as_view()),
    # 以下都是对dataLinks的操作
    path('dataLinks/info/', dataLinks.DataHandle.as_view()),
    # es操作
    path('esLinks/get/', esLinks.EsHandle.as_view()),
]