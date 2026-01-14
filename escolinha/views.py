from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, F, Q
from django.utils import timezone
from .models import Aluno, Pagamento, Turma
from .forms import AlunoForm, PagamentoForm, TurmaForm
from datetime import date, timedelta
import calendar
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import json




# ----- Alunos -----
@login_required
def alunos_list(request):
    alunos = Aluno.objects.filter(is_active=True).select_related("turma").order_by("nome_completo")
    page_number = request.GET.get("page", 1)

    # --- Paginação ---
    paginator = Paginator(alunos, 20)
    page_obj = paginator.get_page(page_number)

    return render(request, "escolinha/alunos_list.html", {"alunos": page_obj, "page_obj": page_obj})

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
            form.save()
        return redirect("alunos_list")
    else:
        form = AlunoForm()
        return render(request, "escolinha/aluno_form.html", {"form": form})

@login_required
def turma_create(request):
    if request.method == "POST":
        form = TurmaForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect("turmas_list")
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
            return redirect("alunos_list")
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
            return redirect("turmas_list")
    else:
        form = TurmaForm(instance=turma)
        return render(request, "escolinha/turma_form.html", {"form": form, "turma": turma})



# ----- Pagamentos -----
@login_required
def pagamentos_list(request, aluno_id):
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    pagamentos = aluno.pagamentos.select_related("aluno").all().order_by("-data_vencimento")
    return render(request, "escolinha/pagamentos_list.html", {
        "aluno": aluno, 
        "pagamentos": pagamentos,
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
            return redirect("pagamentos_list", aluno_id=aluno.id)
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
            return redirect("pagamentos_list", aluno_id=pagamento.aluno.id)
    else:
        form = PagamentoForm(instance=pagamento)
        return render(request, "escolinha/pagamento_form.html", {"form": form, "aluno": pagamento.aluno})



@login_required
def pagamento_delete(request, pk):
    pagamento = get_object_or_404(Pagamento, pk=pk)
    aluno_id = pagamento.aluno.id
    if request.method == "POST":
        pagamento.delete()
        return redirect("pagamentos_list", aluno_id=aluno_id)
    return render(request, "escolinha/pagamento_confirm_delete.html", {"pagamento": pagamento})




@login_required
def dashboard(request):
    today = timezone.now().date()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    turma = request.GET.get("turma")

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    # Base queryset para aplicar filtro de turma
    pagamentos_base = Pagamento.objects.filter(data_vencimento__range=(first_day, last_day))
    if turma:
        pagamentos_base = pagamentos_base.filter(aluno__turma__id=turma)

    # --- Indicadores principais ---
    esperado = pagamentos_base.aggregate(total=Sum("valor"))["total"] or 0

    recebido = pagamentos_base.filter(
        data_pagamento__isnull=False
    ).aggregate(total=Sum("valor"))["total"] or 0

    ativos = (
        pagamentos_base.values("aluno")
        .distinct()
        .count()
    )

    atrasado = pagamentos_base.filter(
        data_pagamento__isnull=True,
        data_vencimento__lt=today
    ).aggregate(total=Sum("valor"))["total"] or 0

    taxa = (float(recebido) / float(esperado) * 100) if esperado else None

    # --- Últimos 6 meses (base: data_vencimento) ---
    faturamento_6m = []
    for i in range(5, -1, -1):
        ref = today.replace(day=1) - timedelta(days=30 * i)
        ano, mes = ref.year, ref.month
        primeiro = date(ano, mes, 1)
        ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])

        pagamentos_mes = Pagamento.objects.filter(
            data_vencimento__range=(primeiro, ultimo),
            data_pagamento__isnull=False
        )
        if turma:
            pagamentos_mes = pagamentos_mes.filter(aluno__turma__id=turma)

        total = pagamentos_mes.aggregate(total=Sum("valor"))["total"] or 0
        faturamento_6m.append({
            "mes": f"{mes:02d}/{ano}",
            "valor": float(total),
        })

    faturamento_labels = [item["mes"] for item in faturamento_6m]
    faturamento_values = [item["valor"] for item in faturamento_6m]

    # --- Formas de pagamento (também pelo mês de vencimento) ---
    formas = (
        pagamentos_base.filter(data_pagamento__isnull=False)
        .values("forma_pagamento")
        .annotate(total=Count("id"))
    )
    formas_labels = [f["forma_pagamento"] for f in formas]
    formas_values = [f["total"] for f in formas]

    # Buscar turmas ativas para o filtro
    turmas = Turma.objects.filter(status=True).order_by("nome")

    context = {
        "recebido": recebido,
        "esperado": esperado,
        "ativos": ativos,
        "atrasado": atrasado,
        "taxa": taxa,
        "faturamento_labels": json.dumps(faturamento_labels),
        "faturamento_values": json.dumps(faturamento_values),
        "formas_labels": json.dumps(formas_labels),
        "formas_values": json.dumps(formas_values),
        "year": year,
        "month": month,
        "turmas": turmas,
        "filtro_turma": turma,
    }
    return render(request, "escolinha/dashboard.html", context)



@login_required
def pagamentos_filter_view(request):
    aluno_nome = request.GET.get("aluno", "").strip()
    status = request.GET.get("status")
    turma = request.GET.get("turma")
    data = request.GET.get("data")  # YYYY-MM
    page_number = request.GET.get("page", 1)

    pagamentos = Pagamento.objects.select_related("aluno").all()

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
    }
    return render(request, "escolinha/pagamentos_filter.html", context)



import urllib.parse

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

    return urllib.parse.quote(msg)  # aplica urlencode