import re
import json
import http.client
from venv import logger

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.users.models import User
from django.shortcuts import render
from utils.views import LoginRequiredjsonMixin
from django.http import JsonResponse, HttpResponseBadRequest

# Create your views here.

"""判断用户名是否重复"""
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

"""注册用户"""
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

"""用户登入"""
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

"""用户退出登入（删除cookie）"""
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

"""用户信息显示"""
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

"""激活邮件的发送（163）"""
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

"""邮箱验证成功后显示并更改状态"""
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


from apps.users.models import Address
""" 添加地址信息并验证 """
class AddressCitiesView(LoginRequiredjsonMixin,View):

    def post(self,request):
        data = json.loads(request.body.decode('utf-8'))
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        user = request.user

        # 2.1 验证必传参数
        if not all([receiver,province_id,city_id,district_id,place,mobile,tel]):
            return HttpResponseBadRequest({'code':400,'errmsg':'参数不全'})
        # 2.2 省市区的id 是否正确
        # 2.3 详细地址的长度
        # 2.4 手机号
        if not re.match(r'^1[3-9]\d{9}',mobile):
            return HttpResponseBadRequest({'code':400,'errmsg': '手机号格式错误'})
        # 2.5 固定电话
        # if tel:
        #     if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})', tel):
        #         return HttpResponseBadRequest('参数tel有误')
        # if email:
        #     if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}', email):
        #         return HttpResponseBadRequest('参数email有误')
        # 2.6 邮箱
        # 3.数据入库
        address = Address.objects.create(
            user=user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})

""" 显示地址信息 """
class AddressView(View):
    def get(self,request):
        #查询数据
        user = request.user
        #addresses = user.addresses

        addresses = Address.objects.filter(user=user,is_deleted=False)

        address_list = []
        for address in addresses:
            address_list.append({
                'id': address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'addresses': address_list})

"""设置默认地址"""
class DefaultAddressView(LoginRequiredjsonMixin, View):
    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return JsonResponse({'code': 0, 'errmsg': '设置默认地址成功'})

"""修改与删除地址"""
class AddressdeledView(View):


    """修改地址"""
    def put(self, request, address_id):

        try:
            # ========== 1. 校验地址是否存在且属于当前登录用户 ==========
            # 查询地址：必须是当前用户的、未被软删除的地址
            address = Address.objects.get(
                id=address_id,
                user=request.user,
                is_deleted=False
            )
        except Address.DoesNotExist:
            # 地址不存在/不属于当前用户
            return JsonResponse({
                'code': 400,
                'errmsg': '地址不存在或无修改权限'
            })
        data = json.loads(request.body.decode('utf-8'))
        """获取更改后的信息"""
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        """保存在数据库"""
        address.receiver = receiver
        address.province_id = province_id
        address.city_id = city_id
        address.district_id = district_id
        address.place = place
        address.mobile = mobile
        address.email = email  # 邮箱可为空
        # 可选：更新地址标题（如收货人姓名）
        address.tel = tel
        # 保存到数据库
        address.save()

        address_dict = {
            'id': address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # ========== 6. 返回成功响应 ==========
        return JsonResponse({'code': 0,'errmsg': '地址修改成功','address': address_dict})
    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return JsonResponse({'code': 0, 'errmsg': '删除地址成功'})

"""修改主题"""
class UpdateTitleAddressView(View):
    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return JsonResponse({'code': 0, 'errmsg': '设置地址标题成功'})

"""修改密码"""
class ChangePasswordView(LoginRequiredMixin, View):
    def put(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        dict = json.loads(request.body.decode())
        old_password = dict.get('old_password')
        new_password = dict.get('new_password')
        new_password2 = dict.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code':400, 'errmsg':'缺少必传参数'})


        result = request.user.check_password(old_password)

        if not result:
            return JsonResponse({'code': 400, 'errmsg': '原始密码不正确'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code': 400, 'errmsg': '密码最少8位,最长20位'})

        if new_password != new_password2:
            return JsonResponse({'code': 400, 'errmsg': '两次输入密码不一致'})

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:

            return JsonResponse({'code': 400, 'errmsg': '修改密码失败'})

        # 清理状态保持信息
        logout(request)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})

        response.delete_cookie('username')
        # # 响应密码修改结果：重定向到登录界面
        return response

"""
最近浏览记录
保存在redis中（mysql也可以）
"""
from apps.goods.models import SKU
from django_redis import get_redis_connection

class UserBrowseHistory(LoginRequiredjsonMixin,View):
    """用户浏览记录"""

    def post(self, request):
        user = request.user
        """保存用户浏览记录"""
        # 接收参数
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')

        # 校验参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': 'sku不存在'})

        # 保存用户浏览数据
        redis_cli = get_redis_connection('history')
        # pl = redis_conn.pipeline()
        # user_id = request.user.id

        # 先去重
        redis_cli.lrem('history_%s' % user.id, 0, sku_id)
        # 再存储
        redis_cli.lpush('history_%s' % user.id, sku_id)
        # 最后截取
        redis_cli.ltrim('history_%s' % user.id, 0, 4)
        # 执行管道
        # redis_cli.execute()

        # 响应结果
        return JsonResponse({'code': 0, 'errmsg': 'OK'})
    def get(self, request):
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0,4)

        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': int(sku_id),
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
            return JsonResponse({'code': 0, 'errmsg': 'OK','skus': skus})
