# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='books',
            name='price',
            field=models.DecimalField(verbose_name='商品价格', decimal_places=2, max_digits=10),
        ),
    ]
