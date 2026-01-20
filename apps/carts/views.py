import json
import pickle
import base64
from urllib import response

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

# Create your views here.
from apps.goods.models import SKU
class CartsView(View):

    '''添加购物车'''
    def post(self, request):
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        try:
            sku = SKU.objects.get(id = sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '无此商品'})
        try:
            count = int(count)
        except Exception:
            count = 1
            # return HttpResponseBadRequest('参数count有误')
        user = request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')

            pipeline = redis_cli.pipeline()
            '''
            数据累加
            1.先获取之前的数据，然后累加
            2.hincrby进行累加
            '''
            # redis_cli.hset('carts_%s' % user.id, sku_id, count)
            pipeline.hincrby('carts_%s'%user.id, sku_id, count)

            #默认勾选
            pipeline.sadd('selected_%s' % user.id, sku_id)
            pipeline.execute()

            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            #获取cookie数据,并判断
            cookie_carts = request.COOKIES.get('carts')
            print(cookie_carts)
            if cookie_carts:
                # carts = pickle.loads(base64.b64encode(cookie_carts.encode()))
                cart_bytes = base64.b64decode(cookie_carts.encode())
                carts = pickle.loads(cart_bytes)
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
            cart_bytes = pickle.dumps(carts)
            base64encode = base64.b64encode(cart_bytes)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts',base64encode.decode(),max_age=3600*24*12)
            return response

    """显示购物车"""
    def get(self,request):
        user = request.user
        if user.is_authenticated: #判断用户是否登入
            #查询购物车
            redis_conn = get_redis_connection('carts')
            #查询购物车数据
            redis_cart = redis_conn.hgetall('carts_%s' % user.id)
            #获取选中状态信息
            cart_selected = redis_conn.smembers('selected_%s' % user.id)
            # print(cart_selected)
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
                'count': int(carts.get(sku.id).get('count')),
                'selected': carts.get(sku.id).get('selected'),
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts.get(sku.id).get('count')),
            })
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'cart_skus': sku_list})

    '''修改购物车'''
    def put(self, request):
        user = request.user
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected')
        print(selected)
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '没有此商品'})
        try:
            count = int(count)
        except Exception:
            count = 1

        #用户已经登陆
        if user.is_authenticated:

            redis_cli = get_redis_connection('carts')

            redis_cli.hset('carts_%s' % user.id, sku_id, count)
            if selected:
                redis_cli.sadd('selected_%s' % user.id,sku_id)
            else:
                redis_cli.srem('selected_%s' % user.id,sku_id)

            return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': {'count': count, 'selected': selected}})

        else:

            cookie = request.COOKIES.get('carts')

            if cookie is not None:
                carts = pickle.loads(base64.b64decode(cookie))
            else:
                carts = {}

            # if sku_id in carts:
            carts[sku_id] = {'count': count, 'selected': selected}

            #加密
            new_carts = base64.b64encode(pickle.dumps(carts))
            response = JsonResponse({'code': 0, 'errmsg': '修改购物车成功', 'cart_sku': {'count': count, 'selected': selected}})
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', new_carts.decode(), max_age=7 * 24 * 3600)
            return response
    '''删除'''
    def delete(self,request):
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        try:
            SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '没有此商品'})

        user = request.user
        if user.is_authenticated:

            redis_cli = get_redis_connection('carts')
            redis_cli.hdel('carts_%s' % user.id,sku_id)
            redis_cli.srem('selected_%s' % user.id,sku_id)

            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            cookie = request.COOKIES.get('carts')
            if cookie is not None:
                carts = pickle.loads(base64.b64decode(cookie))
            else:
                carts = {}

            del carts[sku_id]
            new_carts = base64.b64encode(pickle.dumps(carts))

            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts', new_carts.decode(), max_age=7*24*3600)

            return response



"""全选购物车"""
class CartsSelectAllView(View):

    def put(self,request):
        data = json.loads(request.body.decode())
        #设置默认全选
        selected = data.get('selected',True)
        if selected:
            if not isinstance(selected,bool):  #判断数据是否符合
                return JsonResponse({'code': 400, 'errmsg': '数据错误'})
        user= request.user
        if user is not None and user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            carts = redis_cli.hgetall('carts_%s' % user.id)
            sku_id_list = carts.keys()
            if selected:
                #全选
                redis_cli.sadd('selected_%s' % user.id,*sku_id_list)
            else:
                #取消全选
                redis_cli.srem('selected_%s' % user.id,*sku_id_list)
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:

            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            carts = request.COOKIES.get('carts')
            if carts is not None:
                carts = pickle.loads(base64.b64decode(carts.encode()))
                for sku_id in carts:
                    carts[sku_id]['selected'] = selected
                cookie_cart = base64.b64encode(pickle.dumps(carts)).decode()
                response.set_cookie('carts', cookie_cart,max_age=7*24*3600)
            return response