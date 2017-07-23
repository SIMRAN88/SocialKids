# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-03 17:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=30)),
                ('age', models.IntegerField(default=0)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('has_verified_mobile', models.BooleanField(default=False)),
            ],
        ),
    ]