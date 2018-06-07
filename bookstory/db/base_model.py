from django.db import models
from hashlib import sha1


class BaseModel(models.Model):
	#抽象模型基类
	is_delect = models.BooleanField(default=False,verbose_name='删除标记')
	create_time = models.DateTimeField(auto_now_add=True,verbose_name='创建时间')
	update_time = models.DateTimeField(auto_now=True,verbose_name='更新时间')


	#这是什么意思
	class Meta:
		abstract = True






