from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse


class LoginRequiredjsonMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        return JsonResponse({'code': 400, 'msg': '没有登陆'})