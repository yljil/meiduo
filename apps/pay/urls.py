from django.urls import path
from apps.pay import views

urlpatterns = [
    path('payment/status/', views.PayStatusView.as_view()),
    path('payment/<order_id>/', views.PayUrlView.as_view()),
    # path('payment/status/', views.PayStatusView.as_view()),
]