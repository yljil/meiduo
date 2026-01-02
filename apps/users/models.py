from django.db import models

# Create your models here.
#django自带的
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):  #继承
    mobile = models.CharField(max_length=11,unique=True)
    email_active = models.BooleanField(default=False,verbose_name="验证状态")
    """自己定义模型
    密码要加密
    class User(models.Model):
        username = models.CharField(max_length=20, unique=True)  #唯一
        password = models.CharField(max_length=20)
        mobile = models.CharField(max_length=11)
    """
    class Meta:
        db_table = 'tb_users'  #更改表名默认auth_users
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name
