import json
import pickle
import base64
from django.http import JsonResponse, HttpResponseBadRequest
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
            # return HttpResponseBadRequest('参数count有误')
        user = request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            redis_cli.hset('carts_%s' % user.id, sku_id, count)
            #默认勾选
            redis_cli.sadd('carts_%s' % user.id, sku_id)
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
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

    def get(self,request):
        user = request.user
        if user.is_authenticated: #判断用户是否登入
            #查询购物车
            redis_conn = get_redis_connection('carts')
            #查询购物车数据
            redis_cart = redis_conn.hgetall('carts_%s' % user.id)
            #获取选中状态信息
            cart_selected = redis_conn.smembers('selected_%s' % user.id)

            carts = {}
            for sku_id, count in redis_cart.items():
                carts[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            #查询cookies购物车
            cookie_carts = request.COOKIES.get('carts')
            if cookie_carts:
                # 将cart_str转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                carts = {}

        sku_ids = carts.keys()

        skus = SKU.objects.filter(id__in=sku_ids)
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts.get(sku.id).get('count'),
                'selected': str(carts.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts.get(sku.id).get('count')),
            })
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'cart_skus': sku_list})
