from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("venda", "0003_pagamentovenda"),
    ]

    operations = [
        migrations.AddField(
            model_name="dadosestabelecimento",
            name="limite_gastos",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[MinValueValidator(0)],
                verbose_name="Margem máxima de gastos",
            ),
        ),
    ]
