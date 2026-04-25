from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="dashboard"),
    path("subir-cv/", views.upload_cv, name="upload_cv"),
    path("cv/<int:cv_id>/activar/", views.set_active_cv, name="set_active_cv"),
    path("cv/<int:cv_id>/eliminar/", views.delete_cv, name="delete_cv"),
    path("filtros/", views.update_filters, name="update_filters"),
    path("campana/", views.toggle_campaign, name="toggle_campaign"),
    path("eliminar-cuenta/", views.delete_account, name="delete_account"),
]
