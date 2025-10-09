from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import CustomLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("escolinha.urls")),

    path('login/', CustomLoginView.as_view(), name='login'),  # Usa a CustomLoginView aqui
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
