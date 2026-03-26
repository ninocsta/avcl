from urllib.parse import quote, urlencode
from datetime import date
import calendar
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, F, Min
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Aluno, Pagamento, Turma
from .forms import AlunoForm, PagamentoForm, TurmaForm


def shift_month(year, month, delta):
    month_index = (year * 12) + (month - 1) + delta
    return month_index // 12, (month_index % 12) + 1


def parse_competencia(request, default_date):
    competencia = request.GET.get("competencia", "").strip()
    if competencia:
        try:
            year, month = map(int, competencia.split("-"))
            date(year, month, 1)
            return year, month
        except (ValueError, TypeError):
            pass

    try:
        year = int(request.GET.get("year", default_date.year))
        month = int(request.GET.get("month", default_date.month))
        date(year, month, 1)
        return year, month
    except (ValueError, TypeError):
        return default_date.year, default_date.month

# ----- Alunos -----
@login_required
def alunos_list(request):
    nome = request.GET.get("nome", "").strip()
    turma_id = request.GET.get("turma", "").strip()
    page_number = request.GET.get("page", 1)

    alunos = Aluno.objects.filter(is_active=True).select_related("turma")
    if nome:
        alunos = alunos.filter(nome_completo__icontains=nome)
    if turma_id:
        alunos = alunos.filter(turma_id=turma_id)
    alunos = alunos.order_by("nome_completo")

    # --- Paginação ---
    paginator = Paginator(alunos, 20)
    page_obj = paginator.get_page(page_number)
    turmas = Turma.objects.filter(status=True).order_by("nome")

    extra_query = ""
    if nome:
        extra_query += f"&nome={nome}"
    if turma_id:
        extra_query += f"&turma={turma_id}"

    return render(request, "escolinha/alunos_list.html", {
        "alunos": page_obj,
        "page_obj": page_obj,
        "turmas": turmas,
        "filtro_nome": nome,
        "filtro_turma": turma_id,
        "extra_query": extra_query,
    })

@login_required
def turmas_list(request):
    turmas = Turma.objects.filter(status=True).order_by("nome")
    page_number = request.GET.get("page", 1)

    # --- Paginação ---
    paginator = Paginator(turmas, 20)  # 10 itens por página
    page_obj = paginator.get_page(page_number)
    return render(request, "escolinha/turmas_list.html", {"turmas": page_obj, "page_obj": page_obj})

@login_required
def aluno_create(request):
    if request.method == "POST":
        form = AlunoForm(request.POST)
        if form.is_valid():
            aluno = form.save()
            messages.success(request, "Aluno cadastrado com sucesso.")
            return redirect(f"{reverse('pagamentos_list', args=[aluno.id])}?first_payment=1")
        messages.error(request, "Não foi possível salvar o aluno. Revise os campos.")
    else:
        form = AlunoForm()
    return render(request, "escolinha/aluno_form.html", {"form": form})

@login_required
def turma_create(request):
    if request.method == "POST":
        form = TurmaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Turma criada com sucesso.")
            return redirect("turmas_list")
        messages.error(request, "Não foi possível salvar a turma. Revise os campos.")
    else:
        form = TurmaForm()
    return render(request, "escolinha/turma_form.html", {"form": form})

@login_required
def aluno_update(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    if request.method == "POST":
        form = AlunoForm(request.POST, instance=aluno)
        if form.is_valid():
            form.save()
            messages.success(request, "Aluno atualizado com sucesso.")
            return redirect("alunos_list")
        messages.error(request, "Não foi possível atualizar o aluno. Revise os campos.")
    else:
        form = AlunoForm(instance=aluno)
    return render(request, "escolinha/aluno_form.html", {"form": form, "aluno": aluno})

@login_required
def turma_update(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    if request.method == "POST":
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            form.save()
            messages.success(request, "Turma atualizada com sucesso.")
            return redirect("turmas_list")
        messages.error(request, "Não foi possível atualizar a turma. Revise os campos.")
    else:
        form = TurmaForm(instance=turma)
    return render(request, "escolinha/turma_form.html", {"form": form, "turma": turma})



# ----- Pagamentos -----
@login_required
def pagamentos_list(request, aluno_id):
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    page_number = request.GET.get("page", 1)
    pagamentos = aluno.pagamentos.select_related("aluno").all().order_by("-data_vencimento")

    paginator = Paginator(pagamentos, 20)
    page_obj = paginator.get_page(page_number)

    return render(request, "escolinha/pagamentos_list.html", {
        "aluno": aluno, 
        "pagamentos": page_obj,
        "page_obj": page_obj,
        "tem_pagamentos": pagamentos.exists(),
        "first_payment": request.GET.get("first_payment") == "1",
        "msg_cobranca": whatsapp_message("cobranca"),
        "msg_aviso": whatsapp_message("aviso"),        
        })


@login_required
def pagamento_create(request, aluno_id):
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    if request.method == "POST":
        form = PagamentoForm(request.POST)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.aluno = aluno
            if not pagamento.valor:
                pagamento.valor = aluno.mensalidade
            pagamento.save()
            messages.success(request, "Pagamento registrado com sucesso.")
            return redirect("pagamentos_list", aluno_id=aluno.id)
        messages.error(request, "Não foi possível salvar o pagamento. Revise os campos.")
    else:
        form = PagamentoForm(initial={"aluno": aluno, "valor": aluno.mensalidade})
    return render(request, "escolinha/pagamento_form.html", {"form": form, "aluno": aluno})



@login_required
def pagamento_update(request, pk):
    pagamento = get_object_or_404(Pagamento, pk=pk)
    if request.method == "POST":
        form = PagamentoForm(request.POST, instance=pagamento)
        if form.is_valid():
            form.save()
            messages.success(request, "Pagamento atualizado com sucesso.")
            return redirect("pagamentos_list", aluno_id=pagamento.aluno.id)
        messages.error(request, "Não foi possível atualizar o pagamento. Revise os campos.")
    else:
        form = PagamentoForm(instance=pagamento)
    return render(request, "escolinha/pagamento_form.html", {"form": form, "aluno": pagamento.aluno})



@login_required
def pagamento_delete(request, pk):
    pagamento = get_object_or_404(Pagamento, pk=pk)
    aluno_id = pagamento.aluno.id
    if request.method == "POST":
        pagamento.delete()
        messages.success(request, "Pagamento excluído com sucesso.")
        return redirect("pagamentos_list", aluno_id=aluno_id)
    return render(request, "escolinha/pagamento_confirm_delete.html", {"pagamento": pagamento})


@login_required
@require_POST
def pagamento_mark_paid(request, pk):
    pagamento = get_object_or_404(Pagamento, pk=pk)
    if pagamento.data_pagamento:
        messages.info(request, "Este pagamento já estava marcado como pago.")
    else:
        pagamento.data_pagamento = timezone.now().date()
        pagamento.save(update_fields=["data_pagamento"])
        messages.success(request, f"Pagamento de {pagamento.aluno.nome_completo} marcado como pago.")

    next_url = request.GET.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("pagamentos_list", aluno_id=pagamento.aluno.id)


@login_required
def dashboard(request):
    today = timezone.now().date()
    year, month = parse_competencia(request, today)
    turma = request.GET.get("turma", "").strip()
    periodo = request.GET.get("periodo", "mes")
    if periodo not in {"mes", "3m"}:
        periodo = "mes"
    historico_meses = 3 if request.GET.get("historico") == "3" else 6

    if periodo == "3m":
        start_year, start_month = shift_month(year, month, -2)
        first_day = date(start_year, start_month, 1)
    else:
        first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    competencia = f"{year:04d}-{month:02d}"
    mes_atual = f"{today.year:04d}-{today.month:02d}"

    # Base queryset para aplicar filtro de turma
    pagamentos_base = Pagamento.objects.filter(
        data_vencimento__range=(first_day, last_day)
    ).select_related("aluno", "aluno__turma")
    if turma:
        pagamentos_base = pagamentos_base.filter(aluno__turma__id=turma)

    # --- Indicadores principais ---
    esperado = pagamentos_base.aggregate(total=Sum("valor"))["total"] or 0

    recebido = pagamentos_base.filter(
        data_pagamento__isnull=False
    ).aggregate(total=Sum("valor"))["total"] or 0

    ativos_qs = Aluno.objects.filter(is_active=True)
    if turma:
        ativos_qs = ativos_qs.filter(turma__id=turma)
    ativos = ativos_qs.count()

    atrasado = pagamentos_base.filter(
        data_pagamento__isnull=True,
        data_vencimento__lt=today
    ).aggregate(total=Sum("valor"))["total"] or 0
    inadimplentes_qtd = pagamentos_base.filter(
        data_pagamento__isnull=True,
        data_vencimento__lt=today,
    ).values("aluno").distinct().count()

    taxa = (float(recebido) / float(esperado) * 100) if esperado else None

    # --- Histórico previsto x recebido ---
    historico = []
    for i in range(historico_meses - 1, -1, -1):
        ano, mes = shift_month(year, month, -i)
        primeiro = date(ano, mes, 1)
        ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])

        pagamentos_mes = Pagamento.objects.filter(data_vencimento__range=(primeiro, ultimo))
        if turma:
            pagamentos_mes = pagamentos_mes.filter(aluno__turma__id=turma)

        esperado_mes = pagamentos_mes.aggregate(total=Sum("valor"))["total"] or 0
        recebido_mes = pagamentos_mes.filter(
            data_pagamento__isnull=False
        ).aggregate(total=Sum("valor"))["total"] or 0

        historico.append({
            "mes": f"{mes:02d}/{ano}",
            "esperado": float(esperado_mes),
            "recebido": float(recebido_mes),
        })

    historico_labels = [item["mes"] for item in historico]
    historico_esperado_values = [item["esperado"] for item in historico]
    historico_recebido_values = [item["recebido"] for item in historico]

    # --- Recebimento no prazo vs em atraso ---
    pagamentos_recebidos = pagamentos_base.filter(data_pagamento__isnull=False)
    recebido_no_prazo = pagamentos_recebidos.filter(
        data_pagamento__lte=F("data_vencimento")
    ).aggregate(total=Sum("valor"))["total"] or 0
    recebido_em_atraso = pagamentos_recebidos.filter(
        data_pagamento__gt=F("data_vencimento")
    ).aggregate(total=Sum("valor"))["total"] or 0

    pontualidade_labels = ["No prazo", "Em atraso"]
    pontualidade_values = [float(recebido_no_prazo), float(recebido_em_atraso)]

    # --- Top 10 alunos em atraso (R$) ---
    top_alunos_atraso = (
        pagamentos_base.filter(
            data_pagamento__isnull=True,
            data_vencimento__lt=today,
        )
        .values(
            "aluno_id",
            "aluno__nome_completo",
            "aluno__turma__nome",
            "aluno__contato_responsavel",
        )
        .annotate(
            total_atraso=Sum("valor"),
            parcelas=Count("id"),
            primeiro_vencimento=Min("data_vencimento"),
        )
        .order_by("-total_atraso", "primeiro_vencimento")[:10]
    )

    limite_acoes_rapidas = 10
    pagamentos_atrasados_qs = pagamentos_base.filter(
        data_pagamento__isnull=True,
        data_vencimento__lt=today,
    ).order_by("data_vencimento", "aluno__nome_completo")
    pagamentos_atrasados = pagamentos_atrasados_qs[:limite_acoes_rapidas]
    total_atrasados_registros = pagamentos_atrasados_qs.count()

    # Buscar turmas ativas para o filtro
    turmas = Turma.objects.filter(status=True).order_by("nome")
    periodo_label = (
        f"{first_day.strftime('%m/%Y')} a {last_day.strftime('%m/%Y')}"
        if periodo == "3m"
        else f"{month:02d}/{year}"
    )

    base_params = {}
    if turma:
        base_params["turma"] = turma

    filtro_periodo_params = dict(base_params)
    if periodo == "mes":
        filtro_periodo_params["data"] = competencia
    else:
        filtro_periodo_params["data_inicio"] = first_day.isoformat()
        filtro_periodo_params["data_fim"] = last_day.isoformat()

    dashboard_links = {
        "previsto": f"{reverse('pagamentos_filter')}?{urlencode(filtro_periodo_params)}",
        "recebido": f"{reverse('pagamentos_filter')}?{urlencode({**filtro_periodo_params, 'status': 'pago'})}",
        "atrasado": f"{reverse('pagamentos_filter')}?{urlencode({**filtro_periodo_params, 'status': 'atrasado'})}",
    }

    context = {
        "recebido": recebido,
        "esperado": esperado,
        "ativos": ativos,
        "atrasado": atrasado,
        "inadimplentes_qtd": inadimplentes_qtd,
        "taxa": taxa,
        "periodo": periodo,
        "periodo_label": periodo_label,
        "historico_meses": historico_meses,
        "historico_labels": json.dumps(historico_labels),
        "historico_esperado_values": json.dumps(historico_esperado_values),
        "historico_recebido_values": json.dumps(historico_recebido_values),
        "pontualidade_labels": json.dumps(pontualidade_labels),
        "pontualidade_values": json.dumps(pontualidade_values),
        "top_alunos_atraso": top_alunos_atraso,
        "pagamentos_atrasados": pagamentos_atrasados,
        "total_atrasados_registros": total_atrasados_registros,
        "limite_acoes_rapidas": limite_acoes_rapidas,
        "year": year,
        "month": month,
        "competencia": competencia,
        "mes_atual": mes_atual,
        "turmas": turmas,
        "filtro_turma": turma,
        "dashboard_links": dashboard_links,
        "first_day": first_day,
        "last_day": last_day,
        "msg_cobranca": whatsapp_message("cobranca"),
    }
    return render(request, "escolinha/dashboard.html", context)



@login_required
def pagamentos_filter_view(request):
    aluno_nome = request.GET.get("aluno", "").strip()
    status = request.GET.get("status")
    turma = request.GET.get("turma")
    data = request.GET.get("data")  # YYYY-MM
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    page_number = request.GET.get("page", 1)

    pagamentos = Pagamento.objects.select_related("aluno", "aluno__turma").all()

    # Filtro por aluno
    if aluno_nome:
        pagamentos = pagamentos.filter(aluno__nome_completo__icontains=aluno_nome)

    # Filtro por status
    hoje = timezone.now().date()
    if status == "pago":
        pagamentos = pagamentos.filter(data_pagamento__isnull=False)
    elif status == "pendente":
        pagamentos = pagamentos.filter(data_pagamento__isnull=True, data_vencimento__gte=hoje)
    elif status == "atrasado":
        pagamentos = pagamentos.filter(data_pagamento__isnull=True, data_vencimento__lt=hoje)
    
    # Filtro por turma
    if turma:
        pagamentos = pagamentos.filter(aluno__turma__id=turma)

    # Filtro por mês/ano
    if data:
        ano, mes = map(int, data.split('-'))
        pagamentos = pagamentos.filter(data_vencimento__year=ano, data_vencimento__month=mes)
    else:
        ano, mes = "", ""

    if data_inicio:
        pagamentos = pagamentos.filter(data_vencimento__gte=data_inicio)
    if data_fim:
        pagamentos = pagamentos.filter(data_vencimento__lte=data_fim)

    pagamentos = pagamentos.order_by("-data_vencimento", "aluno__nome_completo")

    # --- Paginação ---
    paginator = Paginator(pagamentos, 20)  # 20 itens por página
    page_obj = paginator.get_page(page_number)

    turmas = Turma.objects.filter(status=True).order_by("nome")

    # Extra query para manter filtros no href da paginação
    extra_query = ""
    if aluno_nome:
        extra_query += f"&aluno={aluno_nome}"
    if status:
        extra_query += f"&status={status}"
    if data:
        extra_query += f"&data={data}"
    if data_inicio:
        extra_query += f"&data_inicio={data_inicio}"
    if data_fim:
        extra_query += f"&data_fim={data_fim}"
    if turma:
        extra_query += f"&turma={turma}"
    context = {
        "page_obj": page_obj,
        "filtro_aluno": aluno_nome,
        "filtro_status": status,
        "ano": str(ano) if data else "",
        "mes": f"{mes:02d}" if data else "",
        "extra_query": extra_query,
        "msg_cobranca": whatsapp_message("cobranca"),
        "msg_aviso": whatsapp_message("aviso"),
        "turmas": turmas,
        "filtro_turma": turma,
        "data_inicio": data_inicio or "",
        "data_fim": data_fim or "",
    }
    return render(request, "escolinha/pagamentos_filter.html", context)



def whatsapp_message(tipo="aviso"):
    if tipo == "cobranca":
        msg = """Olá! Tudo bem?

Verificamos que a mensalidade da escolinha de futsal ainda não foi identificada em nosso sistema.
Pedimos, por gentileza, que o pagamento seja realizado o quanto antes, para evitar qualquer interrupção nas atividades do aluno.

Pagamento via Pix
Chave Pix: 51997457095
Nome: Renato da Costa

Caso o pagamento já tenha sido efetuado, por favor, desconsidere esta mensagem. ✅

Agradecemos sua compreensão e colaboração.

Atenciosamente,
Equipe AVCL – Associação Vila Costa Lagoão"""
    else:
        msg = """Olá! Tudo bem?

A AVCL – Associação Vila Costa Lagoão lembra que a mensalidade da escolinha de futsal já está disponível para pagamento.
Pedimos que o pagamento seja realizado o quanto antes, garantindo que o aluno continue participando normalmente das atividades.

Forma de pagamento – Pix
Chave Pix: 51997457095
Nome: Renato da Costa

Agradecemos pela atenção e pela parceria de sempre!

Atenciosamente,
Equipe AVCL – Associação Vila Costa Lagoão"""

    return quote(msg)  # aplica urlencode
