from django.db import migrations, models


def preencher_chave_agenda(apps, schema_editor):
    HorarioAgendado = apps.get_model("agenda", "HorarioAgendado")
    for horario in HorarioAgendado.objects.select_related("agendamento").iterator():
        agendamento = horario.agendamento
        if agendamento.funcionario_id:
            chave = f"funcionario:{agendamento.funcionario_id}"
        elif agendamento.descricao_agendar_para.strip():
            chave = f"descricao:{agendamento.descricao_agendar_para.strip()}"
        else:
            chave = f"legado:{agendamento.pk}"
        horario.agenda_key = chave
        horario.save(update_fields=("agenda_key",))


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0002_agendamento_descricao_agendar_para_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="horarioagendado",
            name="agenda_horario_data_inicio_unico",
        ),
        migrations.AddField(
            model_name="horarioagendado",
            name="agenda_key",
            field=models.CharField(max_length=180, null=True),
        ),
        migrations.RunPython(
            preencher_chave_agenda,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="horarioagendado",
            name="agenda_key",
            field=models.CharField(max_length=180),
        ),
        migrations.AddConstraint(
            model_name="horarioagendado",
            constraint=models.UniqueConstraint(
                fields=("data", "inicio", "agenda_key"),
                name="agenda_horario_recurso_data_inicio_unico",
            ),
        ),
    ]
