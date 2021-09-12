import operator
import datetime
from functools import reduce

from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Links
from ..serializers import dataLinks
from elasticsearch import Elasticsearch
from ..models import Config, Location

es_hosts = ["121.36.33.190:9200"]
es = Elasticsearch(es_hosts)


class EsHandle(APIView):
    def get(self, request):
        global loc_id
        query_text = request.query_params.get('query_text', None)
        query_title = request.query_params.get('query_title', None)
        gov = request.query_params.get('gov', None)
        zupei_type = request.query_params.get('zupei_type', None)
        province = request.query_params.get('province', None)
        city = request.query_params.get('city', None)
        if province and not city:
            loc_id = Location.objects.get(province=province)
        if province and city:
            loc_id = Location.objects.get(province=province, city=city)
        if not province and city:
            loc_id = Location.objects.get(city=city)
        if not province and not city:
            loc_id=None
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 15))
        must_list = []
        if query_text:
            must_list.append({
                "query_string": {
                    "default_field": "main_text",
                    "query": query_text,
                }
            })
        if query_title:
            must_list.append({
                "query_string": {
                    "default_field": "title",
                    "query": query_title,
                }
            })
        if gov:
            must_list.append({
                            "match": {
                                "gov": str(gov),
                            },
                        })
        if zupei_type:
            must_list.append({
                            "match": {
                                "zupei_type": str(zupei_type),
                            },
                        })
        if loc_id:
            must_list.append({
                            "match": {
                                "loc_id": str(loc_id),
                            },
                        })

        if not must_list:
            must_list.append({"match_all": {}})
        body = {
            "query": {
                "bool": {
                    "must": must_list
                },
            },
            "from": (page - 1) * size,
            "size": size
        }
        print(body)
        res = es.search(index='api_details', body=body)  # 默认按照相关度排序
        table_data = []
        count = len(res['hits']['hits'])
        for i in res['hits']['hits']:
            i['_source']['score'] = i['_score']
            table_data.append(i['_source'])

        return Response({
            "code": 20000,
            "table_data": table_data,
            "count": count
        })