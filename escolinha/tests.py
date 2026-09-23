from django.test import TestCase


class HealthTests(TestCase):
    def test_health_ok_sem_login(self):
        self.assertEqual(self.client.get("/health/").status_code, 200)


class GerarPagamentosMesTests(TestCase):
    def test_cria_mensalidade_e_completa_parcial_idempotente(self):
        from datetime import date
        from decimal import Decimal
        from io import StringIO

        from django.core.management import call_command
        from django.utils import timezone

        from escolinha.models import Aluno, Pagamento, Turma

        hoje = timezone.localdate()
        turma = Turma.objects.create(nome="T")
        cheio = Aluno.objects.create(nome_completo="A", data_nascimento=date(2015, 1, 1), turma=turma, mensalidade=Decimal("100"))
        parcial = Aluno.objects.create(nome_completo="B", data_nascimento=date(2015, 1, 1), turma=turma, mensalidade=Decimal("100"))
        Aluno.objects.create(nome_completo="C", data_nascimento=date(2015, 1, 1), turma=turma, is_active=False)
        Pagamento.objects.create(aluno=parcial, data_vencimento=date(hoje.year, hoje.month, 5), valor=Decimal("30"))

        for _ in range(2):
            call_command("gerar_pagamentos_mes", stdout=StringIO())

        self.assertEqual(list(cheio.pagamentos.values_list("valor", "data_vencimento")), [(Decimal("100"), date(hoje.year, hoje.month, 10))])
        self.assertEqual(sorted(parcial.pagamentos.values_list("valor", flat=True)), [Decimal("30"), Decimal("70")])
        self.assertEqual(Pagamento.objects.count(), 3)
