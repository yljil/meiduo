from django.urls import converters
#判断用户名是否符合要求
#转换器
class UsernameConverter:
    regex = '[A-Za-z0-9_]{5,20}'
    def to_python(self, value):
        return value