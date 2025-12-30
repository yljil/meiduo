from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View


# Create your views here.




"""
前端
    拼接一个url
后端
    请求           接收uuid
    业务逻辑        生成验证码，保存在redis
    响应           返回图片二进制

"""
class ImageCodeView(View):

    def get(self,request,uuid):

        from libs.captcha.captcha import captcha
        #text 图片验证码内容
        #image 是图片二进制
        text,image = captcha.generate_captcha()
        print(text)
        from django_redis import get_redis_connection

        #连接redis数据库,并保存到settings.py中的code库（2号）
        redis_cli = get_redis_connection('code')

        #name,time,value
        redis_cli.setex(uuid,100,text)


        #二进制,不能用json
        #content_type= 数据类型   大类/小类
        #eg: image/jpeg,image/gif,image/png
        return HttpResponse(image,content_type='image/jpeg')




#手机验证码
class SmsCodeView(View):
    def get(self,request,mobile):
        #获取数据
        image_code = request.GET.get('image_code')
        uuid= request.GET.get('image_code_id')
        if not all([image_code,uuid]):
            return JsonResponse({'code':400,'errmsg':'参数不全'})

        #连接redis
        from django_redis import get_redis_connection
        redis_cli = get_redis_connection('code')

        redis_image_code = redis_cli.get(uuid)

        if redis_image_code is None:
            return JsonResponse({'code':400,'errmsg':'图片验证码过期'})

        #全部转为小写
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code':400,'errmsg':'图片验证码错误'})

        #查看标记
        send_flag = redis_cli.get('send_flag_%s'%mobile)
        print(send_flag)
        if send_flag is not None:
            return JsonResponse({'code':400,'errmsg':'不要频繁发送短信'})

        #生成验证码
        from random import randint
        sms_code = '%06d'%randint(0,999999)

        # 管道 3步
        # ① 新建一个管道
        pipeline = redis_cli.pipeline()
        # ② 管道收集指令
        # 5. 保存短信验证码
        pipeline.setex(mobile, 300, sms_code)
        # 添加一个发送标记.有效期 60秒 内容是什么都可以
        pipeline.setex('send_flag_%s' % mobile, 120, 1)
        # ③ 管道执行指令
        pipeline.execute()
        """
        redis_cli.setex(mobile,300,sms_code)

         #添加标记防止重复发送
        redis_cli.setex('send_flag_%s'%mobile,600,1)
        """
        # from libs.yuntongxun.sms import CCP

        # CCP().send_template_sms(mobile,[sms_code,5],1)


        from celery_tasks.sms.tasks import celery_send_sms_code
        celery_send_sms_code.delay(mobile,sms_code)

        return JsonResponse({'code':0,'errmsg':'OK'})
