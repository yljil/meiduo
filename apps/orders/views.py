import base64
import json
import pickle
from decimal import Decimal

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.views import LoginRequiredjsonMixin
# Create your views here.
'''订单功能实现


'''


'''显示订单页面'''
class OrdersSettlementView(LoginRequiredjsonMixin,View):

    def get(self, request):
        user = request.user
        # print(user)
        addresses = Address.objects.filter(is_deleted=False,user=user)
        #获取地址信息
        addresses_list = []
        for address in addresses:
            addresses_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })

        #获取redis中商品的信息
        redis_cli = get_redis_connection('carts')
        pipeline = redis_cli.pipeline()

        pipeline.hgetall('carts_%s' % user.id)
        pipeline.smembers('selected_%s' % user.id)

        result = pipeline.execute()
        #商品数量
        sku_id_count = result[0]
        #商品选中状态
        selected_ids = result[1]

        #获取到被选中商品的数量信息
        selected_carts = {}
        for sku_id in selected_ids:
            selected_carts[int(sku_id)] = int(sku_id_count[sku_id])

        #获取到要显示的商品信息
        sku_list = []
        for sku_id, count in selected_carts.items():
            sku = SKU.objects.get(pk=sku_id)

            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'count': count,
                'price': sku.price
            })
        freight = Decimal('10.00')   #货币类型
        context = {
            'skus': sku_list,
            'addresses': addresses_list,
            'freight': freight
        }
        return JsonResponse({'code': 200, 'errmsg': 'ok', 'context': context})


# class CartsSimpleView(View):
#
#     def get(self, request):
#         user = request.user
#
#         if user.is_authenticated:
#             redis_conn = get_redis_connection('carts')
#             redis_cart = redis_conn.hgetall('carts_%s' % user.id)
#             cart_selected = redis_conn.smembers('selected_%s' % user.id)
#             # 将redis中的两个数据统一格式，跟cookie中的格式一致，方便统一查询
#             cart_dict = {}
#             for sku_id, count in redis_cart.items():
#                 cart_dict[int(sku_id)] = {
#                     'count': int(count),
#                     'selected': sku_id in cart_selected
#                 }
#         else:
#             cart_str = request.COOKIES.get('carts')
#             if cart_str:
#                 cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
#             else:
#                 cart_dict = {}
#
#                 # 构造简单购物车JSON数据
#         cart_skus = []
#         sku_ids = cart_dict.keys()
#         skus = SKU.objects.filter(id__in=sku_ids)
#         for sku in skus:
#             cart_skus.append({
#                 'id': sku.id,
#                 'name': sku.name,
#                 'count': cart_dict.get(sku.id).get('count'),
#                 'default_image_url': sku.default_image.url
#             })
#
#         # 响应json列表数据
#         return JsonResponse({'code': 0, 'errmsg': 'OK', 'cart_skus': cart_skus})


from django.db import transaction
class OrderCommitView(LoginRequiredjsonMixin, View):
    def post(self, request):
        user = request.user
        data = json.loads(request.body.decode())
        address_id = data.get('address_id')
        #支付方式
        pay_method = data.get('pay_method')

        #验证数据
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})

        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数不正确'})

        # if pay_method not in [1,2]:
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': 400, 'errmsg': '参数错误'})

        #生成订单ID(年月日时分秒+用户ID)
        from django.utils import timezone
        from datetime import datetime
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S%f')

        # if pay_method == 1: #货到付款
        #     pay_method = 2
        # else:
        #     pay_method = 1

        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
        from decimal import Decimal
        total_amount = Decimal('0')
        freight = Decimal('10')

        with transaction.atomic():

            point = transaction.savepoint()
            orderinfo = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=0,
                total_amount=total_amount,
                freight=freight,
                pay_method=pay_method,
                status=status
            )

            redis_cli = get_redis_connection('carts')
            sku_id_counts = redis_cli.hgetall('carts_%s' % user.id)
            selected_ids = redis_cli.smembers('selected_%s' % user.id)

            carts = {}
            for sku_id in selected_ids:
                carts[int(sku_id)] = int(sku_id_counts[sku_id])
            for sku_id, count in carts.items():
                for i in range(5):
                    sku = SKU.objects.get(id=sku_id)
                    #判断库存是否充足
                    if sku.stock < count:

                        transaction.savepoint_rollback(point)
                        return JsonResponse({'code': 400, 'errmsg': '库存不足'})
                    # sku.stock -= count
                    # sku.sales += count
                    # sku.save()
                    from time import sleep
                    # sleep(7)


                    old_stock = sku.stock
                    new_stock = sku.stock - count
                    new_sales = sku.sales + count
                    result = SKU.objects.filter(id=sku_id,stock=old_stock).update(stock=new_stock,sales=new_sales)
                    if result == 0:
                        sleep(0.005)
                        continue
                        # transaction.savepoint_rollback(point)
                        # return JsonResponse({'code': 400, 'errmsg': 'XXX'})
                        # pass

                    #总数量和总金额
                    orderinfo.total_count += count
                    orderinfo.total_amount += (count*sku.price)
                    #保存订单信息
                    OrderGoods.objects.create(
                        order=orderinfo,
                        sku=sku,
                        count=count,
                        price=sku.price
                    )
                    break

            orderinfo.save()
            transaction.savepoint_commit(point)

            #将redis中的选中商品移除
            pl = redis_cli.pipeline()
            pl.hdel('carts_%s' % user.id, *selected_ids)
            pl.srem('selected_%s' % user.id, *selected_ids)
            pl.execute()


        return JsonResponse({'code': 0, 'errmsg': 'ok', 'order_id': order_id})

#################################################################
class OrderListView(LoginRequiredjsonMixin, View):
    """订单列表视图"""

    def get(self, request):
        """
        获取当前用户的所有订单列表
        支持分页和状态筛选
        请求参数:
            page: 页码（默认1）
            page_size: 每页数量（默认5）
            status: 订单状态筛选（可选）
        """
        user = request.user

        # 获取请求参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 5))
        status = request.GET.get('status')  # 可选的状态筛选

        # 查询订单
        orders = OrderInfo.objects.filter(user=user)

        # 如果指定了状态，进行筛选
        if status:
            try:
                status = int(status)
                orders = orders.filter(status=status)
            except ValueError:
                pass

        # 按创建时间倒序排列
        orders = orders.order_by('-create_time')

        # 分页
        paginator = Paginator(orders, per_page=page_size)

        try:
            page_orders = paginator.page(page)
        except:
            page_orders = paginator.page(1)
            page = 1

        # 构建订单列表数据
        order_list = []
        for order in page_orders.object_list:
            # 获取订单商品
            order_goods = order.skus.all()
            sku_list = []
            for order_good in order_goods:
                sku_list.append({
                    'id': order_good.sku.id,
                    'name': order_good.sku.name,
                    'count': order_good.count,
                    'price': str(order_good.price),
                    'default_image_url': order_good.sku.default_image.url if order_good.sku.default_image else '',
                    'amount': str(order_good.count * order_good.price)
                })

            # 获取支付方式名称
            pay_method_name = dict(OrderInfo.PAY_METHOD_CHOICES).get(order.pay_method, '未知')

            # 获取订单状态名称
            status_name = dict(OrderInfo.ORDER_STATUS_CHOICES).get(order.status, '未知')

            order_list.append({
                'order_id': order.order_id,
                'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': order.status,
                'status_name': status_name,
                'total_amount': str(order.total_amount + order.freight),  # 总金额包含运费
                'total_count': order.total_count,
                'pay_method': order.pay_method,
                'pay_method_name': pay_method_name,
                'freight': str(order.freight),
                'skus': sku_list
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'orders': order_list,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_count': paginator.count
        })


class OrderDetailView(LoginRequiredjsonMixin, View):
    """订单详情视图"""

    def get(self, request, order_id):
        """
        获取订单详情
        :param order_id: 订单ID
        """
        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '订单不存在'})

        # 订单基本信息
        order_dict = {
            'order_id': order.order_id,
            'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': order.status,
            'status_name': dict(OrderInfo.ORDER_STATUS_CHOICES).get(order.status, '未知'),
            'total_count': order.total_count,
            'total_amount': str(order.total_amount),
            'freight': str(order.freight),
            'payment_amount': str(order.total_amount + order.freight),  # 实付金额
            'pay_method': order.pay_method,
            'pay_method_name': dict(OrderInfo.PAY_METHOD_CHOICES).get(order.pay_method, '未知'),
            'address': {
                'receiver': order.address.receiver,
                'province': order.address.province.name,
                'city': order.address.city.name,
                'district': order.address.district.name,
                'place': order.address.place,
                'mobile': order.address.mobile,
                'tel': order.address.tel or '',
                'email': order.address.email or ''
            },
            'skus': []
        }

        # 订单商品信息
        order_goods = order.skus.all()
        for order_good in order_goods:
            order_dict['skus'].append({
                'id': order_good.sku.id,
                'name': order_good.sku.name,
                'count': order_good.count,
                'price': str(order_good.price),
                'amount': str(order_good.count * order_good.price),
                'default_image_url': order_good.sku.default_image.url if order_good.sku.default_image else '',
                'comment': order_good.comment,
                'score': order_good.score,
                'is_commented': order_good.is_commented
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'order': order_dict
        })