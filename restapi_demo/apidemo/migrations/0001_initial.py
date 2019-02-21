# Generated by Django 2.1.5 on 2019-02-21 13:10

import django.core.validators
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=400)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.CharField(blank=True, max_length=50, null=True)),
                ('priority', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
            ],
        ),
    ]
