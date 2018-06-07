from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from utils.decorators import login_required
from django.http import JsonResponse
from users.models import Address
from django_redis import get_redis_connection
from books.models import Books
from .models import OrderInfo,OrderGoods
from datetime import datetime
from django.db import transaction
from alipay import AliPay
import os
from bookstory import settings
# Create your views here.


@login_required
def order_pay(request):
	'''订单支付'''
	#接受订单id
	order_id =request.POST.get('order_id')

	#数据校验
	if not order_id:
		return JsonResponse({'res':1,'errmsg':'订单不存在'})

	try:
		order = OrderInfo.objects.get(
			order_id=order_id,
			status=1,
			pay_method=3
												)
	except OrderInfo.DoesNotExist:
		return JsonResponse({'res':2,'errmsg':'订单信息出错'})

	#将两个个文件拷贝到order的文件夹下

	app_private_key_path = os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')
	alipay_public_key_path = os.path.join(settings.BASE_DIR, 'apps/order/app_public_key.pem')

	app_private_key_string = open(app_private_key_path).read()
	alipay_public_key_string = open(alipay_public_key_path).read()

	#和支付宝进行交互
	alipay = AliPay(
		appid="2016091500515408",  #应用id
		app_notify_url=None,  #默认回调url
		app_private_key_string=app_private_key_string,
		alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
		sign_type="RSA2",  #RSA 或者 RSA2
		debug=True,  #默认False
	)

	#电脑网站支付,需要挑战到....
	total_pay = order.total_price + order.transit_price

	order_string = alipay.api_alipay_trade_page_pay(
		out_trade_no=order_id,
		total_amount=str(total_pay),
		subject='商硅谷书城%s' %order_id,
		return_url=None,
		notify_url=None
	)

	pay_url = settings.ALIPAY_URL + '?' + order_string
	return JsonResponse({'res':3,'pay_url':pay_url,'message':'OK'})


@login_required
def check_pay(request):
	'''后去用户支付结果'''
	passport_id = request.session.get('passport_id')
	order_id = request.POST.get('order_id')
	#接受订单
	if not order_id:
		return JsonResponse({'res':1,'errmsg':'订单不存在'})
	try:
		order = OrderInfo.objects.get(
			order_id=order_id,
			passport_id=passport_id,
			pay_method=3
		)
	except OrderInfo.DoesNotExist:
		return JsonResponse({'res':2,'errmsg':'订单信息出错'})

	app_private_key_path = os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')
	alipay_public_key_path = os.path.join(settings.BASE_DIR, 'apps/order/app_public_key.pem')

	app_private_key_string = open(app_private_key_path).read()
	alipay_public_key_string = open(alipay_public_key_path).read()
	#支付宝进行交互
	alipay = AliPay(
		appid="2016091500515408",  # 应用id
		app_notify_url=None,  # 默认回调url
		app_private_key_string=app_private_key_string,
		alipay_public_key_string=alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
		sign_type="RSA2",  # RSA 或者 RSA2
		debug=True,  # 默认False

	)
	while True:
		result = alipay.api_alipay_trade_query(order_id)
		code = result.get('code')

		if code == '10000' and result.get('trade_status') == 'TRADE_SUCCES':
			#用户支付成功
			#改变订单支付状态
			order.status = 2
			#填写支付宝交易号
			order.trade_id = result.get('trade_no')
			order.save()
			return JsonResponse({'res':3,'message':'支付成功'})
		elif code == '40004' or (code == '10000' and result.get('trade_status') == 'WAIT_BUYER_PAY'):
			#支付订单还未生成,继续查询
			#用户还未完成支付,继续查询
			continue
		else:
			#支付出错
			return JsonResponse({'res':4,'errmsg':'支付出错'})




@transaction.atomic
def order_commit(request):
	#接受数据
	addr_id = request.POST.get('addr_id')

	pay_method = request.POST.get('pay_method')

	books_ids = request.POST.get('books_ids')

	#进行数据校验
	if not all([addr_id,pay_method,books_ids]):
		return JsonResponse({'res':1,'errmsg':'数据不完整'})

	try:
		addr = Address.objects.get(id=addr_id)
	except Exception as e:
		return JsonResponse({'res':2,'errmsg':'地址信息错误'})

	if int(pay_method) not in OrderInfo.PAY_METHODS_NEUM.values():
		return JsonResponse({'res':3,'errmsg':'不支持的支付方式'})

	#订单创建
	#组织订单信息
	passport_id = request.session.get('passport_id')
	#订单id:20171029110830+用户的id
	order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(passport_id)
	#运费
	transit_price = 10
	#订单商品总数和总金额
	total_count = 0
	total_price = 0

	#事务:原子性:一组sql操作,要么都成功,要么都失败
	#开启事务:begin:
	# 事务回滚:rollbace
	#事务提交:commit;
	#设置保存点:savepoint保存点
	# 回滚到保存点:rollback to 保存点;


	#创建一个保存点(回档)
	sid = transaction.savepoint()

	try:
		order = OrderInfo.objects.create(order_id=order_id,
													passport_id = passport_id,
													addr_id=addr_id,
													total_count=total_count,
													total_price=total_price,
													transit_price=transit_price,
													pay_method=pay_method)

		#向订单商品表中添加订单商品的记录
		books_ids = books_ids.split(',')
		conn = get_redis_connection('default')
		cart_key = 'cart_%d' % passport_id


		for books_id in books_ids:
			books = Books.objects.get_books_by_id(books_id=books_id)
			if books is None:
				transaction.savepoint_rollback(sid)
				return JsonResponse({'res':4,'errmsg':'商品信息错误'})

			count = conn.hget(cart_key,books_id)
			#判断商品的库存
			if int(count) > books.stock:
				transaction.savepoint_rollback(sid)
				return JsonResponse({'res':5,'errmsg':'商品不足'})

			#创建一条订单商品记录
			OrderGoods.objects.create(
				order_id = order_id,
				books_id = books_id,
				count = count,
				price = books.price
			)


			#增加商品的销量,减少商品库存
			books.sales += int(count)
			books.stock -= int(count)
			books.save()

			#累计计算商品的总数亩和总额
			total_count += int(count)
			total_price += int(count)*books.price

		#更新订单的商品总数和总金额
		order.total_count = total_count
		order.total_price = total_price
		order.save()


	except Exception as e:
		transaction.savepoint_rollback(sid)
		return JsonResponse({'res':7,'errmsg':'服务器错误'})

	#清楚购物车对应记录
	conn.hdel(cart_key,*books_ids)

	#提交事务
	transaction.savepoint_commit(sid)

	return JsonResponse({'res':6})



@login_required
def order_place(request):
	#接受数据
	books_ids = request.POST.getlist('books_ids')
	#校验数据
	if not all(books_ids):
		return redirect(reverse('cart:show'))
	#用户收货地址
	passport_id = request.session.get('passport_id')

	addr = Address.objects.get_default_address(passport_id=passport_id)
	# if addr == None:
	# 	return redirect(reverse('user:user_center_site'))
	#用户要购买商品的信息
	books_li = []
	#商品的总数目和总金额
	total_count = 0
	total_price = 0

	conn = get_redis_connection('default')
	cart_key = 'cart_%d' % passport_id

	for books_id in books_ids:
		#根据商品id获取商品的的信息
		books = Books.objects.get_books_by_id(books_id=books_id)
		count = conn.hget(cart_key,books_id)
		books.count = count

		#计算商品的小计
		amount = int(count) * books.price
		books.amount = amount
		books_li.append(books)

		#累计计算商品的总数目和总金额
		total_price += books.amount
		total_count += int(count)

	#商品运费和实付款
	transit_price = 10
	total_pay = total_price + transit_price

	#1,2,3
	books_ids = ','.join(books_ids)

	context = {
		'addr': addr,
		'books_li': books_li,
		'total_count': total_count,
		'total_price': total_price,
		'transit_price': transit_price,
		'total_pay': total_pay,
		'books_ids': books_ids,
	}

	return render(request,'order/place_order.html',context)




