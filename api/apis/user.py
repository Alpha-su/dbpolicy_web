from rest_framework import filters
from rest_framework.views import APIView
from django.contrib.auth.hashers import check_password
from ..paination import MyPagination
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from ..serializers.user import UserInfoSerializer
from ..serializers import user
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from rest_framework_jwt.utils import jwt_decode_handler


class UsersApi(ListAPIView):
    queryset = User.objects.get_queryset().order_by('id')
    serializer_class = user.UserSerializer

    filter_backends = (filters.SearchFilter,) # 自定义过滤器要加进去
    search_fields = ('username',)
    
    pagination_class = MyPagination
    
    table_column = [
        {
            "prop": 'date_joined',
            "label": '加入时间'
        },
    ]
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
    
    def get_paginated_response(self, data):
        count = self.paginator.get_paginated_response(data)
        return Response({
            "code": 20000,
            "data": {
                "table_column": self.table_column,
                "table_data": data,
                "count":count
            }
        })


class UserHandler(APIView):
    
    def get(self, request):
        username = request.GET.get('username', None)
        if not username:
            return JsonResponse({
                "code": 40000,
                "message": "请输入要更改的用户名！"
            })
        
        else:
            try:
                user_info = User.objects.get(username=username)
            except Exception:
                return JsonResponse({
                    "code": 40000,
                    "message": "您要查询的用户不存在！"
                })
            else:
                serializer = UserInfoSerializer(user_info)
                return JsonResponse({
                    "code": 20000,
                    "data": serializer.data
                })
            
    def put(self, request):
        username = request.GET.get('username', None)
        if not username:
            return JsonResponse({
                "code":40000,
                "message":"请输入要更改的用户名！"
            })
        else:
            change_active = request.GET.get('change_active', False)
            new_role = request.GET.get('role', None)
            try:
                user_info = User.objects.get(username=username)
                if change_active:
                    User.objects.filter(username=username).update(is_active=not user_info.is_active)
                if new_role:
                    group_id = Group.objects.get(name=new_role).id
                    user_info.groups.clear()
                    user_info.groups.add(*[group_id])
                    user_info.save()
            except Exception as e:
                print(e)
                return JsonResponse({
                    "code": 40000,
                    "message": "更新用户状态失败！"
                })
            else:
                return JsonResponse({
                    "code": 20000,
                    "message": "更新用户状态成功！"
                })
    
    def post(self, request):
        username = request.data.get('username', None)
        user_result = User.objects.filter(username=username)
        if user_result.exists():
            return JsonResponse({
                "code": 40000,
                "message": "该用户名已经存在！"
            })
        password = request.data.get('password', None)
        role = request.data.get('role', None)
        if not (username and password and role):
            return JsonResponse({
                "code": 40000,
                "message": "请输入要添加的用户信息！"
            })
        else:
            try:
                group_id = Group.objects.get(name=role).id
            except Exception:
                return JsonResponse({
                    "code": 40000,
                    "message": "请输入合法的角色名称！"
                })
            else:
                user_obj = User.objects.create_user(username=username, password=password)
                user_obj.groups.add(*[group_id])
                return JsonResponse({
                    "code": 20000,
                    "message": "用户信息添加成功！"
                })
    
    def delete(self, request):
        username = request.GET.get('username', None)
        if not username:
            return JsonResponse({
                "code": 40000,
                "message": "请输入要更改的用户名！"
            })
        else:
            try:
                User.objects.filter(username=username).delete()
            except Exception:
                return JsonResponse({
                    "code": 40000,
                    "message": "删除用户失败！"
                })
            else:
                return JsonResponse({
                    "code": 20000,
                    "message": "删除用户成功！"
                })
    
    
def get_user_info(request):
    try:
        token = request.GET.get('token')
        toke_user = jwt_decode_handler(token)
        # 获得user_id
        user_id = toke_user["user_id"]
    except Exception:
        data = {
            "code": 60204,
            "message": "请输入正确的用户名和密码",
        }
    else:
        if request.method == 'GET':
            # 通过user_id查询用户信息
            user_info = User.objects.get(pk=user_id)
            serializer = UserInfoSerializer(user_info)
            data = {
                "code" : 20000,
                "data" : serializer.data
            }
        else:
            data = None
    return JsonResponse(data)

class changePwd(APIView):
    def put(self, request):
        username = request.GET.get('username', None)
        old_pwd = request.GET.get('old_pwd', None)
        new_pwd = request.GET.get('new_pwd', None)
        if not (old_pwd and new_pwd and username):
            return Response({
                "code": 40000,
                "message": "请输入完整的更改字段！"
            })
        else:
            try:
                user_info = User.objects.get(username=username)
            except:
                return Response({
                    "code": 40000,
                    "message": "请输入正确的用户名！"
                })
            else:
                if not check_password(old_pwd, user_info.password):
                    return Response({
                        "code": 40000,
                        "message": "请输入正确的旧密码！"
                    })
                else:
                    user_info.set_password(new_pwd)
                    user_info.save()
                    return Response({
                        "code": 20000,
                        "message": "密码更改成功，请重新登录！"
                    })