# Generated by Django 4.2.19 on 2025-03-16 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_feedback_created_at_feedback_sentiment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/'),
        ),
        migrations.AddField(
            model_name='product',
            name='title',
            field=models.CharField(default='Untitled Product', max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
