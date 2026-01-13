#!/usr/bin/env python

import sys
sys.path.insert(0, '../')

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo.settings")

import django
django.setup()


from apps.goods.models import SKU
from utils.goods import get_categories, get_breadcrumb, get_goods_specs

def generate_detail_html(sku):
    """
    生成静态商品详情页面
    :param sku_id: 商品sku id
    """
    # try:
    #     # 获取当前sku的信息
    #     sku = SKU.objects.get(id=sku_id)
    # except SKU.DoesNotExist:
    #     pass
    # 查询商品频道分类
    categories = get_categories()
    # 查询面包屑导航
    breadcrumb = get_breadcrumb(sku.category)

    goods_specs = get_goods_specs(sku)
    # 上下文
    context = {
        'categories': categories,
        'breadcrumb': breadcrumb,
        'sku': sku,
        'specs': goods_specs,
    }
    from django.template import loader
    template = loader.get_template('detail.html')

    html_text = template.render(context)
    from meiduo import settings
    file_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'meiduo/front_end_pc/goods/%s.html' % sku.id)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)

skus = SKU.objects.all()
for sku in skus:
    generate_detail_html(sku)