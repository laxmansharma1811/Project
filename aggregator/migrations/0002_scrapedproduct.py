# Generated by Django 5.1.4 on 2024-12-27 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aggregator', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapedProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_link', models.URLField(max_length=500)),
                ('image_url', models.URLField(max_length=500)),
                ('product_name', models.CharField(max_length=255)),
                ('product_price', models.CharField(max_length=50)),
                ('rating', models.CharField(blank=True, max_length=10, null=True)),
                ('number_of_ratings', models.CharField(blank=True, max_length=50, null=True)),
                ('specifications', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]