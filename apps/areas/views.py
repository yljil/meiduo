from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.areas.models import Area


# Create your views here.
class AreasView(View):

    def get(self, request):

        provinces = Area.objects.filter(parent__isnull=True)

        provinces_list = []
        for province in provinces:
            provinces_list.append(
                {
                    'id': province.id,
                    'name': province.name
                }
            )
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'province_list': provinces_list})
class SubAreasView(View):
    def get(self, request,id):
        up_level = Area.objects.get(id=id)
        down_level = up_level.subs.all()
        data_list = []
        for item in down_level:
            data_list.append({
                'id': item.id,
                'name': item.name
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'sub_data':{'subs': data_list}})