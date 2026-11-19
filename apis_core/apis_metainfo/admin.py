from django.contrib import admin

from .models import Collection, MergeLog, Source, Text, Uri

admin.site.register(Source)
admin.site.register(Collection)
admin.site.register(Text)
admin.site.register(Uri)


@admin.register(MergeLog)
class MergeLogAdmin(admin.ModelAdmin):
    list_display = [
        "source_name",
        "source_pk",
        "target_pk",
        "source_model",
        "created",
        "user",
        "undone_at",
    ]
    list_filter = ["source_model"]
    search_fields = ["source_name", "source_pk", "target_pk"]
    readonly_fields = [
        "target",
        "target_pk",
        "source_pk",
        "source_model",
        "source_name",
        "data",
        "created",
        "user",
        "undone_at",
        "undone_by",
    ]
