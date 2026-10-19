# Generated manually to add sanctioned-project state.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proyectos", "0012_proyecto_es_proyecto_diputada"),
    ]

    operations = [
        migrations.AddField(
            model_name="proyecto",
            name="es_sancionado",
            field=models.BooleanField(
                default=False,
                help_text="Si está marcado, el proyecto aparecerá en Proyectos Sancionados y dejará de verse en los listados activos",
            ),
        ),
    ]