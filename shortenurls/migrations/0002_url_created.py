# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-01 12:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('shortenurls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='url',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
