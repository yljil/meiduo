import re

from django.contrib.auth import login
from django.shortcuts import render
import json
# Create your views here.
from django.views import View
from QQLoginTool.QQtool import OAuthQQ

from apps.oauth.models import OAuthUser
from apps.users.models import User
from meiduo import settings
from django.http import JsonResponse

class QQLoginURLView(View):
    def get(self, request):
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID, #appid
                     client_secret=settings.QQ_CLIENT_SECRET, #appsecret
                     redirect_uri=settings.QQ_CALLBACK_URL, #跳转的页面
                     state='xxxxx')  #不知道什么意识
        qq_login_url = qq.get_qq_url()
        return JsonResponse({'code':0,'errmsg':'ok','login_url':qq_login_url})

class OauthQQView(View):
    def get(self, request):
        code = request.GET.get('code')
        if code is None:
            return JsonResponse({'code':'400','errmsg':'参数不全'})
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID, #appid
                     client_secret=settings.QQ_CLIENT_SECRET, #appsecret
                     redirect_uri=settings.QQ_CALLBACK_URL, #跳转的页面
                     state='xxxxx')  #不知道什么意识

        token = qq.get_access_token(code)

        openid = qq.get_open_id(token)


        try:
            qquser = OAuthUser.objects.get(openid=openid)
        except OAuthUser.DoesNotExist:
            #没有绑定过
            """
            from meiduo import settings
            from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
            # 这个类可以对数据进行加密，还可以添加一个时效
            # secret_key     密钥， expires_in   过期时间(秒)
            s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
            access_token = s.dumps({'openid':openid})
            """
            from apps.oauth.utlis import generic_openid
            access_token = generic_openid(openid)
            response = JsonResponse({'code':'400','access_token':access_token})
            return response
        else:
            #绑定过
            login(request, qquser.user)
            response = JsonResponse({'code':0,'errmsg':'ok'})
            response.set_cookie('username', qquser.user.username)
            return response

    def post(self, request):
        data = json.loads(request.body.decode())
        mobile = data.get('mobile')
        password = data.get('password')
        sms_code = data.get('sms_code')
        openid = data.get('access_token')
        """
        #对数据进行校验
        if not all([mobile,password,sms_code]):
            return JsonResponse({'code':'400','errmsg':'参数不全'})
        if not re.match(r'^1[3-9]\d{9}',mobile):
            return JsonResponse({'code':'400','errmsg': '请输入正确的手机号'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$]',password):
            return JsonResponse({'code':'400','errmsg': '请输入8-20位的密码'})
        
        from django_redis import get_redis_connection

        redis_conn = get_redis_connection('code')

        sms_code_server = redis_conn.get('sms_%s'%mobile)
        if sms_code_server is None:
            return JsonResponse({'code':'400','errmsg':'验证码失效'})

        if sms_code != sms_code_server.decode():
            return JsonResponse({'code':'400','errmsg':'验证码错误'})
        """

        from apps.oauth.utlis import check_access_token
        openid = check_access_token(openid)

        if openid is None:
            return JsonResponse({'code':'400','errmsg':'参数缺失'})

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            #手机号不存在
            user = User.objects.create_user(username=mobile,
                                            mobile=mobile,
                                            password=password,
                                            )
        else:
            if not user.check_password(password):
                return JsonResponse({'code':'400','errmsg':'账号或密码错误'})
        OAuthUser.objects.create(user=user,openid=openid)

        #状态保持
        login(request, user)

        response = JsonResponse({'code':'0','errmsg':'ok'})

        response.set_cookie('username',user.username)
        return response

from meiduo import settings
from itsdangerous import TimedSerializer as Serializer
#这个类可以对数据进行加密，还可以添加一个时效
#secret_key     密钥， expires_in   过期时间(秒)
s = Serializer(secret_key=settings.SECRET_KEY)
to = s.dumps({'openid':'1234567890'})
#解密
s.loads(to)