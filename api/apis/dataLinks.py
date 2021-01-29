import operator
import datetime
from functools import reduce

from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Links
from ..serializers import dataLinks


def solve_date_pattern(date):
    # 专门处理时间格式的函数，接收一个字符串，返回datetime格式的对象
    GMT_FORMAT = '%Y-%M-%d'
    date = date[:10]
    ret_date = datetime.datetime.strptime(date, GMT_FORMAT).date()
    return ret_date
    

class DataHandle(APIView):
    
    def get(self, request):
        search = request.query_params.get('search', None)
        loc = request.query_params.get('loc', None)
        gov = request.query_params.get('gov', None)
        zupei = request.query_params.get('zupei', None)
        begin_date = request.query_params.get('begin_date', None)
        end_date = request.query_params.get('end_date', None)
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 15))

        and_obj = []
        if begin_date:
            begin_date = solve_date_pattern(begin_date)
            # begin_date = datetime.date(2018,7,12)
            # begin_date = datetime.date(2019, 7, 12)
            end_date = solve_date_pattern(end_date)
            and_obj.append(Q(pub_date__range=(begin_date, end_date)))
        if zupei != 'all':
            and_obj.append(Q(zupei_type=zupei))
        
        if search:
            and_obj.append(Q(title__contains=search))
        if loc:
            loc_list = [Q(loc__code=item) for item in loc.split(',')]
            and_obj.append(reduce(operator.or_, loc_list))
        if gov:
            gov_list = [Q(gov=item) for item in gov.split(',')]
            and_obj.append(reduce(operator.or_, gov_list))
        if not and_obj:
            result_list = Links.objects.filter(Q(loc__code="100000"), Q(gov="人民政府"))[(page - 1) * size: page * size]
            count = Links.objects.all().count()
        else:
            result_list = Links.objects.filter(reduce(operator.and_, and_obj))[(page-1)*size:page*size]
            count = Links.objects.filter(reduce(operator.and_, and_obj)).count()
            
        table_data = []
        for qs in result_list:
            serializer = dataLinks.DataLinksSerializer(qs)
            table_data.append(serializer.data)
        return Response({
            "code": 20000,
            "table_data": table_data,
            "count": count
        })