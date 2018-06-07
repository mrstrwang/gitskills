from haystack import indexes
from books.models import Books

#制定对于某个类的某些数据建立索引,一般类名:模型类名+index

class BooksIndex(indexes.SearchIndex,indexes.Indexable):
	text = indexes.CharField(document=True,use_template=True)

	def get_model(self):
		return Books

	def index_queryset(self, using=None):
		return self.get_model().objects.all()





