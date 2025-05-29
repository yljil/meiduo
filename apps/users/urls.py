from django.urls import path

from apps.users import views

urlpatterns = [
    path('username/<username:username>/count/', views.UsernameCountView.as_view()),
]