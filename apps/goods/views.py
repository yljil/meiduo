import os

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import DetailView

from apps.goods.models import SKU, GoodsCategory
# Create your views here.

from django.views import View

from meiduo import settings
from utils.goods import get_categories, get_breadcrumb, get_goods_specs
from apps.contents.models import ContentCategory

class IndexView(View):

    def get(self, request):
        categories = get_categories()

        contents = {}
        contents_categories = ContentCategory.objects.all()
        for cat in contents_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories': categories,
            'contents': contents,
        }

        return render(request, 'index.html', context=context)


"""商品展示分页"""
class ListView(View):
    def get(self,request,category_id):

        # 排序字段
        ordering = request.GET.get('ordering')
        # 每页多少条数据
        page_size = request.GET.get('page_size')
        # 要第几页数据
        page = request.GET.get('page')

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数缺失'})
        # 4.获取面包屑数据
        breadcrumb = get_breadcrumb(category)

        skus = SKU.objects.filter(category=category,is_launched=True)

        from django.core.paginator import Paginator
        # object_list, per_page
        # object_list   列表数据
        # per_page      每页多少条数据
        paginator = Paginator(skus, per_page=page_size)

        # 获取指定页码的数据
        page_skus = paginator.page(page)
        sku_list = []
        #将对象转换为字典数据
        for sku in page_skus.object_list:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })

        # 获取总页码
        total_num = paginator.num_pages

        # 6.返回响应
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'list': sku_list,
                             'count': total_num,
                             'breadcrumb': breadcrumb})


"""商品热销排行"""
class HotGoodsView(View):

    def get(self,request,category_id):
        # 根据销量倒序
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        # 序列化
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })

        return JsonResponse({'code': 0, 'errmsg': 'OK', 'hot_skus': hot_skus})

"""
docker运行
全文检索
Elasticsearch
"""
from haystack.views import SearchView
from django.http import JsonResponse
class MySearchView(SearchView):
    '''重写SearchView类'''
    def create_response(self):
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })
        # 拼接参数, 返回
        return JsonResponse(data_list, safe=False)


'''查询SKU规格信息'''
class DetailView(View):

    def get(self,request,sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')
            # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)
        # 查询SKU规格信息
        goods_specs = get_goods_specs(sku)
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }
        return render(request,'detail.html',context)


"""
访问量
前端发送请求
后端接收，获取数据
实现逻辑
返回json数据
"""
from datetime import date
from apps.goods.models import GoodsVisitCount
class CategoryVisitCountView(View):
    def post(self,request,category_id):
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': '400', 'errmsg': '没有此类'})
        # 2.查询日期数据
        # 获取当天日期
        today_date = date.today()
        try:
            # 3.如果有当天商品分类的数据  就累加数量
            count_data = category.goodsvisitcount_set.get(date=today_date)
        except:
            # 4. 没有, 就新建之后在增加
            count_data = GoodsVisitCount()
        try:
            count_data.count += 1
            count_data.category = category
            count_data.save()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '新增失败'})
        return JsonResponse({'code': 0, 'errmsg': 'OK'})