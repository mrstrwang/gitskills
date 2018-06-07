from django.db import models
#富文本编辑器的
from tinymce.models import HTMLField
from db.base_model import BaseModel
from .enums import BOOKS_TYPE,STATUS_CHOICE,PYTHON,ONLINE
# Create your models here.


class BooksManager(models.Manager):
	# 通过类型id查找商品信息
	def get_books_by_type(self,type_id,limit=None,sort='default'):
		if sort == 'new':
			order_by = ('-create_time',)
		elif sort == 'hot':
			order_by = ('-sales',)
		elif sort == 'price':
			order_by = ('-price',)
		else:
			order_by = ('-pk',)
		#按照primary key降序

		#查询数据
		books_li = self.filter(type_id=type_id).order_by(*order_by)

		if limit:
			books_li = books_li[:limit]

		return books_li


	#根据商品的id获取商品信息
	def get_books_by_id(self,books_id):
		try:
			books = self.get(id=books_id)
		except self.model.DoesNotExist:
			books = None

		return books



class Books(BaseModel):
	books_type_choices = ((k,v) for k,v in BOOKS_TYPE.items())
	status_choices = ((k,v) for k,v in STATUS_CHOICE.items())
	type_id = models.SmallIntegerField(default=PYTHON,choices=books_type_choices,verbose_name='商品类型')
	name = models.CharField(max_length=20,verbose_name='商品名')
	desc = models.CharField(max_length=128,verbose_name='商品简介')
	price = models.DecimalField(max_digits=10,verbose_name='商品价格',decimal_places=2)
	unit = models.CharField(max_length=20,verbose_name='商品种类')
	stock = models.IntegerField(verbose_name='商品库存',default=1)
	sales = models.IntegerField(verbose_name='商品销售',default=0)
	detail = HTMLField(verbose_name='商品详情')
	image = models.ImageField(upload_to='books',verbose_name='商品图片')
	status = models.SmallIntegerField(default=ONLINE,choices=status_choices,verbose_name='商品状态')


	objects = BooksManager()

	def __str__(self):
		return self.name

	class Meta:
		db_table = 's_books'
		verbose_name = '书籍'
		verbose_name_plural = '书籍'


