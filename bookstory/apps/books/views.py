from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from .models import Books
from .enums import *
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
import json
from django_redis import get_redis_connection
import logging

# Create your views here.

logger = logging.getLogger('django.request')

def detail(request,books_id):
	books = Books.objects.get_books_by_id(books_id=books_id)

	if books == None:
		return redirect(reverse('books:index'))

	#新品推荐
	books_li = Books.objects.get_books_by_type(type_id=books.type_id,limit=2,sort='new')

	#标签
	type_title = BOOKS_TYPE[books.type_id]

	#用户登录之后,才记录浏览记录
	if request.session.has_key('islogin'):
		#用户以登陆,记录浏览记录
		con = get_redis_connection('default')
		key = 'history_%d' %request.session.get('passport_id')
		#先从redis列表中移除books.id
		con.lrem(key,0,books.id)
		con.lpush(key,books.id)
		con.ltrim(key,0,4)


	context = {
		'books':books,
		'books_li':books_li,
		'type_title':type_title
	}

	return render(request, 'books/detail.html', context)



def list(request,type_id,page):
	'''商品列表'''
	#获取排序方式
	sort = request.GET.get('sort','default')

	#判断type_id是否合法
	if int(type_id) not in BOOKS_TYPE.keys():
		return redirect(reverse('books:index'))

	books_li = Books.objects.get_books_by_type(type_id=type_id,sort=sort)
	#分页
	paginator = Paginator(books_li,1)

	#获取分页之后的总页数
	num_pages = paginator.num_pages

	#取第page也数据

	if page == '' or int(page)>num_pages:
		page = 1
	else:
		page = int(page)

	#返回值是一个Page类的实力对象
	books_li = paginator.page(page)


	# 进行页码控制
	# 1.总页数<5, 显示所有页码
	# 2.当前页是前3页，显示1-5页
	# 3.当前页是后3页，显示后5页 10 9 8 7
	# 4.其他情况，显示当前页前2页，后2页，当前页
	if num_pages < 5:
		pages = range(1,num_pages + 1)
	elif page < 3:
		pages = range(1,6)
	elif num_pages - page <= 2:
		pages = range(num_pages-4,num_pages+1)
	else:
		pages = range(page-2,page+3)

	#新品推荐
	books_new = Books.objects.get_books_by_type(type_id=type_id, limit=2, sort='new')

	# 定义上下文
	type_title = BOOKS_TYPE[int(type_id)]

	context = {
		'books_li': books_li,
		'books_new': books_new,
		'type_id': type_id,
		'sort': sort,
		'type_title': type_title,
		'pages': pages
	}

	return render(request, 'books/list.html', context)



def index(request):

	logger.info(request.body)


	python_new = Books.objects.get_books_by_type(PYTHON, limit=3, sort='new')
	python_hot = Books.objects.get_books_by_type(PYTHON, limit=4, sort='hot')
	javascript_new = Books.objects.get_books_by_type(JAVASCRIPT, limit=3, sort='new')
	javascript_hot = Books.objects.get_books_by_type(JAVASCRIPT, limit=4, sort='hot')
	algorithms_new = Books.objects.get_books_by_type(ALGORITHMS, limit=3, sort='new')
	algorithms_hot = Books.objects.get_books_by_type(ALGORITHMS, limit=4, sort='hot')
	machinelearning_new = Books.objects.get_books_by_type(MACHINELEARNING, 3, sort='new')
	machinelearning_hot = Books.objects.get_books_by_type(MACHINELEARNING, 4, sort='hot')
	operatingsystem_new = Books.objects.get_books_by_type(OPERATINGSYSTEM, 3, sort='new')
	operatingsystem_hot = Books.objects.get_books_by_type(OPERATINGSYSTEM, 4, sort='hot')
	database_new = Books.objects.get_books_by_type(DATABASE, 3, sort='new')
	database_hot = Books.objects.get_books_by_type(DATABASE, 4, sort='hot')

	context = {
		'python_new': python_new,
		'python_hot': python_hot,
		'javascript_new': javascript_new,
		'javascript_hot': javascript_hot,
		'algorithms_new': algorithms_new,
		'algorithms_hot': algorithms_hot,
		'machinelearning_new': machinelearning_new,
		'machinelearning_hot': machinelearning_hot,
		'operatingsystem_new': operatingsystem_new,
		'operatingsystem_hot': operatingsystem_hot,
		'database_new': database_new,
		'database_hot': database_hot,
	}

	# 设置缓存
	# conn = get_redis_connection('default')
	# python_hot_redis = conn.get('index')
	# if python_hot_redis:
	# 	python_hot_redis = json.loads(python_hot_redis)
	# 	print('命中缓存')
	# 	return render(request, 'books/index.html', {
	# 		'python_hot': python_hot_redis
	# 	})
	#
	# python_hot = Books.objects.get_books_by_type(PYTHON, limit=4, sort='hot')
	# print("命中数据库")
	#
	# python_hot_redis = []
	# for book in python_hot:
	# 	python_hot_redis.append({
	# 		'name': book.name,
	# 		'price': str(book.price)
	# 	})
	#
	# conn.setex('index', 60, json.dumps(python_hot_redis))
	#
	# context = {
	# 	'python_hot': python_hot
	# }

	return render(request, 'books/index.html', context)
