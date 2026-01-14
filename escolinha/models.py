from django.db import models
from django.utils import timezone
import re


class Turma(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome



class Aluno(models.Model):
    nome_completo = models.CharField(max_length=150)
    data_nascimento = models.DateField()
    nome_responsavel = models.CharField(max_length=150, blank=True, null=True)
    contato_responsavel = models.CharField(max_length=50, blank=True, null=True)
    mensalidade = models.DecimalField(max_digits=8, decimal_places=2, default=40.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    turma = models.ForeignKey(
        Turma,
        on_delete=models.PROTECT,
        related_name="alunos"
    )
    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["nome_completo"]
        indexes = [
            models.Index(fields=["is_active", "nome_completo"]),
            models.Index(fields=["turma", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        if self.contato_responsavel:
            self.contato_responsavel = re.sub(r"\D", "", self.contato_responsavel)    
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome_completo




class Pagamento(models.Model):
    FORMAS_PAGAMENTO = (
    ("PIX", "Pix"),
    ("DINHEIRO", "Dinheiro"),
    ("OUTRO", "Outro"),
    )


    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="pagamentos")
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(blank=True, null=True)
    forma_pagamento = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO, default="PIX")
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-data_vencimento", "aluno"]
        indexes = [models.Index(fields=["data_vencimento"])]


    @property
    def esta_pago(self):
        return self.data_pagamento is not None


    @property
    def atrasado(self):
        return (not self.esta_pago) and (self.data_vencimento < timezone.now().date())


    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.data_vencimento}"