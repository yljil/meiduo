from django.db import models

# Create your models here.

class Area(models.Model):
    name = models.CharField(max_length=50,verbose_name='名称')

    parent = models.ForeignKey('self',
                               on_delete=models.SET_NULL,
                               related_name='subs',
                               null=True,
                               blank=True,verbose_name='上级行政区划')
    class Meta:
        db_table = 'tb_areas'
        verbose_name = '省市区'
        verbose_name_plural = '省市区'
    def __str__(self):
        return self.name

"""
查询省
select * from tb_areas where parent_id is None;
Area.objects.filter(parent_id=None)//(parent_id_sinull = True)
市
select * from tb_areas where parent_id=130000;
Area.objects.filter(parent_id=130000)

pr = Area.objects.filter(parent_id=130000)  省
pr.subs.all() 市
区县
select * from tb_areas where parent_id=130600;

ci = Area.objects.filter(parent_id=130600)  #市
ci.subs.all() #区县

"""
