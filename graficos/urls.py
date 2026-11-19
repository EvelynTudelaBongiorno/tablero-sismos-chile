from django.urls import path
from . import views

urlpatterns = [
    path("", views.general, name="general"),
    path("detalle/", views.detalle, name="detalle"),
]
