from django.urls import path
from apps.carts import views

urlpatterns = [
    path('carts/', views.CartsView.as_view()),
]