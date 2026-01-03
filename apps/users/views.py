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
        #判断是否记住登陆，登入有效时间
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

        #request.user 来自于中间件
        info_data = {
            'username': request.user.username,
            'email': request.user.email,
            'mobile': request.user.mobile,
            'email_active': request.user.email_active,
        }
        return JsonResponse({'code':0,'errmsg': 'ok','info_data':info_data})

class EmailView(LoginRequiredjsonMixin,View):
    def put(self, request):
        #获取数据
        data = json.loads(request.body.decode())
        email = data.get('email')
        #验证数据

        #数据库更新数据
        user = request.user
        user.email = email
        user.save() #保存在数据库中
        
        #发送激活邮件
        from django.core.mail import send_mail
        '''
        subject:主题  message:内容  from_email:发件人  recipient_list:收件人列表
        '''
        subject = '激活邮件'
        message = ''
        from_email = 'md<18870297601@163.com>'
        recipient_list = ['<18870297601@163.com>']
        from apps.users.utils import generate_token

        token = generate_token(request.user.id)

        verify_url = "http://www.meiduo.site:8080/success_verify_email.html?tokon=%s"%token
        html_message = '<p>尊贵的用户您好！</p>' \
                       '<p>感谢您使用XX商城。</p>' \
                       '<p>您的邮箱为：%s。点击链接激活邮箱</p>' \
                       '<p><a href="%s">%s</a></p>'%(email, verify_url, verify_url)
        # html_message = "点击激活 <a href='http://itcast.cn/?token=%s'>激活</a>"
        # send_mail(subject=subject,
        #           message=message,
        #           from_email=from_email,
        #           recipient_list=recipient_list,
        #           html_message=html_message)
        from celery_tasks.email.tasks import celery_send_email
        celery_send_email.delay(subject=subject,
                                message=message,
                                from_email=from_email,
                                recipient_list=recipient_list,
                                html_message=html_message
            )

        return JsonResponse({'code':0,'errmsg':'ok'})
class EmailVerifyView(View):
    def put(self, request):
        ##接收请求
        params = request.GET
        #获取参数
        token = params.get('tokon')

        if token is None:
            return JsonResponse({'code':400,'errmsg':'kong'})

        #解密
        from apps.users.utils import check_token
        user_id = check_token(token)
        if user_id is None:
            return JsonResponse({'code':400,'errmsg':'kong'})

        #从数据库中查询到该数据修改并保存
        user = User.objects.get(id=user_id)
        user.email_active = True
        user.save()
        return JsonResponse({'code':0,'errmsg':'ok'})