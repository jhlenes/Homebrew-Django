# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-28 14:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20170528_1143'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='batch_num',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
