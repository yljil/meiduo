

from django.core.files.storage import Storage

class MyStorage(Storage):

    def open(self, name, mode='rb'):
        pass

    def _save(self, name, content,max_length=None):
        pass

    def url(self, name):
        return "http://127.0.0.1:8000/" + name #docker启动是设置的IP