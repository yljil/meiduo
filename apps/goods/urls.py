from django.urls import path
from apps.goods import views

urlpatterns = [
    path('index/',views.IndexView.as_view()),
]