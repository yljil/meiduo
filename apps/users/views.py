import json
import re

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.users.models import User


# Create your views here.
class UsernameCountView(View):
    def get(self,request,username):
        # if not re.match('[a-zA-Z0-9_-]{5,20}', username):
        #     return JsonResponse({'code':200,'errmsg': '用户名不符合'})

        count = User.objects.filter(username=username).count()


        return JsonResponse({'code':0, 'count': count, 'errmsg': 'ok'})

class RegisterView(View):
    def get(self,request):

        body_bytes = request.body
        body_str = body_bytes.decode()
        body_dict = json.load(body_str)

        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        allow = body_dict.get('allow')

        #all([xxx,xxx,xxx]) 只要有None,False 就返回False
        if all([username, password, password2, mobile, allow]):
            return JsonResponse({'code': 400, 'errmsg': ''})

        if not re.match('[a-zA-Z0-9_-]{5,20}',username):
            return JsonResponse({'code': 400, 'errmsg': '用户名XX'})



        User.objects.create_user(username=username,password=password,mobile=mobile,allow=allow)

