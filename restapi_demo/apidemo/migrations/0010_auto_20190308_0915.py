# Generated by Django 2.1.5 on 2019-03-08 09:15

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apidemo', '0009_labels'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Labels',
            new_name='Label',
        ),
    ]
