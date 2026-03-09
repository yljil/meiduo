from django.urls import path
from apps.orders import views

urlpatterns = [
    path('orders/settlement/', views.OrdersSettlementView.as_view()),
    # path('orders/simple/', views.CartsSimpleView.as_view)
    path('orders/commit/', views.OrderCommitView.as_view()),
    path('orders/', views.OrderListView.as_view()),  # 订单列表
    path('orders/<order_id>/', views.OrderDetailView.as_view()),  # 订单详情
]