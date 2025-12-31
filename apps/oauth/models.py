from django.db import models

# Create your models here.
from django.db import models
from utils.models import BaseModel

class OAuthUser(BaseModel):

    user = models.ForeignKey('users.User', on_delete=models.CASCADE,verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid',db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登陆用户数据'
        verbose_name_plural = verbose_name

