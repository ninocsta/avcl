from django import forms
from .models import Aluno, Pagamento, Turma


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = [
            "nome_completo",
            "data_nascimento",
            "nome_responsavel",
            "contato_responsavel",
            "mensalidade",
            "is_active",
            "turma",
        ]
        widgets = {
            "nome_completo": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "type": "text",
                "placeholder": "Nome completo do Aluno"
            }),
            "data_nascimento": forms.DateInput(
                format='%Y-%m-%d', 
                attrs={
                    "class": "input input-bordered w-full",
                    "type": "date"
                }
            ),
            "nome_responsavel": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "type": "text",
                "placeholder": "Nome do responsável"
            }),
            "contato_responsavel": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "type": "tel",
                "placeholder": "DDD + Número"
            }),
            "mensalidade": forms.NumberInput(attrs={
                "class": "input input-bordered w-full",
                "type": "number",
                "step": "0.01",
                "placeholder": "Valor da mensalidade"
            }),
            "turma": forms.Select(attrs={
                "class": "select select-bordered w-full"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "checkbox checkbox-primary"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra turmas ativas
        turmas_ativas = Turma.objects.filter(status=True)
        
        # Se está editando um aluno e ele tem uma turma desativada, inclui ela também
        if self.instance and self.instance.pk and self.instance.turma:
            if not self.instance.turma.status:
                # Combina turmas ativas com a turma atual (desativada)
                turmas_ativas = turmas_ativas | Turma.objects.filter(pk=self.instance.turma.pk)
        
        self.fields["turma"].queryset = turmas_ativas.distinct()
        self.fields["turma"].empty_label = None  # Remove a opção "-----"


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = [
            "data_vencimento",
            "data_pagamento",
            "forma_pagamento",
            "valor"
        ]
        widgets = {            
            "data_vencimento": forms.DateInput(
                format='%Y-%m-%d', attrs={
                    "class": "input input-bordered w-full",
                    "type": "date"
                }
            ),
            "data_pagamento": forms.DateInput(
                format='%Y-%m-%d', attrs={
                    "class": "input input-bordered w-full",
                    "type": "date"
                }
            ),
            "forma_pagamento": forms.RadioSelect(attrs={
                "class": "radio radio-primary"
            }),
            "valor": forms.NumberInput(attrs={
                "class": "input input-bordered w-full",
                "type": "number",
                "step": "0.01",
                "placeholder": "Valor do pagamento"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define PIX como padrão de forma segura
        if len(self.fields["forma_pagamento"].choices) > 1:
            self.fields["forma_pagamento"].initial = "PIX"

class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = [
            "nome",
            "descricao",
            "status",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "type": "text",
                "placeholder": "Nome da Turma"
            }),
            "descricao": forms.Textarea(attrs={
                "class": "textarea textarea-bordered w-full",
                "placeholder": "Descrição da Turma"
            }),
            "status": forms.CheckboxInput(attrs={
            "class": "checkbox checkbox-primary"
        })
        }
        