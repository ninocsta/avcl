from datetime import date

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from escolinha.models import Aluno, Pagamento


class Command(BaseCommand):
    help = (
        "Gera a mensalidade do mês (vencimento dia 10) para os alunos ativos, "
        "completando a diferença quando já houver adiantamento/parcial. Idempotente."
    )

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        vencimento = date(hoje.year, hoje.month, 10)  # vencimento sempre dia 10

        alunos = Aluno.objects.filter(is_active=True)
        criados = 0
        for aluno in alunos:
            total_mes = Pagamento.objects.filter(
                aluno=aluno,
                data_vencimento__year=hoje.year,
                data_vencimento__month=hoje.month,
            ).aggregate(total=Sum("valor"))["total"] or 0

            # Nada no mês = mensalidade inteira; parcial = só a diferença.
            if total_mes < aluno.mensalidade:
                Pagamento.objects.create(
                    aluno=aluno,
                    data_vencimento=vencimento,
                    valor=aluno.mensalidade - total_mes,
                )
                criados += 1

        self.stdout.write(
            f"{alunos.count()} alunos processados, {criados} pagamentos criados "
            f"para {hoje.month}/{hoje.year}"
        )
