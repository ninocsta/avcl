from django.urls import path
from . import views


urlpatterns = [
    path('', views.alunos_list, name='alunos_list'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('alunos/create/', views.aluno_create, name='aluno_create'),
    path('alunos/<int:pk>/edit/', views.aluno_update, name='aluno_update'),
    path('alunos/<int:aluno_id>/pagamentos/', views.pagamentos_list, name='pagamentos_list'),

    path('alunos/<int:aluno_id>/pagamentos/create/', views.pagamento_create, name='pagamento_create'),
    path('pagamentos/<int:pk>/edit/', views.pagamento_update, name='pagamento_update'),
    path('pagamentos/<int:pk>/delete/', views.pagamento_delete, name='pagamento_delete'),
    path("pagamentos/", views.pagamentos_filter_view, name="pagamentos_filter"),

    path('turmas/', views.turmas_list, name='turmas_list'),
    path('turmas/create/', views.turma_create, name='turma_create'),
    path('turmas/<int:pk>/edit/', views.turma_update, name='turma_update'),
]