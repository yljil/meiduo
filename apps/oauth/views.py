from django.shortcuts import render

# Create your views here.
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
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