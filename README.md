# 🎯 AVCL - Sistema de Gestão de Escolinha de Futsal

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2.7-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![DaisyUI](https://img.shields.io/badge/DaisyUI-5A0EF8?style=for-the-badge&logo=daisyui&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

Sistema completo para gestão de alunos, turmas, pagamentos e financeiro desenvolvido para a **Associação Vila Costa Lagoão (AVCL)**.

</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)

---

## 🏆 Sobre o Projeto

O **Sistema AVCL** é uma aplicação web desenvolvida em Django para facilitar a gestão completa de escolinhas esportivas. O sistema oferece controle total sobre:

- **👥 Alunos**: Cadastro completo com dados pessoais, responsáveis e valores
- **📚 Turmas**: Organização de alunos por turmas com status ativo/inativo
- **💰 Pagamentos**: Controle financeiro detalhado com múltiplas formas de pagamento
- **📊 Dashboard**: Visualização de métricas e gráficos em tempo real
- **📱 WhatsApp**: Integração para envio de avisos e cobranças

### 🎯 Problema que Resolve

Gestores de escolinhas esportivas enfrentam dificuldades para:
- Controlar quem está em dia com os pagamentos
- Enviar lembretes e cobranças de forma organizada
- Visualizar a saúde financeira da instituição
- Gerenciar múltiplas turmas e alunos

Este sistema centraliza todas essas operações em uma interface intuitiva e moderna.

---

## ✨ Funcionalidades

### 👥 Gestão de Alunos
- ✅ Cadastro completo (nome, data de nascimento, responsável, contato)
- ✅ Vinculação a turmas
- ✅ Definição de mensalidade personalizada
- ✅ Status ativo/inativo
- ✅ Paginação e busca otimizada

### 📚 Gestão de Turmas
- ✅ Criação e edição de turmas
- ✅ Descrição detalhada
- ✅ Status ativo/inativo
- ✅ Visualização de alunos por turma

### 💰 Gestão de Pagamentos
- ✅ Registro de pagamentos com data de vencimento e pagamento
- ✅ Múltiplas formas de pagamento (PIX, Dinheiro, Outros)
- ✅ Status automático (Pago, Pendente, Atrasado)
- ✅ Filtros avançados (aluno, turma, status, período)
- ✅ Geração automática mensal via Celery

### 📊 Dashboard Analítico
- ✅ Indicadores principais (Recebido, Esperado, Ativos, Atrasado)
- ✅ Taxa de recebimento percentual
- ✅ Gráfico de faturamento dos últimos 6 meses
- ✅ Gráfico de formas de pagamento
- ✅ Filtros por mês/ano e turma

### 📱 Integração WhatsApp
- ✅ Botão direto para enviar mensagem via WhatsApp
- ✅ Templates de mensagens (Aviso e Cobrança)
- ✅ Número de telefone validado e formatado

### 🤖 Automação
- ✅ Geração automática de mensalidades via Celery Beat
- ✅ Processamento em background com Redis
- ✅ Agendamento configurável

---

## 🛠 Tecnologias

### Backend
- **Django 5.2.7** - Framework web robusto e escalável
- **Python 3.8+** - Linguagem de programação
- **POSTGRESQL** - Banco de dados
- **Celery 5.5.3** - Processamento assíncrono de tarefas
- **Redis 5.2.1** - Message broker e cache
- **django-celery-beat** - Agendamento de tarefas periódicas

### Frontend
- **TailwindCSS 4** - Framework CSS utility-first
- **DaisyUI 5** - Componentes prontos para Tailwind
- **Bootstrap Icons** - Ícones vetoriais
- **Chart.js** - Gráficos interativos
- **HTML5/CSS3** - Estrutura e estilização

### Ferramentas
- **django-environ** - Gerenciamento de variáveis de ambiente
- **Git** - Controle de versão

---

## 📦 Requisitos

- Python 3.8 ou superior
- Redis Server
- Git
- pip (gerenciador de pacotes Python)

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/escolinha.git
cd escolinha
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 5. Execute as migrações

```bash
python manage.py migrate
```

### 6. Crie um superusuário

```bash
python manage.py createsuperuser
```

### 7. Inicie o servidor

```bash
python manage.py runserver
```

Acesse: `http://localhost:8000`

---

## ⚙️ Configuração

### Configurar Celery (Tarefas Assíncronas)

#### 1. Inicie o Redis

```bash
# Linux/Mac
redis-server

# Windows (via WSL ou Docker)
docker run -d -p 6379:6379 redis
```

#### 2. Inicie o Celery Worker

Em um novo terminal:

```bash
celery -A app worker --loglevel=info
```

#### 3. Inicie o Celery Beat (Agendador)

Em outro terminal:

```bash
celery -A app beat --loglevel=info
```

### Configurar Geração Automática de Mensalidades

1. Acesse o Django Admin: `http://localhost:8000/admin`
2. Vá em **Periodic Tasks** (django-celery-beat)
3. Crie uma nova tarefa periódica:
   - **Task**: `escolinha.tasks.gerar_pagamentos_mes`
   - **Cron**: `0 0 1 * *` (todo dia 1 às 00:00)
   - **Enabled**: ✅

---

## 📖 Uso

### Acessar o Sistema

1. Acesse `http://localhost:8000/login`
2. Faça login com o superusuário criado
3. Você será redirecionado para a lista de alunos

### Fluxo Básico

1. **Criar Turma**: Menu Turmas → Novo Turma
2. **Cadastrar Aluno**: Menu Alunos → Novo Aluno
3. **Registrar Pagamento**: Clicar no aluno → Novo Pagamento
4. **Visualizar Dashboard**: Menu Dashboard

### Filtros e Buscas

- **Pagamentos**: Filtrar por aluno, status, turma e período
- **Dashboard**: Filtrar por mês/ano e turma
- **Alunos**: Paginação automática (20 por página)

---

## 📂 Estrutura do Projeto

```
escolinha/
├── app/                          # Projeto Django principal
│   ├── settings.py               # Configurações
│   ├── urls.py                   # URLs principais
│   ├── celery.py                 # Configuração Celery
│   └── templates/                # Templates globais
│       ├── base.html             # Layout base
│       └── escolinha/            # Templates do app
│           ├── alunos_list.html
│           ├── aluno_form.html
│           ├── turmas_list.html
│           ├── turma_form.html
│           ├── pagamentos_list.html
│           ├── pagamento_form.html
│           ├── pagamentos_filter.html
│           └── dashboard.html
│
├── escolinha/                    # App principal
│   ├── models.py                 # Modelos (Aluno, Turma, Pagamento)
│   ├── views.py                  # Views e lógica de negócio
│   ├── forms.py                  # Formulários Django
│   ├── urls.py                   # URLs do app
│   ├── tasks.py                  # Tarefas Celery
│   ├── admin.py                  # Configuração do Django Admin
│   └── migrations/               # Migrações do banco
│
├── db.sqlite3                    # Banco de dados
├── manage.py                     # CLI do Django
├── requirements.txt              # Dependências Python
├── .env                          # Variáveis de ambiente
└── README.md                     # Este arquivo
```

---

### Padrões de Código

- Siga a PEP 8 para Python
- Use nomes descritivos para variáveis e funções
- Comente código complexo
- Adicione docstrings em funções públicas


---


## 👨‍💻 Autor

Desenvolvido com ❤️ para a **AVCL - Associação Vila Costa Lagoão**

---




