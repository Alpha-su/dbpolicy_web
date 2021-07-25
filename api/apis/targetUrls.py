import asyncio
import operator
from functools import reduce
from django.db.models import Q
from rest_framework import filters
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.serializers import User
from ..models import Config, Location
from ..paination import MyPagination
from ..serializers import targetUrls


class targetUrlFilter(filters.BaseFilterBackend):

    def query_loc_and_gov(self, qs, loc, gov):
        if not loc:
            loc_result = qs
        else:
            loc_list = [Q(loc__code=item) for item in loc.split(',')]
            loc_result = qs.filter(reduce(operator.or_, loc_list))
        if not gov:
            gov_result = qs
        else:
            gov_list = [Q(gov=item) for item in gov.split(',')]
            gov_result = qs.filter(reduce(operator.or_, gov_list))
        return gov_result & loc_result

    def filter_queryset(self, request, queryset, view):
        target_url = request.query_params.get('target_url', '')
        loc = request.query_params.get('loc', '')
        gov = request.query_params.get('gov', '')
        is_active = request.query_params.get('status', '')

        if not (target_url or loc or gov or is_active):
            return queryset
        base_qs = queryset

        if target_url:
            base_qs = Config.objects.filter(target_url__icontains=target_url)
            if loc or gov:
                base_qs = self.query_loc_and_gov(base_qs, loc, gov)
            else:
                return base_qs
        else:
            base_qs = self.query_loc_and_gov(base_qs, loc, gov)

        if is_active:
            return base_qs.filter(is_active=int(is_active))
        else:
            return base_qs


class targetUrlsApi(ListAPIView):
    queryset = Config.objects.get_queryset().order_by('id')
    serializer_class = targetUrls.targetUrlSerializer

    filter_backends = (targetUrlFilter,)

    pagination_class = MyPagination

    table_column = [
        {
            "prop": 'item_pattern',
            "label": '列表样式'
        },
        {
            "prop": 'main_text_pattern',
            "label": '正文样式'
        },
        {
            "prop": 'date_pattern',
            "label": '时间样式'
        },
        {
            "prop": 'source_pattern',
            "label": '来源样式'
        },
        {
            "prop": 'title_pattern',
            "label": '标题样式'
        },
        {
            "prop": 'next_pattern',
            "label": '翻页样式'
        },
        {
            "prop": 'action_pattern',
            "label": '预执行动作'
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
                "count": count
            }
        })


class ConfigHandle(APIView):

    def delete(self, request):
        id = request.query_params.get('id', None)
        if not id:
            return Response({
                "code": 40000,
                "message": "请输入要删除的网站id！"
            })
        else:
            try:
                Config.objects.filter(pk=id).delete()
            except Exception as e:
                print(e)
                return Response({
                    "code": 40000,
                    "message": "删除网站失败！"
                })
            else:
                return Response({
                    "code": 20000,
                    "message": "删除网站成功！"
                })

    def get(self, request):
        id = request.query_params.get('id', None)
        if not id:
            return Response({
                "code": 40000,
                "message": "请输入要查询的网站id！"
            })

        else:
            try:
                url_config = Config.objects.get(pk=id)
            except Exception:
                return Response({
                    "code": 40000,
                    "message": "您要查询的网站不存在！"
                })
            else:
                serializer = targetUrls.targetUrlSerializer(url_config)
                return Response({
                    "code": 20000,
                    "data": serializer.data
                })

    def put(self, request):
        id = request.query_params.get('id', None)
        if not id:
            return Response({
                "code": 40000,
                "message": "请输入要更改的网站id！"
            })
        else:
            try:
                config_url = Config.objects.get(pk=id)
                Config.objects.filter(pk=id).update(
                    is_active=not config_url.is_active)
            except Exception as e:
                print(e)
                return Response({
                    "code": 40000,
                    "message": "更新网站状态失败！"
                })
            else:
                return Response({
                    "code": 20000,
                    "message": "更新网站状态成功！"
                })

    def post(self, request):
        author = request.query_params.get('author', None)
        loc = request.data.get('loc', None)
        province = request.data.get('province', None)
        city = request.data.get('city', None)
        gov = request.data.get('gov', None)
        target_url = request.data.get('target_url', None)
        zupei_type = request.data.get('zupei_type', None)
        item_pattern = request.data.get('item_pattern', None)
        main_text_pattern = request.data.get('main_text_pattern', None)
        date_pattern = request.data.get('date_pattern', None)
        source_pattern = request.data.get('source_pattern', None)
        next_button = request.data.get('next_button', None)
        title_pattern = request.data.get('title_pattern', None)
        action = request.data.get('action', None)
        author_obj = User.objects.get(username=author)
        try:
            loc_obj = Location.objects.get(code=loc)
        except Exception:
            try:
                loc_obj = Location.objects.create(
                    code=loc, province=province, city=city, file_count=0)
            except Exception:
                return Response({
                    "code": 40000,
                    "message": "您输入的地区信息有误！"
                })
        try:
            Config.objects.create(loc=loc_obj, author=author_obj, gov=gov, target_url=target_url, zupei_type=zupei_type,
                                  item_pattern=item_pattern, main_text_pattern=main_text_pattern, date_pattern=date_pattern,
                                  source_pattern=source_pattern, next_pattern=next_button, action_pattern=action, is_active=True,
                                  file_count=0, title_pattern=title_pattern)
        except Exception as e:
            print(e)
            return Response({
                "code": 40000,
                "message": "创建网站失败，可能是该网站已经存在于数据库中！"
            })
        else:
            return Response({
                "code": 20000,
                "message": "网站信息添加成功！"
            })


class Configupdate(APIView):
    def put(self, request):
        id = request.data.get('id', None)
        target_url = request.data.get('target_url', None)
        zupei_type = request.data.get('zupei_type', None)
        item_pattern = request.data.get('item_pattern', None)
        main_text_pattern = request.data.get('main_text_pattern', None)
        date_pattern = request.data.get('date_pattern', None)
        source_pattern = request.data.get('source_pattern', None)
        next_button = request.data.get('next_button', None)
        title_pattern = request.data.get('title_pattern', None)
        action = request.data.get('action', None)
        if not id:
            return Response({
                "code": 40000,
                "message": "请输入要更改的网站id！"
            })
        else:
            try:
                Config.objects.filter(pk=id).update(target_url=target_url, zupei_type=zupei_type,
                                                    item_pattern=item_pattern, main_text_pattern=main_text_pattern,
                                                    date_pattern=date_pattern, source_pattern=source_pattern,
                                                    next_pattern=next_button, action_pattern=action, title_pattern=title_pattern)
            except Exception as e:
                print(e)
                return Response({
                    "code": 40000,
                    "message": "更新网站配置信息失败！"
                })
            else:
                return Response({
                    "code": 20000,
                    "message": "更新网站配置信息成功！"
                })


class ConfigTestCreate(APIView):
    def post(self, request):
        author = request.query_params.get('author', None)
        loc = request.data.get('loc', None)
        province = request.data.get('province', None)
        city = request.data.get('city', None)
        gov = request.data.get('gov', None)
        target_url = request.data.get('target_url', None)
        zupei_type = request.data.get('zupei_type', None)
        item_pattern = request.data.get('item_pattern', None)
        main_text_pattern = request.data.get('main_text_pattern', None)
        date_pattern = request.data.get('date_pattern', None)
        source_pattern = request.data.get('source_pattern', None)
        next_button = request.data.get('next_button', None)
        action = request.data.get('action', None)
        author_obj = User.objects.get(username=author)
        exists = Config.objects.filter(Q(target_url="{}".format(target_url)) & Q(
            action_pattern="{}".format(action))).exists()
        if exists:
            return Response({
                "code": 40000,
                "message": "该网站已经存在于数据库中，请不必重复添加！"
            })
        else:
            config = {"code": loc, "province": province, "city": city, "gov": gov, "target_url": target_url,
                      "zupei_type": zupei_type, "item_pattern": item_pattern, "main_text_pattern": main_text_pattern,
                      "date_type": date_pattern, "source": source_pattern, "action": action, "next_button": next_button, 'title': ''}
            tester = test_page.Parser(config)
            asyncio.run(test_page.run_parser(tester))
            return Response({
                "code": 20000,
                "status": tester.status_list,
                "data": tester.data_list
            })
