import os

from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
import re
from .models import Passport,Address
from django.http import JsonResponse,HttpResponse
from utils.decorators import login_required
from django.core.paginator import Paginator
from order.models import OrderInfo,OrderGoods
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from bookstory import settings
from django.core.mail import send_mail
#引入绘图模块
from PIL import Image,ImageDraw,ImageFont
import random
import io
from django_redis import get_redis_connection
from books.models import Books


#用户账户激活
def register_active(request,token):
	serializer = Serializer(settings.SECRET_KEY,3600)
	try:
		info = serializer.loads(token)
		passport_id = info['confirm']
		#进行用户激活
		passport = Passport.objects.get(id=passport_id)
		passport.is_active = True
		passport.save()
		#跳转的登陆页
		return redirect(reverse('user:login'))
	except SignatureExpired:
		return HttpResponse('激活链接已过期')




#验证码功能
def verifycode(request):
	#定义变量,用于画面的背景色.宽高
	bgcolor = (random.randrange(20,100),random.randrange(20,100),255)
	width = 100
	height = 25
	#创建换面对象
	im = Image.new('RGB',(width,height),bgcolor)
	#创建画笔对象
	draw = ImageDraw.Draw(im)
	for i in range(0,100):
		xy = (random.randrange(0,width),random.randrange(0,height))
		fill = (random.randrange(0, 255),255,random.randrange(0,255))
		draw.point(xy,fill=fill)

	#定义验证码的被选通值
	str1 = 'QWERTYUIOPASDFGHJKLZXCVNM1234567890'
	#随机选取4个值作为验证码
	rand_str = ''
	for i in range(0,4):
		rand_str +=str1[random.randrange(0,len(str1))]
	#构造自体对象
	font = ImageFont.truetype(os.path.join(settings.BASE_DIR,'Ubuntu-RI.ttf'),20)
	fontcolor = (255,random.randrange(0,255),random.randrange(0,255))
	#绘制字体颜色
	draw.text((5,2),rand_str[0],font=font,fill=fontcolor)
	draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
	draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
	draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)
	#释放画笔
	del draw
	#存入session,用于做进一步验证
	request.session['verifycode'] = rand_str
	buf = io.BytesIO()

	im.save(buf,'png')
	#j将图片数据返回给客户端,mime类型为图片png
	return HttpResponse(buf.getvalue(),'image/png')


@login_required
def user(request):
	passport_id = request.session.get('passport_id')
	addr = Address.objects.get_default_address(passport_id=passport_id)

	#获取用户的最近浏览信息
	con = get_redis_connection('default')
	key = 'history_%d' % passport_id
	#取出用户最近浏览的5个商品的id
	history_li = con.lrange(key,0,4)

	books_li = []
	for books_id in history_li:
		books = Books.objects.get_books_by_id(books_id=books_id)
		books_li.append(books)

	context = {
		'addr':addr,
		'page':'user',
		'books_li':books_li
	}

	return render(request, 'users/user_center_info.html', context)


def register(request):
	if request.method == 'GET':
		return render(request, 'users/register.html')
	elif request.method == 'POST':
		username = request.POST.get('user_name')
		password = request.POST.get('pwd')
		email = request.POST.get('email')

		if not all([username,password,email]):
			return render(request, 'users/register.html', {'errormsg': '信息不能为空'})

		if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
			return render(request, 'users/register.html', {'errormsg': '邮箱格式不正确'})

		p = Passport.objects.check_passport(username=username)

		if p:
			return render(request,'users/register.html',{'errmsg':'用户名已存在!'})


		#在数据库创建密码用户等信息
		# Passport.objects.create(username=username,password=password,email=email)
		passport = Passport.objects.add_one_passport(username=username,password=password,email=email)

		# 生成激活的token itsdangerous
		seriaizer = Serializer(settings.SECRET_KEY,3600)
		token = seriaizer.dumps({'confirm':passport.id})
		token = token.decode()

		#给用户的邮箱发激活邮件
		send_mail('尚硅谷书城用户','',settings.EMAIL_FROM,[email],html_message='<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>' % token)
		#异歩发送短信
		# send_active_email.delay(token, username, email)

		return redirect(reverse('books:index'))


def login(request):
	'''现实登陆界面'''
	if request.COOKIES.get('username'):
		username = request.COOKIES.get('username')
		checked = True
	else:
		username = ''
		checked = ''
	context = {
		'username':username,
		'checked':checked
	}

	return render(request, 'users/login.html', context)

def login_check(request):
	#获取数据
	username = request.POST.get('username')
	password = request.POST.get('password')
	remember = request.POST.get('remember')
	verifycode = request.POST.get('verifycode')

	#数据校验
	if not all([username,password,remember,verifycode]):
		return JsonResponse({'res':2})

	if verifycode.upper() != request.session['verifycode']:
		return JsonResponse({'res':2})


	passport = Passport.objects.get_one_passport(username=username,password=password)

	if passport:
		#这是数据库里面
		next_url = request.session.get('fffff',reverse('books:index'))
		jres = JsonResponse({
			'res':1,'next_url':next_url
		})

		if remember == 'true':
			jres.set_cookie('username',username,max_age=3600*24)
		else:
			jres.delete_cookie('username')

		request.session['islogin'] = True
		request.session['username'] = username
		request.session['passport_id'] = passport.id
		return jres

	else:
		return JsonResponse({'res':0})

def logout(request):
	request.session.flush()
	return redirect(reverse('books:index'))


#我的订单页
def user_center_order(request,page):
	#查询用户的订单信息
	passport_id = request.session.get('passport_id')

	#获取订单信息
	order_li = OrderInfo.objects.filter(passport_id=passport_id)

	#便利获取订单的商品信息
	for order in order_li:
		order_id = order.order_id
		order_books_li = OrderGoods.objects.filter(order_id=order_id)


		#计算商品的小计
		for order_books in  order_books_li:
			count = order_books.count
			price = order_books.price
			amount = count * price
			order_books.amount = amount


		#给order对象动态添加一个属性,保存订单中商品的信息
		order.order_books_li = order_books_li

	paginator = Paginator(order_li,3)

	num_pages = paginator.num_pages

	if not page:
		page = 1
	if page == '' or int(page) > num_pages:
		page = 1
	else:
		page = int(page)

	order_li = paginator.page(page)

	if num_pages < 5:
		pages =range(1,num_pages+1)
	elif page < 3:
		pages = range(1,6)
	elif num_pages - page <=2:
		pages = range(num_pages-4,num_pages+1)
	else:
		pages = range(page-2,page+3)

	context = {
		'order_li':order_li,
		'pages':pages
	}


	return render(request,'users/user_center_order.html',context)




def user_center_site(request):

	'''用户中心-地址页'''
	#获取用户id
	passport_id = request.session.get('passport_id')

	if request.method == "GET":
		#显示 地址页
		addr = Address.objects.get_default_address(passport_id=passport_id)
		return render(request,'users/user_center_site.html',{'addr':addr,'page':'address'})
	else:
		#添加收货地址
		#1接受数据
		recipient_name = request.POST.get('username')
		recipient_addr = request.POST.get('addr')
		zip_code = request.POST.get('zip_code')
		recipient_pthone = request.POST.get('phone')

		#2.进行校验
		if not all([recipient_name, recipient_addr, zip_code, recipient_pthone]):
			return render(request,'users/user_center_site.html',{'errmsg':'参数不能为空!'})

		#3添加收货地址
		Address.objects.add_one_address(
			passport_id=passport_id,
			recipient_name=recipient_name,
			recipient_addr=recipient_addr,
			zip_code=zip_code,
			recipient_pthone=recipient_pthone
		)

		return redirect(reverse('user:user_center_site'))

