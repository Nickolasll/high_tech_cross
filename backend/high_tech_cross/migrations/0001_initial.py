# Generated by Django 4.1.2 on 2022-11-24 17:23

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django_better_admin_arrayfield.models.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=300)),
                ('start_time', models.DateTimeField(default=datetime.datetime(2022, 11, 25, 17, 23, 11, 740578, tzinfo=datetime.timezone.utc))),
                ('initialized', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('used_hints', django_better_admin_arrayfield.models.fields.ArrayField(base_field=models.IntegerField(), default=list, null=True, size=3)),
                ('wrong_attempts', models.IntegerField(default=0)),
                ('completed_at', models.DateTimeField(default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ResponseCache',
            fields=[
                ('request_id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('success', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='TaskDescription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=300)),
                ('coordinates', django_better_admin_arrayfield.models.fields.ArrayField(base_field=models.CharField(max_length=10), size=2)),
                ('description', models.CharField(max_length=300)),
                ('answer', models.CharField(max_length=30)),
                ('hints', django_better_admin_arrayfield.models.fields.ArrayField(base_field=models.CharField(max_length=300), size=3)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('login', models.CharField(max_length=30, unique=True)),
                ('name', models.CharField(max_length=30)),
                ('password', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['login'], name='login_idx'),
        ),
        migrations.AddField(
            model_name='exercise',
            name='competition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='high_tech_cross.competition'),
        ),
        migrations.AddField(
            model_name='exercise',
            name='task_description',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='high_tech_cross.taskdescription'),
        ),
        migrations.AddField(
            model_name='exercise',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='high_tech_cross.team'),
        ),
        migrations.AddField(
            model_name='competition',
            name='tasks',
            field=models.ManyToManyField(to='high_tech_cross.taskdescription'),
        ),
        migrations.AddField(
            model_name='competition',
            name='teams',
            field=models.ManyToManyField(to='high_tech_cross.team'),
        ),
        migrations.AlterIndexTogether(
            name='exercise',
            index_together={('team', 'competition')},
        ),
        migrations.AddIndex(
            model_name='competition',
            index=models.Index(fields=['initialized'], name='initialized_idx'),
        ),
    ]
