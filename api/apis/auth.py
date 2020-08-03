from django.contrib.auth.models import User
from rest_framework import status
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import JSONWebTokenAPIView, jwt_response_payload_handler
from rest_framework.response import Response
from datetime import datetime, timezone


class AuthApi(JSONWebTokenAPIView):
    """
    获取一组数据需要什么
    1. model
    2. 序列化器
    """
    serializer_class = JSONWebTokenSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        user = request.data.get('username')
        user_info = User.objects.filter(username=user)
        if user_info and not user_info.first().is_active:
            return Response({
                'code': 40000,
                'message': "该用户未激活！"
            })
        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response({
                'code':20000,
                'data':response_data
            })
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            # 更改数据库中last_login的值
            user.last_login = datetime.now(tz=timezone.utc)
            user.save()
            return response
        return Response({
            'code':60204,
            'message':"请输入正确的用户名和密码"
        })
