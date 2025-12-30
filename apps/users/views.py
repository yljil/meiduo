import json
import re

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.users.models import User


# Create your views here.

#判断用户名是否重复
class UsernameCountView(View):
    def get(self, request, username):
        #接收用户名
        """判断用户名是否满足要求
                if not re.match('[a-zA-Z0-9_-]{5,20}', username):
            return JsonResponse({'code':200,'errmsg': '用户名不符合'})
        """
        #查询用户名数量
        count = User.objects.filter(username=username).count()

        #返回前端进行判断
        return JsonResponse({'code':0, 'count': count, 'errmsg': 'ok'})

class RegisterView(View):
    def post(self,request):

        body_bytes = request.body  #接收json数据
        body_str = body_bytes.decode()
        body_dict = json.loads(body_str)  #变为字典

        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        allow = body_dict.get('allow')

        #all([xxx,xxx,xxx]) 只要有None,False 就返回False
        if not all([username, password, password2, mobile, allow]):
            return JsonResponse({'code': 400, 'errmsg': '数据不全'})

        if not re.match('[a-zA-Z_-]{5,20}',username):
            return JsonResponse({'code': 400, 'errmsg': '用户名XX'})
        """密码满足规则
            确认密码与密码要一致
            手机号不重复
            要同意协议
        """

        #数据入库
        """这两种都没有加密
        1.
        user = User(username=username, password=password, mobile=mobile)
        user.save()
        2.
        User.objects.create(username=username, password=password, mobile=mobile)
        """
        user = User.objects.create_user(username=username, password=password, mobile=mobile)


        """设置session信息
        request.session['user_id'] = user.id
        """
        # 系统（Django）为我们提供了 状态保持的方法
        from django.contrib.auth import login
        # request, user,
        # 状态保持 -- 登录用户的状态保持
        # user 已经登录的用户信息
        login(request, user)

        # 5. 返回响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


#登入
class LoginView(View):

    def post(self,request):

        #获取json数据
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        remembered = data.get('remembered')

        #判断是否输入账号密码
        if not all([username, password]):
            return JsonResponse({'code': 400, 'errmsg': '数据不全'})


        #根据修改User.USERNAME_FIELD字段
        #来影响authenticate的查询
        if re.match('1[3-9]\d{9}',username):
            User.USERNAME_FIELD = 'mobile'
        else:
            User.USERNAME_FIELD = 'username'

        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)

        if user is None:
            return JsonResponse({'code':400,'errmsg':'账号或密码错误！'})
        from django.contrib.auth import login
        login(request, user)


        #登入有效时间
        if remembered:
            #默认两周
            request.session.set_expiry(None)
        else:
            request.session.set_expiry(0)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})

        response.set_cookie('username', username)
        return response

from django.contrib.auth import logout
class LogoutView(View):
    def delete(self,request):
        logout(request)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.delete_cookie('username')

        return response


"""
LoginRequiredMixin 未登录的返回重定向

"""

from utils.views import LoginRequiredjsonMixin

class CenterView(LoginRequiredjsonMixin, View):

    def get(self, request):
        return JsonResponse({'code':0,'errmsg': 'ok'})