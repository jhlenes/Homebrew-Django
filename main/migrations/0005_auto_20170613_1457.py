# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-13 12:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_auto_20170528_1629'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='batch',
            options={'verbose_name_plural': 'batches'},
        ),
        migrations.AlterModelOptions(
            name='status',
            options={'verbose_name_plural': 'status'},
        ),
        migrations.AddField(
            model_name='point',
            name='point_num',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='point',
            name='hours',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='point',
            unique_together=set([('batch', 'point_num')]),
        ),
    ]
