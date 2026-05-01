from django.urls import path

from . import views

urlpatterns = [
    path("api/companies/filter-options/", views.filter_options_view, name="company_filter_options"),
    path("api/companies/count/", views.companies_count_view, name="company_count"),
]
