# Generated by Django 5.1.2 on 2025-02-23 16:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0005_historialcategoria_proyecto_historial_categorias'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proyecto',
            name='historial_categorias',
        ),
        migrations.AlterField(
            model_name='proyectotemario',
            name='proyecto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='temarios_asociados', to='proyectos.proyecto'),
        ),
        migrations.DeleteModel(
            name='HistorialCategoria',
        ),
    ]
