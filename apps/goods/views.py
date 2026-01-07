from django.shortcuts import render

# Create your views here.

from django.views import View
from utils.goods import get_categories
from apps.contents.models import ContentCategory

class IndexView(View):

    def get(self, request):
        categories = get_categories()

        contents = {}
        contents_categories = ContentCategory.objects.all()
        for cat in contents_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories': categories,
            'contents': contents,
        }

        return render(request, 'index.html', context=context)
