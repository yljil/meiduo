from apps.goods.models import SKU
from haystack import indexes

'''python manage.py rebuild_index'''
class SKUIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    def get_model(self):
        return SKU
    def index_queryset(self, using=None):
        return self.get_model().objects.all()