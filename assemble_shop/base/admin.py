from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    list_per_page = 10

    def save_model(self, request, obj, form, change) -> None:
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
