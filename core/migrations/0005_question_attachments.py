# Generated by Django 5.1.3 on 2024-11-09 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_emailverification_expired_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='attachments',
            field=models.FileField(blank=True, null=True, upload_to='attachments/'),
        ),
    ]
