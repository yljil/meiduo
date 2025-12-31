from django.contrib.auth import login
from django.shortcuts import render

# Create your views here.
from django.views import View
from QQLoginTool.QQtool import OAuthQQ

from apps.oauth.models import OAuthUser
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
        # '40A140CFBD7287354A62906C454E8937'
        token = qq.get_access_token(code)
        openid = qq.get_open_id(token)


        try:
            qquser = OAuthUser.objects.get(openid=openid)
        except OAuthUser.DoesNotExist:
            #没有绑定过
            response = JsonResponse({'code':'400','access_token':openid})
            return response
        else:
            #绑定过
            login(request, qquser.user)
            response = JsonResponse({'code':0,'errmsg':'ok'})
            response.set_cookie('username', qquser.user.username)
            return response