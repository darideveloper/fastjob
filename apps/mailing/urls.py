from django.urls import path
from . import views

urlpatterns = [
    path("cv/<uuid:token>/", views.cv_download, name="cv_download"),
    path("unsubscribe/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
]
