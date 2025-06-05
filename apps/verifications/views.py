from django.http import HttpResponse
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
        from django_redis import get_redis_connection

        #连接redis数据库
        redis_cli = get_redis_connection('code')

        #name,time,value
        redis_cli.setex(uuid,100,text)


        #二进制,不能用json
        #content_type= 数据类型   大类/小类
        #eg: image/jpeg,image/gif,image/png
        return HttpResponse(image,content_type='image/jpeg')
