# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-02 22:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortenurls', '0003_auto_20180402_2200'),
    ]

    operations = [
        migrations.AddField(
            model_name='urlvisits',
            name='last_visit',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
