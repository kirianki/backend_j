# Generated by Django 5.1.7 on 2025-03-26 09:03

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='sector_thumbnails/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Sector',
                'verbose_name_plural': 'Sectors',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProviderProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', django.contrib.gis.db.models.fields.PointField(blank=True, geography=True, null=True, srid=4326)),
                ('address', models.CharField(blank=True, default='', max_length=255)),
                ('business_name', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, default='')),
                ('website', models.URLField(blank=True, null=True)),
                ('county', models.CharField(blank=True, db_index=True, default='', max_length=100)),
                ('subcounty', models.CharField(blank=True, db_index=True, default='', max_length=100)),
                ('town', models.CharField(blank=True, db_index=True, default='', max_length=100)),
                ('verification_document', models.FileField(blank=True, null=True, upload_to='verification_docs/')),
                ('is_verified', models.BooleanField(default=False)),
                ('tags', models.CharField(blank=True, default='', help_text='Comma-separated keywords', max_length=255)),
                ('is_featured', models.BooleanField(db_index=True, default=False)),
                ('membership_tier', models.CharField(choices=[('free', 'Free'), ('premium', 'Premium')], default='free', max_length=50)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recommended_providers', models.ManyToManyField(blank=True, related_name='recommended_by', to='marketplace.providerprofile')),
                ('user', models.OneToOneField(limit_choices_to={'role': 'service_provider'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('sector', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='marketplace.sector')),
            ],
            options={
                'verbose_name': 'Service Provider',
                'verbose_name_plural': 'Service Providers',
            },
        ),
        migrations.CreateModel(
            name='PortfolioMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media_type', models.CharField(choices=[('image', 'Image'), ('video', 'Video')], max_length=10)),
                ('file', models.FileField(upload_to='portfolio_media/')),
                ('caption', models.CharField(blank=True, max_length=255, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_media', to='marketplace.providerprofile')),
            ],
            options={
                'verbose_name': 'Portfolio Media',
                'verbose_name_plural': 'Portfolio Media',
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(db_index=True)),
                ('comment', models.TextField(blank=True, default='')),
                ('provider_response', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('upvotes', models.PositiveIntegerField(default=0)),
                ('downvotes', models.PositiveIntegerField(default=0)),
                ('client', models.ForeignKey(limit_choices_to={'role': 'client'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='marketplace.providerprofile')),
            ],
            options={
                'verbose_name': 'Review',
                'verbose_name_plural': 'Reviews',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subcategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='subcategory_thumbnails/')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='marketplace.sector')),
            ],
            options={
                'verbose_name': 'Subcategory',
                'verbose_name_plural': 'Subcategories',
                'ordering': ['name'],
                'unique_together': {('sector', 'name')},
            },
        ),
        migrations.AddField(
            model_name='providerprofile',
            name='subcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='marketplace.subcategory'),
        ),
    ]
