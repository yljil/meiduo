from django.db import models

# Create your models here.

#自己建立模型
# class User(models.Model):
#     username = models.CharField(max_length=20, unique=True)  #唯一
#     password = models.CharField(max_length=20)
#     mobile = models.CharField(max_length=11)
#


#django自带的
# from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):  #继承
    mobile = models.CharField(max_length=11,unique=True)

    class Meta:
        db_table = 'tb_users'  #更改表名
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name
