# escolinha/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import date
from .models import Aluno, Pagamento
from django.db.models import Sum

@shared_task
def gerar_pagamentos_mes():
    """Gera pagamentos para todos os alunos ativos no início do mês,
    considerando adiantamentos/parciais."""
    hoje = timezone.now().date()
    primeiro_dia = date(hoje.year, hoje.month, 1)
    vencimento = date(hoje.year, hoje.month, 10)  # vencimento sempre dia 10

    alunos = Aluno.objects.filter(is_active=True)

    for aluno in alunos:
        mensalidade = aluno.mensalidade

        # Pagamentos já existentes no mês
        pagamentos_mes = Pagamento.objects.filter(
            aluno=aluno,
            data_vencimento__year=hoje.year,
            data_vencimento__month=hoje.month
        )

        total_mes = pagamentos_mes.aggregate(total=Sum("valor"))["total"] or 0

        # Se não existe nada ainda ou se o valor é menor que a mensalidade, cria/completa
        if total_mes == 0:
            # Cria a mensalidade inteira
            Pagamento.objects.create(
                aluno=aluno,
                data_vencimento=vencimento,
                valor=mensalidade
            )
        elif total_mes < mensalidade:
            # Se já tem pago/adiantado mas é menor que a mensalidade, cria a diferença
            faltante = mensalidade - total_mes
            Pagamento.objects.create(
                aluno=aluno,
                data_vencimento=vencimento,
                valor=faltante
            )

    return f"{alunos.count()} pagamentos processados para {hoje.month}/{hoje.year}"

