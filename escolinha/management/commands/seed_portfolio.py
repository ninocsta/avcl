from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from escolinha.models import Aluno, Pagamento, Turma


class Command(BaseCommand):
    help = "Cria dados ficticios para portfolio em uma base SQLite local."

    demo_username = "demo"
    demo_email = "demo@costatech.dev"
    demo_password = "Demo@123456"

    turmas_data = [
        ("Iniciacao Sub-07", "Turma de entrada para fundamentos tecnicos e socializacao."),
        ("Formacao Sub-09", "Turma focada em dominio de bola, passe e leitura de jogo."),
        ("Desenvolvimento Sub-11", "Treinos com reforco tecnico e primeiros jogos internos."),
        ("Competicao Sub-13", "Equipe com treinos taticos, amistosos e rotina de desempenho."),
        ("Treinamento Feminino", "Turma dedicada ao desenvolvimento tecnico e participacao em torneios."),
    ]

    alunos_data = [
        ("Mariana Alves", "Fernanda Alves", "00000000001", "Iniciacao Sub-07", Decimal("145.00")),
        ("Rafael Martins", "Luciano Martins", "00000000002", "Iniciacao Sub-07", Decimal("145.00")),
        ("Camila Rocha", "Bianca Rocha", "00000000003", "Formacao Sub-09", Decimal("160.00")),
        ("Felipe Andrade", "Sandra Andrade", "00000000004", "Formacao Sub-09", Decimal("160.00")),
        ("Juliana Costa", "Marcelo Costa", "00000000005", "Desenvolvimento Sub-11", Decimal("175.00")),
        ("Pedro Henrique Lima", "Tatiane Lima", "00000000006", "Desenvolvimento Sub-11", Decimal("175.00")),
        ("Beatriz Nunes", "Carlos Nunes", "00000000007", "Competicao Sub-13", Decimal("210.00")),
        ("Gustavo Prado", "Patricia Prado", "00000000008", "Competicao Sub-13", Decimal("210.00")),
        ("Leticia Moura", "Rodrigo Moura", "00000000009", "Treinamento Feminino", Decimal("185.00")),
        ("Thiago Barros", "Luciana Barros", "00000000010", "Treinamento Feminino", Decimal("185.00")),
        ("Ana Clara Freitas", "Paulo Freitas", "00000000011", "Iniciacao Sub-07", Decimal("145.00")),
        ("Enzo Gabriel Souza", "Vanessa Souza", "00000000012", "Formacao Sub-09", Decimal("160.00")),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Apaga os dados do app escolinha e recria a base demo.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Removendo dados existentes do app escolinha...")
            Pagamento.objects.all().delete()
            Aluno.objects.all().delete()
            Turma.objects.all().delete()

        turmas = self._seed_turmas()
        alunos = self._seed_alunos(turmas)
        pagamentos = self._seed_pagamentos(alunos)
        demo_user = self._seed_demo_user()

        self.stdout.write(
            self.style.SUCCESS(
                "Portfolio pronto: "
                f"{len(turmas)} turmas, {len(alunos)} alunos, {pagamentos} pagamentos. "
                f"Login demo: {demo_user.username} / {self.demo_password}"
            )
        )

    def _seed_turmas(self):
        turmas = {}
        for nome, descricao in self.turmas_data:
            turma, _ = Turma.objects.update_or_create(
                nome=nome,
                defaults={"descricao": descricao, "status": True},
            )
            turmas[nome] = turma
        return turmas

    def _seed_alunos(self, turmas):
        alunos = {}
        base_birth_year = timezone.now().year - 11

        for index, (nome, responsavel, contato, turma_nome, mensalidade) in enumerate(self.alunos_data, start=1):
            birth_month = ((index - 1) % 12) + 1
            birth_day = min(20, 3 + index)
            aluno, _ = Aluno.objects.update_or_create(
                nome_completo=nome,
                defaults={
                    "data_nascimento": date(base_birth_year - (index % 4), birth_month, birth_day),
                    "nome_responsavel": responsavel,
                    "contato_responsavel": contato,
                    "mensalidade": mensalidade,
                    "is_active": True,
                    "turma": turmas[turma_nome],
                },
            )
            alunos[nome] = aluno
        return alunos

    def _seed_pagamentos(self, alunos):
        hoje = timezone.localdate()
        total_pagamentos = 0

        status_cycle = [
            "paid_on_time",
            "paid_late",
            "pending_future",
            "overdue",
            "paid_on_time",
            "paid_on_time",
        ]

        for aluno_index, aluno in enumerate(alunos.values()):
            Pagamento.objects.filter(aluno=aluno).delete()

            for offset in range(5, -1, -1):
                year, month = self._shift_month(hoje.year, hoje.month, -offset)
                due_day = 10 + (aluno_index % 4)
                due_date = date(year, month, due_day)
                status = status_cycle[(aluno_index + offset) % len(status_cycle)]
                payment_date = None
                value = aluno.mensalidade + Decimal((aluno_index % 3) * 5)

                if offset >= 3:
                    status = "paid_on_time" if aluno_index % 2 == 0 else "paid_late"
                elif offset == 2 and aluno_index % 4 == 0:
                    status = "overdue"
                elif offset == 1 and aluno_index % 5 == 0:
                    status = "pending_future"
                elif offset == 0:
                    status = ["paid_on_time", "pending_future", "overdue"][aluno_index % 3]

                if status == "paid_on_time":
                    payment_date = due_date if due_date <= hoje else None
                elif status == "paid_late":
                    payment_date = due_date.replace(day=min(28, due_day + 4))
                elif status == "pending_future":
                    if due_date < hoje:
                        due_date = date(hoje.year, hoje.month, min(28, hoje.day + 5 + (aluno_index % 3)))
                elif status == "overdue":
                    if due_date >= hoje:
                        due_date = date(hoje.year, hoje.month, max(1, hoje.day - 7 - (aluno_index % 3)))

                Pagamento.objects.create(
                    aluno=aluno,
                    data_vencimento=due_date,
                    data_pagamento=payment_date,
                    forma_pagamento="PIX" if aluno_index % 3 else "DINHEIRO",
                    valor=value,
                )
                total_pagamentos += 1

        return total_pagamentos

    def _seed_demo_user(self):
        user_model = get_user_model()
        demo_user, _ = user_model.objects.update_or_create(
            username=self.demo_username,
            defaults={
                "email": self.demo_email,
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "first_name": "Demo",
                "last_name": "Portfolio",
            },
        )
        demo_user.set_password(self.demo_password)
        demo_user.save(update_fields=["password", "email", "is_active", "is_staff", "is_superuser", "first_name", "last_name"])
        return demo_user

    def _shift_month(self, year, month, delta):
        month_index = (year * 12) + (month - 1) + delta
        return month_index // 12, (month_index % 12) + 1
