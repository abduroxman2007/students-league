# Generated by Django 5.1.3 on 2024-11-15 19:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='status',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='main_topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='core.maintopic'),
        ),
        migrations.AlterField(
            model_name='question',
            name='sub_topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='core.subtopic'),
        ),
    ]
