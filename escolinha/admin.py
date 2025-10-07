from django.contrib import admin
from .models import Aluno, Pagamento

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "nome_responsavel", "contato_responsavel")
    search_fields = ("nome_completo", "nome_responsavel")
    

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "data_vencimento", "data_pagamento", "forma_pagamento", "valor", "esta_pago")
    list_filter = ("forma_pagamento", "data_vencimento")
    search_fields = ("aluno__nome_completo",)
