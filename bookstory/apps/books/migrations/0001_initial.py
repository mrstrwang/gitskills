# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Books',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('is_delect', models.BooleanField(verbose_name='删除标记', default=False)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('type_id', models.SmallIntegerField(verbose_name='商品类型', choices=[(1, 'python'), (2, 'javascrpy'), (3, '数据结构与算法'), (4, '机器学习'), (5, '操作系统'), (6, '数据库')], default=1)),
                ('name', models.CharField(verbose_name='商品名', max_length=20)),
                ('desc', models.CharField(verbose_name='商品简介', max_length=128)),
                ('price', models.DecimalField(verbose_name='商品价格', max_digits=10, decimal_places=10)),
                ('unit', models.CharField(verbose_name='商品种类', max_length=20)),
                ('stock', models.IntegerField(verbose_name='商品库存', default=1)),
                ('sales', models.IntegerField(verbose_name='商品销售', default=0)),
                ('detail', tinymce.models.HTMLField(verbose_name='商品详情')),
                ('image', models.ImageField(verbose_name='商品图片', upload_to='books')),
                ('status', models.SmallIntegerField(verbose_name='商品状态', choices=[(0, '下线'), (1, '上线')], default=1)),
            ],
            options={
                'verbose_name': '书籍',
                'verbose_name_plural': '书籍',
                'db_table': 's_books',
            },
        ),
    ]
