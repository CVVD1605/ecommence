# Generated by Django 4.2.19 on 2025-03-13 11:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='email',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='name',
        ),
        migrations.AddField(
            model_name='customer',
            name='user',
            field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cart',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carts', to='shop.customer'),
        ),
        migrations.AlterField(
            model_name='cart',
            name='discount',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='cart',
            name='total',
            field=models.FloatField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='discount',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='line_total',
            field=models.FloatField(editable=False),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='price',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='customer',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='contact',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='status',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='shop.customer'),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='shop.product'),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='sentiment_score',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='purchasedetail',
            name='discount',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='purchasedetail',
            name='line_total',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='purchasedetail',
            name='price',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='purchasedetail',
            name='purchaseHeader',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='shop.purchaseheader'),
        ),
        migrations.AlterField(
            model_name='purchaseheader',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='shop.customer'),
        ),
        migrations.AlterField(
            model_name='purchaseheader',
            name='discount',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='purchaseheader',
            name='total',
            field=models.FloatField(),
        ),
    ]
