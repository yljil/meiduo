from django.urls import path

from apps.users import views

urlpatterns = [
    path('usernames/<username:username>/count/', views.UsernameCountView.as_view()), #判断用户名是否重复
    path('register/',views.RegisterView.as_view()),
    path('login/',views.LoginView.as_view()),
    path('logout/',views.LogoutView.as_view()),
    path('center/',views.CenterView.as_view())
]