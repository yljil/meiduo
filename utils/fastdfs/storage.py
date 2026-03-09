

from django.core.files.storage import Storage

class MyStorage(Storage):

    def open(self, name, mode='rb'):
        pass

    def _save(self, name, content,max_length=None):
        pass

    def url(self, name):
        return "http://www.meiduo.site:8888/" + name #docker启动是设置的IP