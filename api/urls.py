from django.urls import path, re_path
from .apis import user, auth


urlpatterns = [
    path('users/', user.UsersApi.as_view()),
    path('user/auth/',auth.AuthApi.as_view()),
    path('users/info/',user.UserHandler.as_view()),
    path('users/update/',user.UserHandler.as_view()),
    path('users/delete/',user.UserHandler.as_view()),
    path('users/create/',user.UserHandler.as_view()),
    re_path('user/info/$', user.get_user_info),
    path('user/pwd/', user.changePwd.as_view())
]