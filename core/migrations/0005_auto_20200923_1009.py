# Generated by Django 2.2.16 on 2020-09-23 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20200923_0855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='file',
            field=models.FileField(blank=True, upload_to='file'),
        ),
    ]
