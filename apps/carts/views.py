import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

# Create your views here.
from apps.goods.models import SKU
class CartsView(View):

    def post(self, request):
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        try:
            sku = SKU.objects.get(id = sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'coed': 400, 'errmsg': '无此商品'})
        try:
            count = int(count)
        except Exception:
            count = 1

        user = request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            redis_cli.hset('carts_%s' % user.id, sku_id, count)
            #默认勾选
            redis_cli.sadd('carts_%s' % user.id, sku_id)
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            import pickle
            import base64
            #获取cookie数据,并判断
            cookie_carts = request.COOKIES.get('carts')
            if cookie_carts:
                carts = pickle.loads(base64.b64encode(cookie_carts))
            else:
                carts = {}

            #判断是否在购物车中
            if sku_id in carts:
                origin_count = carts[sku_id]['count']
                count += origin_count
            #     carts[sku_id] = {
            #         'count': count,
            #         'selected': True
            #     }
            #     pass
            # else:

            #更新数据
            carts[sku_id] = {
                'count': count,
                'selected': True
            }
            carte_bytes = pickle.dumps(carts)
            base64encode = base64.b64encode(carte_bytes)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts',base64encode.decode(),max_age=3600*24*12)
            return response