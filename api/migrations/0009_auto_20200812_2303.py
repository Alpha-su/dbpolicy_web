# Generated by Django 3.0.8 on 2020-08-12 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_auto_20200805_1748'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='config',
            name='zupei_pattern',
        ),
        migrations.AddField(
            model_name='config',
            name='zupei_type',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='config',
            name='action_pattern',
            field=models.CharField(blank=True, default='', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='config',
            name='date_pattern',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='config',
            name='gov',
            field=models.CharField(db_index=True, default='人民政府', max_length=10),
        ),
        migrations.AlterField(
            model_name='config',
            name='item_pattern',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='config',
            name='main_text_pattern',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='config',
            name='next_pattern',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='config',
            name='source_pattern',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='config',
            name='title_pattern',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='links',
            name='gov',
            field=models.CharField(db_index=True, default='人民政府', max_length=10),
        ),
        migrations.AlterField(
            model_name='links',
            name='source',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='links',
            name='sub_url',
            field=models.CharField(max_length=700, unique=True),
        ),
        migrations.AlterField(
            model_name='links',
            name='zupei_type',
            field=models.CharField(blank=True, db_index=True, default='', max_length=128, null=True),
        ),
    ]
