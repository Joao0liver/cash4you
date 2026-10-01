from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from servico.models import Servico

from .forms import horarios_disponiveis
from .models import Agendamento, HorarioAgendado


class AgendaCRUDTests(TestCase):
    def setUp(self):
        self.data = date(2026, 10, 15)
        self.servico = Servico.objects.create(
            descricao="Corte de cabelo",
            preco_venda="45.00",
        )

    def agendar(self, nome, horarios, **extra):
        dados = {
            "data": self.data.isoformat(),
            "horarios": horarios,
            "nome": nome,
            "telefone": "11999998888",
        }
        dados.update(extra)
        return self.client.post(reverse("criar_agendamento"), dados)

    def test_slots_cover_every_day_from_seven_to_twenty_three_in_half_hours(self):
        slots = horarios_disponiveis()

        self.assertEqual(len(slots), 32)
        self.assertEqual(slots[0], ("07:00", "07:00–07:30"))
        self.assertEqual(slots[-1], ("22:30", "22:30–23:00"))

    def test_create_appointment_with_required_fields_and_optional_service(self):
        response = self.agendar(
            "Maria Silva",
            ["09:00", "09:30"],
            email="maria@example.com",
            servicos=[str(self.servico.pk)],
        )

        self.assertRedirects(response, reverse("listar_agendamentos"))
        agendamento = Agendamento.objects.get(nome="Maria Silva")
        self.assertEqual(agendamento.servicos.get(), self.servico)
        self.assertEqual(agendamento.horarios.count(), 2)
        self.assertEqual(
            agendamento.horarios.get(inicio=time(9, 0)).fim,
            time(9, 30),
        )

    def test_services_are_optional(self):
        response = self.agendar("João Silva", ["10:00"])

        self.assertRedirects(response, reverse("listar_agendamentos"))
        self.assertEqual(Agendamento.objects.get().servicos.count(), 0)

    def test_at_least_one_slot_is_required(self):
        response = self.agendar("Maria Silva", [])

        self.assertEqual(response.status_code, 200)
        self.assertIn("horarios", response.context["form"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_name_and_phone_are_required_but_email_is_optional(self):
        for missing_field in ("nome", "telefone"):
            response = self.client.post(
                reverse("criar_agendamento"),
                {
                    "data": self.data.isoformat(),
                    "horarios": ["10:00"],
                    "nome": "" if missing_field == "nome" else "Maria",
                    "telefone": "" if missing_field == "telefone" else "11999998888",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(missing_field, response.context["form"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_reserved_slot_is_shown_unavailable_and_cannot_be_booked_again(self):
        self.agendar("Maria Silva", ["11:00"])

        response = self.agendar("João Silva", ["11:00"])

        self.assertEqual(response.status_code, 200)
        self.assertIn("horarios", response.context["form"].errors)
        self.assertEqual(Agendamento.objects.count(), 1)
        self.assertContains(response, 'aria-label="11:00–11:30 indisponível"')

    def test_invalid_slot_is_rejected(self):
        response = self.agendar("Maria Silva", ["09:15"])

        self.assertEqual(response.status_code, 200)
        self.assertIn("horarios", response.context["form"].errors)
        self.assertEqual(Agendamento.objects.count(), 0)

    def test_list_edit_and_delete_appointment(self):
        self.agendar("Maria Silva", ["12:00"], servicos=[str(self.servico.pk)])
        agendamento = Agendamento.objects.get()

        listing = self.client.get(reverse("listar_agendamentos"))
        self.assertContains(listing, "Maria Silva")
        self.assertContains(listing, "Corte de cabelo")
        self.assertContains(listing, "https://wa.me/5511999998888")

        edit = self.client.post(
            reverse("editar_agendamento", args=[agendamento.pk]),
            {
                "data": self.data.isoformat(),
                "horarios": ["12:30"],
                "nome": "Maria Souza",
                "telefone": "11999997777",
                "email": "",
                "servicos": [str(self.servico.pk)],
            },
        )
        self.assertRedirects(edit, reverse("listar_agendamentos"))
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.nome, "Maria Souza")
        self.assertEqual(list(agendamento.horarios.values_list("inicio", flat=True)), [time(12, 30)])

        confirmation = self.client.get(
            reverse("excluir_agendamento", args=[agendamento.pk])
        )
        self.assertEqual(confirmation.status_code, 200)
        deleted = self.client.post(
            reverse("excluir_agendamento", args=[agendamento.pk])
        )
        self.assertRedirects(deleted, reverse("listar_agendamentos"))
        self.assertEqual(Agendamento.objects.count(), 0)
        self.assertEqual(HorarioAgendado.objects.count(), 0)

    def test_agenda_menu_has_indented_links(self):
        response = self.client.get(reverse("listar_agendamentos"))

        self.assertContains(response, "Agendamentos")
        self.assertContains(response, "Novo agendamento")
        self.assertContains(
            response,
            '<button type="button" class="nav-link text-white w-100 text-start" data-nav-toggle aria-expanded="false" aria-controls="menu-agenda">',
        )
        self.assertContains(
            response,
            '<ul id="menu-agenda" class="nav nav-pills flex-column gap-1 nav-tree" hidden>',
        )
        self.assertContains(response, "function fecharMenus(exceto)")
