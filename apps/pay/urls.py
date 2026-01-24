from django.urls import path
from apps.pay import views

urlpatterns = [
    path('payment/<order_id>/', views.PayUrlView.as_view()),

]