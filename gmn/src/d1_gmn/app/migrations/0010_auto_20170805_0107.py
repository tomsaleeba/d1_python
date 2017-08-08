# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-05 01:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20170603_0546'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('head_pid', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='chain_head_pid', to='app.IdNamespace')),
                ('sid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chain_sid', to='app.IdNamespace')),
            ],
        ),
        migrations.CreateModel(
            name='ChainMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Chain')),
                ('pid', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='chainmember_pid', to='app.IdNamespace')),
            ],
        ),
        migrations.RemoveField(
            model_name='chainidtoseriesid',
            name='head_pid',
        ),
        migrations.RemoveField(
            model_name='chainidtoseriesid',
            name='sid',
        ),
        migrations.RemoveField(
            model_name='persistentidtochainid',
            name='chain',
        ),
        migrations.RemoveField(
            model_name='persistentidtochainid',
            name='pid',
        ),
        migrations.DeleteModel(
            name='ChainIdToSeriesID',
        ),
        migrations.DeleteModel(
            name='PersistentIdToChainID',
        ),
    ]