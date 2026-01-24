from alipay import AliPay, AliPayConfig
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from apps.orders.models import OrderInfo
from meiduo import settings


class PayUrlView(View):
    def get(self, request,order_id):
        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                                          user=user)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '无此订单'})

        app_private_key = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
        #建立支付宝实例
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None, #默认回调url
            app_private_key_string=app_private_key,#私钥
            alipay_public_key_string=alipay_public_key,#公钥
            sign_type="RSA2",
            debug=True,
            config=AliPayConfig(timeout=15)
        )

        subject = '测试订单'

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, #订单id
            total_amount=str(order.total_amount), #总价格
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL,      #支付成功时跳转页面
            notify_url='https://example.com/notify',
        )
        pay_url = settings.ALIPAY_URL + "?" + order_string
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'alipay_url': pay_url})