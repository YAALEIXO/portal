from django.contrib import admin

from bi_links.models import LinkBI

from .models import Setor


class LinkBIInline(admin.TabularInline):
    model = LinkBI
    fields = ("nome", "url", "ativo")
    extra = 1


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa")
    list_filter = ("empresa",)
    search_fields = ("nome", "empresa__nome")
    inlines = [LinkBIInline]

    def save_formset(self, request, form, formset, change):
        if formset.model is LinkBI:
            instances = formset.save(commit=False)
            for obj in instances:
                if not obj.pk:
                    obj.criado_por = request.user
                obj.save()
            formset.save_m2m()
        else:
            formset.save()
