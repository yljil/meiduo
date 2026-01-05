from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.areas.models import Area

from django.core.cache import cache
# Create your views here.
class AreasView(View):
    def get(self, request):
        provinces_list = cache.get('province')
        #判断缓存中是否存在
        if provinces_list is None:

            provinces = Area.objects.filter(parent__isnull=True)

            provinces_list = []
            for province in provinces:
                provinces_list.append(
                    {
                        'id': province.id,
                        'name': province.name
                    }
                )
        #保存缓存数据
            cache.set('province', provinces_list,24*3600)

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'province_list': provinces_list})
class SubAreasView(View):
    def get(self, request,id):
        data_list = cache.get('city:%s'%id)
        if data_list is None:
            #从数据库中查询数据
            up_level = Area.objects.get(id=id)
            #获取该市中所有区的信息
            down_level = up_level.subs.all()

            #改为前端可以接收的数据
            data_list = []
            for item in down_level:
                data_list.append({
                    'id': item.id,
                    'name': item.name
                })
            cache.set('city:%s'%id, data_list, 24 * 3600)
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'sub_data':{'subs': data_list}})
"""
增（注册）
    获取数据
    验证数据
    数据入库
    返回响应
删
    查询指定数据 
    删除数据
    返回响应
改（个人信息）
    查询指定数据
    更改数据
    验证数据
    数据更新
查（信息展示）
    查询指定数据
    将数据转为字典数据
    返回响应
"""


