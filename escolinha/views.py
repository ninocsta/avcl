from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, F, Q
from django.utils import timezone
from .models import Aluno, Pagamento
from .forms import AlunoForm, PagamentoForm
from datetime import date, timedelta
import calendar
from django.db.models import Count




# ----- Alunos -----
def alunos_list(request):
    alunos = Aluno.objects.filter(is_active=True).order_by("nome_completo")
    return render(request, "escolinha/alunos_list.html", {"alunos": alunos})




def aluno_create(request):
    if request.method == "POST":
        form = AlunoForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect("alunos_list")
    else:
        form = AlunoForm()
        return render(request, "escolinha/aluno_form.html", {"form": form})




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




# ----- Pagamentos -----
def pagamentos_list(request, aluno_id):
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    pagamentos = aluno.pagamentos.all().order_by("-data_vencimento")
    return render(request, "escolinha/pagamentos_list.html", {"aluno": aluno, "pagamentos": pagamentos})


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




def pagamento_delete(request, pk):
    pagamento = get_object_or_404(Pagamento, pk=pk)
    aluno_id = pagamento.aluno.id
    if request.method == "POST":
        pagamento.delete()
        return redirect("pagamentos_list", aluno_id=aluno_id)
    return render(request, "escolinha/pagamento_confirm_delete.html", {"pagamento": pagamento})




import json

def dashboard(request):
    today = timezone.now().date()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    # --- Indicadores principais ---
    recebido = Pagamento.objects.filter(
        data_pagamento__range=(first_day, last_day)
    ).aggregate(total=Sum("valor"))["total"] or 0

    esperado = Aluno.objects.filter(is_active=True).aggregate(
        total=Sum("mensalidade")
    )["total"] or 0

    ativos = Aluno.objects.filter(is_active=True).count()

    atrasado = Pagamento.objects.filter(
        data_vencimento__lt=today, data_pagamento__isnull=True
    ).aggregate(total=Sum("valor"))["total"] or 0

    taxa = (float(recebido) / float(esperado) * 100) if esperado else None

    # --- Últimos 6 meses ---
    faturamento_6m = []
    for i in range(5, -1, -1):
        ref = today.replace(day=1) - timedelta(days=30 * i)
        ano, mes = ref.year, ref.month
        primeiro = date(ano, mes, 1)
        ultimo = date(ano, mes, calendar.monthrange(ano, mes)[1])
        total = (
            Pagamento.objects.filter(data_pagamento__range=(primeiro, ultimo))
            .aggregate(total=Sum("valor"))["total"]
            or 0
        )
        faturamento_6m.append({
            "mes": f"{mes:02d}/{ano}",
            "valor": float(total),
        })

    faturamento_labels = [item["mes"] for item in faturamento_6m]
    faturamento_values = [item["valor"] for item in faturamento_6m]

    # --- Formas de pagamento ---
    formas = (
        Pagamento.objects.filter(data_pagamento__range=(first_day, last_day))
        .values("forma_pagamento")
        .annotate(total=Count("id"))
    )
    formas_labels = [f["forma_pagamento"] for f in formas]
    formas_values = [f["total"] for f in formas]

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
    }
    return render(request, "escolinha/dashboard.html", context)



def pagamentos_filter_view(request):
    aluno_nome = request.GET.get("aluno", "").strip()
    status = request.GET.get("status")

    pagamentos = Pagamento.objects.select_related("aluno").all()

    # Filtro por nome do aluno (busca parcial, case-insensitive)
    if aluno_nome:
        pagamentos = pagamentos.filter(aluno__nome_completo__icontains=aluno_nome)

    # Filtro por status
    if status == "pago":
        pagamentos = pagamentos.filter(data_pagamento__isnull=False)
    elif status == "pendente":
        pagamentos = pagamentos.filter(data_pagamento__isnull=True, data_vencimento__gte=timezone.now().date())
    elif status == "atrasado":
        pagamentos = pagamentos.filter(data_pagamento__isnull=True, data_vencimento__lt=timezone.now().date())

    context = {
        "pagamentos": pagamentos,
        "filtro_aluno": aluno_nome,
        "filtro_status": status,
    }
    return render(request, "escolinha/pagamentos_filter.html", context)