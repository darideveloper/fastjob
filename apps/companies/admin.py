from django import forms
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect, render
from django.utils.html import format_html
from .models import Company, Blacklist, Area, Location
from .importers import import_companies_from_xlsx


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class XlsxImportForm(forms.Form):
    xlsx_file = forms.FileField(
        label="Archivo Excel (.xlsx)",
        help_text="Columnas requeridas: name, email. Opcionales: area, location",
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "area", "location", "last_received_at", "created_at")
    list_filter = ("area", "location")
    search_fields = ("name", "email", "area__name", "location__name")
    ordering = ("name",)
    change_list_template = "admin/companies/company/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("import-xlsx/", self.admin_site.admin_view(self.import_xlsx_view), name="companies_company_import_xlsx"),
        ]
        return custom + urls

    def import_xlsx_view(self, request):
        if request.method == "POST":
            form = XlsxImportForm(request.POST, request.FILES)
            if form.is_valid():
                created, updated, errors = import_companies_from_xlsx(request.FILES["xlsx_file"])
                if errors:
                    for err in errors[:10]:
                        messages.warning(request, err)
                messages.success(request, f"Importación completada: {created} creadas, {updated} actualizadas.")
                return redirect("..")
        else:
            form = XlsxImportForm()

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "title": "Importar empresas desde Excel",
        }
        return render(request, "admin/companies/import_xlsx.html", context)


@admin.register(Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ("email", "reason", "added_at")
    search_fields = ("email",)
    list_filter = ("reason",)
    ordering = ("-added_at",)
