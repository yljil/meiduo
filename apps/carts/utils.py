import pickle,base64

from django_redis import get_redis_connection

"""合并cookie和redis数据"""
def merge_cookie_to_redis(request,response):
    #获取cookie数据
    cookie_carts = request.COOKIES.get('carts')
    if cookie_carts is not None:
        carts = pickle.loads(base64.b64decode(cookie_carts))
        #设置字典和列表保存sku_id:count,选中的商品id,未选中商品id
        cookie_dict = {}
        selected_ids = []
        unselected_ids = []
        for sku_id,cookie_selected_dict in carts.items():
            cookie_dict[sku_id] = cookie_selected_dict['count']

            if cookie_selected_dict['selected']:
                selected_ids.append(sku_id)
            else:
                unselected_ids.append(sku_id)

        #将合并数据保存到redis
        redis_cli = get_redis_connection('carts')

        pipeline = redis_cli.pipeline()
        pipeline.hmset('carts_%s' % request.user.id,cookie_dict)
        if len(selected_ids) > 0:
            pipeline.sadd('selected_%s' % request.user.id, *selected_ids)

        if len(unselected_ids) > 0:
            pipeline.srem('selected_%s' % request.user.id, *unselected_ids)
        pipeline.execute()

        response.delete_cookie('carts')

    return response