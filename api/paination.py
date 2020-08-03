from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class MyPagination(PageNumberPagination):
    """自定义分页"""
    # 每页显示多少条数据
    page_size = 10
    # url/?page=1&size=5, 改变默认每页显示的个数
    page_size_query_param = 'size'
    # 最大页数不超过10条
    max_page_size = 40
    # 获取页码数
    page_query_param = 'page'

    def get_paginated_response(self, data):
        # return OrderedDict([
        #     ('count', self.page.paginator.count),
        #     ('next', self.get_next_link()),
        #     ('previous', self.get_previous_link()),
        #     ('results', data)
        # ])
        return self.page.paginator.count
